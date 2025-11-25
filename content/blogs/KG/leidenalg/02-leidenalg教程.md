---
title: "leidenalg 包教程（2）"
showAuthor: false
date: 2022-06-24
description: "leidenalg 包异构网络社区检测"
slug: "02"
tags: ["教程", "KG", "leidenalg"]
series: ["leidenalg"]
series_order: 2
draft: false
---


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
>>> membership, improv = la.find_partition_multiplex(
...                        [G_telephone, G_email],
...                        la.ModularityVertexPartition)
```

### 层权重与不同分区类型

- **层权重（layer_weight）** ：可为不同层指定权重，调整层在整体质量中的重要性。如邮件层权重设为 0.5：

```python
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

当图包含负链接（如冲突或敌意关系）时，可将图分为正负两层，正层权重为正，负层权重为负。例如：

```python
>>> G_pos = G.subgraph_edges(G.es.select(weight_gt = 0), delete_vertices=False)
>>> G_neg = G.subgraph_edges(G.es.select(weight_lt = 0), delete_vertices=False)
>>> G_neg.es['weight'] = [-w for w in G_neg.es['weight']]
>>> part_pos = la.ModularityVertexPartition(G_pos, weights='weight')
>>> part_neg = la.ModularityVertexPartition(G_neg, weights='weight')
>>> diff = optimiser.optimise_partition_multiplex(
...   [part_pos, part_neg],
...   layer_weights=[1,-1])
```

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

其中，$\gamma_{0}$、$\gamma_{1}$ 和 $\gamma_{01}$ 分别表示类内连接、类内连接和类间连接的分辨率参数。通过将三个层的权重和分辨率参数设置为上述方式，可以实现对二分网络的社区检测。

## 五、切片到层的转换

### 背景与方法

多路复用层有两局限：各图需有相同顶点集；节点只能属于一个社区。为突破此限制，引入切片概念。切片是不同图，可有不同顶点集，节点在不同切片中可属不同社区。通过构建耦合图，将切片转换为层。

![](https://leidenalg.readthedocs.io/en/latest/_images/slices.png)

![img](https://leidenalg.readthedocs.io/en/latest/_images/layers_separate.png)

### 示例：三个时间切片

假设三个时间切片 `G_1`、`G_2`、`G_3`，耦合图为 `1 -- 2 -- 3`。转换步骤如下：

1. 创建耦合图并设置权重：

```python
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

**注意** ：通常将切片间层设为 `CPMVertexPartition`，分辨率参数为 0，节点大小设为 0。

## 六、时间社区检测

对于时间切片的社区检测，可以使用 `find_partition_temporal()` 函数。例如：

```python
>>> membership, improvement = la.find_partition_temporal(
... [G_1, G_2, G_3],
... la.CPMVertexPartition,
... interslice_weight=0.1,
... resolution_parameter=gamma)
```

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
