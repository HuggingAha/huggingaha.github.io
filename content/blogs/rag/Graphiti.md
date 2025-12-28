---
title: "Graphiti：全貌与架构 —— 为什么 RAG 还不够？"
showAuthor: false
date: 2025-10-26
description: "实现知识图谱的增量更新（无需全量重建），并支持双时态（Bi-temporal）数据模型，能够追踪事实的“有效时间”和“失效时间”，从而处理事实冲突和演变。自动从非结构化文本/JSON 中提取实体和关系、处理实体消歧、基于图结构的混合检索（语义+关键词+图遍历）。"
slug: "graphiti"
tags: ["RAG", "KG"]
series: [Graphiti]
series_order: 1
draft: false
---

<!-- 渲染公式 -->
{{< katex >}}


<!-- # Graphiti (一)：全貌与架构 —— 为什么 RAG 还不够？ -->

{{< alert "github" >}}
[getzep/graphiti](https://github.com/getzep/graphiti.git)
{{< /alert >}}

在构建智能 Agent 的过程中，"记忆（Memory）"一直是一个核心且棘手的工程挑战。传统的 RAG（Retrieval-Augmented Generation）技术栈——即将文档切片、向量化并存入向量数据库——虽然解决了静态知识的检索问题，但在面对动态、演进的世界状态时往往显得力不从心。例如，当用户昨天说“我住在纽约”，今天说“我搬到了旧金山”时，传统 RAG 可能会同时检索到这两条冲突的信息，却无法告知 Agent 哪条才是当前的真实状态。

**Graphiti** 是一个旨在解决此类问题的开源框架。它定位于一个 **动态的、时序感知的知识图谱引擎**。作为系列博文的第一篇，下面将从宏观视角剖析 Graphiti 的核心概念、分层架构以及它如何试图通过工程手段解决动态知识管理难题。

## 核心概念：从文档到情节 (From Documents to Episodes)

Graphiti 与传统知识库最大的区别在于其数据模型的设计。它不以“文档（Document）”为中心，而是引入了 **“情节（Episode）”** 作为最基础的数据摄入单元。

### 1. Episodic Memory（情景记忆）
在源码 `graphiti_core/nodes.py` 中，`EpisodicNode` 被定义为图谱中的一种特殊节点。它不仅存储原始数据（`content`），还记录了数据的来源类型（Message/JSON/Text）和发生时间（`valid_at`）。每一个被提取出的实体和事实，都会通过 `MENTIONS` 边回溯到其来源的 `EpisodicNode`。

这种设计使得 Graphiti 能够保留 **数据的上下文来源**。当图谱中的某个事实（Edge）被检索时，系统不仅知道“发生了什么”，还能追溯到“是基于哪次对话或哪个文件得知的”。

### 2. Bi-temporal Data Model（双时态数据模型）
Graphiti 试图解决的一个核心问题是 **事实的时效性**。在 `graphiti_core/edges.py` 的 `EntityEdge` 定义中，我们可以看到双时态设计的具体实现：

*   **System Time (系统时间):** `created_at` 和 `expired_at`。记录数据何时被写入数据库，以及何时被标记为过时（逻辑删除）。这是不可变的审计日志。
*   **Valid Time (有效时间):** `valid_at` 和 `invalid_at`。记录事实在现实世界中生效和失效的时间范围。

通过维护 `invalid_at`，Graphiti 能够处理事实的 **演变**。当新信息与旧信息冲突时（例如“居住地变更”），系统不会覆盖旧记录，而是更新旧记录的 `invalid_at`，从而维护了一条连续的历史时间线。

## 宏观架构解析

Graphiti 的架构可以清晰地划分为接口层、核心引擎层和基础设施层。

{{< mermaid >}}
graph TD
    User[Client / Agent] --> Interface_Layer
    
    subgraph Interface_Layer [接口层]
        MCP[MCP Server]
        API[FastAPI Server]
    end
    
    MCP --> Core[Graphiti Core Orchestrator]
    API --> Core
    
    subgraph Graphiti_Core [核心引擎 graphiti_core]
        Core --> Ingestion[增量摄入 Pipeline]
        Core --> Retrieval[混合检索引擎]
        
        Ingestion --> Extractor[实体/关系提取]
        Ingestion --> Temporal[时序冲突检测]
        Ingestion --> Dedupe[实体消歧与去重]
        
        Retrieval --> HybridSearch["混合搜索 (BM25 + Vector + BFS)"]
        Retrieval --> Reranker["重排序 (RRF / CrossEncoder)"]
    end
    
    subgraph Infrastructure [基础设施]
        LLM["LLM Client (OpenAI/Anthropic)"]
        DB["(Graph DB: Neo4j / FalkorDB)"]
    end
    
    Ingestion --> LLM
    Ingestion --> DB
    Retrieval --> DB
{{< /mermaid >}}


### 1. 接口层 (Interface Layer)
项目提供了两种对外的交互方式：
*   **REST API:** 基于 FastAPI 实现的标准 HTTP 服务，位于 `server/` 目录。
*   **MCP Server:** 位于 `mcp_server/` 目录。这是一个基于 **Model Context Protocol** 的实现，允许 Claude Desktop 或 Cursor 等支持 MCP 的客户端直接调用 Graphiti 的能力（如 `add_memory`, `search_nodes`）。这表明 Graphiti 的设计初衷就是作为 Agent 的“外挂大脑”。

### 2. 核心引擎 (Graphiti Core)
这是逻辑最密集的部分，位于 `graphiti_core/`。它主要包含两条路径：

*   **写入路径 (Write Path):** 由 `graphiti.py` 中的 `add_episode` 方法编排。这是一个重度依赖 LLM 的流程。它不只是简单的写入，而是包含了一个 **“读取-比对-写入”** 的闭环：
    1.  从文本中提取实体和关系。
    2.  利用 Embedding 检索图谱中已存在的相似实体（Entity Resolution）。
    3.  利用 LLM 判断新旧实体是否为同一对象（去重）。
    4.  检测新事实是否与旧事实在语义上冲突，并据此更新时间戳。

    这种设计虽然保证了图谱的质量和一致性，但也带来了显著的性能开销。每次写入都需要多次 LLM 调用和数据库查询，使其成为一个 IO 密集型操作。

*   **读取路径 (Read Path):** 由 `search/` 模块负责。Graphiti 实现了一个复杂的混合检索策略。它不仅仅是向量搜索，还结合了全文检索（BM25）和图遍历（BFS）。
    *   **Configurable Strategy:** 通过 `SearchConfig` 对象，开发者可以灵活配置检索策略。
    *   **Reranking:** 支持 RRF（倒数排名融合）和 Cross-Encoder 等重排序算法，以在多路召回的结果中筛选出最相关的内容。

### 3. 基础设施层 (Infrastructure Layer)
Graphiti 采用了适配器模式来隔离底层依赖：
*   **GraphDriver:** 在 `driver/` 目录中，通过 `GraphDriver` 抽象基类屏蔽了 Neo4j 和 FalkorDB 的语法差异（如向量索引的创建和查询语法）。
*   **LLMClient:** 支持 OpenAI, Anthropic, Gemini 等多种模型提供商。

## 关键流程概览

### 增量构建 (Incremental Building)
Graphiti 的核心价值在于“增量”。不同于 GraphRAG 等需要全量文档构建索引的方案，Graphiti 旨在处理流式数据。当 `add_episode` 被调用时，它只处理当前片段，并尝试将其“编织”进现有的图谱网络中。这种编织过程依赖于复杂的实体解析算法，我们将在后续博文中详细分析。

### 混合检索 (Hybrid Retrieval)
在检索方面，Graphiti 并不迷信向量。源码显示，它在搜索边（Edge）时，会同时发起全文本检索（匹配关键词）、向量检索（匹配语义）和广度优先搜索（匹配拓扑结构）。这种多路召回策略旨在解决向量检索在处理精确匹配（如人名）时的精度问题，以及利用图谱特有的结构信息。

## 总结

Graphiti 试图用自动化的手段解决知识图谱构建中最繁琐的实体对齐和时序维护问题。然而，这种自动化是有代价的：它对 LLM 的推理能力和 Token 消耗有很高的依赖，且随着图谱规模的增长，冲突检测和去重的计算成本也会增加。
