---
title: "Graphiti：双时态逻辑与冲突处理"
showAuthor: false
date: 2025-10-26
description: "实现知识图谱的增量更新（无需全量重建），并支持双时态（Bi-temporal）数据模型，能够追踪事实的“有效时间”和“失效时间”，从而处理事实冲突和演变。自动从非结构化文本/JSON 中提取实体和关系、处理实体消歧、基于图结构的混合检索（语义+关键词+图遍历）。"
slug: "graphiti-code-2"
tags: ["RAG", "KG"]
series: [Graphiti]
series_order: 3
draft: false
---

<!-- 渲染公式 -->
{{< katex >}}



{{< alert "github" >}}
[getzep/graphiti](https://github.com/getzep/graphiti.git)
{{< /alert >}}


<!-- # Graphiti 源码：双时间逻辑与冲突处理 -->

## 引言

在现实世界中，信息往往是流动的。“现任美国总统是拜登”这句话在 2024 年是事实，但在 2025 年可能就不再是了。传统的知识图谱或向量数据库通常只存储“当前状态”，对于过往的历史信息往往直接覆盖或丢弃。这种“健忘”的设计使得 AI Agent 难以理解世界的演变过程。

Graphiti 最具创新性的设计之一，就是内置了对 **时间** 的“一等公民”支持。它实现了一个 **双时态（Bi-temporal）** 数据模型，并结合 LLM 的语义理解能力，构建了一套自动化的冲突检测与状态演变机制。本文将深入源码，剖析 Graphiti 是如何用代码捕捉“时间”的。

## 1. 双时态数据模型：Valid Time vs System Time

在 `graphiti_core/edges.py` 的 `EntityEdge` 类定义中，我们看到了四个与时间相关的字段。这并非冗余设计，而是为了实现双时态逻辑的标准范式。

### 1.1 有效时间 (Valid Time)
*   **`valid_at` (生效时间):** 事实在现实世界中开始成立的时间。
*   **`invalid_at` (失效时间):** 事实在现实世界中停止成立的时间。

这两个字段定义了事实的 **生命周期**。例如，用户说“我 2020 年搬到了上海，2022 年离开了”，那么这条“居住在上海”的边，其 `valid_at` 为 2020，`invalid_at` 为 2022。如果 `invalid_at` 为 `None`，则表示该事实当前仍然有效（Present）。

### 1.2 系统时间 (System Time)
*   **`created_at` (创建时间):** 这条记录被写入数据库的时间。
*   **`expired_at` (过期时间):** 这条记录被系统标记为“逻辑删除”或“被修正”的时间。

这两个字段服务于 **审计与版本控制**。它们记录了系统对世界认知变化的过程。


## 2. 自动化时间提取

Graphiti 不仅被动接收时间，还会主动从文本中提取时间信息。这一逻辑封装在 `graphiti_core/utils/maintenance/temporal_operations.py` 的 `extract_edge_dates` 函数中。

### 2.1 相对时间解析
LLM Prompt (`prompts/extract_edge_dates.py`) 接收了一个关键参数：`reference_timestamp`（通常是 Episode 的发生时间）。Prompt 被明确指示：
> "Use the reference timestamp as the current time when determining the valid_at and invalid_at dates."

这意味着如果用户说“我**去年**入职的”，LLM 会结合 `reference_timestamp` 计算出具体的年份并填充 `valid_at`。

### 2.2 代码实现细节
源码中使用了 `ensure_utc` 辅助函数（位于 `utils/datetime_utils.py`），强制将所有提取出的时间转换为 UTC 时区。这是一个容易被忽视但至关重要的工程细节，它避免了跨时区部署时的时间线混乱。

```python
# graphiti_core/utils/datetime_utils.py
def ensure_utc(dt: datetime | None) -> datetime | None:
    if dt is None: return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    # ...
```

## 3. 冲突检测与状态演变

当新事实进入系统时，最复杂的问题出现了：**新事实是否与旧事实冲突？** 如果冲突，系统该如何演变？

这一核心逻辑由 `resolve_extracted_edge` 函数（`edge_operations.py`）编排。

### 3.1 第一步：候选者筛选 (Candidate Selection)
系统首先需要找到“可能”冲突的旧边。显然，检查全图是不现实的。Graphiti 使用 `get_edge_invalidation_candidates` 函数（`search_utils.py`）进行高效筛选：

1.  **拓扑约束:** 只查找连接**相同** Source 和 Target 实体的边。
2.  **语义约束:** 计算新边与旧边的 Embedding 相似度，只保留语义相关的边。

### 3.2 第二步：LLM 语义判决 (Semantic Adjudication)
筛选出的候选边被送入 LLM，进行纯逻辑层面的矛盾判断。

**Prompt (`prompts/invalidate_edges.py`):**
```text
Based on the provided EXISTING FACTS and a NEW FACT, determine which existing facts the new fact contradicts.
```

LLM 不需要关心时间，只关心逻辑。例如：
*   事实 A: "Alice likes Bob"
*   事实 B: "Alice hates Bob"
*   **判定:** 冲突。

*   事实 A: "Alice lives in NY"
*   事实 B: "Alice works in NY"
*   **判定:** 不冲突（兼容）。

### 3.3 第三步：时序逻辑解析 (Temporal Resolution)
一旦 LLM 确认了语义冲突，`resolve_edge_contradictions` 函数（`edge_operations.py`）就会接管，根据时间戳执行确定性的更新逻辑。

```python
# graphiti_core/utils/maintenance/edge_operations.py

def resolve_edge_contradictions(resolved_edge, invalidation_candidates):
    invalidated_edges = []
    for edge in invalidation_candidates:
        # Case: 新事实 (resolved_edge) 在时间上覆盖了旧事实 (edge)
        if (edge.valid_at < resolved_edge.valid_at):
            # 关键操作：将旧边的失效时间 (invalid_at) 设为新边的生效时间
            edge.invalid_at = resolved_edge.valid_at
            
            # 标记旧记录被修改的时间
            edge.expired_at = utc_now()
            
            invalidated_edges.append(edge)
    return invalidated_edges
```

**场景推演：**
1.  **T1:** 系统记录 `(Alice)-[LIVES_IN]->(NY)`，`valid_at=2020`。
2.  **T2:** 用户输入 "Alice moved to SF in 2023"。
3.  **冲突检测:** LLM 判定 "LIVES_IN NY" 与 "LIVES_IN SF" 语义冲突。
4.  **状态更新:**
    *   旧边 (NY) 被更新：`invalid_at` 设为 2023。
    *   新边 (SF) 被写入：`valid_at` 设为 2023，`invalid_at` 为空。

结果是，Graphiti 自动维护了一条连续的时间线：2020-2023 在 NY，2023 至今在 SF。

## 4. 逻辑流转图

下图展示了从新事实提取到旧事实失效的完整逻辑分支：

{{< mermaid >}}
graph TD
    NewEdge[新提取的边] --> FindCandidates[搜索: 连接相同节点的旧边]
    FindCandidates --> VectorFilter[过滤: 语义相似度筛选]
    VectorFilter --> LLM[LLM 判断: 是否存在逻辑矛盾?]
    
    LLM -- 无矛盾 --> SaveNew[仅保存新边]
    LLM -- 有矛盾 --> TimeCheck{时间检查}
    
    TimeCheck -- 新边时间 > 旧边时间 --> Invalidate[更新旧边: invalid_at = 新边.valid_at]
    Invalidate --> SaveBoth[保存新边 + 更新旧边]
    
    TimeCheck -- 新边时间 < 旧边时间 --> Ignore["忽略新边 (或标记为历史补充)"]
    
    SaveBoth --> DB[(Graph Database)]
{{< /mermaid >}}

## 5. 实现分析

### 5.1 软删除与全量历史
Graphiti 的设计哲学是“永不遗忘”。通过 `invalid_at` 标记，旧事实依然存在于数据库中。这虽然支持了强大的历史查询，但也带来了一个显著的工程挑战：**数据膨胀**。随着时间推移，数据库中可能充斥着大量已失效的历史数据。目前的源码中尚未包含自动化的归档（Archiving）或生命周期管理（TTL）机制，这在长期使用中可能需要额外的维护脚本。

### 5.2 对 LLM 判决的依赖
整个时序逻辑的基石是 LLM 对“语义冲突”的判断。这是一个非确定性的环节。如果 LLM 误判（例如认为“喜欢苹果公司”和“喜欢吃苹果”冲突），系统可能会错误地将有效事实标记为失效。Prompt Engineering 在这里起到了决定性作用。

## 总结

Graphiti 通过双时态模型和 LLM 辅助的冲突检测，成功地将时间维度引入了知识图谱。它不再是一个静态的事实库，而是一个能够理解“变化”的动态系统。这种能力对于构建能够长期陪伴用户、理解用户状态演变的 AI Agent 至关重要。
