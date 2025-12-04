---
title: "构建高效AI Agent-Anthropic"
showAuthor: false
date: 2024-12-21
description: "构建高效AI Agent-Anthropic"
slug: "building-effective-agents-translate"
tags: ["Agent", "Anthropic"]
# series: [""]
# series_order: 1
draft: false
---

<!-- 渲染公式 -->
{{< katex >}}


# 译文-构建高效AI Agent-Anthropic

{{< alert "claude" >}}
[engineering/building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents)
{{< /alert >}}

在过去的一年里，我们与数十个跨行业构建大型语言模型（LLM）Agent 的团队进行了合作。我们发现，最成功的实施案例无一例外地使用了简单、可组合的模式，而非复杂的框架。

在这篇文章中，我们将分享与客户合作以及我们自己构建 Agent 时学到的经验，并为开发者提供构建高效 Agent 的实用建议。

## 什么是 Agent？

“Agent”可以有多种定义。一些客户将 Agent 定义为能够长时间独立运行、使用各种工具完成复杂任务的完全自主系统。另一些客户则用这个词来描述遵循预定义工作流程、更具规范性的实施方案。在 Anthropic，我们将这些变体都归类为 Agent 系统，但在架构上对“工作流”和“Agent”做了重要区分：

- **工作流（Workflows）**：LLM 和工具通过预定义的代码路径进行编排的系统。
- **Agent**：LLM 动态指导自身流程和工具使用，并保持对任务完成方式控制权的系统。

接下来，我们将详细探讨这两种 Agent 系统。在附录 1（“实践中的 Agent”）中，我们描述了客户在使用这些系统中发现特别有价值的两个领域。

## 何时（以及何时不）使用 Agent

在使用 LLM 构建应用程序时，我们建议尽可能寻找最简单的解决方案，仅在需要时才增加复杂性。这可能意味着根本不构建 Agent 系统。Agent 系统通常以延迟和成本换取更好的任务性能，您应考虑这种权衡在何时有意义。

当确实需要更高复杂性时，对于定义明确的任务，工作流提供了可预测性和一致性；而当需要大规模的灵活性和模型驱动的决策时，Agent 是更好的选择。然而，对于许多应用来说，通过检索和上下文示例来优化单次 LLM 调用通常就足够了。

## 何时以及如何使用框架

有许多框架可以使 Agent 系统的实现变得更容易，包括：

- LangChain 的 LangGraph
- Amazon Bedrock 的 AI Agent 框架
- Rivet，一个拖放式 GUI LLM 工作流构建器
- Vellum，另一个用于构建和测试复杂工作流的 GUI 工具

这些框架通过简化标准的底层任务（如调用 LLM、定义和解析工具、将调用链接在一起）使入门变得容易。然而，它们常常创建额外的抽象层，这可能会掩盖底层的提示和响应，使调试变得更加困难。它们也可能诱使你在本可以用更简单设置解决问题时增加不必要的复杂性。

我们建议开发者从直接使用 LLM API 开始：许多模式可以用几行代码实现。如果您确实使用了框架，请确保您理解其底层代码。对底层机制的错误假设是客户出错的常见原因。

请参阅[cookbook](https://github.com/anthropics/anthropic-cookbook)获取一些示例实现。

## 构建块、工作流和 Agent

在本节中，我们将探讨在生产中看到的 Agent 系统的常见模式。我们将从我们的基础构建块——增强型 LLM——开始，并逐步增加复杂性，从简单的组合式工作流到自主 Agent。

### 构建块：增强型 LLM

Agent 系统的基本构建块是经增强的 LLM，这些增强功能包括检索、工具和记忆。我们目前的模型可以主动使用这些功能——生成自己的搜索查询、选择合适的工具，并决定保留哪些信息。

<figure>
  <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/12/zwR20K.png" alt="The augmented LLM">
  <figcaption style="text-align: center;">The augmented LLM</figcaption>
</figure>


我们建议在实现中关注两个关键方面：根据您的具体用例定制这些功能，并确保它们为您的 LLM 提供一个简单、文档齐全的接口。

在本文的其余部分，我们假设每次 LLM 调用都可以访问这些增强功能。

### 工作流：提示链 (Prompt Chaining)

提示链将一个任务分解为一系列步骤，其中每个 LLM 调用处理前一个调用的输出。您可以在任何中间步骤上添加程序化检查（见下图中的“gate”），以确保流程仍在正轨上。

<figure>
  <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/12/zAqIbE.png" alt="The prompt chaining workflow">
  <figcaption style="text-align: center;">The prompt chaining workflow</figcaption>
</figure>

**何时使用此工作流**：此工作流非常适合可以轻松、清晰地分解为固定子任务的情况。其主要目标是通过使每次 LLM 调用成为一个更容易的任务来换取更高的准确性，尽管这会增加延迟。

**示例**：

- 生成营销文案，然后将其翻译成另一种语言。
- 编写一份文档大纲，检查大纲是否满足某些标准，然后根据大纲撰写文档。

### 工作流：路由 (Routing)

路由对输入进行分类，并将其导向一个专门的后续任务。此工作流允许关注点分离，并构建更专业的提示。没有此工作流，针对一种输入的优化可能会损害在其他输入上的性能。

<figure>
  <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/12/EpOxxW.png" alt="The routing workflow">
  <figcaption style="text-align: center;">The routing workflow</figcaption>
</figure>

**何时使用此工作流**：当存在可以分开处理的明确类别，并且分类可以被 LLM 或更传统的分类模型/算法准确处理时，路由效果很好。

**示例**：

- 将不同类型的客户服务查询（一般问题、退款请求、技术支持）引导到不同的下游流程、提示和工具中。
- 将简单/常见的问题路由到像 Claude 3.5 Haiku 这样较小的模型，而将困难/不寻常的问题路由到像 Claude 3.5 Sonnet 这样能力更强的模型，以优化成本和速度。

### 工作流：并行化 (Parallelization)

LLM 有时可以同时处理一个任务，并以编程方式汇总它们的输出。这种工作流，即并行化，主要有两种变体：

- **分段 (Sectioning)**：将任务分解为并行运行的独立子任务。
- **投票 (Voting)**：多次运行同一任务以获得多样化的输出。

<figure>
  <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/12/oVDZtT.png" alt="The parallelization workflow">
  <figcaption style="text-align: center;">The parallelization workflow</figcaption>
</figure>


**何时使用此工作流**：当划分的子任务可以为了速度而并行化，或者当需要多个视角或尝试以获得更高置信度的结果时，并行化是有效的。对于具有多种考虑因素的复杂任务，如果每个考虑因素都由单独的 LLM 调用处理，LLM 通常表现更好。

**示例**：

- **分段**：实施安全护栏，其中一个模型实例处理用户查询，而另一个实例筛选不当内容或请求。
- **分段**：自动化评估 LLM 性能，其中每个 LLM 调用评估模型在给定提示上性能的不同方面。
- **投票**：审查一段代码是否存在漏洞，其中几个不同的提示会审查并标记代码中发现的问题。

### 工作流：编排者-工作者 (Orchestrator-Workers)

在编排者-工作者工作流中，一个中央 LLM 动态地分解任务，将它们委托给工作者 LLM，并综合它们的结果。

<figure>
  <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/12/MzUXga.png" alt="The orchestrator-workers workflow">
  <figcaption style="text-align: center;">The orchestrator-workers workflow</figcaption>
</figure>


**何时使用此工作流**：此工作流非常适合您无法预测所需子任务的复杂任务。与并行化的关键区别在于其灵活性——子任务不是预先定义的，而是由编排者根据具体输入确定的。

**示例**：

- 每次都需要对多个文件进行复杂更改的编码产品。
- 涉及从多个来源收集和分析信息以寻找可能相关信息的搜索任务。

### 工作流：评估者-优化者 (Evaluator-Optimizer)

在评估者-优化者工作流中，一个 LLM 调用生成响应，而另一个在循环中提供评估和反馈。

<figure>
  <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/12/xVS61h.png" alt="评估者-优化者工作流">
  <figcaption style="text-align: center;">评估者-优化者工作流</figcaption>
</figure>


**何时使用此工作流**：当我们有明确的评估标准，并且迭代改进能提供可衡量的价值时，此工作流特别有效。这类似于人类作者在撰写精炼文档时经历的迭代写作过程。

**示例**：

- 文学翻译，其中翻译者 LLM 最初可能无法捕捉到细微差别，但评估者 LLM 可以提供有用的评论。
- 复杂的搜索任务，需要多轮搜索和分析以收集全面信息，由评估者决定是否需要进一步搜索。

### Agents

随着 LLM 在关键能力（理解复杂输入、进行推理和规划、可靠地使用工具以及从错误中恢复）上的成熟，Agent 开始在生产环境中出现。Agent 通过用户的命令或互动讨论开始工作。一旦任务明确，Agent 便独立规划和操作，可能会返回给人类以获取更多信息或判断。

<figure>
  <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/12/vfbQKN.png" alt="自主 Agent">
  <figcaption style="text-align: center;">自主 Agent</figcaption>
</figure>

**何时使用 Agent**：Agent 可用于开放式问题，这些问题难以或不可能预测所需步骤数量，也无法硬编码固定路径。Agent 的自主性使其成为在受信任环境中扩展任务的理想选择。

Agent 的自主性意味着更高的成本和潜在的复合错误。我们建议在沙盒环境中进行广泛测试，并配备适当的安全护栏。

**示例**：

- 一个用于解决 [SWE-bench](https://www.anthropic.com/research/swe-bench-sonnet) 任务的编码 Agent，这些任务涉及根据任务描述对多个文件进行编辑。
- 我们的[“计算机使用”](https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo)参考实现，其中 Claude 使用计算机来完成任务。

<figure>
  <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/12/uNgZPl.png" alt="High-level flow of a coding agent">
  <figcaption style="text-align: center;">High-level flow of a coding agent</figcaption>
</figure>


## 结合和定制这些模式

这些构建模块并非规定性的。它们是开发者可以塑造和组合以适应不同用例的常见模式。对于任何LLM功能来说，成功的关键在于衡量性能并在实现上进行迭代。重复一遍：只有当它明显改善结果时，你才应该考虑增加复杂性。

## 总结

在 LLM 领域取得成功，关键不在于构建最复杂的系统，而在于根据您的需求构建正确的系统。从简单的提示开始，通过全面的评估对其进行优化，只有当更简单的解决方案无法满足需求时，才添加多步 Agent 系统。

在实施 Agent 时，我们遵循三个核心原则：

1. **保持设计的简单性。**
2. **通过明确展示 Agent 的规划步骤来优先考虑透明度。**
3. **通过详尽的工具文档和测试，精心打造您的 Agent-计算机接口（ACI）。**

通过遵循这些原则，您可以创建不仅功能强大，而且可靠、可维护并受用户信任的 Agent。

---

### 附录 1：实践中的 Agent

我们与客户的合作揭示了 AI Agent 两个特别有前景的应用，它们展示了上述模式的实用价值。

**A. 客户支持**
客户支持将熟悉的聊天机器人界面与通过工具集成增强的功能相结合。这是一个非常适合更开放式 Agent 的领域，因为：

- 支持互动自然地遵循对话流程，同时需要访问外部信息和执行操作。
- 可以集成工具来拉取客户数据、订单历史和知识库文章。
- 可以以编程方式处理退款或更新工单等操作。
- 成功与否可以通过用户定义的解决方案来明确衡量。

**B. 编码 Agent**
软件开发领域已显示出 LLM 功能的巨大潜力，其能力从代码补全发展到自主解决问题。Agent 在此特别有效，因为：

- 代码解决方案可通过自动化测试进行验证。
- Agent 可以利用测试结果作为反馈来迭代解决方案。
- 问题空间定义明确且结构化。
- 产出质量可以客观衡量。


### 附录 2：为您的工具进行提示工程

无论您在构建哪种 Agent 系统，工具都可能是您 Agent 的重要组成部分。工具使 Claude 能够通过在我们的 API 中指定其确切结构和定义来与外部服务和 API 交互。

我们为决定工具格式提出的建议如下：

- 给模型足够的 token 在“思考”后再行动。
- 保持格式接近于模型在互联网上自然见过的文本格式。
- 确保没有格式上的“开销”，例如必须保持数千行代码的准确计数，或对其编写的任何代码进行字符串转义。

一个经验法则是，思考一下投入到人机界面（HCI）中的精力，并计划投入同样多的精力来创建优秀的 **Agent-计算机接口（ACI）**。以下是一些想法：

- **设身处地为模型着想**：根据描述和参数，使用这个工具是否显而易见？如果需要仔细思考，那么对模型来说可能也是如此。
- **测试模型如何使用您的工具**：在我们的工作台中运行许多示例输入，看看模型会犯什么错误，然后进行迭代。
- **Poka-yoke（防错）您的工具**：更改参数，使其更难出错。例如，我们发现当 Agent 移出根目录后，模型在使用相对文件路径的工具时会出错。为了解决这个问题，我们更改了工具，使其始终需要绝对文件路径——我们发现模型完美地使用了这个方法。
