---
title: "Superpowers：构建可组合、工程化的 AI 智能体框架"
showAuthor: false
date: 2026-01-08
description: "Superpowers：构建可组合、工程化的 AI 智能体框架"
slug: "superpowers"
tags: ["Agent", "skills"]
series: ["skills系列"]
series_order: 3
draft: false
---

<!-- 渲染公式 -->
{{< katex >}}



<!-- # Superpowers：构建可组合、工程化的 AI 智能体框架 -->

{{< alert "github" >}}
[obra/superpowers](https://github.com/obra/superpowers) | [Plugin Marketplace](https://github.com/obra/superpowers-marketplace)
{{< /alert >}}

**Superpowers** 是一个专为 AI 编程智能体（如 Claude Code）设计的可组合框架。它不仅仅是一个提示词库，更是一套通过标准化“技能（Skills）”来强制执行严格软件工程规范的系统。

在当前的 AI 辅助开发中，智能体往往容易陷入上下文丢失、逻辑幻觉或产生“看起来能运行但难以维护”的代码。Superpowers 通过引入**技能即代码 (Skills as Code)** 的理念，强制智能体遵循测试驱动开发 (TDD)、系统化调试和多阶段代码审查等行业最佳实践，将 AI 从随意的聊天机器人转变为遵守纪律的工程伙伴。


## 核心架构与原理

Superpowers 的核心组件是 **技能 (Skill)**。

*   **定义**：每个技能都是一个包含 YAML 元数据（Frontmatter）的 Markdown 文件 (`SKILL.md`)。
*   **发现与解析**：框架通过插件系统（如 Claude Code 插件或 OpenCode 插件）动态扫描、解析并加载这些技能。
*   **强制调用**：系统通过 `SessionStart` 钩子注入引导指令，强制智能体在执行任何操作前，必须先检索并调用相关技能。
*   **层级覆盖 (Shadowing)**：支持 `Project > Personal > Superpowers` 的优先级机制。开发者可以在项目级定义特定技能，覆盖个人或默认的通用技能，实现高度定制化。
*   **跨平台适配与工具映射 (The Tool Mapping Layer)**：Superpowers 内置了一个“中间件”层，能够屏蔽底层系统的差异。例如，它会自动将通用的 `Tasks` 工具映射为 OpenCode 的 `@mention` 子智能体机制，或将 `TodoWrite` 映射为 `update_plan`。这意味着同一套技能代码可以在 Claude Code、OpenCode 甚至 Codex 等不同平台上无缝运行，实现了真正的“一次编写，到处运行”。

<figure>
  <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2026/01/9zH1bb.png" alt="">
  <figcaption style="text-align: center;">架构设计</figcaption>
</figure> 


## 核心技能库详解

Superpowers 提供了一套全面的技能库，涵盖了软件开发的各个生命周期。这些技能不仅仅是流程指令，还集成了**静态知识库 (Static Knowledge Base)**。例如，TDD 技能会自动索引反模式文档 (`@testing-anti-patterns.md`)，让 AI 在写测试时能够查阅具体的错误案例，如同工程师手边的参考手册，实现了 "Instruction + Reference" 的双重增强。

<figure>
  <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2026/01/5JRpnL.png" alt="">
  <figcaption style="text-align: center;">工作流程与原则</figcaption>
</figure> 


### 1. 测试 (Testing)：工程质量的基石

测试不仅仅是开发的后置环节，而是 Superpowers 框架中的驱动力。

*   **test-driven-development (测试驱动开发)**
    *   **核心原则**：强制执行 **红-绿-重构 (RED-GREEN-REFACTOR)** 循环。
    *   **铁律 (The Iron Law)**：“没有失败的测试，就不能编写生产代码。”
    *   **流程**：智能体必须先编写一个能够复现需求或 Bug 的失败测试（Red），然后编写最小量的代码使其通过（Green），最后优化代码结构（Refactor）。
    *   **反模式防御**：技能文档明确列出了常见的测试反模式（如测试 Mock 的行为而非真实逻辑、在生产代码中通过 `if(test)` 留后门等），并指导智能体避免这些陷阱。

### 2. 调试 (Debugging)：根因分析优先

针对 AI 容易进行“猜测性修复”的问题，调试技能强制要求系统化的分析过程。

*   **systematic-debugging (系统化调试)**
    *   **四阶段法**：
        1.  **根本原因调查 (Root Cause Investigation)**：通过日志、追踪和复现，定位错误的源头，而非仅仅观察症状。
        2.  **模式分析 (Pattern Analysis)**：对比正常与异常的执行路径。
        3.  **假设与测试 (Hypothesis & Testing)**：提出单一变量假设并验证。
        4.  **实施 (Implementation)**：只有在确认根因后才进行修复。
    *   **辅助技术**：集成 `root-cause-tracing`（调用栈回溯）、`defense-in-depth`（深度防御验证）和 `condition-based-waiting`（基于条件的等待，消除测试中的 Flaky 等待）等子技能。
*   **verification-before-completion (完成前验证)**
    *   在标记任务完成前，强制运行验证逻辑，确保修复确实有效且未引入回归错误。

### 3. 协作与工作流 (Collaboration & Workflow)

Superpowers 将复杂的开发任务拆解为结构化的工作流，确保 AI 与人类开发者的顺畅协作。

*   **brainstorming (头脑风暴)**
    *   **强制性起点**：在编写任何代码之前，智能体必须调用此技能。
    *   **交互模式**：通过问答（Q&A）形式澄清需求，探索 2-3 种技术方案并权衡利弊（Trade-offs），最终输出一份详细的设计文档。
*   **writing-plans (编写计划)**
    *   基于设计文档，将工作拆解为一系列微小的、可执行的步骤（Tasks）。每个步骤都必须包含明确的 TDD 预期。
*   **executing-plans (执行计划)**
    *   **批处理执行**：智能体不会一次性写完所有代码，而是按批次执行任务。
    *   **架构师检查点 (Architect Checkpoints)**：在每批任务完成后，智能体必须暂停并报告进度，等待人类的反馈或批准，从而确保持续的监督。
*   **using-git-worktrees (使用 Git Worktrees)**
    *   自动为新功能或修复创建隔离的 Git 工作树，允许开发者在同一仓库中并行处理多个任务而不污染主工作区。
*   **finishing-a-development-branch (完成开发分支)**
    *   在任务结束时，提供结构化的选项：本地合并、创建 Pull Request 或清理工作区，并再次运行全量测试。

### 4. 代码审查与质量控制 (Code Review)

框架内置了专门的“审查者智能体”角色，模拟资深工程师的 Code Review 流程。

*   **requesting-code-review (请求代码审查)**
    *   开发者或执行智能体调用此技能，唤起 `superpowers:code-reviewer` 智能体。该智能体不负责写代码，只负责根据预定义的清单（代码质量、架构一致性、测试覆盖率）对变更进行严格审查。
*   **receiving-code-review (接收代码审查)**
    *   指导开发者（或智能体）如何处理反馈。强调“响应模式（The Response Pattern）”：阅读 -> 理解 -> 验证 -> 评估 -> 响应 -> 实施。它鼓励基于技术事实的讨论，而不是盲目接受所有建议。

### 5. 高级编排 (Advanced Orchestration)

针对复杂问题，Superpowers 支持多智能体协作。

*   **dispatching-parallel-agents (调度并行代理)**
    *   **场景**：当测试套件中有多个互不相关的独立故障时。
    *   **机制**：主智能体识别独立的故障域，并并行启动多个子智能体，每个子智能体在一个隔离的环境中修复一个特定的故障，最后合并结果。
*   **subagent-driven-development (子代理驱动开发)**
    *   这是框架中最复杂的编排模式。它将实现计划转化为流水线：
        1.  **Orchestrator**：分发任务。
        2.  **Implementer**：执行 TDD 编写代码。
        3.  **Spec Reviewer**：**第一道防线**，检查代码是否符合原始需求规格。
        4.  **Code Quality Reviewer**：**第二道防线**，检查代码风格、可维护性和最佳实践。
    *   只有通过了两级审查的代码才会被标记为完成。

### 6. 元技能 (Meta-Skills)

Superpowers 具有自我进化的能力。

*   **writing-skills (编写技能)**
    *   指导用户或智能体如何编写新的 `SKILL.md`。它采用 **Skill TDD** 方法：先编写一个能触发 AI 错误行为的“压力场景（Pressure Scenario）”（Red），然后编写技能文档来修正该行为（Green），最后优化文档结构（Refactor）。
*   **using-superpowers (使用 Superpowers)**
    *   这是系统的“引导加载程序”。它教会智能体如何查找、读取和理解其他技能，并确立了“在行动前必须调用技能”的根本原则。

## 总结

Superpowers 并非试图让 AI 变得“更有创造力”，而是让 AI 变得**更守纪律**。通过将 TDD、系统化调试和代码审查等工程铁律固化为可执行的“技能”，Superpowers 为 AI 辅助软件开发提供了一个可靠、可扩展且高质量的框架。

对于希望在团队中规模化使用 AI 编程的组织而言，Superpowers 提供了一种将隐性工程知识转化为显性 AI 行为准则的有效路径。
