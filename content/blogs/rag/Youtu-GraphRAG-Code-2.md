---
title: "Youtu-GraphRAG 源码：有界自动化——Schema 引导的图谱构建与动态演进"
showAuthor: false
date: 2025-12-26
description: ""
slug: "youtu-graphrag-code-2"
tags: ["GraphRAG"]
series: ["Youtu-GraphRAG"]
series_order: 3
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


<!-- # Youtu-GraphRAG 源码深度解读 (2)：有界自动化——Schema 引导的图谱构建与动态演进 -->

## 1. 引言

在构建知识图谱（Knowledge Graph, KG）时，开发者通常面临一个两难选择：是采用 **Schema-Free**（开放式信息抽取，灵活性高但噪声大、实体对齐难）还是 **Schema-Based**（基于预定义本体，结构严谨但难以覆盖长尾知识）。

`youtu-graphrag` 在架构上选择了一种折中方案：**“有界自动化” (Bounded Automation)**。它以种子 Schema 作为冷启动约束，同时引入 Agent 机制允许系统在运行过程中自动发现新类型并反向更新 Schema。这种设计意在平衡结构化的规范性与非结构化数据的多样性。

## 2. 种子 Schema 与数据约束

构建过程的起点是定义在 `schemas/` 目录下的 JSON 文件。`KTBuilder` 类在初始化时会加载该文件作为抽取的“宪法”。

### 2.1 物理结构
以 `schemas/demo.json` 为例，Schema 定义了三类核心要素：

```json
{
  "Nodes": ["person", "organization", "event", ...],
  "Relations": ["located_in", "employed_by", ...],
  "Attributes": ["date", "description", "status", ...]
}
```

### 2.2 Prompt 注入
在 `models/constructor/kt_gen.py` 中，`_get_construction_prompt` 方法负责将内存中的 Schema 对象序列化为 JSON 字符串，并注入到 LLM 的 Prompt 中。

```python
# models/constructor/kt_gen.py

def _get_construction_prompt(self, chunk: str) -> str:
    recommend_schema = json.dumps(self.schema, ensure_ascii=False)
    # ...
    # 将 schema 填入模板
    return self.config.get_prompt_formatted(..., schema=recommend_schema, chunk=chunk)
```

查看 `config/base_config.yaml` 中的 Prompt 模板 (`prompts.construction.general_agent`)，可以看到系统通过自然语言指令对 LLM 施加了强约束：

> "Prioritize the following predefined schema for extraction; \`\`\`{schema}\`\`\`"

这种显式的 Schema 注入虽然能显著提高抽取结果的规范性，但在工程实践中也引入了**上下文窗口压力**。随着 Schema 的演进，如果节点类型增加到数百个，Prompt 的 Token 消耗将急剧上升，甚至挤占待处理文本 (`chunk`) 的空间。

## 3. 图谱构建的核心逻辑 (Level 1 & Level 2)

`KTBuilder` 将非结构化文本转化为图结构的过程，主要体现在 `process_level1_level2`（非 Agent 模式）和 `process_level1_level2_agent`（Agent 模式）方法中。

### 3.1 属性节点化 (Level 1 Attribute)
不同于主流属性图（Property Graph）将属性作为节点内的 KV 对存储，`youtu-graphrag` 选择将属性升格为独立的节点。

在 `_process_attributes_agent` 方法中：

```python
# models/constructor/kt_gen.py

def _process_attributes_agent(self, extracted_attr: dict, chunk_id: int, ...):
    for entity, attributes in extracted_attr.items():
        for attr in attributes:
            attr_node_id = f"attr_{self.node_counter}"
            self.graph.add_node(
                attr_node_id,
                label="attribute", # 显式标记为属性节点
                properties={"name": attr, "chunk id": chunk_id},
                level=1,           # 定义为 Level 1
            )
            # ... 建立实体到属性的边 ...
```

这种设计虽然增加了图的规模（节点数量激增），但为基于属性值的**跨实体关联**提供了拓扑基础。例如，两个不同的实体如果都具有 "2023" 这个时间属性，它们在图中就会通过 "2023" 这个属性节点间接相连，这对于多跳推理至关重要。

### 3.2 实体与关系 (Level 2 Entity/Relation)
实体节点的构建逻辑位于 `_find_or_create_entity_direct`。值得注意的是，代码通过 `self.lock` (Threading Lock) 保护了节点计数器 `self.node_counter` 和图的写入操作，这表明该 Builder 设计为支持多线程并发处理 (`max_workers` 默认为 32)。

## 4. 动态演进机制 (The Agentic Loop)

这是该框架最复杂的特性。在 `agent` 模式下，系统不仅执行抽取，还执行 Schema 的自适应更新。

### 4.1 演进触发
LLM 的响应不仅包含抽取的数据，还可能包含 `new_schema_types` 字段。这是通过 Prompt 中的以下指令触发的：

> "If you find new and important entity types... include them in a 'new_schema_types' field."

### 4.2 物理回写与竞争风险
一旦检测到新类型，`process_level1_level2_agent` 会调用 `_update_schema_with_new_types`。

```python
# models/constructor/kt_gen.py 

def _update_schema_with_new_types(self, new_schema_types: Dict[str, List[str]]):
    # 1. 读取磁盘上的 Schema 文件
    with open(schema_path, 'r', encoding='utf-8') as f:
        current_schema = json.load(f)
    
    # 2. 合并去重逻辑 (简单的字符串比对)
    if "nodes" in new_schema_types:
        for new_node in new_schema_types["nodes"]:
            if new_node not in current_schema.get("Nodes", []):
                current_schema["Nodes"].append(new_node)
                updated = True
    
    # 3. 实时回写磁盘
    if updated:
        with open(schema_path, 'w', encoding='utf-8') as f:
            json.dump(current_schema, f, ...)
        # 4. 更新内存对象
        self.schema = current_schema
```

从源码分析，这里的实现存在明显的工程隐患：
1.  **并发写冲突:** 虽然内存操作有线程锁保护，但对文件系统的读写操作缺乏文件锁（File Lock）。在多进程部署（如 Gunicorn）场景下，多个 Worker 同时发现新类型并尝试回写 `json` 文件时，极易导致 Schema 文件损坏或更新丢失。
2.  **Schema 污染与漂移:** 代码仅通过字符串是否存在来判断是否添加新类型。这意味着语义相同但词面不同的词（如 `Company` 和 `Corporation`）会被视为不同类型添加到 Schema 中。随着时间推移，Schema 可能迅速膨胀并充满冗余，导致后续的抽取 Prompt 变得混乱。

## 5. 总结

`youtu-graphrag` 的构建模块通过 **Schema 引导** 确保了知识抽取的基线质量，并通过 **Agent 演进** 赋予了系统适应新领域的能力。

然而，源码层面的实现揭示了其作为原型系统的特征：它依赖于简单的文件回写机制来实现状态共享。在将其推向生产环境时，架构师应当考虑引入中心化的元数据管理服务（Metadata Service）来替代文件操作，并增加“人在回路”（Human-in-the-loop）的审核机制，以防止 Agent 对 Schema 造成不可逆的污染。
