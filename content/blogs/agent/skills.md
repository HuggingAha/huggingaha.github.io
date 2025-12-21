---
title: "Claude Agent Skills：元工具架构分析"
showAuthor: false
date: 2025-11-01
description: "Claude Agent Skills：元工具架构分析"
slug: "claude-skills"
tags: ["Agent", "skills"]
series: ["skills系列"]
series_order: 1
draft: false
---

<!-- 渲染公式 -->
{{< katex >}}


<!-- # Claude Agent Skills：元工具架构的技术解构与工程实践 -->

{{< alert "bell" >}}
参考链接：[claude-skills-blog](https://www.claude.com/blog/skills)、[agents-kills](https://agentskills.io/)、[claude-skills-deep-dive](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)、[Github](https://github.com/anthropics/skills.git)
{{< /alert >}}


<!-- <figure>
  <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/12/TOa2vy.png" alt="图1: Agent Skills 的元工具执行流程图">
  <figcaption style="text-align: center;">图1: Agent Skills 的元工具执行流程图</figcaption>
</figure> -->

<!-- # Agent Skills Specification：智能体能力的标准化架构与工程实践 -->

Agent Skills（智能体技能）不仅仅是大语言模型（LLM）的工具扩展，它代表了一种**基于 Prompt 的元工具（Meta-Tool）架构**。该规范旨在通过 **渐进式披露（Progressive Disclosure）** 机制，解决通用大模型在垂直领域应用中面临的上下文窗口限制、指令复杂性与执行确定性三大挑战。本文将从架构设计、文件规范、执行逻辑以及与现有技术栈（MCP, Function Calling）的对比四个维度进行系统分析。


## 一、 核心设计理念：渐进式披露 (Progressive Disclosure)

Agent Skills 的核心工程价值在于**上下文管理（Context Management）**。传统的 Prompt 工程倾向于一次性将所有规则灌入上下文，导致 Token 消耗巨大且模型注意力分散。Skills 架构采用漏斗模型（如图中顶部所示），将信息加载分为三个层级：

1.  **Metadata 层（轻量加载）**
    *   **内容**：仅包含技能的名称（Name）和简述（Description）。
    *   **机制**：在系统启动或对话初期，系统仅将这部分极少量的文本加载到 LLM 的上下文中。
    *   **目的**：使 LLM 能够以最小的 Token 消耗“感知”到成百上千种技能的存在，并基于语义判断是否需要调用。

2.  **Instructions 层（按需加载）**
    *   **内容**：`SKILL.md` 中的完整 Markdown 指令、Prompt 模板、SOP（标准作业程序）。
    *   **机制**：**Lazy Loading（懒加载）**。只有当 LLM 决定调用特定技能时，系统才读取该层内容并注入到当前的对话上下文中。
    *   **目的**：将通用 LLM 临时转化为特定领域的“专家”，而在任务结束后释放上下文。

3.  **Scripts & Assets 层（执行加载）**
    *   **内容**：Python/Bash 脚本、大型参考文档、模板文件。
    *   **机制**：仅在具体执行步骤中，通过工具调用或路径引用来访问。
    *   **目的**：处理高密度信息或确定性逻辑，避免无关数据污染上下文。


## 二、 规范解剖：目录结构与文件定义

Agent Skills 采用标准化的目录结构来封装能力，使其具备可移植性和复用性。

### 2.1 目录结构标准
一个标准的 Skill 包（`my-skill/`）包含以下组件：

*   **`SKILL.md` (Core/Mandatory)**：技能的核心定义文件，承载元数据与指令。
*   **`/scripts` (Optional)**：存放可执行代码（Python, Bash, JS 等）。用于承载逻辑运算、数据清洗等**确定性任务**。
*   **`/references` (Optional)**：存放领域知识文档（Markdown/JSON）。供 LLM 在运行时阅读（RAG source）。
*   **`/assets` (Optional)**：存放静态资源（HTML 模板、CSV 样本、图片）。通常用于生成最终交付物。

### 2.2 SKILL.md：双重定义的载体
`SKILL.md` 采用了 YAML Frontmatter 与 Markdown Body 结合的格式，分别服务于系统的路由与模型的推理。

*   **YAML Frontmatter (定义层 - Define)**
    *   **面向对象**：路由系统 / 宿主程序。
    *   **关键字段**：
        *   `name`: 技能调用的唯一标识符（ID）。
        *   `description`: 用于语义路由的描述文本，决定了 LLM 何时触发该技能。
        *   `version`: 版本控制。
    *   **作用**：作为“索引”存在于上下文的 Metadata 层。

*   **Markdown Body (指南层 - Guide)**
    *   **面向对象**：LLM (Claude/GPT)。
    *   **关键内容**：自然语言编写的步骤说明、约束条件、Few-Shot 示例。
    *   **作用**：当技能被激活时，这部分内容被“展开”并注入 Prompt，指导 AI 如何一步步完成任务。


## 三、 运行机制：概率与确定性的融合

LLM 本质是概率模型，擅长意图理解和规划，但不擅长精确计算和逻辑执行。Skills 架构通过 **“LLM Brain + Deterministic Script”** 的模式解决了这一矛盾。

### 3.1 确定性逻辑 (Deterministic Logic) 的卸载

流程如下：
1.  **触发 (Trigger)**：LLM 规划出任务路径，决定执行某个具体步骤（如“计算销售额同比增长”）。
2.  **委托 (Delegate)**：LLM 不直接进行计算（防止幻觉），而是调用 `/scripts` 目录下的 Python 脚本（如 `data_proc.py`）。
3.  **执行 (Execute)**：脚本在沙箱中运行，执行精确的数学运算或数据处理。
4.  **反馈 (Feedback)**：脚本将结构化的 Result Data 返回给 LLM。

这种设计将复杂的认知负载从 **概率性的生成（Generation）** 转移到了 **确定性的代码执行（Execution）** 上，显著增强了系统的鲁棒性。


## 四、 技术栈对比：Skills, MCP 与 Function Calling

为了精准定位 Skills，需将其与现有的 AI 基础设施概念进行对比。

### 4.1 抽象层级对比

| 概念 | 抽象层级 | 核心职责 | 类比 |
| :--- | :--- | :--- | :--- |
| **Function Calling** | **原子层 (Mechanism)** | 接口执行。LLM 输出 JSON 参数以调用函数。 | **“手”**：能够抓取物体，但不知道抓什么、为什么要抓。 |
| **MCP** | **连接层 (Protocol)** | 标准化连接。统一 AI 与外部数据/工具的通信协议。 | **“神经/血管”**：连接大脑与手脚，传输数据，但不包含业务逻辑。 |
| **Agent Skills** | **逻辑层 (Module)** | 流程编排。封装 Prompt (SOP) + 代码，定义“如何做”。 | **“技能手册/小脑”**：指导手去完成“泡咖啡”这一复杂动作序列的知识。 |

### 4.2 深度分析

1.  **Skills 与 Function Calling 的关系**：
    *   Function Calling 是底层**能力**，Skills 是上层**应用**。
    *   一个 Skill 的执行过程中，通常会包含多次 Function Calling（例如调用 `bash` 运行脚本，调用 `read_file` 读取文档）。Skills 为 Function Calling 提供了上下文背景和执行顺序的约束。

2.  **Skills 与 MCP (Model Context Protocol) 的关系**：
    *   **互补而非替代**。
    *   **MCP 解决“连接外部”**：它标准化了如何连接 Google Drive、PostgreSQL 或 GitHub。它提供的是“原材料”和“通道”。
    *   **Skills 解决“内部处理”**：它定义了当通过 MCP 获取到数据后，应该按照什么步骤进行分析、总结和报告。
    *   *最佳实践*：通过 MCP 获取数据，利用 Skill 定义的脚本和 Prompt 处理数据。

### 4.3 Token 消耗差异
*   **Function Calling / MCP (Raw)**：如果在 System Prompt 中挂载 100 个工具的完整 Schema，每次对话都会消耗大量 Token，且容易造成模型困惑。
*   **Skills**：利用前文提到的“渐进式披露”，初始仅加载几百 Token 的索引。其 Token 效率在工具数量增加时呈指数级优势。


## 五、 总结

Agent Skills Specification 提供了一个标准化的框架，用于构建健壮（Robust）且可互操作（Interoperable）的 AI Agents。

它不是一项单一的黑科技，而是一套**工程实践的组合**：
1.  利用 **Metadata** 实现路由的低成本化。
2.  利用 **Context Injection** 实现能力的即插即用。
3.  利用 **Scripts** 实现逻辑的确定性。

对于开发者而言，采用 Skills 规范意味着从“编写单一的 Prompt”转向“构建模块化的智能体操作系统组件”。
