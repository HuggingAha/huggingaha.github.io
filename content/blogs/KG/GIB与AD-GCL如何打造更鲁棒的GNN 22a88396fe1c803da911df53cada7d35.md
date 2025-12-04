---
title: "GIB与AD-GCL如何打造更鲁棒的GNN"
showAuthor: false
date: 2022-10-09
description: "Modular-Manifolds-Thinking-Machines"
slug: "Modular-Manifolds-Thinking-Machines"
tags: ["论文", "KG", "GNN"]
# series: [""]
# series_order: 1
draft: false
---

<!-- 渲染公式 -->
{{< katex >}}


## 从信息论视角重塑图表示：GIB与AD-GCL如何打造更鲁棒的GNN

图神经网络（GNN）已成为处理图结构化数据的强大工具，在社交网络、药物发现、知识图谱等众多领域取得了巨大成功。然而，标准的GNN模型在看似强大的背后，隐藏着一个致命的弱点：**它们对微小的扰动（Perturbation）异常敏感**。无论是对图结构进行微小的修改，还是对节点特征添加一些噪声，都可能导致GNN的预测结果发生灾难性的错误 [1]。

这种脆弱性引发了一个根本性的问题：**一个好的图表示（Graph Representation）究竟应该是什么样的？** 仅仅在测试集上取得高精度就足够了吗？

普渡大学Pan Li教授团队的工作从信息论的视角出发，对这一问题进行了深刻的反思，并提出了**图信息瓶颈（Graph Information Bottleneck, GIB）和对抗性图对比学习（Adversarial Graph Contrastive Learning, AD-GCL）**两大核心思想，为构建更鲁棒、更泛化的GNN模型指明了方向。


## 1. 问题的根源：GNN学到了什么？

GNN的脆弱性根源在于，在强大的过参数化（Over-parameterization）能力下，模型为了拟合训练数据，往往会学到大量与预测目标**不相关的信息（Irrelevant Information）**。

可以将输入数据`D`（包括图结构`A`和节点特征`X`）所包含的信息，与预测目标`Y`所需的信息，用一个韦恩图来表示：

- **最小充分信息（Minimal Sufficient Info.）**: 图中红色和蓝色区域的交集。这是对预测`Y`有用且必要的信息。
- **不相关信息（Irrelevant Info.）**: 蓝色区域中不与红色区域相交的部分。这部分信息与`Y`无关，但却是输入数据`D`的一部分。

一个理想的表示`Z`，应该**只包含最小充分信息**。然而，标准GNN在训练时，会不可避免地将大量不相关信息也编码到表示`Z`中。这些不相关信息就像“噪声”，虽然在干净的训练集上有助于区分样本，但在面对攻击或分布外数据时，就会成为模型的“阿喀琉斯之踵”，极大地影响模型的鲁棒性。

因此，一个好的图表示，不仅要性能优越，更要具备**鲁棒性**和**稳定性**。其核心在于——**捕获最小化的充分信息（Capturing the minimal sufficient information）**。


## 2. 监督学习下的理想解：图信息瓶颈 (GIB)

信息瓶颈（Information Bottleneck）理论 [2] 为实现这一目标提供了数学框架。其核心思想是在“压缩”和“预测”之间找到一个最佳平衡点。

将这一原理应用于图数据，提出了**图信息瓶颈（GIB）[3]**。其目标是学习一个表示`Z`，它满足两个条件：

1. **充分性 (Sufficiency)**: `Z`需要包含尽可能多关于预测目标`Y`的信息。
2. **最小性 (Minimality)**: `Z`需要尽可能“忘记”原始输入数据`D`的信息，即对`D`进行最大程度的压缩。

这两个目标通过优化以下目标函数来实现，其中`I(·;·)`代表互信息（Mutual Information）：

$$
\min_{p(Z|D)} [-I(Y; Z) + \beta I(D; Z)]
$$

- `max I(Y; Z)`（最大化与`Y`的互信息）：等价于最小化`I(Y; Z)`，确保表示的**预测能力**。
- `min I(D; Z)`（最小化与`D`的互信息）：通过压缩，强制表示**丢弃不相关信息**，提升鲁棒性。
- `β`是一个权衡系数，用于平衡预测性能和压缩程度。

GIB原则为构建鲁棒GNN提供了一个理论上界。实验证明，在监督学习场景下，基于GIB训练的GNN在面对对抗性攻击和随机噪声时，其鲁棒性远超传统GNN模型。


## 3. 从监督到自监督：对抗图对比学习 (AD-GCL)

GIB虽好，但它有一个致命的依赖：**需要任务标签`Y`**。在许多现实场景中，获取高质量的标签是极其昂贵甚至不可能的，这限制了GIB的广泛应用。

此时，学界自然会转向自监督学习，尤其是目前最主流的**图对比学习（Graph Contrastive Learning, GCL）[4]**。GCL的核心思想是，一个图经过数据增强（如图/边/属性的扰动）后，其“身份”不应改变。因此，模型的目标是最大化同一个图的两个不同增强视图（view）的表示之间的一致性（或互信息）。

$$
\max_{f} I(f(t_1(G)); f(t_2(G)))
$$

这本质上是一个**InfoMax**原则——最大化信息。然而，InfoMax原则本身存在问题。为了最大化两个视图的互信息，模型可能仍然会走“捷径”，去学习那些虽然与任务无关、但在不同视图中保持一致的“噪声”或“伪影”作为识别信号。实验表明，如果用随机标签来监督一个InfoMax模型，它依然能很好地区分不同图，但其学到的表示对于真实任务毫无泛化能力。

**这揭示了InfoMax与鲁棒性之间的内在矛盾。**

如何将GIB的“最小化信息”思想融入无需标签的GCL框架中？答案是：**通过对抗学习让数据增强本身变得可学习**。

由此，提出了**对抗图对比学习（AD-GCL）[5]**。它将GCL从一个单纯的最大化问题，转变为一个**生成器（Augmenter）和编码器（Encoder）之间的Min-Max对抗游戏**。

$$
\min_{T \in \mathcal{T}} \max_{f} I(f(G); f(t(G))) \quad \text{where } t(G) \sim T(G)
$$

这个过程可以理解为：

- **编码器 (f)**：努力工作，试图**最大化**原始图`G`和增强视图`t(G)`表示之间的一致性，以识别出图的身份。
- **增强器 (T)**：扮演“对手”的角色，智能地生成一个“最难”的增强视图`t(G)`，试图**最小化**这种一致性，让编码器难以识别。

在这场对抗博弈中，增强器会丢弃掉所有冗余、不相关的信息，只保留最核心、最本质的结构和特征。为了在这种“最苛刻”的条件下依然能识别出图的身份，编码器被迫**只能学习那些区分图身份的最小充分信息**。

通过这种方式，AD-GCL在没有标签`Y`的情况下，巧妙地实现了GIB的“最小化充分表示”的目标。实验结果表明，AD-GCL在无监督和迁移学习任务上取得了SOTA性能，尤其在多个数据集上显著优于传统的、基于固定增强策略的GCL方法。


## 4. 另一维度的思考：距离编码

除了信息论层面的鲁棒性问题，标准GNN还存在固有的结构表达能力缺陷，例如无法区分某些同构图、无法有效捕获节点间的相对位置信息等。

为了解决这个问题，该团队还探索了**距离编码（Distance Encoding）[6]**。其核心思想是：

1. 预先计算一些能够反映图结构拓扑的特征，例如节点对之间的**最短路径距离（Shortest Path Distance, SPD）**。
2. 将这些预计算出的结构特征（距离编码）作为额外的输入，与原始节点特征拼接在一起，再送入GNN进行学习。

这种简单的“插件式”增强，能直接为GNN提供它们本身难以捕获的、宝贵的拓扑和位置信息，从而在链路预测、图分类等多个任务上大幅提升模型性能。

---

## 总结

Pan Li教授团队的工作为重塑图表示学习提供了全新视角。

1. **理论基石 - GIB**: 指出了理想图表示的核心是**捕获最小充分信息**，并给出了监督学习下的数学框架，为鲁棒性研究提供了理论指导 [3]。
2. **实践飞跃 - AD-GCL**: 通过巧妙的**对抗性学习框架**，将GIB的思想推广到更具挑战性、也更具实用价值的自监督对比学习中，让模型在没有标签的情况下，学会“在对抗中丢弃冗余，保留精华” [5]。
3. **能力拓展 - 距离编码**: 提出了一个正交于信息瓶颈思想的有效技巧，通过直接注入结构信息来弥补GNN的内在表达能力缺陷 [6]。

这些工作不仅在学术上具有开创性，也为工业界构建更可靠、更强大的图智能应用提供了坚实的理论基础和可行的技术路径。

---

## 参考文献

[1] Zügner, D., Akbarnejad, A., & Günnemann, S. (2018). Adversarial attacks on neural networks for graph data. In *Proceedings of the 24th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining*.

[2] Tishby, N., Pereira, F. C., & Bialek, W. (2000). The information bottleneck method. *arXiv preprint physics/0004057*.

[3] Wu, T., Ren, H., Li, P., & Leskovec, J. (2020). Graph Information Bottleneck. In *Advances in Neural Information Processing Systems 33*.

[4] You, Y., Chen, T., Sui, Y., & Chen, M. (2020). Graph contrastive learning with augmentations. In *Advances in Neural Information Processing Systems 33*.

[5] Suresh, S., Hao, C., Neville, J., & Li, P. (2021). Adversarial Graph Augmentation to Improve Graph Contrastive Learning. In *Advances in Neural Information Processing Systems 34*.

[6] Li, P., Wang, Y., Wang, H., & Leskovec, J. (2020). Distance encoding: Design provably more powerful neural networks for graph representation learning. In *Advances in Neural Information Processing Systems 33*.
