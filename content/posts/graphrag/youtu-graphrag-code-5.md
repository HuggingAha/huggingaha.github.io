---
title: "Youtu-GraphRAG 源码：Agentic 分解与 IRCoT 迭代推理"
date: 2025-12-26T09:50:00+08:00
description: "解析 Agentic 分解与 IRCoT 迭代推理：用「检索-思考-再检索」循环逐步逼近多跳问题的答案。"
categories: ["notes"]
topics: ["graphrag"]
tags: ["rag", "knowledge-graph"]
series: ["youtu-graphrag"]
series_order: 6
showAuthor: false
aliases: ["/blogs/rag/youtu-graphrag-code-5/"]
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


<!-- # Youtu-GraphRAG 源码深度解读 (5)：Agentic 分解与 IRCoT 迭代推理 -->

## 1. 引言

在 RAG 系统中，面对“谁是电影《X》导演的父亲？”这类多跳问题（Multi-hop Question），简单的向量检索往往失效，因为向量空间难以捕捉多重关系的逻辑链路。

`youtu-graphrag` 引入了 **Agentic RAG** 的范式来解决这一难题。它不再试图一次性检索出所有答案，而是模仿人类专家的解题思路：先将大问题拆解为小问题，然后通过“检索-思考-再检索”的循环逐步逼近答案。这一过程被称为 **IRCoT (Iterative Retrieval Chain of Thought)**。

## 2. 战略层：GraphQ 问题分解器

推理的第一步并非直接检索，而是降维。`GraphQ` 模块负责利用图 Schema 将复杂的自然语言问题转化为“图可解”的原子子问题。

### 2.1 Schema 感知的分解 (Schema-Aware Decomposition)
在 `models/retriever/agentic_decomposer.py` 中，`decompose` 方法调用 LLM 进行拆解。与普通分解不同，Prompt 中显式注入了图的 Ontology（本体论/Schema）。

```python
# Prompt 核心指令 (config/base_config.yaml)
"""
Given the following ontology and the question, decompose the complex question...
CRITICAL REQUIREMENTS:
1. Each sub-question must be... Explicitly reference entities and relations...
2. Identify all schema types that might be involved
"""
```

这种设计迫使 LLM 在分解时“戴着镣铐跳舞”，确保生成的子问题中的术语（如关系谓词）尽可能与图谱中的定义对齐，从而提高后续检索的命中率。

### 2.2 类型预判与搜索空间剪枝
`GraphQ` 的另一个重要产出是 `involved_types`。LLM 会预测回答该问题可能涉及的节点类型（如 `person`）、关系类型（如 `directed_by`）和属性。

在后续的 `KTRetriever` 检索中，这些类型信息充当了**预过滤器**。如果 LLM 预测只涉及“人物”和“电影”，检索器就可以直接忽略“地点”或“组织”类型的节点。这种机制在数百万节点的大规模图谱中，对于降低检索噪声、提升信噪比具有重要的工程价值。

## 3. 执行层：Map-Reduce 并行检索

分解得到的子问题（`sub_questions`）通常是相互独立的简单事实查询。`main.py` 中的 `initial_question_decomposition` 实现了类似 Map-Reduce 的处理逻辑：

1.  **Map (并行执行):** 系统检测到多个子问题后，会调用 `kt_retriever.process_subquestions_parallel`。这利用了 Python 的 `ThreadPoolExecutor` 并发地对每个子问题执行检索。
2.  **Reduce (结果聚合):** 所有子问题的检索结果（三元组和文本块）被汇总到一个集合中。

```python
# main.py

if len(sub_questions) > 1:
    logger.info("🚀 Using parallel sub-question processing...")
    aggregated_results, _ = kt_retriever.process_subquestions_parallel(...)
    all_triples.update(aggregated_results['triples'])
```

这一设计显著降低了首轮检索的延迟。然而，并行度受限于 LLM API 的速率限制（Rate Limit）和 Embedding 模型的并发吞吐能力，在实际部署时通常需要配置 token 桶等限流机制。

## 4. 核心大脑：IRCoT 迭代推理循环

对于逻辑依赖性强的问题（例如：先查出A是谁，再查A做了什么），并行检索无法解决。这时系统进入 **IRCoT** 模式。

### 4.1 状态机设计
`agent_retrieval` 函数（位于 `main.py`）维护了一个基于 LLM 的状态机循环。循环的驱动力来自于 Prompt 的特殊指令：

> "If you have enough information... write **'So the answer is:'**..."
> "If you need more information... write **'The new query is:'**..."

### 4.2 动态上下文累积
在每一轮迭代（Step）中，系统执行以下操作：
1.  **构建上下文:** 将当前累积的所有三元组（Triples）和文本块（Chunks）拼接成 Context。
2.  **LLM 决策:** LLM 阅读 Context 和历史思维链（Thoughts），决定是输出答案还是发起新查询。
3.  **动态检索:** 如果发起新查询，`KTRetriever` 会针对这个*新生成的问题*执行检索。
4.  **知识更新:** 新检索到的知识被合并入 `all_triples` 和 `all_chunk_ids` 集合中。

```python
# main.py (Agent Loop)

while step <= max_steps:
    # ... Prompt Construction ...
    response = kt_retriever.generate_answer(ircot_prompt)
    
    if "So the answer is:" in response:
        break # 终止条件
        
    if "The new query is:" in response:
        new_query = ...
        # 执行新一轮检索，更新知识库
        retrieval_results, _ = kt_retriever.process_retrieval_results(new_query, ...)
        all_triples.update(retrieval_results['triples'])
```

### 4.3 潜在风险分析
这种串行迭代机制虽然推理能力强大，但也带来了两个显著的工程挑战：
1.  **延迟叠加 (Latency Stacking):** 每一轮 Step 都包含一次 LLM 调用和一次检索操作。如果迭代 5 次，总耗时可能是单次 RAG 的 5-10 倍。
2.  **上下文溢出 (Context Overflow):** 随着知识不断累积 (`context += ...`)，Prompt 的长度单调增加。如果不引入动态的 Token 截断或相关性过滤机制，很容易在后期迭代中通过 Token Limit 导致崩溃。

## 5. 落地回归：Chunk 回溯 (Graph-to-Text)

虽然推理过程依赖于图谱（三元组），但最终生成答案时，系统并未抛弃原始文本。

在检索的每一阶段，系统都会通过节点属性中的 `chunk id` 回溯到原始文档片段，并使用 `_rerank_chunks_by_relevance` 对这些片段进行重排序。最终提供给 LLM 的上下文是 **“结构化骨架（图）+ 非结构化血肉（文本）”** 的混合体。这确保了生成的答案既有逻辑的严密性，又有原文的细节丰富度。

## 6. 总结

`youtu-graphrag` 的推理层展示了一个成熟的 Agentic 系统雏形。它通过 **GraphQ** 实现了复杂问题的降维，通过 **IRCoT** 实现了动态的路径规划。

从 Schema 的定义，到图谱的构建与演进，再到多粒度的存储与索引，最后到 Agent 的动态推理，`youtu-graphrag` 提供了一套完整的、垂直统一的解决方案。
