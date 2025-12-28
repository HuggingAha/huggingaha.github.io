---
title: "Hybrid-RAG-System：构建高置信度医疗问答系统"
showAuthor: false
date: 2025-07-15
description: ""
slug: "hybrid-rag-system"
tags: ["RAG", "医疗"]
series: []
series_order: 1
draft: false
---

<!-- 渲染公式 -->
{{< katex >}}


<!-- # Hybrid-RAG-System 源码：构建高置信度医疗问答系统 -->

{{< alert "github" >}}
[EasonWong0327/Hybrid-RAG-System](https://github.com/EasonWong0327/Hybrid-RAG-System.git)
{{< /alert >}}

## 1. 引言

在通用领域，RAG（检索增强生成）系统的核心指标通常是“流畅度”和“相关性”。然而，在医疗AI领域，核心指标必须是 **“准确性”** 和 **“安全性”**。一个流畅但错误的医疗建议（幻觉）可能导致严重的后果。

**Hybrid-RAG-System** 是一个企业级医疗问答解决方案。根据对源码的阅读，其架构本质并非单纯的“Chatbot”，而是一套由 **“规则引擎 + 统计模型 + 大语言模型”** 组成的混合决策流水线。其核心价值在于实现了一套完整的 **可信AI (Trustworthy AI)** 闭环，解决了医疗场景中最为棘手的“幻觉”与“知识冲突”问题。

## 2. 系统架构概览

该系统基于 **FastAPI** 构建服务层，底层融合了 **ElasticSearch**（精确检索）和 **Faiss**（语义检索），核心智力由 **Qwen3-4B** 提供。但其架构的灵魂在于贯穿全流程的**审计模块**。

### 宏观架构图

{{< mermaid >}}
graph TD
    User[用户输入] --> API[FastAPI 网关]
    API --> DST[Smart DST<br>智能对话状态跟踪]
    
    subgraph "检索层 (Recall)"
        DST -- 增强查询 --> Router[自适应权重路由]
        Router --> ES[ElasticSearch<br>关键词检索]
        Router --> Faiss[Faiss<br>向量检索]
        ES & Faiss --> Candidates[候选文档集]
    end
    
    subgraph "清洗层 (Sanitization)"
        Candidates --> ConflictDet[知识冲突检测器]
        ConflictDet -- 标记矛盾/剂量错误 --> Context[安全上下文]
    end
    
    subgraph "生成层 (Generation)"
        Context --> Prompt[动态 Prompt 构建<br>注入冲突警告]
        Prompt --> LLM[Qwen3-4B]
        LLM -- Logits/Text --> RawAns[原始回答]
    end
    
    subgraph "审计层 (Auditing)"
        RawAns --> HallucinationDet[增强型幻觉检测器]
        RawAns --> ToxicityDet[毒性检测器]
        HallucinationDet -- 评分/拦截 --> FinalAns[最终回答]
    end
    
    FinalAns --> User
{{< /mermaid >}}


## 3. 核心设计探秘

将按照数据流动的方向，分析支撑该系统的五大核心模块。

### 3.1 听懂人话：智能对话状态跟踪 (Smart DST)
*   **源码位置:** `QA/core/dialogue/smart_dst.py`
*   **设计挑战:** 用户口语（“脑袋疼”）与专业文档（“头痛”）存在术语鸿沟；多轮对话中存在指代模糊。

**核心实现:**  
该模块放弃了不可控的端到端生成，采用了 **“词典映射 + 规则填充”** 的确定性策略。 
1.  **高级实体识别 (`_advanced_entity_recognition`):** 强制将同义词映射回标准主实体。
2.  **查询增强 (`_generate_enhanced_query`):** 利用上下文栈回溯历史实体，解决指代消解。

```python
# 代码片段：同义词归一化与置信度计算
def _advanced_entity_recognition(self, query: str):
    # 遍历医疗实体词典
    for variant in all_variants:
        if variant in query:
            # 关键：无论用户说的是土话还是术语，系统内部统一使用 main_entity
            confidence = 1.0 if variant == main_entity else 0.8
            entity_mention = EntityMention(text=variant, ...)
```

### 3.2 动态寻源：自适应混合检索 (Adaptive Hybrid Retrieval)
*   **源码位置:** `QA/core/retrievers/adaptive_hybrid_retriever.py`
*   **设计挑战:** 向量检索不懂“阿司匹林”的具体拼写，关键词检索不懂“感觉像针扎一样”的语义。

**核心实现:**
系统引入了 **元认知（Meta-Cognition）** 步骤。在检索前，先判断查询意图，再动态调整 ElasticSearch (ES) 和 Faiss 的权重。

```python
# 代码片段：基于意图的动态权重路由
def _calculate_weights(self, query_analysis):
    # 默认权重
    weights = {'faiss': 0.6, 'es': 0.4}
    
    # 策略路由
    if query_type == 'factual': # 事实类问题依赖语义
        weights['faiss'] = 0.7 
    elif query_type == 'treatment': # 治疗方案依赖精确匹配
        weights['faiss'] = 0.8 # 注：此处代码倾向语义，但在低置信度时会反转
        
    # 兜底机制：如果语义理解置信度低，强制依赖关键词
    if confidence < 0.3:
        weights['faiss'] *= 0.9
        weights['es'] *= 1.1
    return weights
```

### 3.3 输入清洗：知识冲突检测机制 (Knowledge Conflict Detector)
*   **源码位置:** `QA/core/detectors/knowledge_conflict_detector.py`
*   **设计挑战:** 检索回来的 Top-K 文档可能包含相互矛盾的信息（如不同来源的剂量建议）。

**核心实现:**
这是该系统最独特的**预处理防线**。它不盲目信任检索结果，而是假设文档间存在对抗关系。它能识别五类冲突：观点、剂量、时效、权威性、严重程度。

*   **剂量冲突检测:** 专门的正则提取逻辑，防止数值错误。
*   **冲突注入:** 检测结果不会被丢弃，而是转化为**结构化警告**注入 Prompt。

```python
# 代码片段：剂量冲突检测逻辑
if len(set(values)) > 1: # 如果提取出的剂量数值不一致
    conflict = ConflictDetail(
        conflict_type=ConflictType.DOSAGE_CONFLICT,
        description=f"发现{unit}剂量冲突: {', '.join(set(values))}",
        severity="high", # 标记为高危
        recommendation="剂量冲突，必须咨询医生确认正确剂量"
    )
```

### 3.4 概率生成：白盒监控与动态 Prompt
*   **源码位置:** `QA/core/generators/qwen3_generator.py`
*   **设计挑战:** LLM 何时在瞎编？如何让它知道上下文有冲突？

**核心实现:**
1.  **动态 Prompt:** 将冲突检测器的结果（警告和建议）显式写入 Prompt，利用 LLM 的 In-Context Learning 能力进行自我修正。
2.  **白盒监控:** 深入模型推理层，捕获 **Logits** 并计算困惑度 (Perplexity)。如果生成的某个关键实体概率极低，即便语句通顺，系统也会标记风险。

```python
# 代码片段：计算生成概率分布
for i, (score, token_id) in enumerate(zip(scores, generated_tokens)):
    probs = torch.softmax(score[0], dim=-1)
    token_prob = probs[token_id].item() # 获取当前Token的置信度
    # ... 计算困惑度 ...
```

### 3.5 输出审计：增强型幻觉检测 (Enhanced Hallucination Detector)
*   **源码位置:** `QA/core/detectors/hallucination_detector.py`
*   **设计挑战:** 如何防止模型生成违背常识或违反法规的内容？

**核心实现:**
这是系统的**最后一道防线**。它是一个包含 8 个维度的综合审计器。
1.  **医疗知识图谱 (KG):** 内置微型 KG，通过逻辑推理（而非概率）拦截常识性错误（如“高血压禁忌”校验）。
2.  **语义一致性:** 使用 BERT 计算生成文本与检索文档的向量相似度。
3.  **合规性正则:** 强制过滤“100%治愈”、“神药”等违规词汇。

```python
# 代码片段：基于KG的事实核查
def _verify_medical_facts(self, text, entities):
    for entity in entities:
        if entity in self.medical_knowledge_graph:
            # 检查文本是否包含了该疾病的"禁忌"
            for contraindication in kg_info.get('contraindications', []):
                if contraindication in text:
                    fact_violations.append(...) # 记录违规
```


## 4. 关键数据流分析 (Case Study)

追踪一个典型的高风险用例：**“高血压患者能喝两杯白酒吗？”**

1.  **Phase 1: 理解 (Smart DST)**
    *   输入：“能喝两杯白酒吗？”（假设上下文已知高血压）。
    *   动作：DST 回溯上下文，重写查询为 `疑似疾病:高血压 | 饮食禁忌:白酒 | 剂量:两杯`。
2.  **Phase 2: 检索 (Hybrid Retriever)**
    *   动作：ES 检索“高血压 AND 白酒”，Faiss 检索语义相关文档。
    *   结果：检索到两篇文档。Doc A 说“少量饮酒可能有益”，Doc B 说“严禁饮酒，影响药效”。
3.  **Phase 3: 清洗 (Conflict Detector)**
    *   动作：识别到 Doc A 和 Doc B 存在 **Viewpoint Conflict (观点冲突)**。
    *   输出：生成警告 `[警告] 检测到关于'饮酒'的观点冲突，存在风险`。
4.  **Phase 4: 生成 (Generator)**
    *   动作：Prompt 被修改，包含上述警告。
    *   LLM 输出：“虽然有部分观点认为少量饮酒可行，但鉴于存在冲突且酒精可能影响降压药效果，建议高血压患者避免饮酒。”
5.  **Phase 5: 审计 (Hallucination Detector)**
    *   动作：查阅内置 KG，发现 `高血压 -> contraindications -> 过度饮酒`。
    *   判断：回答符合 KG 逻辑，语义与文档一致，无违规词。
    *   结果：**放行**。


## 5. 总结

*   **核心优势:** 它最大的亮点在于 **“不信任”**。它不信任用户的表达（引入 DST），不信任单一的检索（引入混合检索），不信任检索到的源文档（引入冲突检测），也不信任 LLM 的生成（引入幻觉检测）。
*   **架构哲学:** 通过引入确定性的规则引擎（正则、词典、KG）来约束概率性的神经网络（LLM、Embedding），从而实现了医疗场景所需的**可解释性**和**可控性**。
*   **改进空间:** 目前的知识图谱（KG）和实体词典是硬编码在 Python 文件中的。在生产环境中，这部分应当解耦并对接专业的图数据库（如 Neo4j）或医疗术语服务，以支持实时更新和更大规模的知识库。
