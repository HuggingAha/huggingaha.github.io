---
title: "REFRAG：Rethinking RAG based Decoding"
showAuthor: false
date: 2025-09-12
description: "REFRAG"
slug: "REFRAG-Rethinking-RAG-based-Decoding"
tags: ["论文", "RAG", "Meta"]
# series: [""]
# series_order: 1
# weight: 4
draft: false
---

<!-- 渲染公式 -->
{{< katex >}}


> **论文**：[REFRAG: Rethinking RAG based Decoding](https://arxiv.org/abs/2509.01092)  
> **代码（非官方）**：[simulanics/REFRAG](https://github.com/simulanics/REFRAG.git)

## RAG 的效率困境

LLM在利用外部知识库进行检索增强生成（Retrieval-Augmented Generation, RAG）方面展现了卓越的能力。然而，这一能力并非没有代价。RAG 系统通常会将检索到的多个文本段落拼接起来，形成一个很长的上下文（Long-Context）输入给 LLM。处理这种长上下文会引发两个核心问题：

1. **高延迟**：尤其是首个 Token 的生成时间（Time-to-First-Token, TTFT）会随着上下文长度二次方增长，严重影响实时交互体验。
2. **高内存占用**：LLM 推理过程中需要缓存键值对（Key-Value Cache），其内存消耗与上下文长度成正比，限制了吞吐量。

论文《REFRAG: Rethinking RAG based Decoding》指出，RAG 的上下文具有独特的“稀疏性”。检索到的段落通常是为了内容多样性或去重而选择的，彼此之间语义关联较弱，导致模型内部的注意力模式呈现出“块对角（block-diagonal）”特性。这意味着在解码过程中，大部分跨段落的注意力计算是冗余且不必要的。

基于这一洞察，研究者提出了 REFRAG，一个专为 RAG 应用设计的、能 **“压缩、感知和扩展”上下文的高效解码框架**。实验结果表明，REFRAG 可以在不损失模型效果（Perplexity）的前提下，实现高达 **30.85 倍**的 TTFT 加速，并将 LLM 的有效上下文窗口扩展 16 倍。

## REFRAG 的核心思想与架构

REFRAG 的核心思想是：**用预先计算好的、压缩后的“块嵌入（chunk embeddings）”来替代大部分原始的上下文 Token**。这从根本上缩短了输入到解码器的序列长度，从而解决了延迟和内存占用的瓶颈。

其模型架构如「图1」所示，主要由两部分构成：

- **轻量级编码器（Light-weight Encoder）**：例如 RoBERTa。它的任务是将输入的上下文文本（Context Text）分割成多个固定大小的“块（chunks）”，并为每个块生成一个紧凑的向量表示，即“块嵌入”。这个过程可以预先计算并缓存，以实现高效复用。
- **解码器（Decoder-only Foundation Model）**：例如 LLaMA。它不再接收冗长的原始上下文 Token，而是接收用户的查询（Question）Token 和由编码器生成的“块嵌入”序列。

<figure>
  <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/11/cvrI9N.png" alt="REFRAG主要设计">
  <figcaption>Figure1 REFRAG主要设计</figcaption>
</figure>


这种架构带来了三大优势：

1. **缩短输入长度**：解码器的输入序列长度从 `(查询Token数 + 上下文Token数)` 锐减为 `(查询Token数 + 块数)`。由于一个块可以包含数十个 Token，输入长度被大幅压缩，显著降低了计算量。
2. **消除冗余计算**：块嵌入可以被预先计算和缓存。在多次推理或多轮对话中，相同的上下文段落无需重复编码。
3. **降低注意力复杂度**：注意力计算的复杂度从与上下文 Token 数量的二次方相关，转变为与块数量的二次方相关，极大地提升了效率。


## 关键技术：REFRAG 的训练方法

为了让解码器能够理解并有效利用这些“块嵌入”，REFRAG 采用了一套精心设计的训练流程，包含持续预训练（Continual Pre-training, CPT）和监督微调（Supervised Fine-tuning, SFT）两个阶段。其中，CPT 阶段是实现高效压缩的关键。

### 1. 重构任务（Reconstruction Task）

这是对齐编码器和解码器的核心步骤。在这一任务中，研究者**冻结解码器的参数**，只训练轻量级编码器和一个投影层（projection layer）。训练目标是让编码器生成的“块嵌入”经过投影后，能够被解码器准确地**重构**出原始的文本块。

> 这个设计的精妙之处在于，它强迫“块嵌入”必须包含足够的信息来还原原文，从而确保了压缩过程的信息保真度，使得嵌入向量成为原始文本块的一个忠实表征。
> 

### 2. 课程学习（Curriculum Learning）

直接从多个块嵌入中重构长文本是一项非常困难的任务。为了解决这一优化难题，REFRAG 引入了[课程学习（Curriculum Learning）](https://www.kimi.com/share/d334qnimisdmr5rv8rmg)策略。训练从最简单的任务开始，例如只用一个块嵌入重构一个文本块，然后逐步增加难度，过渡到用多个块嵌入重构多个文本块。如「图6」所示，训练过程中，简单任务（如 `1 x k`）的样本比例逐渐减少，而复杂任务（如 `256 x k`）的样本比例逐渐增加。

<figure>
  <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/11/jiyLZN.png" alt="训练期间课程学习中的数据混合">
  <figcaption>Figure6 训练期间课程学习中的数据混合</figcaption>
</figure>


### 3. 基于强化学习的选择性压缩（RL-based Selective Compression）

REFRAG 的一个重要创新是并非所有上下文都同等重要。某些关键的文本块可能需要以原始 Token 的形式呈现给解码器，以获得最精确的答案。为此，REFRAG 引入了一个基于强化学习（Reinforcement Learning, RL）的轻量级策略网络。

该策略网络学习判断哪些文本块应该被“扩展”为原始 Token，哪些可以保持为压缩的“块嵌入”。其奖励信号是解码器在预测下一个段落时的困惑度（Perplexity）的负数。通过这种方式，模型学会在效率和精度之间做出动态权衡：

- **对于信息量大、与查询高度相关的关键块，策略网络会选择扩展它们**，确保解码器能获取最完整的信息。
- **对于大部分辅助性或冗余的上下文，则保持其压缩状态**，以最大化效率。

这种“随处压缩（compress anywhere）”的能力使得 REFRAG 非常灵活，能够支持多轮对话和复杂的智能体（agentic）应用。

## 实验效果与分析

研究者在多个数据集上对 REFRAG 进行了严谨的评估，并与 LLaMA、CEPE 等多个基线模型进行了比较。

### 延迟与吞吐量

如「图2」所示，REFRAG 在系统性能上取得了显著提升。

<figure>
  <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/11/a0ZWgr.png" alt="REFRAG在𝑘=16时的推理加速经验验证。">
  <figcaption>Figure2 REFRAG在𝑘=16时的推理加速经验验证。</figcaption>
</figure>

- **TTFT 加速**：在 16384 个 Token 的中长上下文场景下，当压缩率 `k=16` 时，REFRAG (Cached) 实现了 **16.53 倍**的 TTFT 加速，是当时 SOTA 模型 CEPE (2.01x) 的 8 倍以上。当压缩率 `k=32` 时，TTFT 加速更是达到了 **30.85 倍**。
- **吞吐量提升**：相较于 LLaMA，REFRAG 实现了高达 **6.78 倍**的吞吐量提升，同样远超 CEPE。

### 模型效果（Perplexity）

性能的提升并未以牺牲模型效果为代价。如「表1」和「表 2」所示，在 ArXiv、Book 等多个评估数据集上：

- REFRAG 在不同压缩率下（`REFRAG8`, `REFRAG16`）的困惑度均优于 CEPE、REPLUG 等基线模型。
- 即使面对比训练时更长的上下文，REFRAG 依然能保持优异的性能，证明了其良好的泛化能力。
- 与 LLaMA 相比，REFRAG 的 TTFT 加速 16.53 倍，同时在四个数据集上的平均困惑度还**提升了 9.3%**。

![table 1、table 2](https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/11/RHoonL.png)


### 下游应用性能

1. **RAG 性能**：在 RAG 任务中，无论是在强检索器还是弱检索器场景下，REFRAG 都表现出色。如 [图 4] 所示，在**同等延迟**下（例如 REFRAG 处理 8 个段落 vs LLaMA 处理 1 个段落），REFRAG 由于能看到更广的上下文，其平均性能提升了 1.22% (强检索器) 到 1.93% (弱检索器)。
    
    <figure>
        <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/11/zXPoOt.png" alt="强检索器场景（左）与弱检索器场景（右）下的 RAG 性能对比">
        <figcaption>Figure4 强检索器场景（左）与弱检索器场景（右）下的 RAG 性能对比</figcaption>
    </figure>
    
2. **多轮对话**：在多轮对话任务中，传统模型因上下文窗口限制（如 LLaMA 的 4k）不得不截断历史对话，导致信息丢失。而 REFRAG 凭借其压缩能力，可以在有限的计算预算内保留更完整的对话历史，从而在多个数据集上显著优于基线模型（「表 4」）。

    <figure>
        <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/11/6EtkQl.png" alt="在多轮RAG任务上的表现，对于#段落=5和#段落=10的情况。">
        <figcaption>Table4 在多轮RAG任务上的表现，对于#段落=5和#段落=10的情况。</figcaption>
    </figure>
    

## 结论

REFRAG 提出了一种专为 RAG 应用优化的新型解码框架。它通过一个轻量级编码器将冗长的上下文压缩为高效的“块嵌入”，并利用强化学习策略智能地决定何时解压关键信息，从而在不牺牲模型精度的前提下，极大地降低了 RAG 系统的推理延迟、提升了吞吐量。

这项工作不仅为解决 LLM 在长上下文应用中的效率瓶颈提供了一个实用且可扩展的方案，也揭示了针对特定应用场景（如 RAG）设计专门优化策略的重要性，为未来高效大模型推理系统的发展开辟了新的方向。
