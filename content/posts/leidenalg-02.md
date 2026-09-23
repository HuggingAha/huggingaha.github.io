---
title: "leidenalg 包教程（2）"
date: 2022-06-24
description: "leidenalg 包异构网络社区检测"
categories: ["notes"]
topics: ["knowledge-graph"]
tags: ["knowledge-graph", "graph-algorithm"]
series: ["leidenalg"]
series_order: 2
showAuthor: false
aliases: ["/blogs/kg/leidenalg/02/"]
---

<!-- 渲染公式 -->
{{< katex >}}



## 一、引言

在复杂网络分析中，社区检测是关键任务之一。`leidenalg` 库提供了多路复用（Multiplex）社区检测功能，适用于处理多个图层或切片的网络。本文将介绍如何使用 `leidenalg` 进行多路复用社区检测。

## 二、多路复用社区检测基础概念

### 层（Layer）与切片（Slice）

- **层（Layer）** ：多个图定义在相同顶点集上，但边集不同。每个节点属于同一社区。
- **切片（Slice）** ：图可以有不同的顶点集，节点在不同切片中可属于不同社区。需将切片转换为层才能使用相同算法。

## 三、层多路复用（Layer Multiplex）

### 示例：电话与邮件通信图

假设 `G_telephone` 和 `G_email` 分别表示朋友间电话和邮件通信图，顶点集相同。可使用 `find_partition_multiplex()` 函数进行社区检测：

```python
>>> import igraph as ig
>>> import leidenalg as la
>>> G_telephone = ig.Graph(edges=[(0, 1), (1, 2)], n=3)
>>> G_email = ig.Graph(edges=[(0, 2), (1, 2)], n=3)
>>> optimiser = la.Optimiser()
>>> membership, improv = la.find_partition_multiplex(
...                        [G_telephone, G_email],
...                        la.ModularityVertexPartition)
```

### 层权重与不同分区类型

- **层权重（layer_weight）** ：可为不同层指定权重，调整层在整体质量中的重要性。如邮件层权重设为 0.5：

```python
>>> part_telephone = la.ModularityVertexPartition(G_telephone)
>>> part_email = la.ModularityVertexPartition(G_email)
>>> diff = optimiser.optimise_partition_multiplex(
...   [part_telephone, part_email],
...   layer_weights=[1,0.5])
```

- **不同分区类型** ：可为不同层使用不同分区类型，如为电话图使用 `CPMVertexPartition`，邮件图使用更高分辨率参数：

```python
>>> part_telephone = la.CPMVertexPartition(
...                    G_telephone, resolution_parameter=0.01)
>>> part_email = la.CPMVertexPartition(
...                    G_email, resolution_parameter=0.3)
>>> diff = optimiser.optimise_partition_multiplex(
...                    [part_telephone, part_email])
```

### 负链接处理

当图包含负链接（如冲突或敌意关系）时，可将图分为正负两层，正层权重为正，负层权重为负。

**具体例子** ：一个 6 人的社交小团体，节点 0、1、2 与节点 3、4、5 是两派。正权重边表示友好（同派内部），负权重边表示敌对（跨派之间）：

```python
>>> G = ig.Graph(n=6, edges=[(0, 1), (1, 2), (0, 2),      # 派内友好
...                          (3, 4), (4, 5), (3, 5),
...                          (0, 3), (1, 4), (2, 5)])     # 跨派敌对
>>> G.es['weight'] = [1, 1, 1, 1, 1, 1, -1, -1, -1]
>>> G_pos = G.subgraph_edges(G.es.select(weight_gt = 0), delete_vertices=False)
>>> G_neg = G.subgraph_edges(G.es.select(weight_lt = 0), delete_vertices=False)
>>> G_neg.es['weight'] = [-w for w in G_neg.es['weight']]  # 负层内部权重取正
>>> part_pos = la.ModularityVertexPartition(G_pos, weights='weight')
>>> part_neg = la.ModularityVertexPartition(G_neg, weights='weight')
>>> diff = optimiser.optimise_partition_multiplex(
...   [part_pos, part_neg],
...   layer_weights=[1,-1])
>>> part_pos.membership
[0, 0, 0, 1, 1, 1]
```

`layer_weights=[1, -1]` 的含义：正层的模块度正常计入，负层**反着**计入——负层内部的连接会拉低质量，相当于把「存在负链接的节点对」往不同社区推。对本例，正层想把两个三角形各自抱团，负层想把跨派对子拆开，两个目标不冲突，因此稳定结果是 `{0,1,2}` 与 `{3,4,5}` 两个社区，即 `membership` 为 `[0, 0, 0, 1, 1, 1]`（社区编号本身无意义，0/1 整体互换等价）。

## 四、二分网络社区检测

二分网络中节点分为两类，如产品和顾客，仅允许两类间链接。可通过创建三个层来检测社区：

- **层 1** ：所有节点大小为 1，包含相关链接。
- **层 2** ：仅一类节点大小为 1，无链接。
- **层 3** ：另一类节点大小为 1，无链接。

将层 2 和层 3 的层权重设为 -1，层 1 权重设为 1，可实现二分网络社区检测。例如：

```python
>>> p_01, p_0, p_1 = la.CPMVertexPartition.Bipartite(G,
...                    resolution_parameter_01=0.1)
>>> diff = optimiser.optimise_partition_multiplex([p_01, p_0, p_1],
...                                        layer_weights=[1, -1, -1])
```

CPM 方法的公式为：

$$
Q=\sum_{i j}[A_{i j}-(\gamma_{0}\delta(s_{i},0)+\gamma_{1}\delta(s_{i},1))\delta(s_{i},s_{j})-\gamma_{01}(1-\delta(s_{i},s_{j}))]\delta(\sigma_{i},\sigma_{j})
$$

其中，\(\gamma_{0}\)、\(\gamma_{1}\) 和 \(\gamma_{01}\) 分别表示类内连接、类内连接和类间连接的分辨率参数。通过将三个层的权重和分辨率参数设置为上述方式，可以实现对二分网络的社区检测。

## 五、切片到层的转换

### 背景与方法

多路复用层有两局限：各图需有相同顶点集；节点只能属于一个社区。为突破此限制，引入切片概念。切片是不同图，可有不同顶点集，节点在不同切片中可属不同社区。通过构建耦合图，将切片转换为层。

![](https://leidenalg.readthedocs.io/en/latest/_images/slices.png)

![img](https://leidenalg.readthedocs.io/en/latest/_images/layers_separate.png)

### 示例：三个时间切片

**具体例子** ：把 3 个学期看作 3 个时间切片，6 名学生（节点 0–5）在同一学期合作过项目就连一条边：

- `G_1`（第 1 学期）：节点 0、1、2 互相合作（一个三角形），3、4、5 没有合作；
- `G_2`（第 2 学期）：0、1、2 继续合作，3、4、5 也开始合作（两个三角形）；
- `G_3`（第 3 学期）：0、1、2 的合作解散，只剩 3、4、5 合作。

耦合图为 `1 -- 2 -- 3`，表示只把相邻学期耦合起来（同一学生在相邻学期的「身份」之间连一条权重为 0.1 的边）。CPM 分辨率参数取 `gamma = 0.5`：一个 3 节点三角形抱团的质量收益是「3 条边 − γ × 3 个节点对」，即 3 − 3γ；γ < 1 时收益为正，三角形才会成团，γ ≥ 1 时会被拆散。

转换步骤如下：

1. 创建三个切片，设置边权，再创建耦合图：

```python
>>> G_1 = ig.Graph(n=6, edges=[(0, 1), (1, 2), (0, 2)])                   # 第 1 学期
>>> G_2 = ig.Graph(n=6, edges=[(0, 1), (1, 2), (0, 2),
...                            (3, 4), (4, 5), (3, 5)])                  # 第 2 学期
>>> G_3 = ig.Graph(n=6, edges=[(3, 4), (4, 5), (3, 5)])                   # 第 3 学期
>>> for g in (G_1, G_2, G_3):
...     g.es['weight'] = 1                        # CPM 分区要求显式的边权
>>> gamma = 0.5
>>> G_coupling = ig.Graph.Formula('1 -- 2 -- 3')
>>> G_coupling.es['weight'] = 0.1  # 切片间耦合强度
>>> G_coupling.vs['slice'] = [G_1, G_2, G_3]
```

1. 转换为层：

```python
>>> layers, interslice_layer, G_full = la.slices_to_layers(G_coupling)
```

1. 创建各层分区，并优化：

```python
>>> partitions = [la.CPMVertexPartition(H, node_sizes='node_size',
...                                          weights='weight', resolution_parameter=gamma)
...               for H in layers]
>>> interslice_partition = la.CPMVertexPartition(interslice_layer, resolution_parameter=0,
...                                                   node_sizes='node_size', weights='weight')
>>> diff = optimiser.optimise_partition_multiplex(partitions + [interslice_partition])

```

对本例，预期的结果是：第 1 学期 `{0,1,2}` 是一个社区（3、4、5 在该学期没有边，归属由耦合项锚定）；第 2 学期分成 `{0,1,2}`、`{3,4,5}` 两个社区；第 3 学期只剩 `{3,4,5}` 一个社区。耦合强度 0.1 的意义就体现在这种跨学期的连续性上——比如节点 3 在第 1 学期没有任何合作记录，本可随意归属，但会被它在第 2 学期的归属拉到同一社区。

**注意** ：通常将切片间层设为 `CPMVertexPartition`，分辨率参数为 0，节点大小设为 0。

## 六、时间社区检测

对于时间切片的社区检测，可以用 `find_partition_temporal()` 函数把上面整个流程（切片转层 + 多路复用优化）封装成一步。沿用上一节的 `G_1`、`G_2`、`G_3` 和 `gamma = 0.5`：

```python
>>> membership, improvement = la.find_partition_temporal(
... [G_1, G_2, G_3],
... la.CPMVertexPartition,
... interslice_weight=0.1,
... resolution_parameter=gamma)
>>> membership
[[0, 0, 0, 1, 1, 1], [0, 0, 0, 1, 1, 1], [0, 0, 0, 1, 1, 1]]
```

`membership` 是按切片给出的节点社区编号列表（3 个切片各一个），预期形如上面的结果：节点 0、1、2 在三个学期中同属一个社区，节点 3、4、5 同属另一个，归属跨学期保持平滑。（社区编号本身可能整体不同，如 0/1 全部互换；没有边的节点在个别切片中的归属也可能受随机初始化影响。）

或者使用 `time_slices_to_layers()` 函数获取层和分区：

```python
>>> layers, interslice_layer, G_full = la.time_slices_to_layers([G_1, G_2, G_3], interslice_weight=0.1)
>>> partitions = [la.CPMVertexPartition(H, node_sizes='node_size', weights='weight', resolution_parameter=gamma) for H in layers]
>>> interslice_partition = la.CPMVertexPartition(interslice_layer, resolution_parameter=0, node_sizes='node_size', weights='weight')
>>> diff = optimiser.optimise_partition_multiplex(partitions + [interslice_partition])
```

## 七、总结

本文介绍了 `leidenalg` 库的多路复用社区检测功能，包括层与切片的概念、层多路复用的实现、负链接与二分网络的处理，以及切片到层的转换方法和时间社区检测。通过这些方法，可更灵活地分析复杂网络的社区结构。

## 八、参考文献

1. Mucha, P. J., Richardson, T., Macon, K., Porter, M. A., & Onnela, J.-P. (2010). Community structure in time-dependent, multiscale, and multiplex networks. Science, 328(5980), 876–8. 10.1126/science.1184819
2. Traag, V. A., & Bruggeman, J. (2009). Community detection in networks with positive and negative links. Physical Review E, 80(3), 036115. 10.1103/PhysRevE.80.036115
3. Barber, M. J. (2007). Modularity and community detection in bipartite networks. Physical Review E, 76(6), 066102. 10.1103/PhysRevE.76.066102
