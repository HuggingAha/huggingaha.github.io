---
title: "Graphiti：混合检索与重排序策略"
showAuthor: false
date: 2025-10-26
description: "实现知识图谱的增量更新（无需全量重建），并支持双时态（Bi-temporal）数据模型，能够追踪事实的“有效时间”和“失效时间”，从而处理事实冲突和演变。自动从非结构化文本/JSON 中提取实体和关系、处理实体消歧、基于图结构的混合检索（语义+关键词+图遍历）。"
slug: "graphiti-code-3"
tags: ["RAG", "KG"]
series: [Graphiti]
series_order: 4
draft: false
---

<!-- 渲染公式 -->
{{< katex >}}



{{< alert "github" >}}
[getzep/graphiti](https://github.com/getzep/graphiti.git)
{{< /alert >}}


<!-- # Graphiti：神经中枢 —— 混合检索与重排序策略 -->

## 引言

在构建了包含双时态信息的知识图谱后，下一个核心问题是：**如何从中检索出对 AI Agent 有用的信息？** 简单的关键词匹配（Full-text Search）在面对语义模糊的查询时往往力不从心，而单纯的向量检索（Vector Search）又容易丢失图谱的结构信息。

Graphiti 的检索模块（Search Module）是其架构中的“神经中枢”。它实现了一个高度模块化、策略驱动的混合检索管道，将 BM25、向量相似度、图遍历（BFS）以及多种重排序（Reranking）算法有机结合。本文将深入 `graphiti_core/search/` 目录，分析其实现逻辑。

## 1. 策略模式：灵活的 `SearchConfig`

Graphiti 并没有硬编码单一的搜索逻辑，而是采用了 **策略模式（Strategy Pattern）**。每一次搜索请求都由一个 `SearchConfig` 对象驱动，它定义了“用什么方法搜”以及“如何排序结果”。

在 `graphiti_core/search/search_config.py` 中：

```python
class SearchConfig(BaseModel):
    edge_config: EdgeSearchConfig | None
    node_config: NodeSearchConfig | None
    # ...
    
class EdgeSearchConfig(BaseModel):
    search_methods: list[EdgeSearchMethod] # [bm25, cosine_similarity, bfs]
    reranker: EdgeReranker # [rrf, mmr, cross_encoder, node_distance]
```

开发者可以根据场景选择预定义的“配方”。例如，`search_config_recipes.py` 中定义的 `EDGE_HYBRID_SEARCH_NODE_DISTANCE` 专门用于“查找与特定节点最相关的边”，而 `COMBINED_HYBRID_SEARCH_CROSS_ENCODER` 则侧重于通过重排序模型获取最高精度的结果。


## 2. 并行执行与多路召回

主入口 `search()` 函数位于 `graphiti_core/search/search.py`。它的实现极具并发性，利用 `semaphore_gather` 同时在 Edge, Node, Episode, Community 四个维度发起搜索。

以 `edge_search` 为例，它实现了**多路召回（Multi-way Retrieval）**：

1.  **全文检索 (BM25):** `edge_fulltext_search`
    *   **原理:** 利用 Neo4j/FalkorDB 的全文索引，匹配关键词。
    *   **作用:** 捕获精确匹配（如人名、特定术语）。
2.  **向量相似度 (Cosine):** `edge_similarity_search`
    *   **原理:** 计算 Query Vector 与 `fact_embedding` 的余弦相似度。
    *   **作用:** 捕获语义相关性（如搜“职业”匹配到“工程师”）。
3.  **图遍历 (BFS):** `edge_bfs_search`
    *   **原理:** 如果指定了 `bfs_origin_node_uuids`，则从这些节点出发，进行 N 跳（默认3跳）的广度优先搜索。
    *   **作用:** 捕获拓扑相关性（如“朋友的朋友”），这是传统 RAG 无法做到的。

这些搜索方法并行执行，最终汇总为一个候选集（Candidates Pool），等待重排序。


## 3. 重排序算法详解 (Rerankers)

召回只是第一步，如何从成百上千个候选结果中挑出最相关的 Top-K？Graphiti 实现了四种重排序策略。

### 3.1 RRF (Reciprocal Rank Fusion)
*   **代码:** `graphiti_core/search/search_utils.py` -> `rrf`
*   **逻辑:** 不依赖具体的分数，只依赖排名位置。公式为 `1 / (rank + k)`。
*   **优势:** 鲁棒性强，无需额外模型调用，是默认且最高效的选择。

### 3.2 MMR (Maximal Marginal Relevance)
*   **代码:** `graphiti_core/search/search_utils.py` -> `maximal_marginal_relevance`
*   **逻辑:** 这是一个纯 NumPy 实现。它在“与查询的相关性”和“与已选结果的多样性”之间进行权衡。
*   **优势:** 避免返回大量重复信息。
*   **性能隐忧:** 该实现需要将所有候选结果的 Embedding 加载到内存中构建相似度矩阵。在大规模候选集下，内存压力和计算开销不容忽视。

### 3.3 Node Distance (图距离重排序)
*   **代码:** `graphiti_core/search/search_utils.py` -> `node_distance_reranker`
*   **逻辑:** 这是一种 **图特有** 的算法。它执行 Cypher 最短路径查询，优先返回那些在拓扑结构上距离 `center_node` 更近的事实。
*   **场景:** 当 Agent 聚焦于某个特定实体（如“分析 Alice 的社交圈”）时，此策略效果极佳。

### 3.4 Cross-Encoder (交叉编码器)
*   **代码:** `graphiti_core/cross_encoder/`
*   **逻辑:** 将 Query 和 Fact 拼接，送入模型直接打分。`GeminiRerankerClient` 是直接使用 Gemini 模型来打分，`BGERerankerClient` 使用专门的 Reranker 模型来打分。
*   **OpenAI 实现的 Hack:** Graphiti 的 `OpenAIRerankerClient` 有一个实现细节。它并没有使用专门的 Rerank API，而是构造了一个 Prompt 让 GPT-4o-mini 判断 `True/False`，并利用 **Logprobs**（对数概率）来计算置信度分数。
    ```python
    # 伪代码
    logit_bias={'True_Token_ID': 1, 'False_Token_ID': 1}
    logprobs = await client.chat.completions.create(..., logprobs=True)
    score = np.exp(logprobs[0].logprob) # 将对数概率转为 0-1 分数
    ```
    这种做法虽然巧妙利用了生成式模型的能力，但相比专用 Rerank 模型（如 BGE, Cohere），在延迟和成本上通常更高。


## 4. 搜索流程全景图

{{< mermaid >}}
graph TD
    Query[User Query] --> Embed[生成 Query Vector]
    
    subgraph Multi-way_Retrieval [多路召回]
        Embed --> BM25[BM25 Search]
        Embed --> Vector[Vector Search]
        Embed --> BFS[BFS Graph Traversal]
    end
    
    BM25 --> Candidates[候选集池]
    Vector --> Candidates
    BFS --> Candidates
    
    subgraph Reranking_Strategy [重排序策略]
        Candidates --> RRF[RRF Fusion]
        Candidates --> MMR[MMR Diversity]
        Candidates --> NodeDist[Node Distance]
        Candidates --> CrossEnc[Cross-Encoder]
    end
    
    RRF -.-> Final[Top-K Results]
    MMR -.-> Final
    NodeDist -.-> Final
    CrossEnc -.-> Final
{{< /mermaid >}}


## 5. 实现分析

### 5.1 忠实于“图”的本质
Graphiti 的搜索不仅仅是 RAG 的“向量检索+”。它通过 `BFS` 和 `Node Distance Reranker` 真正利用了图的 **连接性**。这使得它不仅能回答“关于 X 的事实”，还能回答“与 X 相关联的事实”，这是其核心竞争力。

### 5.2 性能与成本的权衡
*   **Cross-Encoder:** 虽然精度最高，但其昂贵的 API（GeminiRerankerClient/OpenAIRerankerClient）调用成本（每一条候选边都要算一次）使其不适合作为初筛手段，只能用于最后的小范围精排。
*   **并发控制:** 为了应对多路搜索带来的并发压力，代码中广泛使用了 `semaphore_gather`。这是一种在应用层进行流控的必要手段，防止瞬间打满数据库连接池或触发 API Rate Limit。

## 总结

Graphiti 的检索模块展示了一个成熟的搜索系统应有的灵活性。它通过配置化将简单的搜索原语组合成复杂的检索策略，既保留了向量检索的语义优势，又引入了图特有的拓扑推理能力。
