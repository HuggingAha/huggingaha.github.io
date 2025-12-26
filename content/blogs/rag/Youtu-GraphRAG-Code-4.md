---
title: "Youtu-GraphRAG 源码：多粒度双路检索——Dual FAISS 索引与其物理存储设计"
showAuthor: false
date: 2025-12-26
description: ""
slug: "youtu-graphrag-code-4"
tags: ["GraphRAG"]
series: ["Youtu-GraphRAG"]
series_order: 5
draft: false
---

<!-- 渲染公式 -->
{{< katex >}}



{{< alert "github" >}}
[TencentCloudADP/Youtu-GraphRAG](https://github.com/TencentCloudADP/youtu-graphrag.git)
{{< /alert >}}


<!-- <figure>
  <img src="" alt="">
  <figcaption style="text-align: center;"></figcaption>
</figure> -->



<!-- # Youtu-GraphRAG 源码深度解读 (4)：多粒度双路检索——Dual FAISS 索引与其物理存储设计 -->

## 1. 引言

在传统的 RAG 系统中，检索通常意味着对文本块（Chunks）进行向量相似度搜索。然而，在 GraphRAG 语境下，单纯的文本检索会丢失图的拓扑信息。如何既利用向量的高效性，又保留图的结构性，是检索器设计的核心挑战。

`youtu-graphrag` 给出的答案是 **“多粒度索引” (Multi-Granularity Indexing)** 配合 **“双路检索” (Dual-Path Retrieval)**。系统并未止步于单一的节点索引，而是构建了四套独立的 FAISS 索引，并通过两条并行路径分别召回细节与全貌。

## 2. 四重索引机制

`DualFAISSRetriever` 在初始化阶段会构建四个独立的向量索引文件。这种设计显著增加了存储成本，但也极大地丰富了检索的语义维度。

### 2.1 索引类型与构建逻辑

1.  **Node Index (节点索引):**
    *   **内容:** `name + description`。
    *   **作用:** 传统的实体链接与召回。
2.  **Relation Index (关系索引):**
    *   **内容:** 边的类型名称（如 `directed_by`, `located_in`）。
    *   **作用:** 捕捉问题中的谓词语义（例如问“导演是谁”，能通过 `directed_by` 快速定位相关边）。
3.  **Triple Index (三元组索引):**
    *   **内容:** `HeadNodeText, Relation, TailNodeText` 组成的完整句子。
    *   **作用:** 这是最细粒度的索引。它将图的最小结构单元（边）文本化，使得检索器能直接匹配完整的语义事实，而不仅仅是单个实体。
4.  **Community Index (社区索引):**
    *   **内容:** 社区名称 + 社区摘要。
    *   **作用:** 响应宏观主题查询。

### 2.2 物理存储
代码显示，这些索引并非仅存在于内存，而是被持久化到 `retriever/faiss_cache_new/{dataset}/` 目录下。除了 `.index` 文件（FAISS 索引），系统还保存了 `.json` 映射文件（ID 到文本的映射）和 `.pt` 文件（PyTorch Tensor 格式的原始 Embedding），以支持后续的重排序计算。

## 3. 双路检索逻辑 (Dual-Path Logic)

检索的核心入口是 `dual_path_retrieval` 方法。它并非简单的线性执行，而是并行触发了两条路径，分别对应不同的检索意图。

### 3.1 Path 1: 基于三元组的微观检索 (`retrieve_via_triples`)
此路径旨在精准定位事实。
1.  **向量搜索:** 首先在 `Triple Index` 中查找 Top-K 相似的三元组。
2.  **拓扑扩展 (3-Hop Expansion):**
    这是该模块最激进的设计。在 `_process_triple_index` 方法中，系统不仅返回命中的三元组，还会调用 `_collect_neighbor_triples`，进而触发 `_get_3hop_neighbors`。
    *   **逻辑:** 以命中节点为中心，向外进行广度优先搜索（BFS），获取 3 跳范围内的所有邻居节点及其关联的三元组。
    *   **意图:** 试图通过图结构补充上下文，解决向量检索“只见树木不见森林”的问题。

  {{< alert >}}
  这种无限制的 3 跳扩展在稠密图中可能存在显著的性能风险。代码中的 `_get_3hop_neighbors` 使用队列进行 BFS，且未设置最大邻居数量限制（Limit/Top-K）。如果命中了一个度数极高的“超级节点”（Hub Node），待处理的三元组数量将呈指数级爆炸，可能导致检索延迟从毫秒级飙升至秒级甚至超时。在生产化改造时，此处必须引入基于度中心性的剪枝策略。
  {{< /alert >}}


3.  **重排序 (Reranking):** 扩展后的三元组集合可能包含大量噪声。系统随后调用 `_calculate_triple_relevance_scores`，计算 Query 与每个三元组文本的余弦相似度，并过滤掉低于阈值（默认 0.1）的结果。

### 3.2 Path 2: 基于社区的宏观检索 (`retrieve_via_communities`)
此路径旨在获取背景知识。
1.  **向量搜索:** 在 `Community Index` 中查找 Top-K 相似的社区。
2.  **成员展开:** 通过 `comm_map` 找到对应的社区 ID，进而检索该社区包含的所有成员实体 (`_get_community_nodes`)。
3.  **结果:** 返回一组与主题高度相关的节点集合，这些节点可能在微观路径中未被覆盖。

## 4. 缓存与性能优化

为了缓解 Embedding 和图遍历带来的计算压力，`DualFAISSRetriever` 实现了多层缓存：

*   **FAISS 搜索缓存:** `faiss_search_cache` 记录了 Query Embedding 哈希值对应的搜索结果，应对重复查询。
*   **节点 Embedding 缓存:** `node_embedding_cache` 存储了所有节点的向量表示。代码支持从 `.pt` (Torch) 或 `.npz` (Numpy) 加载，这显示了对不同运行环境的兼容性考量。
*   **GPU 加速:** 在 `_preload_faiss_indices` 中，代码检测 CUDA 环境。如果可用，会自动将 CPU 索引转移至 GPU (`faiss.index_cpu_to_gpu`)，这对大规模向量库的检索速度提升是决定性的。

## 5. 总结

`DualFAISSRetriever` 采用了 **"Recall broadly, Filter strictly" (广召回，严过滤)** 的设计哲学。

通过同时维护四套索引，它确保了无论是微观实体还是宏观社区都能被向量化；通过 3 跳邻居扩展，它利用图拓扑捕捉了向量空间难以表达的关联性。尽管其激进的扩展策略在稠密图场景下需要工程上的约束与剪枝，但这种**索引与拓扑深度耦合**的设计，正是 GraphRAG 区别于传统 RAG 的核心竞争力所在。
