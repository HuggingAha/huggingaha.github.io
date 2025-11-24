---
title: "GATNE：面向属性、多重、异构网络的统一表示学习框架"
showAuthor: false
date: 2022-07-22
description: "GATNE：面向属性、多重、异构网络的统一表示学习框架"
slug: "GATNE-Representation-Learning-for-Attributed-Multiplex-Heterogeneous-Network"
tags: ["论文", "KG", "表示学习", "AMHEN"]
# series: [""]
# series_order: 1
# weight: 4
draft: false
---

<!-- 渲染公式 -->
{{< katex >}}


> **代码**：[THUDM/GATNE](https://github.com/THUDM/GATNE.git)  
> **论文**：[Representation Learning for Attributed Multiplex Heterogeneous Network](https://arxiv.org/abs/1905.01669)

在现实世界中，无论是电商推荐、社交网络还是金融风控，我们面对的数据网络日益复杂。传统的网络表示学习（Network Embedding）方法，如DeepWalk或node2vec，在处理仅包含单一类型节点和边的同构网络（Homogeneous Network）时表现出色，但当网络变得更加复杂时，这些方法便捉襟见肘。

真实世界的网络通常是**属性化的（Attributed）**、**多重的（Multiplex）且异构的（Heterogeneous）**。例如，在一个电商网络中：

- **异构性**：存在“用户”和“商品”两种不同类型的节点。
- **多重性**：用户与商品之间存在多种类型的关系（边），如“点击”、“收藏”、“加入购物车”、“购买”等。
- **属性化**：每种节点都拥有丰富的属性信息，如用户的年龄、性别，商品的价格、品牌等。

这种网络被称为**属性化多重异构网络（Attributed Multiplex Heterogeneous Network, AMHEN）**。处理此类网络是学术界和工业界面临的重大挑战。清华大学与阿里巴巴达摩院的研究者在KDD 2019上发表的论文《Representation Learning for Attributed Multiplex Heterogeneous Network》中，提出了一个名为**GATNE (General Attributed Multiplex HeTerogeneous Network Embedding)** 的统一框架，旨在有效解决这一难题。

---

## 1. 问题的提出：真实世界网络的复杂性与挑战

在深入模型之前，首先要理解AMHEN带来的核心挑战：

1. **多重关系融合（Multiplex Edges）**：一个节点对（如一个用户和一个商品）之间可能存在多种关系。这些关系强度不同，语义各异（例如，“购买”关系比“点击”关系更能体现用户的兴趣）。如何有效地区分并融合这些关系，学习到一个统一的、信息丰富的节点表示是首要难题。
2. **异构性与属性信息利用**：不同类型的节点和边具有完全不同的特征空间和语义含义。模型必须能够处理这种异构性，并有效利用节点自带的丰富属性信息，而不是仅仅依赖网络结构。
3. **部分观测与归纳能力（Partial Observations & Inductive Learning）**：真实世界的网络是动态变化的，新节点（如新用户、新商品）不断涌现。模型必须具备**归纳学习（Inductive Learning）的能力，能够为未在训练阶段出现过的节点生成表示，而不是像传统方法那样只能进行直推式学习（Transductive Learning）**。
4. **可扩展性（Scalability）**：工业级网络通常包含数十亿的节点和数百亿的边，对算法的效率和扩展性提出了极高的要求。

GATNE框架正是为了系统性地应对以上所有挑战而设计的。

---

## 2. GATNE 模型核心设计

GATNE的核心思想是将一个节点在特定关系下的最终表示（Overall Embedding）分解为三个部分：**基向量（Base Embedding）**、**边向量（Edge Embedding）和属性向量（Attribute Embedding）**。其中，边向量的设计是其精髓所在。

### 2.1 核心思想：基向量 + 边向量分解

对于网络中的任意一个节点 \(v_i\)，其在特定边类型 \(r\) 下的最终表示 \(v_{i,r}\)，被分解为两个主要部分：

1. **基向量 \(b_i\)**：这个向量是**与边类型无关**的，由节点本身决定，并**在所有边类型上共享**。它旨在捕获节点固有的、通用的基础特征。
2. **边向量 \(u_{i,r}\)**：这个向量是**与边类型相关**的。同一个节点 \(v_i\) 在面对不同类型的边（如“点击”边和“购买”边）时，会拥有不同的边向量。它旨在捕获节点在特定关系下的上下文语义。

这种分解的设计非常巧妙，它允许模型在学习通用节点特征的同时，为每种关系保留其独特的语义信息。

### 2.2 边向量的聚合：从邻居获取上下文

节点的边向量 \(u_{i,r}\) 并非直接学习，而是通过聚合其在边类型 \(r\) 下的邻居节点信息来动态生成。这一思想借鉴了GraphSAGE [1] 的聚合机制。一个节点的 \(k\) 阶边向量由其邻居的 \(k-1\) 阶边向量聚合而成：

$$
\mathbf{u}{i, r}^{(k)}=\text{aggregator}\left(\left\{\mathbf{u}{j, r}^{(k-1)}, \forall v_{j} \in N_{i, r}\right\}\right)
$$

其中，\(N_{i,r}\) 是节点 \(v_i\) 在边类型 \(r\) 下的邻居集合。聚合函数（aggregator）可以是均值、最大池化等。通过多层聚合，节点的边向量能够捕获到其在高阶邻域内的结构信息。

### 2.3 自注意力机制的引入：动态融合多重关系

GATNE最核心的创新在于如何将一个节点的多个边向量（每个对应一种边类型）融合成一个最终的边向量部分。如果一个网络有 \(m\) 种边类型，那么每个节点 \(v_i\) 就会有 \(m\) 个基础边向量 \(\{u_{i,1}, u_{i,2}, ..., u_{i,m}\}\)。

GATNE并未使用简单的拼接或平均，而是引入了**自注意力机制（Self-Attention）**[2]来动态地计算不同边向量的权重。对于目标边类型 \(r\)，模型会为所有类型的边向量 \(u_{i,p} (p=1,...,m)\) 计算一个注意力系数 \(a_{i,r,p}\)。

$$
a_{i,r} = \text{softmax}(\mathbf{w}_r^T \tanh(\mathbf{W}_r \mathbf{U}_i))^T
$$

其中，\(\mathbf{U}i = [u{i,1}, ..., u_{i,m}]\) 是节点 \(v_i\) 所有边向量的拼接矩阵，\(\mathbf{W}_r\) 和 \(\mathbf{w}_r\) 是针对目标边类型 \(r\) 的可学习的注意力参数。

最终，节点 \(v_i\) 在边类型 \(r\) 下的整体表示 \(v_{i,r}\) 由基向量和加权融合后的边向量组合而成：

$$
\mathbf{v}{i, r}=\mathbf{b}{i}+\alpha_{r} \mathbf{M}{r} \mathbf{U}{i} \mathbf{a}_{i, r}
$$

其中 \(\mathbf{M}_r\) 是可学习的变换矩阵，\(\alpha_r\) 是一个超参数，用于控制边向量的重要性。

通过自注意力机制，GATNE能够根据目标任务（目标边类型 \(r\)）动态地判断其他类型的关系对当前任务的贡献度，从而实现信息的智能、高效融合。

---

## 3. 从直推式到归纳式学习：GATNE-I

上述模型（论文中称为GATNE-T）是**直推式的**，它为训练集中出现的每个节点直接学习基向量 \(b_i\)。这无法处理新节点。

为了解决这个问题，论文提出了GATNE的归纳式版本——**GATNE-I**。其核心改动在于，**不再为每个节点学习独立的基向量和初始边向量，而是学习一个从节点属性生成这些向量的函数**。

具体来说，节点的基向量 \(b_i\) 和初始边向量 \(u_{i,r}^{(0)}\) 由其原始属性 \(x_i\) 通过一个变换函数（如多层感知机MLP）生成：

$$
\mathbf{b}i = h_z(\mathbf{x}i)
$$

$$
\mathbf{u}{i,r}^{(0)} = g{z,r}(\mathbf{x}_i)
$$

其中 \(z\) 是节点 \(v_i\) 的类型，\(h_z\) 和 \(g_{z,r}\) 是针对不同节点类型和边类型的可学习的函数。节点的最终表示也加入了一个直接由属性变换而来的项：

$$
\mathbf{v}{i, r}=h{z}\left(\mathbf{x}{i}\right)+\alpha{r} \mathbf{M}{r} \mathbf{U}{i} \mathbf{a}{i, r}+\beta{r} \mathbf{D}{z} \mathbf{x}{i}
$$

通过这种方式，只要一个新节点带有属性信息，GATNE-I就能为其生成高质量的表示，完美解决了冷启动和归纳学习的挑战。

---

## 4. 模型优化与训练

GATNE的训练过程采用了基于元路径的随机游走（meta-path based random walks）[3]来生成节点序列，这种策略能够有效保留异构网络中的复杂语义关系。在生成的序列上，模型采用异构Skip-gram目标，并通过负采样进行优化。目标函数为：

$$
E=-\log \sigma\left(\mathbf{c}{j}^{T} \cdot \mathbf{v}{i, r}\right)-\sum_{l=1}^{L} \mathbb{E}{v{k} \sim P_{n}(v)}\left[\log \sigma\left(-\mathbf{c}{k}^{T} \cdot \mathbf{v}{i, r}\right)\right]
$$

---

## 5. 实验效果与结论

GATNE在Amazon、YouTube、Twitter以及阿里巴巴的真实工业数据集上进行了广泛的实验。结果表明，无论是在链路预测还是在真实的推荐系统A/B测试中，GATNE均显著优于包括DeepWalk、metapath2vec、MNE在内的所有基线模型。
例如，在阿里巴巴数据集上，GATNE-I相比当时最优的方法，在F1分数上取得了高达5.99%的提升。在阿里巴巴推荐系统的离线A/B测试中，GATNE-I的Top-N点击命中率相比MNE和DeepWalk分别提升了3.26%和24.26%，展现了其强大的工业应用价值。

**总结来说，GATNE的主要贡献在于：**

1. **统一框架**：首次提出了一个能够统一处理属性、多重关系和异构性的网络表示学习框架AMHEN。
2. **创新的表示分解**：将节点表示分解为共享的基向量和关系特定的边向量，兼顾了通用性与特异性。
3. **自注意力融合**：巧妙地运用自注意力机制，实现了对多重关系的动态、加权融合，极大地提升了模型的表达能力。
4. **兼具直推式与归纳式能力**：同时提出了GATNE-T和GATNE-I两个版本，使其既能处理静态网络，也能应对动态网络中的新节点问题，具备很强的实用性。

GATNE的设计为复杂图表示学习提供了一个强大且优雅的解决方案，对学术研究和工业应用都具有重要的指导意义。
