---
title: "解析几何：旋转"
date: 2026-02-15T10:00:00+08:00
description: "从基向量像推导二维与三维旋转矩阵，理解正交变换的保距保角性质，并注意高维旋转的顺序不可交换。"
categories: ["notes"]
topics: ["math"]
tags: ["math"]
series: ["analytical-geometry"]
series_order: 7
showAuthor: false
aliases: ["/blogs/math/analytical-geometry/07/"]
---

<!-- 渲染公式 -->
{{< katex >}}


<!-- # 旋转 (Rotations) -->

除了投影，**旋转 (Rotation)** 是另一类基础且重要的线性变换。作为一种正交变换，旋转的核心特性是**保持向量的长度和向量间的角度**，即保持空间的刚性结构，仅改变对象的朝向。这使得它在计算机图形学、机器人控制和数据增强等领域扮演着关键角色。

![*图3.14 旋转变换的图示*](%E6%97%8B%E8%BD%AC%20(Rotations)/image.png)

*图3.14 旋转变换的图示*

---

## 二维空间中的旋转

在二维平面中，旋转的定义非常直观：将所有向量围绕原点逆时针旋转一个指定的角度 \(\theta\)。

**推导旋转矩阵**

我们可以通过观察标准基向量 \(\mathbf{e}_1=[1, 0]^\top\) 和 \(\mathbf{e}_2=[0, 1]^\top\) 经过旋转后的新位置来确定旋转矩阵 \(\mathbf{R}(\theta)\)。

![*图3.16 二维标准基的旋转*](%E6%97%8B%E8%BD%AC%20(Rotations)/image%201.png)

*图3.16 二维标准基的旋转*

- 旋转后的 \(\mathbf{e}_1\) 变为 \(\Phi(\mathbf{e}_1)\)，根据简单的三角学，其新坐标为：
    
    $$
    \Phi(\mathbf{e}_1) = \begin{bmatrix} \cos\theta \\ \sin\theta \end{bmatrix}
    $$
    
- 旋转后的 \(\mathbf{e}_2\) 变为 \(\Phi(\mathbf{e}_2)\)，其新坐标为：
    
    $$
    \Phi(\mathbf{e}_2) = \begin{bmatrix} \cos(\theta+90^\circ) \\ \sin(\theta+90^\circ) \end{bmatrix} = \begin{bmatrix} -\sin\theta \\ \cos\theta \end{bmatrix}
    $$
    

由于线性变换矩阵的列就是变换后的基向量，我们将这两个新坐标向量并排放置，得到二维旋转矩阵：

$$
\mathbf{R}(\theta) = \begin{bmatrix} \Phi(\mathbf{e}_1) & \Phi(\mathbf{e}_2) \end{bmatrix} = \begin{bmatrix} \cos\theta & -\sin\theta \\ \sin\theta & \cos\theta \end{bmatrix}
$$

- **应用:** 将任意向量 \(\mathbf{x} = [x_1, x_2]^\top\) 旋转 \(\theta\) 角，其新坐标 \(\mathbf{x}'\) 为 \(\mathbf{x}' = \mathbf{R}(\theta)\mathbf{x}\)。
- **性质:** 可以验证，旋转矩阵是正交矩阵，即 \(\mathbf{R}(\theta)^\top\mathbf{R}(\theta) = \mathbf{I}\)。此外，它的行列式 \(\det(\mathbf{R}(\theta)) = \cos^2\theta - (-\sin^2\theta) = 1\)，这表明它是一个纯粹的旋转，不包含反射（翻转）。

## 三维空间中的旋转

在三维空间中，旋转变得更加复杂，因为它需要一个**旋转轴**和一个旋转角度。最基本的三维旋转是围绕三个坐标轴的旋转。按照惯例，我们使用**右手定则**来定义正方向：如果右手大拇指指向旋转轴的正方向，那么四指弯曲的方向就是正角度的旋转方向。

**绕坐标轴的旋转矩阵**

- **绕Z轴旋转 \(\theta\) 角:**
此时，\(z\) 坐标保持不变，而 \(xy\) 平面进行二维旋转。
    
    $$
    \mathbf{R}_z(\theta) = \begin{bmatrix} \cos\theta & -\sin\theta & 0 \\ \sin\theta & \cos\theta & 0 \\ 0 & 0 & 1 \end{bmatrix}
    $$
    
- **绕X轴旋转 \(\theta\) 角:**
\(x\) 坐标保持不变，而 \(yz\) 平面进行旋转。
    
    $$
    \mathbf{R}_x(\theta) = \begin{bmatrix} 1 & 0 & 0 \\ 0 & \cos\theta & -\sin\theta \\ 0 & \sin\theta & \cos\theta \end{bmatrix}
    $$
    
- **绕Y轴旋转 \(\theta\) 角:**
\(y\) 坐标保持不变，\(xz\) 平面进行旋转。根据右手定则，从 \(y\) 轴正向看去，\(z\) 轴到 \(x\) 轴是逆时针方向。
    
    $$
    \mathbf{R}_y(\theta) = \begin{bmatrix} \cos\theta & 0 & \sin\theta \\ 0 & 1 & 0 \\ -\sin\theta & 0 & \cos\theta \end{bmatrix}
    $$
    

**重要注意事项：旋转的不可交换性**

在三维（及更高维）空间中，旋转的顺序至关重要。即，**旋转是不可交换的**。先绕X轴旋转再绕Z轴旋转，与先绕Z轴再绕X轴旋转，得到的结果通常是不同的。

$$
\mathbf{R}_x(\theta_1)\mathbf{R}_z(\theta_2) \ne \mathbf{R}_z(\theta_2)\mathbf{R}_x(\theta_1)
$$

这与二维旋转（可以交换）形成了鲜明对比。

---

## 高维空间中的旋转 (Givens Rotation)

旋转的概念可以推广到 \(n\) 维空间。一个**吉文斯旋转 (Givens Rotation)** 是一种在 \(n\) 维空间中，仅在一个二维平面（由两个坐标轴 \(i\) 和 \(j\) 张成）上进行旋转，同时保持所有其他 \(n-2\) 个维度不变的变换。

其旋转矩阵 \(\mathbf{R}_{ij}(\theta)\) **大部分是单位矩阵**，只在第 \(i\) 行 \(i\) 列、第 \(i\) 行 \(j\) 列、第 \(j\) 行 \(i\) 列和第 \(j\) 行 \(j\) 列的位置上嵌入一个二维旋转矩阵的元素：

$$
r_{ii} = \cos\theta, \quad r_{jj} = \cos\theta \\ r_{ij} = -\sin\theta, \quad r_{ji} = \sin\theta
$$

所有复杂的 \(n\) 维旋转都可以通过一系列吉文斯旋转的组合来构造。

---

## **知识点总结**

- 旋转是一种保持向量长度和角度的正交变换。
- 二维旋转由一个角度 \(\theta\) 定义，其矩阵为 \(\mathbf{R}(\theta) = \begin{bmatrix} \cos\theta & -\sin\theta \\ \sin\theta & \cos\theta \end{bmatrix}\)。
- 三维旋转需要指定旋转轴和角度，最基本的是绕三个坐标轴的旋转。
- 在三维及更高维度空间中，旋转操作的顺序是不可交换的。
- 吉文斯旋转是在高维空间中只在一个二维平面上进行旋转的基本操作。

---

至此，我们完成了第三章“解析几何”的学习。从最核心的**内积**出发，我们构建了一整套描述向量空间几何属性的工具。我们学会了如何使用**范数**来衡量向量的长度，如何通过内积定义**角度**和**正交性**，并掌握了两种关键的几何变换：**正交投影**和**旋转**。这些概念不仅为抽象的线性代数提供了直观的几何图像，更为重要的是，它们是理解和设计高级机器学习算法（如线性回归、主成分分析、支持向量机）不可或缺的数学基石。
