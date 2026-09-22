---
title: "解析几何：内积"
date: 2026-02-15T09:10:00+08:00
description: "从点积推广到内积，掌握对称性、双线性和正定性，并理解 SPD 矩阵如何刻画度量、核矩阵和优化曲率。"
categories: ["notes"]
topics: ["math"]
tags: ["math"]
series: ["analytical-geometry"]
series_order: 2
showAuthor: false
aliases: ["/blogs/math/analytical-geometry/02/"]
---

<!-- 渲染公式 -->
{{< katex >}}


<!-- # 内积 (Inner Products) -->

在上一节中，我们看到范数可以用来衡量向量的“长度”，但不同的范数（如L1和L2）定义了不同的长度。L2范数（欧几里得范数）之所以在几何上如此特殊和自然，是因为它源自一个更基本、更强大的概念——**内积 (Inner Product)**。内积不仅能定义长度，还能定义向量间的**角度**，是连接代数与几何的核心桥梁。

## 从点积到一般内积

在 \(\mathbb{R}^n\) 空间中，我们最熟悉的内积形式是**点积 (Dot Product)**，也称为标量积 (Scalar Product)。

$$
\mathbf{x}^\top\mathbf{y} = \sum_{i=1}^n x_i y_i
$$

点积接收两个向量 \(\mathbf{x}\) 和 \(\mathbf{y}\)，并输出一个标量。这个标量蕴含了两个向量在方向和大小上的综合信息。然而，点积只是内积的一种具体实现。内积是一个更具一般性的概念，其定义基于一组特定的性质。

## 内积的数学定义

**准确的数学定义**

在一个向量空间 \(V\) 上，**内积 (Inner Product)** 是一个双线性映射（Bilinear Mapping），我们通常记作 \(\langle \cdot, \cdot \rangle\)。它接收两个向量 \(\mathbf{x}, \mathbf{y} \in V\)，并返回一个实数，即 \(\langle \mathbf{x}, \mathbf{y} \rangle \in \mathbb{R}\)。这个映射必须满足以下三个性质：

1. **对称性 (Symmetry)**
对于任意 \(\mathbf{x}, \mathbf{y} \in V\)，都有：
    
    $$
    \langle \mathbf{x}, \mathbf{y} \rangle = \langle \mathbf{y}, \mathbf{x} \rangle
    $$
    
    - **直观解释:** 衡量 \(\mathbf{x}\) 与 \(\mathbf{y}\) 的关系，和衡量 \(\mathbf{y}\) 与 \(\mathbf{x}\) 的关系是一样的，顺序不重要。
2. **双线性 (Bilinearity)**
对于任意 \(\mathbf{x}, \mathbf{y}, \mathbf{z} \in V\) 和标量 \(\lambda, \psi \in \mathbb{R}\)，内积对它的每一个参数都表现出线性：
    
    $$
    \langle \lambda\mathbf{x} + \psi\mathbf{y}, \mathbf{z} \rangle = \lambda\langle \mathbf{x}, \mathbf{z} \rangle + \psi\langle \mathbf{y}, \mathbf{z} \rangle
    $$
    
    - **直观解释:** 我们可以像处理普通乘法一样，将内积“分配”到向量的和上，并可以自由地提出标量乘子。由于对称性，它对第二个参数也同样是线性的。
3. **正定性 (Positive Definiteness)**
对于任意 \(\mathbf{x} \in V\)：
    
    $$
    \langle \mathbf{x}, \mathbf{x} \rangle \ge 0 \quad \text{并且} \quad (\langle \mathbf{x}, \mathbf{x} \rangle = 0 \iff \mathbf{x} = \mathbf{0})
    $$
    
    - **直观解释:** 一个向量与自身的内积永远是非负的。这个值等于零的唯一情况是该向量本身就是零向量。正是这个性质，使得我们可以利用内积来定义一个有效的长度（范数）。

**理解要点**

- 一个配备了内积的向量空间 \((V, \langle \cdot, \cdot \rangle)\) 被称为**内积空间 (Inner Product Space)**。
- 如果内积采用的是标准的点积，这个空间就是我们熟悉的**欧几里得向量空间 (Euclidean Vector Space)**。
- 点积只是满足这三条公理的一种内积。我们可以定义出无穷多种不同的内积。

## 内积与对称正定矩阵

在有限维向量空间中，内积与一类特殊的矩阵——**对称正定矩阵 (Symmetric, Positive-Definite, SPD) Matrix**——有着深刻且唯一的对应关系。

**数学严谨性**

考虑一个 \(n\) 维向量空间 \(V\) 和一组基 \(\{ \mathbf{b}_1, \dots, \mathbf{b}_n \}\)。空间中的任意两个向量 \(\mathbf{x}\) 和 \(\mathbf{y}\) 都可以用这组基的坐标 \(\tilde{\mathbf{x}}, \tilde{\mathbf{y}} \in \mathbb{R}^n\) 来表示。它们的内积可以通过双线性展开：

$$
\langle \mathbf{x}, \mathbf{y} \rangle = \left\langle \sum_{i=1}^n \tilde{x}_i \mathbf{b}_i, \sum_{j=1}^n \tilde{y}_j \mathbf{b}_j \right\rangle = \sum_{i=1}^n \sum_{j=1}^n \tilde{x}_i \tilde{y}_j \langle \mathbf{b}_i, \mathbf{b}_j \rangle
$$

如果我们定义一个矩阵 \(\mathbf{A}\)，其元素为 \(\mathbf{A}_{ij} = \langle \mathbf{b}_i, \mathbf{b}_j \rangle\)，上述公式可以简洁地写成矩阵形式：

$$
\langle \mathbf{x}, \mathbf{y} \rangle = \tilde{\mathbf{x}}^\top \mathbf{A} \tilde{\mathbf{y}}
$$

这个矩阵 \(\mathbf{A}\) 必须满足：

1. **对称 (Symmetric):** 因为内积是对称的 (\(\langle \mathbf{b}_i, \mathbf{b}_j \rangle = \langle \mathbf{b}_j, \mathbf{b}_i \rangle\))，所以 \(\mathbf{A} = \mathbf{A}^\top\)。
2. **正定 (Positive-Definite):** 因为内积是正定的 (\(\langle \mathbf{x}, \mathbf{x} \rangle > 0\) 对所有 \(\mathbf{x} \ne \mathbf{0}\) 成立)，所以对于任何非零坐标向量 \(\tilde{\mathbf{x}}\)，都有 \(\tilde{\mathbf{x}}^\top \mathbf{A} \tilde{\mathbf{x}} > 0\)。

**核心洞察**

> 在 \(\mathbb{R}^n\) 空间中，定义一个内积等价于指定一个对称正定矩阵 \(\mathbf{A}\)。标准的点积 \(\mathbf{x}^\top\mathbf{y}\) 只是其中最简单的情况，对应于 \(\mathbf{A}\) 为单位矩阵 \(\mathbf{I}\)。
> 

**应用场景**
SPD矩阵在机器学习中无处不在，它们通常代表着“良性”的结构：

- **协方差矩阵:** 衡量多维数据分布。
- **核矩阵 (Kernel Matrix):** 在支持向量机和高斯过程中，隐式地定义了高维特征空间的内积。
- **海森矩阵 (Hessian Matrix):** 在优化问题中，一个正定的海森矩阵保证了我们找到了一个局部最小值点。

## **示例**

1. **一个非点积的内积 (Example 3.3)**
在 \(\mathbb{R}^2\) 中，我们可以定义如下内积：
    
    $$
    \langle \mathbf{x}, \mathbf{y} \rangle := x_1y_1 - (x_1y_2 + x_2y_1) + 2x_2y_2
    $$
    
    这可以被证明满足对称性、双线性和正定性，因此是一个合法的内积，尽管它不是标准的点积。
    
2. **判断矩阵是否为SPD (Example 3.4)**
考虑矩阵 \(\mathbf{A}_1 = \begin{bmatrix} 9 & 6 \\ 6 & 5 \end{bmatrix}\) 和 \(\mathbf{A}_2 = \begin{bmatrix} 9 & 6 \\ 6 & 3 \end{bmatrix}\)。
    - 对于 \(\mathbf{A}_1\)，我们计算二次型 \(\mathbf{x}^\top\mathbf{A}_1\mathbf{x}\)：
        
        $$
        \mathbf{x}^\top\mathbf{A}_1\mathbf{x} = 9x_1^2 + 12x_1x_2 + 5x_2^2 = (9x_1^2 + 12x_1x_2 + 4x_2^2) + x_2^2 = (3x_1 + 2x_2)^2 + x_2^2
        $$
        
        因为平方项非负，且只有当 \(x_1=0, x_2=0\) 时结果才为0，所以 \(\mathbf{A}_1\) 是**正定的**。它也是对称的，故 \(\mathbf{A}_1\) 是一个SPD矩阵。
        
    - 对于 \(\mathbf{A}_2\)，我们计算二次型 \(\mathbf{x}^\top\mathbf{A}_2\mathbf{x}\)：
        
        $$
        \mathbf{x}^\top\mathbf{A}_2\mathbf{x} = 9x_1^2 + 12x_1x_2 + 3x_2^2 = (3x_1 + 2x_2)^2 - x_2^2
        $$
        
        这个表达式可能为负。例如，取 \(\mathbf{x} = [2, -3]^\top\)，结果为 \((6-6)^2 - (-3)^2 = -9 < 0\)。因此，\(\mathbf{A}_2\) **不是正定的**。
        

---

## 小节

- 内积是点积的推广，是定义向量间几何关系（长度、角度）的基础。
- 内积必须满足对称性、双线性和正定性三大公理。
- 在 \(\mathbb{R}^n\) 中，任何内积都可以由一个唯一的对称正定矩阵 \(\mathbf{A}\) 表示：\(\langle \mathbf{x}, \mathbf{y} \rangle = \mathbf{x}^\top\mathbf{A}\mathbf{y}\)。
- SPD矩阵在机器学习的多个核心领域中扮演关键角色。

---

**后续**

我们已经建立了内积这一强大的工具。现在，是时候利用它来构建第一个，也是最直观的几何概念了。内积的正定性保证了 \(\langle \mathbf{x}, \mathbf{x} \rangle\) 是一个非负实数，这让我们自然地联想到“长度的平方”。在下一节中，我们将正式探讨如何**由内积诱导出范数**，从而为任意内积空间中的向量赋予**长度**，并由此定义向量间的**距离**。
