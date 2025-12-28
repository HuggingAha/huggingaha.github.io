---
title: "Graphiti：驱动抽象与 MCP 服务"
showAuthor: false
date: 2025-10-26
description: "实现知识图谱的增量更新（无需全量重建），并支持双时态（Bi-temporal）数据模型，能够追踪事实的“有效时间”和“失效时间”，从而处理事实冲突和演变。自动从非结构化文本/JSON 中提取实体和关系、处理实体消歧、基于图结构的混合检索（语义+关键词+图遍历）。"
slug: "graphiti-code-4"
tags: ["RAG", "KG"]
series: [Graphiti]
series_order: 5
draft: false
---

<!-- 渲染公式 -->
{{< katex >}}



{{< alert "github" >}}
[getzep/graphiti](https://github.com/getzep/graphiti.git)
{{< /alert >}}


<!-- # Graphiti：连接世界 —— 驱动抽象与 MCP 服务 -->

## 引言

在前几篇文章中，介绍了 Graphiti 的核心引擎：如何构建图谱、维护时序逻辑以及执行混合检索。然而，一个优秀的开源项目不仅要有强大的内核，还需要有良好的 **扩展性** 和 **互操作性**。

Graphiti 在这方面做了两件关键的事情：
1.  **向内：** 通过驱动抽象层（Driver Abstraction）兼容多种图数据库。
2.  **向外：** 通过 MCP（Model Context Protocol）服务将能力标准化地暴露给 AI Agent。


## 1. 数据库驱动抽象：Open/Closed 原则的实践

Graphiti 目前支持 **Neo4j** 和 **FalkorDB** 两种后端。为了避免在上层业务逻辑中充斥着 `if db_type == 'neo4j': ...` 的判断，它设计了一个 `GraphDriver` 抽象层。

### 1.1 核心接口设计
在 `graphiti_core/driver/driver.py` 中，`GraphDriver` 定义了最小功能集：
```python
class GraphDriver(ABC):
    @abstractmethod
    def execute_query(self, cypher_query_: str, **kwargs: Any) -> Coroutine:
        # 统一的异步查询接口
        pass
```
上层逻辑（如搜索、写入）只依赖这个接口，完全不感知底层数据库的连接池、事务机制或协议细节。

### 1.2 Cypher 适配
虽然 Neo4j 和 FalkorDB 都使用 Cypher 语言，但在向量索引和函数调用上存在显著差异。Graphiti 在 `graphiti_core/graph_queries.py` 中通过**工厂函数**模式解决了这个问题。

**案例：向量相似度计算**
*   **Neo4j:** 使用 `vector.similarity.cosine`，返回值是 [0, 1] 的相似度。
*   **FalkorDB:** 使用 `vec.cosineDistance`，返回值是距离。

代码通过 `get_vector_cosine_func_query` 函数动态生成适配的 Cypher 片段：
```python
def get_vector_cosine_func_query(vec1, vec2, db_type='neo4j'):
    if db_type == 'falkordb':
        # 手动将距离转换为相似度
        return f'(2 - vec.cosineDistance({vec1}, vecf32({vec2})))/2'
    return f'vector.similarity.cosine({vec1}, {vec2})'
```

### 1.3 性能与兼容性的权衡
FalkorDB 的驱动实现（`falkordb_driver.py`）为了兼容性做了一些妥协。例如，它需要在 Python 层面手动将 `datetime` 对象转换为 ISO 字符串，因为 FalkorDB 的原生驱动对时间类型的支持与 Graphiti 的期望不一致。这种转换虽然带来了一定的 CPU 开销，但保证了双时态逻辑在不同数据库上的一致性。


## 2. MCP 服务：Agent 的“大脑外挂”

Graphiti 并不满足于做一个 Python 库，它通过 **MCP (Model Context Protocol)** 将自己变成了一个即插即用的服务。这使得 Claude Desktop、Cursor 等支持 MCP 的客户端可以直接“挂载” Graphiti 作为长时记忆。

### 2.1 架构：FastMCP 与异步队列
MCP 服务代码位于 `mcp_server/graphiti_mcp_server.py`。它使用了 `FastMCP` 框架来定义工具（Tools）。

**挑战：** Graphiti 的写入操作（提取、去重、冲突检测）非常耗时，直接同步调用会阻塞 Agent 的交互界面，导致用户体验极差。

**解法：Fire-and-Forget 模式**
服务器实现了一个基于 `asyncio.Queue` 的后台任务队列。
```python
# graphiti_mcp_server.py

@mcp.tool()
async def add_memory(...):
    # 将任务放入队列，不等待执行结果
    await episode_queues[group_id].put(process_episode)
    # 立即返回成功响应
    return SuccessResponse(message="Episode queued for processing...")
```
这种设计确保了 Agent 能够获得秒级的响应反馈，而复杂的图谱构建逻辑在后台从容执行。

### 2.2 Schema 注入：个性化记忆
Graphiti MCP Server 不仅仅是透传 API，它还通过定义特定的 Pydantic 模型（`Requirement`, `Preference`, `Procedure`）向系统注入了**领域知识**。

```python
ENTITY_TYPES = {
    'Requirement': Requirement, # 提取用户需求
    'Preference': Preference,   # 提取用户偏好
    'Procedure': Procedure,     # 提取操作流程
}
```
这告诉底层的 LLM 提取器：“请特别留意这三类信息”。这使得 Graphiti 从通用的知识图谱变成了 **专属于 Agent 的个性化记忆体**。

### 2.3 `cursor_rules.md`：Prompt Engineering 的延伸
源码中包含的 `cursor_rules.md` 是系统的一部分。它不是给 Python 解释器看的，而是给 AI Agent（如 Cursor）看的。它明确规定了 Agent 的行为准则：
*   **"Search First":** 行动前必须先搜索记忆。
*   **"Capture Immediately":** 发现新信息必须立即写入。

这展示了 AI 原生应用开发时，**代码逻辑与提示词工程（Prompt Engineering）的深度融合。**


## 3. 总结

Graphiti 这个时序知识图谱引擎 **从单纯的“检索”走向“认知”与“记忆”**：

1.  **理念:** 用“情节”和“双时态”解决 RAG 的状态缺失问题。
2.  **构建:** 用 Embedding + LLM 实现智能的实体解析。
3.  **时序:** 用语义冲突检测维护世界状态的演变。
4.  **检索:** 用混合搜索策略挖掘深层关联。
5.  **生态:** 用驱动抽象和 MCP 协议连接数据库与 Agent。
