---
title: "解析几何：角度与正交性"
date: 2026-02-15T09:30:00+08:00
description: "用内积计算向量夹角并定义正交性，理解余弦相似度的用途，掌握正交矩阵保长度和角度的原因。"
categories: ["notes"]
topics: ["math"]
tags: ["math"]
series: ["analytical-geometry"]
series_order: 4
showAuthor: false
aliases: ["/blogs/math/analytical-geometry/04/"]
---

<!-- 渲染公式 -->
{{< katex >}}


<!-- # 角度与正交性 (Angles and Orthogonality) -->

内积除了能定义向量的长度外，还能捕捉向量空间中的几何形态，特别是向量之间的**方向关系**。这通过定义它们之间的**角度 (Angle)** 来实现，并引出解析几何中一个至关重要的概念——**正交性 (Orthogonality)**。

---

### 角度 (Angle)

柯西-施瓦茨不等式 \((|\langle \mathbf{x}, \mathbf{y} \rangle| \le \|\mathbf{x}\| \|\mathbf{y}\|)\) 保证了对于任意两个非零向量 \(\mathbf{x}\) 和 \(\mathbf{y}\)，下式的值总是在 \([-1, 1]\) 区间内：

$$
-1 \le \frac{\langle \mathbf{x}, \mathbf{y} \rangle}{\|\mathbf{x}\| \|\mathbf{y}\|} \le 1
$$

这使得我们可以用这个比值来定义它们夹角 \(\omega\) 的余弦值。

**准确的数学定义**

两个非零向量 \(\mathbf{x}\) 和 \(\mathbf{y}\) 之间的**角度 \(\omega \in [0, \pi]\)** 由以下公式定义：

$$
\cos\omega = \frac{\langle \mathbf{x}, \mathbf{y} \rangle}{\|\mathbf{x}\| \|\mathbf{y}\|}
$$

- **直观解释:** 这个公式量化了向量间的方向相似度。
    - 如果 \(\langle \mathbf{x}, \mathbf{y} \rangle > 0\)，则 \(\cos\omega > 0\)，夹角 \(\omega\) 是锐角 (\(< 90^\circ\))，表示两个向量大致指向同一方向。
    - 如果 \(\langle \mathbf{x}, \mathbf{y} \rangle < 0\)，则 \(\cos\omega < 0\)，夹角 \(\omega\) 是钝角 (\(> 90^\circ\))，表示两个向量大致指向相反方向。
    - 如果 \(\langle \mathbf{x}, \mathbf{y} \rangle = 0\)，则 \(\cos\omega = 0\)，夹角 \(\omega = 90^\circ\)，表示两个向量垂直。
- **应用场景:** 在机器学习中，这个公式（特别是当内积为点积时，称为**余弦相似度**）被广泛用于衡量文本、图像等高维数据向量的相似性。余弦相似度只关心方向而不关心大小，这在很多场景下非常有用。

**数值示例 (Example 3.6)**

计算向量 \(\mathbf{x} = [1, 1]^\top\) 和 \(\mathbf{y} = [1, 2]^\top\) 在标准点积下的夹角 \(\omega\)。

1. 计算内积：\(\langle \mathbf{x}, \mathbf{y} \rangle = \mathbf{x}^\top\mathbf{y} = 1 \cdot 1 + 1 \cdot 2 = 3\)
2. 计算各自的长度（L2范数）：
$$\|\mathbf{x}\| = \sqrt{1^2+1^2} = \sqrt{2}$$
    
$$\|\mathbf{y}\| = \sqrt{1^2+2^2} = \sqrt{5}$$
    
3. 计算角度的余弦：
$$\cos\omega = \frac{3}{\sqrt{2} \cdot \sqrt{5}} = \frac{3}{\sqrt{10}}$$
因此，夹角 \(\omega = \arccos\left(\frac{3}{\sqrt{10}}\right) \approx 0.32 \text{ rad} \approx 18^\circ\)。

![*图3.5 两个向量间的夹角*](%E8%A7%92%E5%BA%A6%E4%B8%8E%E6%AD%A3%E4%BA%A4%E6%80%A7%20(Angles%20and%20Orthogonality)/image.png)

*图3.5 两个向量间的夹角*

---

### 正交性 (Orthogonality)

正交性是“垂直”这一几何概念在任意内积空间中的推广，是内积最关键的应用之一。

**准确的数学定义**

两个向量 \(\mathbf{x}\) 和 \(\mathbf{y}\) 被称为**正交 (Orthogonal)**，如果它们的内积为零。我们记作 \(\mathbf{x} \perp \mathbf{y}\)。

$$\mathbf{x} \perp \mathbf{y} \iff \langle \mathbf{x}, \mathbf{y} \rangle = 0$$

- **推论:** 根据定义，**零向量与任何向量都正交**。
- **标准正交 (Orthonormal):** 如果两个向量不仅正交，而且它们的长度（范数）都为1，那么它们被称为**标准正交**。

**重要洞察：正交性是相对的**

一个非常关键的认知是，**正交性是相对于所选的内积而言的**。两个向量在一个内积定义下可能是正交的，但在另一个内积定义下则未必。

---

**数值示例 (Example 3.7)**

考虑向量 \(\mathbf{x} = [1, 1]^\top\) 和 \(\mathbf{y} = [-1, 1]^\top\)。

1. **在标准点积下:**\(\langle \mathbf{x}, \mathbf{y} \rangle = \mathbf{x}^\top\mathbf{y} = 1 \cdot (-1) + 1 \cdot 1 = 0\)
因此，\(\mathbf{x} \perp \mathbf{y}\)。它们的夹角是 \(90^\circ\)。
2. **在一个不同的内积下:**
假设内积由矩阵 \(\mathbf{A} = \begin{bmatrix} 2 & 0 \\ 0 & 1 \end{bmatrix}\) 定义，即 \(\langle \mathbf{x}, \mathbf{y} \rangle = \mathbf{x}^\top\mathbf{A}\mathbf{y}\)。
$$\langle \mathbf{x}, \mathbf{y} \rangle = [1, 1] \begin{bmatrix} 2 & 0 \\ 0 & 1 \end{bmatrix} \begin{bmatrix} -1 \\ 1 \end{bmatrix} = [1, 1] \begin{bmatrix} -2 \\ 1 \end{bmatrix} = -2 + 1 = -1 \ne 0$$
在这个内积空间中，\(\mathbf{x}\) 和 \(\mathbf{y}\) **不正交**。我们可以计算出它们的夹角约为 \(109.5^\circ\)。

![*图3.6 向量间的角度依赖于内积*](%E8%A7%92%E5%BA%A6%E4%B8%8E%E6%AD%A3%E4%BA%A4%E6%80%A7%20(Angles%20and%20Orthogonality)/image%201.png)

*图3.6 向量间的角度依赖于内积*

---

### 正交矩阵 (Orthogonal Matrix)

**准确的数学定义**

一个方阵 \(\mathbf{A} \in \mathbb{R}^{n \times n}\) 被称为**正交矩阵**，如果它的所有列（或行）构成一组**标准正交基 (Orthonormal Basis)**。这等价于以下条件：

$$
\mathbf{A}^\top\mathbf{A} = \mathbf{A}\mathbf{A}^\top = \mathbf{I}
$$

一个直接且极其重要的推论是，正交矩阵的逆矩阵就是它的转置：

$$
\mathbf{A}^{-1} = \mathbf{A}^\top
$$

**几何意义**

用正交矩阵对向量进行变换（即 \(\mathbf{y} = \mathbf{A}\mathbf{x}\)）是一种**保距、保角**的变换。这意味着：

1. **保持长度不变:**\(\|\mathbf{A}\mathbf{x}\|^2 = (\mathbf{A}\mathbf{x})^\top(\mathbf{A}\mathbf{x}) = \mathbf{x}^\top\mathbf{A}^\top\mathbf{A}\mathbf{x} = \mathbf{x}^\top\mathbf{I}\mathbf{x} = \mathbf{x}^\top\mathbf{x} = \|\mathbf{x}\|^2\)
2. **保持角度不变:**
两个向量 \(\mathbf{x}, \mathbf{y}\) 变换后的内积 \(\langle \mathbf{A}\mathbf{x}, \mathbf{A}\mathbf{y} \rangle = (\mathbf{A}\mathbf{x})^\top(\mathbf{A}\mathbf{y}) = \mathbf{x}^\top\mathbf{A}^\top\mathbf{A}\mathbf{y} = \mathbf{x}^\top\mathbf{y} = \langle \mathbf{x}, \mathbf{y} \rangle\)。由于内积和长度都不变，它们之间的角度也保持不变。

几何上，正交变换对应于空间中的**旋转 (Rotation)** 和/或**反射 (Reflection)**。

---

## **章节知识点总结**

- 向量间的角度由内积和范数共同定义：\(\cos\omega = \frac{\langle \mathbf{x}, \mathbf{y} \rangle}{\|\mathbf{x}\| \|\mathbf{y}\|}\)。
- 正交性是垂直的推广，定义为 \(\langle \mathbf{x}, \mathbf{y} \rangle = 0\)。
- 正交性是一个相对概念，它依赖于所选的内积。
- 正交矩阵的列（行）是标准正交的，其逆等于其转置。
- 正交变换（如旋转和反射）保持向量的长度和向量间的角度不变。

---

**后续**

我们已经看到，由标准正交向量构成的矩阵（正交矩阵）具有非常优美的性质。这自然引出一个问题：我们能否为任何向量空间找到一组由相互正交的向量构成的基？这样的**标准正交基 (Orthonormal Basis)** 将会极大地简化我们的计算。在下一节中，我们将介绍如何系统地从任意一组基出发，构造出一组标准正交基。
