---
title: "LoRA：无憾之选-Thinking Machines"
showAuthor: false
date: 2025-10-01
description: "LoRA-Without-Regret-ThinkingMachines"
slug: "LoRA-Without-Regret-ThinkingMachines"
tags: ["翻译", "LLM", "微调", "LoRA", "ThinkingMachines"]
# series: [""]
# series_order: 1
draft: false
---

<!-- 渲染公式 -->
{{< katex >}}

<!-- # 译文-LoRA：无憾之选-Thinking Machines -->

![image.png](https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/11/shReGW.png)

> [blog](https://thinkingmachines.ai/blog/lora/)

## TL;DR

Thinking Machines 通过大量实验证明，在后训练（Post-Training）阶段，只要正确掌握关键细节，**LoRA 能够以更高的计算效率和更低的内存占用，达到与全量微调（FullFT）完全相同的最终性能和样本效率**。这被称为“低悔恨区域（low-regret regime）”。

### **关键实验发现**

*   **1. 监督微调（SFT）的表现**
    *   **中小数据集**：在指令微调和推理任务的中小型数据集上，LoRA 的表现与 FullFT 持平。
    *   **容量限制**：当数据集过大且超过 LoRA 的参数容量时，性能会不如 FullFT。
    *   **Batch Size 敏感性**：LoRA 对大批量（Large Batch Size）的容忍度低于 FullFT。当批量过大时，无论秩（Rank）多高，LoRA 的损失都会受到惩罚。

*   **2. 强化学习（RL）的表现**
    *   **极低秩依然有效**：在 RL（如 PPO/GRPO）中，即使 **Rank=1**，LoRA 也能完全匹配 FullFT 的性能。
    *   **理论解释**：基于信息论，RL 每个 episode 提供的有效信息量极低（约 1 bit，仅依靠标量奖励信号），因此不需要像监督学习那样大的参数容量。

*   **3. LoRA 的应用范围（关键！）**
    *   **必须覆盖所有层**：要达到 FullFT 的效果，必须将 LoRA 应用于**所有权重矩阵**，特别是 **MLP 和 MoE 层**。
    *   **仅 Attention 是不够的**：仅在 Attention 层使用 LoRA 效果明显较差，即使增加秩也无法弥补这一差距。

### **超参数与工程细节**

*   **学习率（LR）设置**：
    *   LoRA 的最佳学习率通常是 **FullFT 的 10 倍**。
    *   由于引入了 $1/r$ 的缩放因子，LoRA 的最佳学习率在不同秩（Rank）下大致保持不变（独立于秩）。
    *   对于短时间的训练任务，可能需要更高的学习率乘数（约 15 倍）。

*   **计算效率**：
    *   LoRA 的训练计算量（FLOPs）约为 FullFT 的 **2/3**（因为反向传播时无需计算庞大权重矩阵的梯度）。
    *   LoRA 在多租户服务（Multi-tenant serving）和显存占用上具有天然优势。

### **实操建议总结**
1.  **范围**：对所有层（特别是 MLP/MoE）启用 LoRA，不要只微调 Attention。
2.  **LR**：将学习率设置为全量微调最佳 LR 的 10 倍左右。
3.  **Batch Size**：避免使用过大的 Batch Size。
4.  **RL 场景**：在强化学习中可以放心使用非常低的秩（如 Rank 8-16），效果不会打折。

---

## 引言


当今领先的语言模型包含超过万亿参数，在数十万亿tokens上进行预训练。基础模型的性能随着规模不断提升，因为这些万亿参数对于学习和表示书面人类知识中的所有模式是必要的。

相比之下，后训练涉及更小的数据集，通常聚焦于更狭窄的知识领域和行为范围。使用太字节（terabit）的权重来表示来自千兆字节（gigabit）或兆字节（megabit）训练数据的更新似乎是浪费的。这种直觉激发了参数高效微调（Parameter Efficient Fine-Tuning，PEFT），它通过更新一组更小的参数来调整大型网络。

领先的PEFT方法是低秩适应（Low-Rank Adaptation），即LoRA。LoRA将原始模型中的每个权重矩阵 \(W\) 替换为修改后的版本 \(W' = W + \gamma BA\) ，其中B和A是矩阵，它们一起包含的参数远少于W，\(\gamma\) 是一个常数缩放因子。实际上，LoRA创建了微调所带来更新的低维表示。

LoRA可能在后训练的成本和速度方面提供优势，并且还有一些操作性原因使其优于完整微调（以下简称FullFT）：

- **多租户服务（Multi-tenant serving）**。由于LoRA训练一个适配器（即A和B矩阵）同时保持原始权重不变，单个推理服务器可以在内存中保留许多适配器（不同的模型版本）并以批处理方式同时从它们采样。[Punica: Multi-Tenant LoRA Serving](https://arxiv.org/abs/2310.18547)（Chen, Ye等，2023）现代推理引擎如vLLM和SGLang实现了此功能。
- **训练的布局大小（Layout size for training）**。当微调整个模型时，优化器状态需要与原始权重一起存储，通常以更高的精度存储。因此，FullFT通常需要比从同一模型采样多一个数量级的加速器，从而需要不同的布局。对于训练，除了存储权重外，我们通常还需要为所有权重存储梯度和优化器动量；此外，这些变量通常以比推理时用于存储权重的精度（bfloat16或更低）更高的精度（float32）存储。由于LoRA训练的权重少得多且使用的内存少得多，它可以在仅比用于采样的布局稍大的布局上进行训练。这使得训练更容易获得，并且通常更高效。
- **加载和传输的便利性（Ease of loading and transfer）**。由于存储的权重更少，LoRA适配器在设置或在机器之间传输时速度快且容易。

这些原因足以解释自2021年原始LoRA论文发表以来LoRA日益增长的流行度。[LoRA: Low-Rank Adaptation of Large Language Models](https://arxiv.org/abs/2106.09685)（Hu等，2021）然而，文献对于LoRA相对于FullFT的表现如何尚不清楚。

人们一致认为LoRA在类似预训练的设置中表现不佳，[LoRA Learns Less and Forgets Less](https://arxiv.org/abs/2405.09673)（Biderman等，2024）即那些具有非常大数据集且超过LoRA参数存储限制的情况。但对于后训练中典型的数据集大小，LoRA有足够的容量来存储必要的信息。然而，这一事实并不保证样本效率和计算效率。问题是：LoRA能否匹配完整微调的性能，如果能，在什么条件下？

在我们的实验中，我们发现确实，当我们正确掌握几个关键细节时，LoRA以与FullFT相同的样本效率学习并达到相同的最终性能。

## 对于LoRA重要的因素

本文涵盖了我们进行的一系列监督微调和强化学习实验，以确定LoRA在哪些条件下匹配FullFT效率。为此，我们与之前关于LoRA的实验做了一些不同的事情：

- 我们研究了训练集大小和LoRA参数数量之间的一般关系，而不是专注于特定的数据集和任务。
- 在监督学习中，我们测量对数损失（log loss）而不是采用基于采样的评估，同样以普遍性为目标。对数损失测量在训练步数和训练参数的范围内给出了干净的结果和缩放定律（scaling laws）。

我们发现：

- 对于小型到中型指令调整和推理数据集上的监督微调，LoRA的表现与完整微调相同。
- 对于超过LoRA容量的数据集，LoRA表现不如FullFT。损失并非达到一个无法突破的明确下限，而是LoRA导致训练效率下降，这取决于模型容量与数据集大小之间的关系。
- 在某些情况下，LoRA对大批量大小的容忍度低于完整微调——当批量大小增加超过某一点时，它在损失方面付出更大的代价。增加LoRA秩（rank）无法缓解这一惩罚；这是矩阵乘积参数化的一个特性，它具有与优化原始权重矩阵不同的训练动态。
- 即使在小数据设置中，当应用于所有权重矩阵，特别是MLP和MoE层时，LoRA表现更好。仅注意力（attention-only）LoRA表现不佳，即使我们通过对仅注意力LoRA使用更高的秩来匹配可训练参数的数量。
- 即使秩很小，LoRA在强化学习中的表现也等同于FullFT。我们发现RL需要非常低的容量，基于信息论论证，我们预期到这一结果。

我们还研究了用于LoRA的超参数对其相对于完整微调的学习率的影响。我们检查了超参数（如初始化尺度和乘数）中的一些不变性，并解释为什么1/r预因子使最优学习率（LR）近似独立于秩。我们还通过实验展示了LoRA的最优LR与FullFT的最优LR之间的关系。

我们实验的结果是对"低悔恨区域"（low-regret regime）的描述，在该区域中，LoRA在数据集大小和LoRA参数方面的表现与FullFT相似。我们发现这个区域涵盖了大多数后训练场景，为在许多应用中使用高效微调打开了大门。

## 方法和结果

我们设计实验来详细测量LoRA在一系列条件下相对于FullFT的性能。以下是我们实验设置的一些细节：

- 我们在三个数量级上改变LoRA秩，秩在1到512之间，并将这些与完整微调进行比较。
- 为了消除使用次优学习率带来的潜在混淆，我们为每个实验条件扫描了LR。我们使用恒定学习率计划（无预热或冷却）。
- 我们的实验使用了Llama 3系列模型 [The Llama 3 Herd of Models](https://arxiv.org/abs/2407.21783)（Dubey等，2024）和Qwen3模型 [Qwen3 Technical Report](https://arxiv.org/abs/2505.09388)（Qwen团队，2025），包括一个混合专家（MoE）模型。
- 主要的监督学习实验使用了Tulu3 [Tulu 3: Pushing Frontiers in Open Language Model Post-Training](https://arxiv.org/abs/2411.15124)（Ivison等，2024）和OpenThoughts3 [OpenThoughts: Data Recipes for Reasoning Models](https://arxiv.org/abs/2506.04178)（Guha等，2025）数据集，分别聚焦于指令遵循和推理。这两组在范围、结构和应用上差异显著，支持了我们结果的普遍性。
- 我们的RL实验使用数学推理任务，以答案正确性作为奖励。

### LoRA秩

我们在Tulu3数据集和OpenThoughts3数据集的子集上训练了一个epoch。对于每个数据集和模型大小，我们扫描了LoRA秩和学习率。在下面的图中，我们为每个秩绘制一条彩色线，其中该线是通过在每个训练步骤取所有学习率上的逐点最小值获得的：

<figure>
  <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/11/YeIIul.png" alt="Tulu3和OpenThoughts3数据集上各种等级的LoRA训练曲线。FullFT和高等级LoRA具有相似的学习曲线，损失随着步数的对数线性下降。当适配器容量不足时，低等级LoRA会脱离最小损失曲线。在底部图表中（1B模型），高等级LoRA在一个数据集上表现优于FullFT，而在另一个数据集上表现较差。由于训练动态或泛化行为的差异，LoRA在不同数据集上的表现可能存在一些随机变化。">
  <figcaption style="text-align: center;">图1：Tulu3和OpenThoughts3数据集上各种等级的LoRA训练曲线。FullFT和高等级LoRA具有相似的学习曲线，损失随着步数的对数线性下降。当适配器容量不足时，低等级LoRA会脱离最小损失曲线。在底部图表中（1B模型），高等级LoRA在一个数据集上表现优于FullFT，而在另一个数据集上表现较差。由于训练动态或泛化行为的差异，LoRA在不同数据集上的表现可能存在一些随机变化。</figcaption>
</figure>

我们看到FullFT和高秩LoRA具有相似的学习曲线，损失随步数的对数线性减少。中等和低秩LoRA在某个与秩相关的步数阈值处脱离最小损失学习曲线。直观地说，当适配器耗尽容量时学习会减慢，而容量又由秩决定。

接下来，我们绘制损失如何随LR变化，以检查我们的扫描是否涵盖了每个秩的最佳学习率。

<figure>
  <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/11/2DQc66.png" alt="在 Tulu3 上，各种 LoRA 秩的学习率与最终损失。高秩 LoRA 和 FullFT 的最小损失大致相同。LoRA 的最佳 LR 高 10 倍。">
  <figcaption style="text-align: center;">图2：在 Tulu3 上，各种 LoRA 秩的学习率与最终损失。高秩 LoRA 和 FullFT 的最小损失大致相同。LoRA 的最佳 LR 高 10 倍。</figcaption>
</figure>

我们发现FullFT的最优学习率比高秩LoRA低10倍。参见Biderman等（2024），图S1，对于使用采样评估的实验，它发现了类似的10倍比率。我们将在稍后讨论LoRA超参数时回到这一点。

所有不同秩的LoRA运行的最优LR似乎相似；我们在下面为这一发现提供理论解释。然而，确实存在一些秩依赖性，Rank=1的最优LR低于更高秩LoRA。在Rank=4和Rank=512之间，最优LR变化不到2倍。

#### 批量大小效应

我们发现在某些设置中，LoRA对大批量大小的容忍度低于FullFT。性能差距随着更大的批量大小而增长，与秩无关。对于下一个实验，我们使用了 OpenThoughts3 的一个小型10,000示例子集。

<figure>
  <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/11/fhgfHD.png" alt="批量大小对LoRA与FullFT性能的影响。左图：不同批量大小的学习曲线显示，在较大的批量大小下，LoRA（虚线）和FullFT（实线）之间存在持续的差距。右图：最终损失作为批量大小的函数，显示LoRA为增加的批量大小付出了更大的代价。">
  <figcaption style="text-align: center;">图3：批量大小对LoRA与FullFT性能的影响。左图：不同批量大小的学习曲线显示，在较大的批量大小下，LoRA（虚线）和FullFT（实线）之间存在持续的差距。右图：最终损失作为批量大小的函数，显示LoRA为增加的批量大小付出了更大的代价。</figcaption>
</figure>

图3中的左侧图显示，在大批量大小下，LoRA（虚线）和FullFT（实线）学习曲线之间存在持续的差距。对于较小的批量大小32，差距较小并随时间缩小。

右侧图表将最终损失绘制为批量大小的函数。我们看到LoRA的损失差距随着更大的批量大小而越来越偏离FullFT。

大批量下的学习差距似乎不依赖于秩，而是LoRA的一个特性。可能的原因是矩阵乘积参数化（BA）在该数据集上的优化动态不如完整矩阵（W）有利。然而，LoRA和FullFT都在较小的批量大小下达到最佳损失，因此这个差距在实践中可能不那么重要。

## 应用LoRA的层

我们研究了将LoRA应用于网络中不同层的效果。Hu等的原始论文建议仅将LoRA应用于注意力矩阵，许多后续论文也遵循了这一建议，尽管最近的趋势是将其应用于所有层。与我们的结果类似，QLoRA论文也发现LoRA表现不如MLP或MLP+注意力，尽管他们发现MLP+注意力 > MLP > 注意力，而我们发现前两者大致相同。实际上，当将LoRA应用于所有层，特别是MLP（包括MoE）层时，我们获得了更好的结果。事实上，将LoRA应用于注意力矩阵除了应用于MLP外没有显示出额外的好处。Biderman等（2024）获得了类似的结果，仅注意力LoRA在仅MLP之上没有提供额外好处。

<figure>
  <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/11/eoI3gK.png" alt="仅注意力机制的LoRA明显不如仅MLP的LoRA，并且在LoRA-on-MLP的基础上无法进一步提高性能。这种效应适用于密集模型（Llama-3.1-8B）和稀疏MoE（Qwen3-30B-A3B-Base）。">
  <figcaption style="text-align: center;">图4：仅注意力机制的LoRA明显不如仅MLP的LoRA，并且在LoRA-on-MLP的基础上无法进一步提高性能。这种效应适用于密集模型（Llama-3.1-8B）和稀疏MoE（Qwen3-30B-A3B-Base）。</figcaption>
</figure>

仅注意力LoRA的表现不佳不能用参数较少来解释。在这个特定案例中，秩256的仅注意力版本表现不如秩128的仅MLP版本，尽管它们的参数数量大致相同。（比较下表中的粗体数字。）

<figure>
  <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/11/Pz3BMb.png" alt="Llama-3.1-8B 上 LoRA 的参数计数">
  <figcaption style="text-align: center;">Llama-3.1-8B 上 LoRA 的参数计数</figcaption>
</figure>

对于MoE实验，我们为每个专家训练了一个单独的LoRA，每个专家的秩等于总秩除以活跃专家的数量（Qwen3 MoE等于8）。这种缩放使MoE层的LoRA参数与FullFT参数的比率与其他层相同。

我们在另外两个设置中进行了类似的实验，比较不同的LoRA层：（1）在OpenThoughts3数据集的小子集上进行监督学习，秩=256，以及（2）在MATH数据集上进行强化学习。我们在下一节描述我们的实验设置。在这些设置中，仅注意力LoRA表现也不如仅MLP LoRA（其表现与MLP+注意力相似）。

<figure>
  <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/11/xE8RLf.png" alt="当改变我们应用LoRA的层时，学习率与最终损失或奖励的关系。">
  <figcaption style="text-align: center;">图5：当改变我们应用LoRA的层时，学习率与最终损失或奖励的关系。</figcaption>
</figure>


### 强化学习

我们实验的一个关键发现是，当运行强化学习的策略梯度算法时，即使秩低至1，LoRA也完全匹配FullFT的学习性能。

对于这些实验，我们使用了一个基本的策略梯度算法，带有重要性采样修正；\(\text{objective} =\sum_t \frac{p_{\text{learner}}}{p_{\text{sampler}}} Adv_t\)（参见 [Your Efficient RL Framework Secretly Brings You Off-Policy RL Training](https://fengyao.notion.site/off-policy-rl)

）。我们使用了类似GRPO的中心化方案[🔗](https://arxiv.org/abs/2402.03300)（Shao等，2024），其中我们为每个问题采样多个完成并减去每组的平均奖励。

图6（下方）显示了在MATH [🔗](https://arxiv.org/abs/2103.03874)（Hendrycks等，2021）和GSM [🔗](https://arxiv.org/abs/2110.14168)（Cobbe等，2021）数据集上的LR扫描，为每个使用典型的超参数。我们使用Llama-3.1-8B基础模型，因为已知Qwen2.5和Qwen3在预训练数据上改善了其数学性能，如Qwen技术报告所述[🔗](https://arxiv.org/abs/2412.15115)（Qwen团队，2024），这使得更难测量仅在RL期间学习的内容。

LoRA显示出更宽的有效学习率范围，并达到与FullFT（黑线）相同的峰值性能，至少在RL的噪声所允许的精度限制内。

<figure>
  <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/11/LCyVtg.png" alt="在小学数学（GSM，左图）或 MATH（右图）数据集上进行强化学习时，学习率与最终奖励（准确率）的关系。">
  <figcaption style="text-align: center;">图6：在小学数学（GSM，左图）或 MATH（右图）数据集上进行强化学习时，学习率与最终奖励（准确率）的关系。</figcaption>
</figure>

这一结果由信息论论证所预期。监督学习可以说每个episode提供O（token数量）比特。相比之下，在策略梯度方法中，学习由优势函数（advantage function）驱动，该函数每个episode仅提供O（1）比特。当每个episode包含数千个token时，RL每个训练token吸收的信息比监督学习少约1000倍。

我们可以根据我们的实验使用更精确的数字。在MATH示例中，我们训练了约10,000个问题，每个问题32个样本。假设每个完成产生一个信息比特，整个训练过程只需要吸收320,000比特。Llama-3.1-8B的rank-1 LoRA已经有300万个参数（*我们通过在模型中所有权重矩阵上相加 \(rank·d_{in}\)（对于矩阵A）和 \(rank·d_{out}\)（对于矩阵B）来计算这一点。*），几乎是那个数字的10倍。即使在rank-1时，LoRA也有足够的容量来吸收训练期间提供的所有信息。

作为另一个比较点，[DeepSeek-R1-Zero](https://www.nature.com/articles/s41586-025-09422-z) 在530万个episode上训练（*训练进行了10,400步，每步包含32个独特问题，每个问题采样16次）*，对应于530万比特的信息。这少于低秩LoRA中的参数数量，我们预测结果可以用LoRA复现。

为了进一步验证我们关于LoRA在推理RL中有效性的发现，我们使用Qwen3-8b-base在DeepMath数据集[🔗](https://arxiv.org/abs/2504.11456)（He等，2025）上进行了更大规模的实验，因为它比MATH数据集大得多，通常包含更难的问题。为了加快实验速度，我们将样本限制为8192个token的长度用于训练和评估。这个样本长度允许回溯和推理，但相对于更长的思维链限制了性能。

<figure>
  <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/11/EiFxar.png" alt="在 DeepMath 数据集上使用 Qwen3-8b-base 进行的实验。在左图中，我们展示了不同秩和完全微调的学习曲线。对于每种设置，我们都展示了最佳学习率，从而产生最高的最终性能。在右图中，我们绘制了学习率与最终性能的关系图。与我们之前的数学实验一样，LoRA 似乎具有更宽的接近最佳学习率的峰值。">
  <figcaption style="text-align: center;">图7：在 DeepMath 数据集上使用 Qwen3-8b-base 进行的实验。在左图中，我们展示了不同秩和完全微调的学习曲线。对于每种设置，我们都展示了最佳学习率，从而产生最高的最终性能。在右图中，我们绘制了学习率与最终性能的关系图。与我们之前的数学实验一样，LoRA 似乎具有更宽的接近最佳学习率的峰值。</figcaption>
</figure>

<figure>
  <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/11/6gwnFS.png" alt="图8：来自 DeepMath 数据集和 Qwen3-8b-Base 的实验的其他图表。左图显示了 AIME 测试集上的基准分数，该测试集比训练集更具挑战性。右图显示了训练步骤中的思维链 (CoT) 长度，这可以被看作是学习推理的标志。">
  <figcaption style="text-align: center;">来自 DeepMath 数据集和 Qwen3-8b-Base 的实验的其他图表。左图显示了 AIME 测试集上的基准分数，该测试集比训练集更具挑战性。右图显示了训练步骤中的思维链 (CoT) 长度，这可以被看作是学习推理的标志。</figcaption>
</figure>

我们观察到，当为每个设置选择最优学习率时，不同大小的LoRA和完整微调的训练进展几乎相同。此外，当我们在AIME 2024和AIME 2025的保留问题上评估模型时，我们看到类似的发现。此外，我们从LoRA和完整微调运行中观察到类似的定性行为：两者都发展出高级推理行为，如回溯、自我验证和上下文探索，这在模型CoT的延长中是可见的。

## 设置LoRA超参数

LoRA采用的一个障碍是需要选择最优超参数，这些超参数与为FullFT优化的超参数不同。在本节中，我们表明这个问题并不像乍看起来那么令人生畏，并讨论我们与超参数选择相关的发现。

### 最优学习率和秩

遵循Hu等，我们考虑以下LoRA参数化：

$$
W' = W + \frac{\alpha}{r}BA
$$

其中 \(r\) 是LoRA秩，\(\alpha\) 是LoRA缩放因子，\(A\)、\(B\) 是LoRA权重矩阵（秩为 \(r\)）。我们对本文中的实验使用 \(\alpha = 32\)，遵循其他实现的标准实践。

\(1/r\) 缩放因子使最优学习率近似独立于秩。事实上，一个更强的条件成立——在训练开始时学习曲线完全相同，无论秩如何。这种效果是惊人的，在我们的实验中，不同秩的学习曲线的接近程度让我们担心bug导致秩参数被忽略。因此，在短训练区域中，最优LR也独立于秩。然而，如我们在学习率与损失的图（图2）中所示，在更长训练区域中，最优LR对秩有一定依赖性。

<figure>
  <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/11/k1Byty.png" alt="这些图着眼于在训练初期，对于具有相同学习率的不同秩的学习曲线的差异。左图显示了学习曲线。右图显示了秩 16 和 256 之间的差异，这种差异随着时间的推移而增大。奇怪的是，在最初的几个步骤中，它是负的（尽管很小），因此曲线的这一部分在图中缺失了。">
  <figcaption style="text-align: center;">图9：这些图着眼于在训练初期，对于具有相同学习率的不同秩的学习曲线的差异。左图显示了学习曲线。右图显示了秩 16 和 256 之间的差异，这种差异随着时间的推移而增大。奇怪的是，在最初的几个步骤中，它是负的（尽管很小），因此曲线的这一部分在图中缺失了。</figcaption>
</figure>

我们可以通过查看第一次训练更新后LoRA矩阵的预期更新来部分解释这一结果。我们可以将LoRA乘积 \(BA\) 视为 \(r\) 个rank-1外积的总和：\(BA = \sum_{i=1}^r b_i a_i^T = \sum_{i=1}^r \Delta_i\)，其中我们定义 \(\Delta_i = b_i a_i^T\)。这里，\(\partial \text{Loss}/\partial \Delta_i\) 对所有 \(i\) 都相同；然而梯度 \(\partial \text{Loss}/\partial b_i\) 和 \(\partial \text{Loss}/\partial a_i\) 将依赖于初始化（例如，\(\partial \text{Loss}/\partial b_i\) 依赖于 \(a_i\）。由于 \(a_i\) 和 \(b_i\) 的初始化不依赖于秩，因此 \(\mathbb{E}[\Delta_i]\) 对所有 \(i\) 都相同且不依赖于秩。在训练的第一步，每个这些项的预期更新相等且独立于秩。因此 \((1/r)\sum_{i=1}^r \Delta_i\) 只是 \(r\) 个具有相同期望的项的样本平均值，所以平均值的期望，即适配器 \((1/r)BA\) 的变化，不依赖于秩。

### 参数化不变性

LoRA可能适用四个超参数：

1. 出现在 \(α / r\) 中的缩放因子 \(α\)。
2. 下投影矩阵 \(A\) 的学习率，\(LR_A\)。
3. 上投影矩阵 \(B\) 的学习率，\(LR_B\)。
4. 矩阵 \(A\) 的初始化尺度，\(\text{init}_A\)。对于随机初始化，这是 \(A\) 初始元素的标准差。矩阵 \(B\) 初始化为零，因此不需要定义 \(\text{init}_B\)。

必须调整四个不同的参数似乎令人不知所措。然而，训练动态中的不变性意味着其中两个是冗余的，学习行为由两个决定。我们通过注意到当使用Adam训练且 \(ε = 0\) 时*（我们可以将此结果扩展到 \(ε > 0\)；我们需要将其缩放 \(1/q\)，因为梯度按该因子缩放）*，优化过程对以下两参数变换是不变的。

对于 \(p, q > 0\)：

- \(α → \frac{1}{pq} \cdot α\)
- \(\text{init}_A → p \cdot \text{init}_A\)
- \(LR_A → p \cdot LR_A\)
- \(LR_B → q \cdot LR_B\)

由于四个自由度中的两个不影响学习过程，我们剩下一个2D参数空间。我们可以为这个2D空间选择不同的基，例如以下这个便于直接解释：

- \(α \cdot \text{init}_A \cdot LR_B\)。这决定了初始更新的规模，或者等效地，学习曲线的初始斜率。由于 \(B\) 初始化为零，\(LR_A\) 和对 \(A\) 的初始更新无关紧要。
- \(\text{init}_A / LR_A\)。由于Adam在每一步将 \(A\) 的元素更新约 \(LR_A\) ，这个时间尺度参数决定了将 \(A\) 显著转换离开其初始状态所需的步数。

我们可以用这个基础重新解释之前关于LoRA的一些提案。

LoRA+ [🔗](https://arxiv.org/abs/2402.12354) （Hayou等，2024）提议对 \(A\) 和 \(B\) 使用不同的LR，\(B\) 的速率更高。用我们上面的基础表示，增加 \(LR_B\) 等价于增加 \(\text{init}_A/LR_A\)，使 \(A\) 在更长的时间尺度上变化。

[Unsloth的LoRA超参数指南](https://docs.unsloth.ai/get-started/fine-tuning-llms-guide/lora-hyperparameters-guide)建议对高秩LoRA使用更高的 \(α\) 值，例如通过避免 \(1/r\) 缩放。这也等价于增加 \(\text{init}_A/LR_A\)。当我们增加 \(α\) 时，需要相应降低 \(LR_A\) 和 \(LR_B\) 以获得相同的更新大小。这反过来简单地使 \(LR_A\) 相对于 \(\text{init}_A\) 更小。

在我们的实验中，我们使用了Huggingface [`peft`](https://github.com/huggingface/peft)库中使用的标准参数化（Mangrulkar等，2022），由Hu等提出：\(A\) 使用尺度为 \(1/\sqrt{d_{in}}\) 的均匀分布，\(B\) 零初始化，两者使用相同的LR，\(α = 32\)。在我们的调参过程中，未能找到比该组合更优的超参数。

### LoRA与FullFT的最优学习率

我们的实验表明，对于相同应用，LoRA的最优LR始终是FullFT使用的10倍，无论是监督学习还是强化学习。这显示在每个性能（损失或奖励）相对于学习率的U形图中。这一观察应该使从FullFT到LoRA的学习超参数转移更加直接。

我们尚未对这一观察有充分的理论解释。我们可以尝试从最优LoRA LR对秩不变以及完整秩LoRA与FullFT直接可比这些事实推导出这一结果。这种分析建议LR比率为模型的隐藏大小除以 \(2 \cdot \alpha\)，这与最优比率固定为10且独立于基础模型的经验结果不匹配。

对于我们的经验分析，我们对14个不同的Llama和Qwen模型在Tulu3数据集上进行了LoRA和FullFT的LR扫描。根据这些扫描，我们拟合了一个函数，该函数基于模型的隐藏大小和它是Llama还是Qwen的指示器来预测最优学习率。使用的函数形式为：

$$
\text{LR} = M_{\text{LoRA}} \cdot \left(\frac{2000}{\text{hidden size}}\right)^{\text{model pow} + \text{LoRA pow}}
$$

其中：

- \(M_{\text{LoRA}}\) 是使用LoRA时应用的乘数（如果是FullFT则为1）
- \(\text{model pow}\) 是指数调整，为每个模型源（Llama和Qwen）分别计算
- \(\text{LoRA pow}\) 是LoRA的额外指数调整
- \(\text{hidden size}\) 是模型残差流（residual stream）的维度。

我们通过使用线性插值根据我们扫描的数据预测损失来对预测的学习率进行评分，并通过对14个问题的预测损失求和来评估参数。我们的优化发现LoRA相对于FullFT的乘数为9.8，Qwen3和Llama模型对hidden_size的依赖性不同，但LoRA LR对hidden_size的依赖性与FullFT LR相同，即优化发现 \(\text{LoRA pow} = 0\)。

### 短期和长期运行中的学习率

LoRA的典型初始化在有效学习率的变化中创建了一个隐式计划。这导致短期和长期训练运行之间的差异，以及与FullFT相比学习曲线形状的一些差异。

在训练开始时，\(B\) 初始化为零。当 \(B\) 非常小时，对 \(A\) 的更改对添加到原始网络权重的适配器 \(BA\) 的影响可以忽略不计。随着 \(B\) 变大，对 \(A\) 的更新开始对网络输出产生更大的影响，有效学习率在训练过程中随着 \(B\) 在规模上接近 \(A\) 而增加。我们发现，到Tulu3和OpenThoughts数据集上完整训练运行结束时，\(B\) 矩阵的谱范数（spectral norms）最终大于 \(A\) 矩阵。

这意味着对于较短的训练运行，最优LR应该设置得更高。初步证据表明，对于短运行基于传闻证据，更高的乘数在约100步或更少时有效。，相对于FullFT的最优乘数约为15倍，对于更长的运行收敛到前述的10倍乘数。

## 讨论

我们希望超越我们的经验结果，讨论一些与LoRA性能和适用性相关的更广泛的考虑因素，这些因素对研究人员和构建者都会感兴趣。

首先，让我们更深入地检查我们的主要结果，即LoRA表现与完整微调类似的两个条件：

1. LoRA应用于网络的所有层，特别是容纳大多数参数的MLP/MoE层。
2. LoRA在不受容量约束时表现良好，即可训练参数的数量超过要学习的信息量，这可以根据数据集大小估计。

当（1）满足时，我们在训练开始时获得与FullFT类似的学习动态。然后，根据（2），LoRA继续看起来像FullFT，直到我们开始达到容量限制。

### 为什么可能需要在所有层上使用LoRA

如我们之前所示，如果我们仅将LoRA放在注意力层上，即使在微小数据区域，我们也会获得更慢的学习。

一种可能的解释可能来自将经验神经切线核（empirical Neural Tangent Kernel，eNTK）视为进行少量微调时发生情况的近似，遵循Malladi等。[A Kernel-Based View of Language Model Fine-Tuning](https://arxiv.org/abs/2210.05643)（Malladi等，2022）eNTK基于梯度的点积，具体来说是梯度 \(g_i = \partial/\partial\theta \log p(\text{token}_i | \text{prefix}_i)\)，以及 \(K(i, j) = g_i \cdot g_j\)。因此，具有最多参数的层通常对核具有最大的影响。该论文还指出，当您训练所有层时，LoRA的eNTK与完整微调的eNTK大致相同。因此LoRA训练 \(\approx\) eNTK（LoRA）\(\approx\) eNTK（FullFT）\(\approx\) FullFT。只有当我们将LoRA应用于包含构成点积的大多数参数的层时，近似eNTK（LoRA）\(\approx\) eNTK（FullFT）才成立。

### 监督学习和强化学习需要多少容量？

过去的工作[Physics of Language Models: Part 3.3, Knowledge Capacity Scaling Laws](https://arxiv.org/abs/2404.05405)（Allen-Zhu和Li，2024）表明神经网络可以每个参数存储2比特。这些结果涉及在长训练极限中吸收的最大信息量，而不是计算效率或学习速度。

每个参数2比特的结果依赖于巧妙构建的合成数据集，以包含精确量的信息。估计给定现实学习问题所需的信息内容并不那么直接。一个经典观察是，当最小化对数损失时，在第一个epoch期间测量的总对数损失提供了数据集描述长度的测量。也就是说，记忆数据集所需的比特数的上界。LLM数据集通常每个token的损失约为1比特（0.69 nats），具体取决于数据集和模型大小。

这个估计测量了完美记忆数据集所需的容量，这高估了减少测试数据对数损失的"可泛化"学习所需的实际容量。测量监督学习的容量要求以及这些要求如何与可训练参数数量相互作用是未来工作的一个开放问题。

对于RL，我们声称策略梯度算法每个episode学习大约1比特的信息，因为在episode结束时有一个单一的奖励值。这不是RL的基本属性，因为其他算法可以想象从每个episode中学习更多。例如，基于模型的RL算法训练学习代理预测观察并构建世界模型，可能从每个episode中提取更多信息。每个episode 1比特的声明可能仅狭义地适用于策略梯度算法。

我们可以用信息论术语来完善比特计数论证。将一个episode（由轨迹 \(\tau\) 和最终奖励组成）视为提供关于未知奖励函数 \(R\) 的一些信息的消息（即噪声信道）。我们将以当前策略和训练历史为条件，查看策略梯度估计器与 \(R\) 之间的互信息。REINFORCE更新是 \(G = S \cdot \text{Adv}\)，其中 \(S = \nabla \log p_\theta(\tau)\)。给定历史，\(S\) 独立于 \(R\)，因此唯一依赖于 \(R\) 的组件是标量优势。

根据数据处理不等式：

$$
I(G ; R | \text{history}) \leq I((S, \text{Adv}) ; R | \text{history}) = I(\text{Adv} ; R | S, \text{history}) \leq H(\text{Adv}).
$$

如果我们将优势量化为 \(B\) 个箱（bins），那么 \(H(\text{Adv}) \lesssim \log(B)\)。也就是说，每个episode获得的有用信息的比特数是 \(O(1)\)，独立于模型大小。这些比特告诉我们我们处于奖励函数的离散集合（或等效地，最优策略类）的哪个成员中。这种互信息分析反映了一些优化算法理论分析中使用的方法。[Information Complexity of Black-Box Convex Optimization: A New Look via Feedback Information Theory](https://www.mit.edu/~rakhlin/papers/ibc_optimization.pdf)（Raginsky和Rakhlin，2009）请注意，这个估计是训练吸收信息的上界；实际学习量将取决于策略初始化和其他细节。例如，如果我们用一个没有获得任何奖励的策略初始化，那么优势的熵为零（不是log(B)），它不会学到任何东西。

### LoRA的计算效率优势

我们上面的实验根据训练步数测量学习进度，但我们也可能对不同方法的计算效率感兴趣。我们计算出LoRA每次传递的FLOP略多于完整微调的⅔。因此，它通常在整体计算效率上优于FullFT。

我们通过分析给定权重矩阵上前向-反向传递中使用的FLOP来推导这个⅔比率。这些操作占神经网络模型中绝大多数FLOP。我们使用以下符号：

- \(W \in \mathbb{R}^{N \times N}\) 是权重矩阵
- \(x \in \mathbb{R}^N\) 是输入向量
- \(y = Wx \in \mathbb{R}^N\) 是输出向量
- \(\bar{x}, \bar{y} \in \mathbb{R}^N\) 是反向传递中计算的相对于 \(x\) 和 \(y\) 的损失梯度
- \(\bar{W} \in \mathbb{R}^{N \times N}\) 是相对于 \(W\) 的损失梯度

完整微调执行以下操作：

**前向**

- \(y = Wx\)（\(N^2\) 次乘加）

**反向**

- \(\bar{x} = W^T \bar{y}\)（\(N^2\) 次乘加）
- \(\bar{W} \mathrel{+}= x \bar{y}^T\)（\(N^2\) 次乘加）

前向传递需要 \(N^2\) 次乘加，反向传递需要另外 \(2 \cdot N^2\)，总共 \(3N^2\)。因此，需要两者的训练使用的FLOP是仅前向推理的3倍。

对于LoRA，我们用 \(W + BA\) 替换 \(W\)，其中 \(B \in \mathbb{R}^{N \times R}\) 和 \(A \in \mathbb{R}^{R \times N}\)，\(R \ll N\)。由于我们只更新 \(\bar{A}\) 和 \(\bar{B}\)，我们用一个便宜得多的操作替换更新 \(\bar{W}\) 的第三步。\(A\) 和 \(B\) 是 \(N \cdot R\) 矩阵，因此每个上的完整前向-反向计算需要 \(3NR\) 次乘加，而不是 \(W\) 的 \(3N^2\)。两者的总和是 \(6NR\)。我们还对 \(Wx\) 和 \(\bar{x}\) 执行前向-反向传递，相当于FullFT的前两步。乘加的总数是 \(2N^2 + 6NR\)。当 \(R \ll N\) 时，这略多于 \(3N^2\) 的 \(\frac{2}{3}\)。

如果我们根据FLOP这种分析省略了用于注意力的FLOP，在长上下文设置中可能很重要。而不是训练步数绘制LoRA性能，它将显示出相对于FullFT的明显优势。

### 开放问题

与我们的结果相关的几个问题，我们希望在未来看到研究：

- **完善我们对LoRA性能的预测**以及它与完整微调匹配的精确条件。我们已经粗略描述了等效性能的区域，并可以根据token或episode估计所需的容量，但我们还不能做出准确的预测。
- **我们对LoRA学习率和训练动态的理论理解有限**。解释LoRA和FullFT学习率之间比率的更完整理论将是有价值的。
- **LoRA变体**（如[PiSSA](https://arxiv.org/abs/2404.02948)（Meng, Wang & Zhang，2024））根据本文的方法论测量时表现如何？
- **将LoRA应用于MoE层有多种选择**。LoRA用户将受益于对它们表现如何的研究，以及每种方法与张量并行（tensor parallelism）和专家并行（expert parallelism）等对大型MoE模型重要的方法的兼容性。

## 结束语

在Thinking Machines，我们相信微调在许多专业领域推进AI实用性的力量。我们对LoRA的兴趣源于使这种力量广泛可及并易于根据特定需求定制的目标。

除了实际用途外，LoRA研究还引导我们对模型容量、数据集复杂性和样本效率进行更深入的研究。观察学习速度和性能如何依赖于容量为研究机器学习中的基本问题提供了一个视角。我们期待在未来推进这项研究。
