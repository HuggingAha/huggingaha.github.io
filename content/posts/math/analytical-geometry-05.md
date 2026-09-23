---
title: "解析几何：标准正交基与格拉姆-施密特正交化"
date: 2026-02-15T09:40:00+08:00
description: "构造标准正交基，按减去投影的思路执行 Gram-Schmidt 正交化，并用正交补理解向量的唯一分解。"
categories: ["notes"]
topics: ["math"]
tags: ["math"]
series: ["analytical-geometry"]
series_order: 5
showAuthor: false
aliases: ["/blogs/math/analytical-geometry/05/"]
---

<!-- 渲染公式 -->
{{< katex >}}


<!-- # 标准正交基与格拉姆-施密特正交化 -->

我们已经看到，向量的正交性是一个非常有用且强大的性质。如果一个向量空间的基是由两两正交的向量组成的，那么在这个“坐标系”下进行计算会变得异常简单。这就引出了**标准正交基**的概念。

---

## 什么是标准正交基？

**准确的数学定义**

考虑一个内积空间 \(V\) 和它的一组基 \(B = \{\mathbf{b}_1, \dots, \mathbf{b}_n\}\)。

- 如果基中任意两个不同的向量都相互正交，即：
    
    $$
    \langle \mathbf{b}_i, \mathbf{b}_j \rangle = 0 \quad \text{for } i \ne j
    $$
    
    那么这组基被称为**正交基 (Orthogonal Basis)**。
    
- 如果在正交基的基础上，每个基向量的长度都为1，即：
    
    $$
    \|\mathbf{b}_i\| = \sqrt{\langle \mathbf{b}_i, \mathbf{b}_i \rangle} = 1 \quad \text{for all } i
    $$
    
    那么这组基就被称为**标准正交基 (Orthonormal Basis, ONB)**。
    

**理解要点**

- 标准正交基是“最理想”的坐标系。想象一下三维空间中的 \((1,0,0), (0,1,0), (0,0,1)\)，它们就是最标准的ONB。
- 在ONB下，计算一个向量的坐标、进行投影等操作都会得到极大的简化。
- 一个重要的问题是：我们是否总能为任意向量空间找到一个标准正交基？答案是肯定的，而构造它的方法就是格拉姆-施密特过程。

## 格拉姆-施密特正交化 (Gram-Schmidt Orthogonalization)

格拉姆-施密特过程是一种算法，它可以将任意一组线性无关的向量（即一组基）转化为一组标准正交向量，且这组新向量张成的空间与原空间完全相同。

**核心思想：迭代式正交化**

其核心思想是 **“减去投影，保留垂直”**。从一组基 \(\{\mathbf{b}_1, \dots, \mathbf{b}_n\}\) 出发，我们逐步构造正交基 \(\{\mathbf{u}_1, \dots, \mathbf{u}_n\}\)：

1. **第一步：** 直接取第一个基向量作为新的正交基的第一个成员。
    
    $$
    \mathbf{u}_1 = \mathbf{b}_1
    $$
    
2. **第二步：** 取第二个基向量 \(\mathbf{b}_2\)，并减去它在 \(\mathbf{u}_1\) 方向上的**投影**。剩下的部分就必然与 \(\mathbf{u}_1\) 正交。
    
    $$
    \mathbf{u}_2 = \mathbf{b}2 - \pi_{\text{span}(\mathbf{u}_1)}(\mathbf{b}_2) = \mathbf{b}_2 - \frac{\langle \mathbf{b}_2, \mathbf{u}_1 \rangle}{\|\mathbf{u}_1\|^2} \mathbf{u}_1
    $$
    
3. **第k步：** 取第k个基向量 \(\mathbf{b}_k\)，并减去它在所有已构造好的正交向量 \(\{\mathbf{u}_1, \dots, \mathbf{u}_{k-1}\}\) 所张成的子空间上的投影。
    
    $$
    \mathbf{u}_k = \mathbf{b}_k - \sum_{j=1}^{k-1} \pi_{\text{span}(\mathbf{u}_j)}(\mathbf{b}_k) = \mathbf{b}_k - \sum_{j=1}^{k-1} \frac{\langle \mathbf{b}_k, \mathbf{u}_j \rangle}{\|\mathbf{u}_j\|^2} \mathbf{u}_j
    $$
    
4. **最后一步（归一化）：** 将得到的所有正交向量 \(\mathbf{u}_k\) 都除以它们各自的长度，即可得到一组标准正交基。

![*图3.12 格拉姆-施密特过程的几何图示*](https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2026/09/ag05-gram-schmidt.png)

*图3.12 格拉姆-施密特过程的几何图示*

---

**数值示例 (Example 3.12)**

假设在 \(\mathbb{R}^2\) 中有一组基 \(\mathbf{b}_1 = [2, 0]^\top, \mathbf{b}_2 = [1, 1]^\top\)，我们使用标准点积对其进行正交化。

1. **构造 \(\mathbf{u}_1\):**
$$\mathbf{u}_1 = \mathbf{b}_1 = [2, 0]^\top$$
2. **构造 \(\mathbf{u}_2\):**
$$\mathbf{u}_2 = \mathbf{b}_2 - \frac{\mathbf{b}_2^\top \mathbf{u}_1}{\|\mathbf{u}_1\|^2} \mathbf{u}_1 = [1, 1]^\top - \frac{1 \cdot 2 + 1 \cdot 0}{2^2 + 0^2} [2, 0]^\top = [1, 1]^\top - \frac{2}{4} [2, 0]^\top = [1, 1]^\top - [1, 0]^\top = [0, 1]^\top$$
我们得到了一组正交基 \(\{\mathbf{u}_1, \mathbf{u}_2\} = \{[2, 0]^\top, [0, 1]^\top\}\)。可以验证它们的点积为0。
3. **归一化:**
$$\mathbf{u}'_1 = \frac{\mathbf{u}_1}{\|\mathbf{u}_1\|} = \frac{1}{2}[2, 0]^\top = [1, 0]^\top$$
$$\mathbf{u}'_2 = \frac{\mathbf{u}_2}{\|\mathbf{u}_2\|} = \frac{1}{1}[0, 1]^\top = [0, 1]^\top$$
最终得到的标准正交基为 \(\{[1, 0]^\top, [0, 1]^\top\}\)，即标准基。

### 正交补 (Orthogonal Complement)

正交补的概念为投影提供了更深刻的理论背景。

**准确的数学定义**

给定一个向量空间 \(V\) 和它的一个子空间 \(U\)， \(U\) 的**正交补 (Orthogonal Complement)**，记作 \(U^\perp\)，是 \(V\) 中所有与 \(U\) 中**每一个**向量都正交的向量所构成的集合。

$$U^\perp := \{ \mathbf{v} \in V \mid \langle \mathbf{v}, \mathbf{u} \rangle = 0 \text{ for all } \mathbf{u} \in U \}$$

- **直观解释:**
    - 在三维空间中，一个平面（二维子空间）\(U\) 的正交补 \(U^\perp\) 就是穿过原点且垂直于该平面的法线（一维子空间）。
    - 一条直线（一维子空间）的正交补则是穿过原点且垂直于该直线的平面。
- **唯一分解:** 正交补最重要的性质是，任何向量 \(\mathbf{x} \in V\) 都可以被**唯一地**分解为一个在 \(U\) 中的部分和一个在 \(U^\perp\) 中的部分。这个在 \(U\) 中的部分，正是 \(\mathbf{x}\) 到子空间 \(U\) 的**正交投影**。

---

**章节知识点总结 (3.5, 3.6, 3.8.3)**

- 标准正交基 (ONB) 是由两两正交且长度为1的向量构成的基。
- 格拉姆-施密特过程是一种将任意基转化为标准正交基的算法，其核心是迭代地减去投影。
- 一个子空间 \(U\) 的正交补 \(U^\perp\) 包含了所有与 \(U\) 正交的向量。
- 任何向量都可以唯一分解为其在子空间 \(U\) 上的投影和在 \(U^\perp\) 上的投影之和。

**引出下一节**

格拉姆-施密特过程的核心操作是**投影**。这个操作本身在机器学习中具有极其重要的意义，它不仅是理论的基石，更是解决实际问题的强大工具。例如，如何在高维数据中找到信息量最大的低维表示（降维）？如何求解一个没有精确解的线性方程组（线性回归）？这些问题的答案都深植于**正交投影**之中。在下一节中，我们将系统地推导和研究正交投影的计算方法及其应用。
