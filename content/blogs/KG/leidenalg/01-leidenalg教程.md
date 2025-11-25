---
title: "leidenalg 包教程（1）"
showAuthor: false
date: 2022-06-21
description: "leidenalg 包基础用法介绍"
slug: "01"
tags: ["教程", "KG", "leidenalg"]
series: ["leidenalg"]
series_order: 1
draft: false
---


## 安装

简单来说，可以使用`pip install leidenalg`直接安装。

也可以使用源码进行安装， 安装这个包需要`C`核心库`igraph`和python包`python-igraph`，然后可以通过`python setup.py test`安装

不建议Windows，使用源代码进行安装。

## 介绍

`leidenalg`软件包建立在`igraph`基础之上，有助于网络的社区发现。leiden是大型网络中社区发现方法的通用算法。如果只想对给定的图$G$进行模块化社区发现可以：

```python
import leidenalg as la
import igraph as ig

partition = la.find_partition(G, la.ModularityVertexPartition) # 模块化顶点分区
```

在`igraph`包中内置了`Louvain`算法`community_multilevel()`，可以简单的将无向无权重图进行分区。在`leidenalg`包中，有一些其他的功能，并且使用的`leidena`算法比`louvain`算法性能更好。

例子：`Zachary` 空手道俱乐部网络

```python
import igraph as ig
import leidenalg as la

# 加载 Zachary 空手道俱乐部图
G = ig.Graph.Famous('Zachary')

# 检测具有模块化的社区
partition = la.find_partition(G, la.ModularityVertexPartition)

# 绘制结果
ig.plot(partition)
```

![image.png](https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/11/image.png)

在这种情况下，算法实际上会找到最佳分区，可以使用`igraph`包中的`community_optimal_modularity()`来检查,会得到不同的结果。

但是，这样做会得到很多的子社区。下面介绍使用`CPMVertexPartition`如何将它一分为二：

```python
partition = la.find_partition(G, la.CPMVertexPartition, resolution_parameter = 0.05);
ig.plot(partition)

```

![image.png](https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/11/image%201.png)

传递给`find_partition`的额外参数`**kwargs`都会传递给给定`partition_type`。可以传递`resolution_parameter`、`weights` 、`node_sizes`等参数。

除此之外，`leidenalg`还支持有向图和加权图，可以在一定程度上自定义优化程序，而且还支持处理多路复用图（多元异构图）。

## 高级技巧

### 1. 优化器

`leidenalg`包提供对函数的简单访问`find_partition()`，但是底层使用`Optimiser`类完成。显示构建一个`Optimiser`对象：

```python
optimiser = la.Optimiser()
```

函数`find_partition()`不在执行任何其他操作，仅在提供的分区上调用`optimise_partition`。

```python
diff = optimiser.optimise_partition(partition)
```

`optimise_partition()`简单地尝试优化分区，可以反复调用以不断优化

```python
G = ig.Graph.Erdos_Renyi(100, p=5./100)
partition = la.ModularityVertexPartition(G)
diff = 1
while diff > 0:
    diff = optimiser.optimise_partition(partition)
```

调用可能没有改进当前分区，下一次可能会改进。

进行重复迭代可以调用内置的函数，传入参数：

```python
diff = optimiser.optimise_partition(partition, n_iterations=10)
```

如果`n_iterations<0`，优化器会持续下去优化，直到遇到没有改进的分区的迭代。

`optimise_partition()`的执行过程又是建立在`move_nodes()`和`merge_nodes()`算法之上，可以自行调用：

```python
diff = optimiser.move_nodes(partition)
diff = optimiser.merge_nodes(partition)
```

使用以上基本算法实现`Louvain`算法聚合分区，并在聚合分区上重复使用`move_nodes()`:

```python
partition = la.ModularityVertexPartition(G)
while optimiser.move_nodes(partition) > 0:
    partition = partition.aggregate_partition()
```

尽管这样可以找到最终的聚合分区，但是在各个节点级别上的实际分区仍然不清楚。为了做到这一点，我们需要基于聚合分区更新成员关系，为此我们使用函数 `from_coarse_partition()`

```python
partition = la.ModularityVertexPartition(G)
partition_agg = partition.aggregate_partition()
while optimiser.move_nodes(partition_agg) > 0:
    partition.from_coarse_partition(partition_agg)
    partition_agg = partition_agg.aggregate_partition()
```

现在`partition_agg`包含聚合分区，并且`partition`包含原始图`G`的实际分区。`partition_agg.quality() == partition.quality()` 两个基本等价。

也可以使用`merge_nodes()`代替`move_nodes()`，函数的选择取决于特定的替换社区。

在`Leiden`算法中，可以先细化分区，再聚合。算法可以使用函数数`move_nodes_constrained()`和 `merge_nodes_constrained()`来完成：

```python
# Set initial partition 设置初始化分区
partition = la.ModularityVertexPartition(G)
refined_partition = la.ModularityVertexPartition(G)
partition_agg = refined_partition.aggregate_partition()

while optimiser.move_nodes(partition_agg):

	  # Get individual membership for partition 得到个体分区的资格
	  partition.from_coarse_partition(partition_agg, refined_partition.membership)
	
	  # Refine partition 细化分区
	  refined_partition = la.ModularityVertexPartition(G)
	  optimiser.merge_nodes_constrained(refined_partition, partition)
	
	  # Define aggregate partition on refined partition 在细化分区上定义聚合分区
	  partition_agg = refined_partition.aggregate_partition()
	
	  # But use membership of actual partition使用实际分区的资格
	  aggregate_membership = [None] * len(refined_partition)
	  for i in range(G.vcount()):
	    aggregate_membership[refined_partition.membership[i]] = partition.membership[i]
	  partition_agg.set_membership(aggregate_membership)
```

这些函数又依赖两个关键的基本函数： `diff_move()`和`move_node()`。前者计算移动节点时的差异，后者实际移动节点，并更新所有必要的内部管理。函数`move_nodes()`然后执行：

```python
for v in G.vs:
	  best_comm = max(range(len(partition)),
	                  key=lambda c: partition.diff_move(v.index, c))
	  partition.move_node(v.index, best_comm)
```

实际的实现更为复杂，总体是这个思路。

### 2. Resolution profile 分辨率配置文件

该参数的作用是一种阈值：社区的密度至少要达到$\gamma$，而社区之间的密度要低于$\gamma$*，较高的分辨率会导致更多的社区，而较低的分辨率会导致更少的社区*

一些如`CPMVertexPartition`或`RBConfigurationVertexPartition`方法接受的分辨率（解析）参数。虽然某些方法具有某种“天生”的分辨率参数，但实际上却是十分武断的。然而，这里使用的方法（以线性方式依赖于分辨率参数）允许对分辨率参数的范围内进行有效扫描。这些方法可以表述为$Q = E - \gamma N$。

在`CPMVertexPartition`中 $E= \sum_c m_c$ 表示社区 $c$ 中的边的数量，$N=\sum_c {n_c \choose 2}$ 表示期望的社区 $c$ 内部的边的总和。如果存在最佳分区 $\gamma_1$ 和 $\gamma_2$，那么 $\gamma_1 ≤ \gamma ≤ \gamma_2$ 都是最佳分区。

可以使用`Optimiser`对象构建这样的分辨率参数：

```python
G = ig.Graph.Famous('Zachary')
optimiser = la.Optimiser()
profile = optimiser.resolution_profile(G, la.CPMVertexPartition,
                                       resolution_range=(0,1))

```

绘制分辨率参数与子社区总边数的关系图，结果如下：

![image.png](https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/11/image%202.png)

现在，配置文件包含一个指定类型的分区列表（例子中为`CPMVertexPartition`），用于解析参数发生变化。特别是，`profile[i]`应该更好直到`profile[i+1]`，或者有另外的说明，对于`profile[i].resolution_parameter`和 `profile[i+1].resolution_parameter`之间的分区的分辨率参数`i`更好。当然，会有一些变化，因为`optimise_partition()`会找到不同质量的分区，不同的运行，变化点也可能会有所不同。

此函数会重复调用`optimise_partition()` ，因此可能需要大量时间。特别是对于改变点附近的分辨率参数，可能有许多可能的分区，因此需要大量运行。

### 3. 固定（确定）节点

由于某些原因，只更新分区（子社区）的一部分可能是有益的。例如，在一些数据上已经运行了`leiden`算法，并对结果进行了一些分析，随后又收集了一些新的数据，特别是新的节点，那么保持以前的社区分配不变，而只更新新节点的社区分配，这样做可能是有益的。

可以使用`is_membership_fixed`参数传入`find_partition()`来完成分区。

例如，假设我们之前检测到图`G`的分区，它被扩展到图`G2`。假设之前退出的节点是相同的，我们可以通过以下方式创建一个新的分区:

```python
new_membership = list(range(G2.vcount()))
new_membership[:G.vcount()] = partition.membership
```

然后，我们只能按照如下方式更新新节点的社区分配

```python
new_partition = la.CPMVertexPartition(G2, new_membership, resolution_parameter=partition.resolution_parameter)
is_membership_fixed = [i < G.vcount() for i in range(G2.vcount())]

diff = optimiser.optimise_partition(partition, is_membership_fixed=is_membership_fixed)
```

在这个例子中，使用了`CPMVertexPartition`，也可以使用其他`VertexPartition`。

### 4. 最大社区规模

在某种情况下，可能需要限制最大子社区的规模，可以通过`max_comm_size`参数来指定最大子社区规模。此参数可以在优化期间进行设定产生约束，也可以直接传递到`find_partition()`。

```python
partition = la.find_partition(G, la.ModularityVertexPartition, max_comm_size=10) # 限定最大子社区规模为10
```

---

## 参考

- [leidenalg](https://leidenalg.readthedocs.io/en/latest/)
- Traag, V. A., Krings, G., & Van Dooren, P. (2013). Significant scales in community structure. Scientific Reports, 3, 2930. [10.1038/srep02930](http://doi.org/10.1038/srep02930)[2](https://leidenalg.readthedocs.io/en/latest/advanced.html#id2)
- Zanini, F., Berghuis, B. A., Jones, R. C., Robilant, B. N. di, Nong, R. Y., Norton, J., Clarke, Michael F., Quake, S. R. (2019). northstar: leveraging cell atlases to identify healthy and neoplastic cells in transcriptomes from human tumors. BioRxiv, 820928. [10.1101/820928](https://doi.org/10.1101/820928)
