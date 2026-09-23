---
title: "解析几何：正交投影"
date: 2026-02-15T09:50:00+08:00
description: "推导向直线和高维子空间的正交投影公式，掌握法方程与投影矩阵，并连接最小二乘法和线性回归。"
categories: ["notes"]
topics: ["math"]
tags: ["math"]
series: ["analytical-geometry"]
series_order: 6
showAuthor: false
aliases: ["/blogs/math/analytical-geometry/06/"]
---

<!-- 渲染公式 -->
{{< katex >}}


# 正交投影 (Orthogonal Projections)

正交投影是连接线性代数与数据科学应用（如数据压缩、降维和线性回归）的核心桥梁。其根本目标是：**在给定的子空间 \(U\) 中，找到一个离特定向量 \(\mathbf{x}\) 最近的点**。这个“最近的点”就是 \(\mathbf{x}\) 在 \(U\) 上的正交投影。

---

## 投影的数学定义

在深入研究正交投影之前，我们先给出投影的一般性定义。

**准确的数学定义**

一个线性映射 \(\pi: V \to U\) (其中 \(U\) 是 \(V\) 的子空间) 被称为**投影 (Projection)**，如果它满足**幂等性 (Idempotent)**，即对自身应用两次和应用一次的效果相同：

$$
\pi^2 = \pi \circ \pi = \pi
$$

- **直观解释:** 对一个向量进行投影后，它已经落在了子空间 \(U\) 上。再对这个结果进行投影，它当然不会再移动，仍然是其自身。
- **投影矩阵:** 如果投影 \(\pi\) 由一个矩阵 \(\mathbf{P}_\pi\) *表示，*那么这个**投影矩阵**必须满足*：*
    
    $$
    \mathbf{P}_\pi^2 = \mathbf{P}_\pi
    $$
    

## 投影到一维子空间（直线）

我们从最简单的情况开始：将一个向量 \(\mathbf{x}\) 投影到由单个非零向量 \(\mathbf{b}\) 张成的一维子空间 \(U\)（即一条穿过原点的直线）上。我们用 \(\pi_U(\mathbf{x})\) 表示这个投影点。

**核心推导思路**

投影点 \(\pi_U(\mathbf{x})\) 必须满足两个条件：

1. **位置条件:** 投影点必须在直线上，因此它必然是 \(\mathbf{b}\) 的一个标量倍，即 \(\pi_U(\mathbf{x}) = \lambda\mathbf{b}\)，其中 \(\lambda\) 是我们要找的坐标。
2. **正交条件:** 连接向量 \(\mathbf{x}\) 与其投影点 \(\pi_U(\mathbf{x})\) 的向量（即误差向量 \(\mathbf{x} - \pi_U(\mathbf{x})\)）必须与直线本身（即与基向量 \(\mathbf{b}\)）正交。

![*图3.10 向量到一维子空间的投影*](https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2026/09/ag06-projection-1d-subspace.png)

*图3.10 向量到一维子空间的投影*

基于正交条件，我们有：

$$
\langle \mathbf{x} - \pi_U(\mathbf{x}), \mathbf{b} \rangle = 0
$$

将 \(\pi_U(\mathbf{x}) = \lambda\mathbf{b}\) 代入：

$$
\langle \mathbf{x} - \lambda\mathbf{b}, \mathbf{b} \rangle = 0
$$

利用内积的双线性，我们得到：

$$
\langle \mathbf{x}, \mathbf{b} \rangle - \lambda\langle \mathbf{b}, \mathbf{b} \rangle = 0
$$

解出坐标 \(\lambda\)：

$$
\lambda = \frac{\langle \mathbf{x}, \mathbf{b} \rangle}{\langle \mathbf{b}, \mathbf{b} \rangle} = \frac{\langle \mathbf{x}, \mathbf{b} \rangle}{\|\mathbf{b}\|^2}
$$

**投影公式**

将 \(\lambda\) 代回，我们得到了投影点 \(\pi_U(\mathbf{x})\) 和投影矩阵 \(\mathbf{P}_\pi\) 的通用公式。

- **投影点:**
    
    $$
    \pi_U(\mathbf{x}) = \lambda \mathbf{b} = \frac{\langle \mathbf{x}, \mathbf{b} \rangle}{\|\mathbf{b}\|^2} \mathbf{b}
    $$
    
- **投影矩阵 (使用标准点积):**
当内积为标准点积时，\(\langle \mathbf{x}, \mathbf{b} \rangle = \mathbf{b}^\top\mathbf{x}\)。投影公式变为：
    
    $$
    \pi_U(\mathbf{x}) = \frac{\mathbf{b}^\top\mathbf{x}}{\|\mathbf{b}\|^2} \mathbf{b} = \left(\frac{\mathbf{b}\mathbf{b}^\top}{\|\mathbf{b}\|^2}\right)\mathbf{x}
    $$
    
    因此，投影矩阵为：
    
    $$
    \mathbf{P}_\pi = \frac{\mathbf{b}\mathbf{b}^\top}{\mathbf{b}^\top\mathbf{b}}
    $$
    
- **注意:** \(\mathbf{b}^\top\mathbf{b}\) 是一个标量（内积），而 \(\mathbf{b}\mathbf{b}^\top\) 是一个 \(n \times n\) 的秩为1的矩阵（外积）。

## 投影到高维子空间

现在，我们将问题推广到将向量 \(\mathbf{x}\) 投影到由一组线性无关的基向量 \(\{\mathbf{b}_1, \dots, \mathbf{b}_m\}\) 张成的 \(m\) 维子空间 \(U\) 上。

**核心推导思路**

同样，投影点 \(\pi_U(\mathbf{x})\) 必须满足两个条件：

1. **位置条件:** 投影点必须在子空间 \(U\) 中，因此它必然是基向量的线性组合。如果我们将基向量作为列组成矩阵 \(\mathbf{B} = [\mathbf{b}_1 \dots \mathbf{b}_m]\)，那么投影点可以写成：
    
    $$
    \pi_U(\mathbf{x}) = \mathbf{B}\boldsymbol{\lambda}
    $$
    
    其中 \(\boldsymbol{\lambda} = [\lambda_1, \dots, \lambda_m]^\top\) 是待求的坐标向量。
    
2. **正交条件:** 误差向量 \(\mathbf{x} - \pi_U(\mathbf{x})\) 必须与子空间 \(U\) **完全正交**，这意味着它必须与 \(U\) 的**每一个**基向量都正交。
    
    $$
    \langle \mathbf{x} - \mathbf{B}\boldsymbol{\lambda}, \mathbf{b}_i \rangle = 0 \quad \text{for } i = 1, \dots, m
    $$
    

---

**法方程与投影公式**

使用标准点积，上述 \(m\) 个正交条件可以统一写成矩阵形式：

$$
\mathbf{B}^\top (\mathbf{x} - \mathbf{B}\boldsymbol{\lambda}) = \mathbf{0}
$$

整理得到：

$$
\mathbf{B}^\top\mathbf{x} - \mathbf{B}^\top\mathbf{B}\boldsymbol{\lambda} = \mathbf{0}
$$

这就导出了著名的**法方程 (Normal Equation)**：

$$
\mathbf{B}^\top\mathbf{B}\boldsymbol{\lambda} = \mathbf{B}^\top\mathbf{x}
$$

由于基向量是线性无关的，矩阵 \(\mathbf{B}^\top\mathbf{B}\) 是可逆的。解出坐标向量 \(\boldsymbol{\lambda}\)：

$$
\boldsymbol{\lambda} = (\mathbf{B}^\top\mathbf{B})^{-1}\mathbf{B}^\top\mathbf{x}
$$

- **投影点:**
    
    $$
    \pi_U(\mathbf{x}) = \mathbf{B}\boldsymbol{\lambda} = \mathbf{B}(\mathbf{B}^\top\mathbf{B})^{-1}\mathbf{B}^\top\mathbf{x}
    $$
    
- **投影矩阵:**
    
    $$
    \mathbf{P}_\pi = \mathbf{B}(\mathbf{B}^\top\mathbf{B})^{-1}\mathbf{B}^\top
    $$
    
    - **伪逆:** 这里的矩阵 \((\mathbf{B}^\top\mathbf{B})^{-1}\mathbf{B}^\top\) 被称为矩阵 \(\mathbf{B}\) 的**伪逆 (Pseudo-inverse)**。

---

**与最小二乘法的联系**
法方程是**线性回归**和**最小二乘法**的核心。在这些问题中，我们试图求解一个可能无解的超定方程组 \(\mathbf{B}\boldsymbol{\lambda} = \mathbf{x}\)。最佳近似解（最小化误差 \(\|\mathbf{x} - \mathbf{B}\boldsymbol{\lambda}\|^2\) 的解）正是将 \(\mathbf{x}\) 投影到 \(\mathbf{B}\) 的列空间上得到的解。

---

**当基是标准正交基 (ONB) 时**

如果子空间 \(U\) 的基 \(\mathbf{B}\) 恰好是一组标准正交基，那么 \(\mathbf{B}^\top\mathbf{B} = \mathbf{I}\)（单位矩阵）。此时，投影公式得到巨大简化：

- **坐标:** \(\boldsymbol{\lambda} = \mathbf{B}^\top\mathbf{x}\)
- **投影矩阵:** \(\mathbf{P}_\pi = \mathbf{B}\mathbf{I}^{-1}\mathbf{B}^\top = \mathbf{B}\mathbf{B}^\top\)
这突显了使用标准正交基在计算上的巨大优势——无需计算矩阵的逆。

---

## **知识点总结**

- 正交投影是在子空间中寻找离某点最近的点的过程，投影矩阵满足 \(\mathbf{P}^2 = \mathbf{P}\)。
- 投影到由 \(\mathbf{B}\) 的列向量张成的子空间，其投影矩阵为 \(\mathbf{P}_\pi = \mathbf{B}(\mathbf{B}^\top\mathbf{B})^{-1}\mathbf{B}^\top\)。
- 求解投影坐标的核心是解**法方程** \(\mathbf{B}^\top\mathbf{B}\boldsymbol{\lambda} = \mathbf{B}^\top\mathbf{x}\)，这与最小二乘法紧密相关。
- 如果基是标准正交的，投影矩阵简化为 \(\mathbf{P}_\pi = \mathbf{B}\mathbf{B}^\top\)，大大降低了计算复杂度。

---

**后续**

我们已经研究了正交投影。需要注意，投影一般不是正交变换，而是满足幂等性的线性映射：它通常不可逆，也不保持向量长度和距离。另一类同样重要的正交变换是**旋转 (Rotation)** 。旋转在保持向量长度和角度的同时，改变其在空间中的朝向。这在计算机图形学、机器人学和数据增强等领域有广泛应用。在下一节中，我们将具体探讨如何在二维和三维空间中表示和执行旋转操作。
