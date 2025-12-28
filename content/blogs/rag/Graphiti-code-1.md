---
title: "Graphiti：实体解析与增量摄入"
showAuthor: false
date: 2025-10-26
description: "实现知识图谱的增量更新（无需全量重建），并支持双时态（Bi-temporal）数据模型，能够追踪事实的“有效时间”和“失效时间”，从而处理事实冲突和演变。自动从非结构化文本/JSON 中提取实体和关系、处理实体消歧、基于图结构的混合检索（语义+关键词+图遍历）。"
slug: "graphiti-code-1"
tags: ["RAG", "KG"]
series: [Graphiti]
series_order: 2
draft: false
---

<!-- 渲染公式 -->
{{< katex >}}



{{< alert "github" >}}
[getzep/graphiti](https://github.com/getzep/graphiti.git)
{{< /alert >}}

<!-- # Graphiti (二)：实体解析与增量摄入 -->


构建知识图谱的核心挑战在于 **实体解析（Entity Resolution）**，即判断新提取的实体（如 "Apple"）是指向一个新的节点，还是与图中已存在的节点（如 "Apple Inc."）指代同一对象。在传统 ETL 流程中，这通常依赖于基于规则的算法（如 Levenshtein 距离）。然而，在增量式、非结构化的数据流中，传统的规则往往难以应对语义的多义性和上下文的依赖性。

Graphiti 在 `add_episode` 流程中实现了一套基于 **Embedding 召回** 与 **LLM 判决** 的两阶段去重机制。本文将依据源码，详细追踪数据从原始文本转化为图谱节点与边的完整路径，重点剖析其如何处理实体消歧与关系构建。

## 1. 增量摄入总线：`add_episode`

位于 `graphiti_core/graphiti.py` 的 `add_episode` 方法是写入路径的入口。它并非简单的线性流程，而是一个包含多次读写交互的闭环系统。

该方法的主要逻辑步骤如下：

1.  **上下文检索：** 调用 `retrieve_episodes` 获取历史 Episode，作为 LLM 理解当前文本的背景。
2.  **实体提取：** 调用 `extract_nodes` 从文本中识别实体。
3.  **实体解析与映射：** 调用 `resolve_extracted_nodes` 对新实体进行去重，并建立 UUID 映射表。
4.  **关系提取：** 调用 `extract_edges` 提取实体间的关系，并利用映射表修正 UUID 指针。
5.  **关系解析与冲突检测：** 调用 `resolve_extracted_edges` 处理边的去重和时序冲突。
6.  **持久化：** 调用 `add_nodes_and_edges_bulk` 将最终结果写入图数据库。

{{< mermaid >}}
flowchart TD
    Start([Input: Episode Content]) --> Context[Retrieve Previous Episodes]
    Context --> ExtractNodes["1. Extract Nodes (LLM)"]
    ExtractNodes --> ResolveNodes["2. Resolve Nodes (Hybrid Search + LLM)"]
    
    ResolveNodes -- UUID Mapping --> ExtractEdges["3. Extract Edges (LLM)"]
    
    ExtractEdges --> ResolveEdges[4. Resolve Edges & Conflict Check]
    ResolveEdges --> Persist[5. DB Persistence]
    
    subgraph Node_Resolution [节点解析逻辑]
        ResolveNodes --> Search[Search Candidates]
        Search --> DedupePrompt[LLM Deduplication]
        DedupePrompt --> Map[Build UUID Map]
    end
{{< /mermaid >}}


## 2. 实体解析的核心实现：`resolve_extracted_nodes`

实体解析逻辑封装在 `graphiti_core/utils/maintenance/node_operations.py` 中。这是一个典型的 RAG（检索增强生成）应用场景：先检索候选，再生成判断。

### 2.1 第一阶段：基于混合搜索的候选召回 (Recall)

对于每一个新提取的实体，Graphiti 并不会全表扫描，而是利用其搜索模块寻找相似的“候选旧实体”。

```python
# graphiti_core/utils/maintenance/node_operations.py

search_results: list[SearchResults] = await semaphore_gather(
    *[
        search(
            clients=clients,
            query=node.name,
            group_ids=[node.group_id],
            search_filter=SearchFilters(),
            config=NODE_HYBRID_SEARCH_RRF, # 使用 RRF 混合搜索配置
        )
        for node in extracted_nodes
    ]
)
```

这里使用了 `NODE_HYBRID_SEARCH_RRF` 配置（定义在 `search_config_recipes.py`），意味着它同时利用了：
*   **BM25 (全文检索):** 捕捉字面拼写相似性（如 "Graphiti" vs "Graphiti Core"）。
*   **Cosine Similarity (向量检索):** 捕捉语义相似性（如 "iPhone Maker" vs "Apple"）。

这种混合召回策略有效地平衡了精确匹配和模糊语义匹配，大大缩小了后续 LLM 需要判断的范围。

### 2.2 第二阶段：基于 LLM 的语义判决 (Adjudication)

召回候选集后，Graphiti 将“新实体列表”和“候选旧实体列表”一并送入 LLM 进行裁决。

**Prompt:** 位于 `graphiti_core/prompts/dedupe_nodes.py` 的 `nodes` 函数。

```python
# Prompt 结构摘要
content = f"""
<PREVIOUS MESSAGES>...<CURRENT MESSAGE>... # 上下文

<ENTITIES> # 新提取的实体
...
<EXISTING ENTITIES> # 搜索召回的候选旧实体
...

Task:
For each entity, return... the duplicate_idx as an integer.
- If an entity is a duplicate..., return the idx of the candidate it is a duplicate of.
- If an entity is not a duplicate..., return -1.
"""
```

**关键指令分析：**
Prompt 中明确指示 LLM 依据“语义等价性（Semantic Equivalence）”进行判断，即它们是否指代现实世界中的同一个对象。上下文（Messages）在这里起到了至关重要的消歧作用。例如，如果文中提到 "Java" 且上下文是地理，LLM 应当避免将其与编程语言 "Java" 节点合并。

### 2.3 第三阶段：UUID 映射与修正

LLM 返回的结果被解析为 `NodeResolutions` 对象。代码随即构建一个 `uuid_map` 字典。

```python
resolved_nodes = []
uuid_map = {} # {新实体临时UUID: 旧实体真实UUID}

for resolution in node_resolutions:
    # ...
    if resolution.duplicate_idx != -1:
        # 判定为重复：使用旧节点
        resolved_node = existing_nodes[resolution.duplicate_idx]
        uuid_map[extracted_node.uuid] = resolved_node.uuid
    else:
        # 判定为新实体：使用新节点
        resolved_node = extracted_node
    # ...
```

这个 `uuid_map` 是后续步骤的关键。在提取边（Edge）时，LLM 输出的是基于新实体的临时 UUID。`extract_edges` 完成后，系统会立即使用 `uuid_map` 将边两端的节点 ID 替换为图谱中最终确认的真实 UUID。这确保了新提取的关系能够正确地“挂载”到现有的图谱结构上。


## 3. 关系提取与处理：`extract_edges` 与 `resolve_extracted_edges`

边的处理逻辑与节点类似，但在去重之外增加了更复杂的逻辑。

### 3.1 关系提取 (Edge Extraction)
`graphiti_core/utils/maintenance/edge_operations.py` 中的 `extract_edges` 函数负责从文本中提取三元组。

值得注意的是，Graphiti 支持**自定义 Schema**。`add_episode` 允许传入 `edge_types` 和 `edge_type_map` 参数。这些定义会被注入到 Prompt 中，引导 LLM 提取特定类型的关系（如 `WORKS_FOR`, `IS_LOCATED_IN`）。

### 3.2 关系去重与 Embedding 过滤
与节点去重不同，边的去重逻辑更加依赖向量相似度。在 `resolve_extracted_edges` 中：

1.  **Scope 限制：** 仅检索连接相同 Source 和 Target 节点的边。
2.  **Embedding 计算：** 对新边的 `fact` 文本（如 "Alice works at Google"）计算 Embedding。
3.  **相似度过滤：** 计算新边与候选边的 Cosine Similarity。只有相似度超过阈值（默认 0.6）的边才会被视为潜在重复项送入 LLM。

这种预过滤机制（`dedupe_edges_bulk` 中也有体现）显著减少了 LLM 的 Context 长度，因为边的描述文本通常比实体名称长得多，全部送入 LLM 成本过高。


## 4. 批量模式下的优化 (Bulk Optimization)

在 `graphiti_core/utils/bulk_utils.py` 中，针对 `add_episode_bulk` 场景，Graphiti 引入了额外的优化策略以应对大量数据的同时摄入。

### 4.1 内存中去重 (In-Memory Deduplication)
在批量处理时，新的一批数据内部可能存在大量重复（例如多个 Episode 都提到了 "Elon Musk"）。Graphiti 首先在内存中对这一批新提取的节点进行相互比对。

为了提高效率，这里引入了一个基于规则的快速筛选层：
```python
# 近似 BM25：基于词重叠 (Word Overlap)
node_words = set(node.name.lower().split())
existing_node_words = set(existing_node.name.lower().split())
has_overlap = not node_words.isdisjoint(existing_node_words)
```
只有当词重叠检测失败时，才回退到向量相似度计算。这种分层过滤策略在大规模数据处理中能有效降低计算开销。

### 4.2 并查集 (Union-Find) 的应用
为了处理复杂的传递性重复关系（例如 A=B, B=C，则 A=C），代码中实现了 `UnionFind` 类和 `compress_uuid_map` 函数。这确保了在一个批次内，无论实体出现的顺序如何，所有指向同一对象的引用最终都会被统一映射到同一个规范 UUID 上。

## 5. 实现分析

### 5.1 串行依赖导致的延迟
从代码流程来看，`resolve_extracted_nodes`（节点解析）必须在 `extract_edges`（关系提取）之前完成，因为关系提取依赖于节点解析生成的 `uuid_map` 来修正指针。而 `resolve_extracted_edges`（关系解析）又必须在关系提取之后进行。

这种**强串行依赖**（Node Extract -> Node Resolve -> Edge Extract -> Edge Resolve）导致了处理单个 Episode 的端到端延迟较高。虽然代码在每一层内部使用了 `semaphore_gather` 进行并发处理（例如并发搜索多个实体的候选），但层与层之间无法流水线化。

### 5.2 对 LLM 语义判断的依赖
系统的去重准确率高度依赖 LLM 在 `dedupe_nodes` Prompt 下的表现。源码中并未包含对 LLM 判决置信度的检查机制。如果 LLM 产生幻觉或误判（例如将 "Java Island" 误判为 "Java Language"），这种错误将被永久写入图谱数据库，且后续很难通过自动化手段发现和修复。

## 总结

Graphiti 的构建过程是一个 **AI Native** 工作流。它并没有试图用传统的确定性算法解决模糊的实体解析问题，而是通过 Search + LLM 的组合，将这一难题转化为一个语义理解任务。虽然这带来了较高的延迟和 Token 成本，但却赋予了系统处理非结构化、语义模糊数据的强大能力，这是构建高质量 Agent 记忆体的关键基础。
