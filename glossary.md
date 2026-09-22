# Glossary — 写作术语表

写作与 AI 校对时的用词基准。新增术语按「决策 → 记录在此 → 全站一致」的流程处理。

## 固定不译（保留英文）

| 术语 | 说明 |
|---|---|
| Agent | 不译「智能体」；正文可用「AI Agent」，标题保持简洁 |
| LLM / RAG / RLHF / GNN / MCP | 全大写缩写，不写 Llm/Rag |
| Context Engineering | 译作「上下文工程」，首次出现：上下文工程（Context Engineering） |
| Memory | 译作「记忆」；指系统组件时保留原名（如 `TreeTextMemory`） |
| Prompt | 译作「提示词」或保留 Prompt，全站统一用「提示词」 |

## 固定译名

| 英文 | 中文 |
|---|---|
| hallucination | 幻觉 |
| evaluation | 评估（不译「评价」） |
| inference | 推理（指模型推理）；「推断」仅用于统计语境 |
| reasoning | 推理/思考：模型能力语境用「推理」 |
| alignment | 对齐 |
| fine-tuning | 微调 |
| embedding | 嵌入/向量表示：技术实现语境用「嵌入」 |
| workflow | 工作流 |
| orchestration | 编排 |

## 排版规则

- **中英文之间加半角空格**：「构建高效 AI Agent」而非「构建高效AI Agent」
- **加粗与全角标点之间留半角空格**：`**重点** 是` 而非 `**重点**是`（Goldmark 的 CommonMark flanking 规则，见 scripts/fix_cjk_bold.py）
- 中文正文用全角标点（，。：；「」）；代码、命令、路径、公式内用半角
- 缩写首次出现给全称：大语言模型（LLM）、检索增强生成（RAG）
- 人称规则：译文保留原文的「我们」；教程对读者称「你」；观点文章用「我」
- 删除 AI 腔填充句：「值得注意的是」「总而言之」「在当今时代」
