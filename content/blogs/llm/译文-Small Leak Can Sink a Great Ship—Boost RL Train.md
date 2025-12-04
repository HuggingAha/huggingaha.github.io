---
title: "译文-Small Leak Can Sink a Great Ship—Boost RL Training on MoE with 𝑰𝒄𝒆𝑷𝒐𝒑!"
showAuthor: false
date: 2025-09-23
description: "RL-Training-MoE-IcePop"
slug: "Small-Leak-Can-Sink-a-Great-Ship-Boost-RL-Training-on-MoE-with-IcePop"
tags: ["论文", "翻译", "LLM", "MoE", "RL", "IcePop"]
# series: [""]
# series_order: 1
draft: false
---

<!-- 渲染公式 -->
{{< katex >}}


<!-- # 小漏洞可以击沉大船——用𝐼𝑐𝑒𝑃𝑜𝑝增强MoE上的RL训练！ -->

> [huggingface/inclusionAI](https://huggingface.co/inclusionAI) || [modelscope/inclusionAI](https://modelscope.cn/organization/inclusionAI)  
> [notion/icepop](https://ringtech.notion.site/icepop)
> 


**TL;DR**  
最近的工作[[1]](https://www.notion.so/Small-Leak-Can-Sink-a-Great-Ship-Boost-RL-Training-on-MoE-with-27688396fe1c8144896ad187a98b06e1?pvs=21)强调了当前强化学习（RL）训练框架中模型训练和推理生成之间的不匹配问题。我们观察到，这个问题在 **专家混合（MoE）架构中可能会加剧** ☹️。特别是当模型倾向于生成长响应时，这种差异会**进一步放大** 😱。尽管之前的工作[[1]](https://www.notion.so/Small-Leak-Can-Sink-a-Great-Ship-Boost-RL-Training-on-MoE-with-27688396fe1c8144896ad187a98b06e1?pvs=21)提出通过引入重要性采样校正来缓解这个问题，但我们认为，随着训练的进行，这种技术可能在基准测试中达到性能瓶颈。相反，我们提出了一种简单而有效的方法——‣𝑰𝒄𝒆𝑷𝒐𝒑 🤩 ，即使在强大的 SFT-ed MoE 模型上，也能通过 RL 实现稳定的训练和卓越的下游性能。

---

## MoE上的不匹配问题

不匹配问题指的是当前 RL 训练框架中训练后端和推理引擎之间的概率差异，这不可避免地将在线策略训练转变为离线策略[[1]](https://www.notion.so/Small-Leak-Can-Sink-a-Great-Ship-Boost-RL-Training-on-MoE-with-27688396fe1c8144896ad187a98b06e1?pvs=21)。我们观察到，这种实现差距在 MoE 模型上的 RL 训练过程中变得更加显著。与密集模型不同，为了实现更高的参数效率，MoE 架构采用了一种路由机制，该机制在训练和推理过程中仅为每个 token 选择少数排名靠前的"专家"。然而，我们发现这种结构设计加剧了在线策略 RL（on-policy RL）训练期间的不匹配问题，从而阻止了 MoE 模型充分释放强化学习的潜力。

<figure>
  <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/11/ykTlwA.png" alt="MoE和密集模型之间 \(|\log p_{\rm infer} - \log p_{\rm train}|\) 的比较。我们选择了三个代表性模型：[Ring-mini-2.0](https://huggingface.co/inclusionAI/Ring-mini-2.0)(MoE)，Qwen3-4B（密集），Qwen3-30B-A3B（MoE），显示MoE模型通常在训练和推理引擎之间表现出更大的差异。我们将包含更多不同模型大小的比较。">
  <figcaption style="text-align: center;">图1：MoE和密集模型之间 \(|\log p_{\rm infer} - \log p_{\rm train}|\) 的比较。我们选择了三个代表性模型：[Ring-mini-2.0](https://huggingface.co/inclusionAI/Ring-mini-2.0)(MoE)，Qwen3-4B（密集），Qwen3-30B-A3B（MoE），显示MoE模型通常在训练和推理引擎之间表现出更大的差异。我们将包含更多不同模型大小的比较。</figcaption>
</figure>


根据下面的策略梯度方程，我们可以看到另一个不匹配问题出现了，即 \(\textcolor{red}{\theta_{\rm infer}}\) 和 \(\textcolor{blue}{\theta_{\rm train}}\)。在MoE模型中，路由函数 \(\texttt{TopK}(\cdot)\) 为每个输入token动态激活一部分"专家"（如：网络）。理想情况下，对于固定的输入，无论策略模型部署在哪个引擎上，\(\texttt{TopK}(\cdot)\) 的输出都应该是相同的。然而，当 \(\textcolor{red}{\theta_{\rm infer}}\) 和 \(\textcolor{blue}{\theta_{\rm train}}\) 之间存在显著差距时，这将不可避免地导致 \(\textcolor{red}{\pi_{\rm infer}}\) 和 \(\textcolor{blue}{\pi_{\rm train}}\) 之间的更大分歧。

$$
\small{\begin{equation}\theta \leftarrow \theta + \mu \cdot \mathbb{E}_{a\sim \textcolor{red}{\pi_{{\rm{infer}}}}(\textcolor{red}{\theta_{\rm infer}} ), \ \textcolor{red}{\theta_{\rm infer}} \sim \mathtt{TopK}_{\rm infer}(a)}\left[ R(a) \cdot \nabla_{\theta}\log \textcolor{blue}{\pi_{\rm{train}}}(a;\textcolor{blue}{\theta_{\rm train}});\textcolor{blue}{\theta_{\rm train}} \!\sim \!\texttt{TopK}_{\rm train}(a) \right]\end{equation}}
$$

对于 MoE 模型，我们识别出训练-推理差异问题的两个主要原因：

- **训练和推理阶段选择的专家可能不同。**
    
    > 我们之前的分析表明，即使在第一个 MoE 层中，已经有一小部分 token 在训练后端和推理引擎中激活了不同的专家。
    > 
    
    例如，当选择 Top-k 和 Top-(k+1) 专家的概率非常接近时，即使是轻微的精度差异也可能导致在训练期间和推理期间选择不同的专家，从而导致计算概率的巨大差异。
    
- **随着更多路由网络的堆叠，不匹配变得明显。**
    
    > 我们进一步注意到，随着 MoE 层的加深，在训练后端和推理引擎中调用相同专家的 token 比例迅速下降约10%。
    > 
    
    在每一层，路由网络决定激活哪些专家。在深层 MoE 模型中，它为每层选择多个专家，因此即使每次调用  \(\texttt{TopK}(\cdot)\) 的小差异也会累积，并随着深度的增长而越来越放大。
    

### 这对 MoE RL 会产生什么影响？

{{< alert "bell" >}}
概率差异被放大，特别是对于长序列。
{{< /alert >}}


在训练的最开始，我们发现在某些 token 位置已经明显存在显著的概率差异。由于预测的自回归特性，出现在后面位置的 token 更容易受到差异累积的影响，导致变异范围更大。

<figure>
  <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/11/tesizl.png" alt="在步骤0时，不同 token 位置的概率差异。">
  <figcaption style="text-align: center;">图2：在步骤0时，不同 token 位置的概率差异。</figcaption>
</figure>


随着训练的进行，问题加剧：训练和推理引擎之间同一 token 的概率差距在各个 token 位置持续增加，甚至影响长序列中的前面 token，并破坏优化过程的稳定性。

<figure>
  <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/11/MhHskf.png" alt="训练后，训练和推理引擎在不同 token 位置计算的对数概率。">
  <figcaption style="text-align: center;">图3：训练后，训练和推理引擎在不同 token 位置计算的对数概率。</figcaption>
</figure>


{{< alert "bell" >}}
不匹配问题很快导致在线策略 MoE RL 训练崩溃。
{{< /alert >}}

在在线策略 RL 训练中，与密集模型相比，我们观察到负责生成长序列的 MoE 模型更容易受到这种不匹配问题的影响，经常导致训练崩溃。

<figure>
  <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/11/ns4Eah.png" alt="崩溃模型的训练信号。">
  <figcaption style="text-align: center;">图4：崩溃模型的训练信号。</figcaption>
</figure>

例如，上图显示差异在步骤150后逐渐增加，一旦差异超过0.05，训练基本上就失败了。由于实现不同，概率差异可能因复合效应而变得更大。

- **引理**（复合概率差异）
    
    设 \(\pi_{\text{infer}}(\cdot;\theta)\) 和 \(\pi_{\text{train}}(\cdot;\theta)\) 为推理和训练策略。将步骤 \(t\) 的概率差异定义为：
    
    $$
    \delta_t \;=\; D_{\mathrm{KL}}\!\big(\pi_{\text{infer}}(\cdot;\theta_t)\,\|\,\pi_{\text{train}}(\cdot;\theta_t)\big).
    $$
    
    它测量推理引擎的分布偏离训练引擎分布的程度。
    
    在使用不匹配引擎的 RL 训练期间，参数更新为：
    
    $$
    \theta_{t+1} \;=\; \theta_t \;+\; \mu\,g_t, \qquad g_t \;=\; \mathbb{E}_{a\sim \pi_{\text{infer}}(\theta_t)}\!\big[R(a)\,\nabla_\theta \log \pi_{\text{train}}(a;\theta_t)\big].
    $$
    
    在线策略更新是 \(g_t^\star = \mathbb{E}_{a\sim \pi{_\text{train}}(\theta_t)}[R(a)\,\nabla_\theta \log \pi_{\text{train}}(a;\theta_t)]\) ，偏差是 \(b_t = g_t - g_t^\star\)。假设以下局部条件对 \(\theta\) 成立。
    
    1. **平滑差异**
        
        \(\delta(\theta)\) 是 \(L\)-平滑的，满足 \(\big|\,\delta(\theta+\Delta)-\delta(\theta)\,\big| \;\le\; L\,\|\Delta\| \;+\; c_0 \|\Delta\|^2\)，其中 \(c_0\) 是曲率常数。
        
        这意味着小的参数更新只会导致差异的小变化。
        
    2. **偏差与差异成正比**
        
        \(\|b_t\| \;\ge\; c_1\,\delta_t, ~~\big\langle \nabla_\theta \delta(\theta_t),\, b_t \big\rangle \;\ge\; c_2\,\delta_t\)， 其中 \(c_1\) 是偏差幅度系数，\(c_2\) 是偏差对齐系数。
        
        不匹配越大，偏差越多地推向恶化方向。
        
    3. **有界在线策略漂移（ drift）**
        
        存在 \(M\ge 0\) 使得 \(\big|\langle \nabla_\theta \delta(\theta_t),\, g_t^\star \rangle\big| \le M\)
        
        仅在线策略训练不会导致失控分歧；不稳定性主要来自偏差。
        

## 用 *IcePop* 释放 MoE RL：丢弃所有噪声梯度更新！

为了解决上述问题，我们提出了一种简单而有效的技术，𝑰𝒄𝒆𝑷𝒐𝒑 🤩。我们应用双侧掩码（double-sided masking）来缓解概率差异的有害复合效应（compounding effects），只保留“健康”的梯度更新。

- **双侧裁剪（Double-sided clipping）**：不仅裁剪*训练概率≫推理概率*的token，还裁剪*训练概率≪推理概率*的token。
- **掩码（Masking）**：*差异过大*的token从梯度更新中移除。

$$
\begin{align*}
\mathcal{J}_{{\text{IcePop}}}(\theta) &= \mathbb{E}_{x \sim \mathcal{D}, \{y_i\}_{i=1}^G \sim \pi_{\textcolor{red}{\text{infer}}}(\cdot \mid x; \theta_{\rm old})} \left[ \frac{1}{G} \sum_{i=1}^G \frac{1}{|y_i|} \sum_{t=1}^{|y_i|} \Big[\mathcal{M}\Bigl(\frac{\pi_{\textcolor{blue}{\text{train}}}(y_{i,t} \mid x, y_{i, \lt t};\theta_{\text{old}})}{\pi_{\textcolor{red}{\text{infer}}}(y_{i,t} \mid x, y_{i, \lt t}; \theta_{\mathrm{old}})}; \alpha, \beta\Bigr) \right. \\
&\left. \qquad \qquad \qquad \qquad \quad \qquad \cdot \min \left( r_{i,t}\widehat{A}_{i,t}, \text{clip} \left( r_{i,t}, 1 - \varepsilon, 1 + \varepsilon \right) \widehat{A}_{i,t} \right) \right]\Bigg]
\end{align*}
$$


其中 \(r_{i,t} = \frac{\pi_{\textcolor{blue}{\text{train}}}(y_{i,t} \mid x, y_{i, \lt t}; \ \theta)}{\pi_{\textcolor{blue}{\text{train}}}(y_{i,t} \mid x, y_{i, \lt t}; \ \theta_{\text{old}})}\)，掩码函数如下：

$$
\begin{equation}
\mathcal{M}(k) =\begin{cases} k & \text{if \ } k \in [\alpha, \beta] \\ 0 & \text{otherwise}\end{cases}
\end{equation}
$$

以及两个超参数 \(\alpha\)、\(\beta\) 来控制下限和上限。

IcePop 的梯度:

$$
\small{\nabla_\theta \mathcal{J}_{\text{IcePop}}(\theta) \sim \small{\begin{equation}\mathbb{E}_{a \sim \textcolor{red}{\pi_{\text{infer}}}(\theta_{\text{old}})} \Bigg[\mathcal{M}\Bigg(\frac{\textcolor{blue}{\pi_{\text{train}}}(a;\theta_{\text{old}})}{\textcolor{red}{\pi_{\text{infer}}}(a;\theta_{\text{old}})}\Bigg ) \cdot \nabla_\theta \log \textcolor{blue}{\pi_{\text{train}}}(a;\theta) \cdot \hat{A} \cdot r(a)\Bigg)\Bigg].\end{equation}}}
$$

我们的工作与 TIS[[1]](https://www.notion.so/Small-Leak-Can-Sink-a-Great-Ship-Boost-RL-Training-on-MoE-with-27688396fe1c8144896ad187a98b06e1?pvs=21) 的区别：

- 当 \(\dfrac{\textcolor{blue}{\pi_{\text{train}}}(a;\theta_{\text{old}})}{\textcolor{red}{\pi_{\text{infer}}}(a;\theta_{\text{old}})} \lt \alpha\) 时，\(\textcolor{blue}{\pi_{\text{train}}}\) 倾向于为动作分配较小的值，相反，\(\textcolor{red}{\pi_{\text{infer}}}\) 输出较高的概率，当比率足够小时，表明训练和推理引擎之间存在巨大分歧。TIS 乘以一个小系数来缓解噪声梯度更新，但是，随着训练的进行，我们发现这种小干扰可以逐渐放大，最终导致基准性能的“平台期”。
- 当 \(\dfrac{\textcolor{blue}{\pi_{\text{train}}}(a;\theta_{\text{old}})}{\textcolor{red}{\pi_{\text{infer}}}(a;\theta_{\text{old}})} > \beta\) 时，TIS 继续通过乘以一个适中的系数来更新策略梯度。对于IcePop，梯度为零，这意味着我们放弃所有噪声更新，只保留那些健康的策略梯度。

- 👂🏼想听听**IcePop**名字背后的故事吗？
    
    😄 我们在享受冰棍时想出了这个名字！
    
    - 就像冰棍能够让过热的东西冷却下来一样，该算法通过在两侧裁剪极端概率比并掩码差异过大的 token 来 **“冷却”** 不稳定的在线策略训练。
    - 这种选择性校正 **“弹出”** 不稳定的贡献，同时保留高效更新，从而在不减慢推理的情况下稳定训练。


## 实验

在本文中，我们在[Ring-mini-2.0](https://huggingface.co/inclusionAI/Ring-mini-2.0)上比较了三种设置，这是由[InclusionAI](https://inclusionai.github.io/)开发的MoE模型。它拥有16.8B总参数和0.75B激活参数：**(1) IcePop，(2) [TIS](https://fengyao.notion.site/off-policy-rl)**，以及 **(3) baseline**——不带KL项的原版GRPO，在重复运行中始终失败和崩溃。我们收集了具有挑战性的推理问题作为训练数据集。使用IcePop，我们发现在线策略训练的不稳定性可以得到有效解决，甚至比TIS取得更好的性能。

{{< alert "fire" >}}
在下游任务上，**IcePop** 优于 **TIS** 和 **baseline**。
{{< /alert >}}

- **模型评估**：在具有挑战性的基准AIME25上，**IcePop** 在整个训练过程中持续优于 **TIS**，表现出很大的提升，最终将基础分数（63%）提高了**14%以上，并将与 TIS** 的性能差距扩大了相对6%。

<figure>
  <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/11/KXry1k.png" alt="AIME25上Avg@64的性能比较。我们使用相同的设置评估所有模型。">
  <figcaption style="text-align: center;">图5：AIME25上Avg@64的性能比较。我们使用相同的设置评估所有模型。</figcaption>
</figure>



## 更多分析

- **概率差异**
    
    不解决不匹配问题，概率差异增长迅速，如基线设置所示。相比之下，TIS 和 IcePop 都将训练-推理概率的 KL 散度保持在合理范围内。尽管随着训练的进行，所有三种方法的最大概率差异都在上升，但 IcePop 的差异保持相对较低，甚至在400步内有所减少。我们还注意到，TIS 始终显示比我们的方法更大的极端差异和更快的增长，这可能是由于在训练期间包含了噪声策略更新。

    <figure>
    <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/11/CKVxoE.png" alt="概率差异的最大值。">
    <figcaption style="text-align: center;">图6：概率差异的最大值。</figcaption>
    </figure>
- **训练稳定性**
    我们相信稳定的训练过程是坚实的基础，为展示强化学习的力量提供了充足的空间。值得注意的是，IcePop 和 TIS 都在600个梯度步骤内缓解了 RL 训练的不稳定性，避免了基线设置中发生的快速训练崩溃。

    <div style="display: flex; gap: 20px; justify-content: center;">
    <figure style="width: 48%; margin: 0;">
        <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/11/I0Kgb0.png" alt="训练奖励对比" style="width: 100%;">
        <figcaption style="text-align: center;">图7：训练奖励。基线的奖励在180-200步后崩溃。IcePop 和 TIS 都保持稳定增长。</figcaption>
    </figure>
    <figure style="width: 48%; margin: 0;">
        <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/11/R6XCYV.png" alt="梯度范数对比" style="width: 100%;">
        <figcaption style="text-align: center;">图8：梯度范数（Gradient norm）。基线爆炸，IcePop 和 TIS 保持稳定。</figcaption>
    </figure>
    </div>

    <!-- <figure>
    <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/11/I0Kgb0.png" alt="训练奖励。基线的奖励在180-200步后崩溃。IcePop 和 TIS 都保持稳定增长。">
    <figcaption style="text-align: center;">图7：训练奖励。基线的奖励在180-200步后崩溃。IcePop 和 TIS 都保持稳定增长。</figcaption>
    <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/11/R6XCYV.png" alt="梯度范数（Gradient norm）。基线爆炸，IcePop 和 TIS 保持稳定。">
    <figcaption style="text-align: center;">图8：梯度范数（Gradient norm）。基线爆炸，IcePop 和 TIS 保持稳定。</figcaption>
    </figure> -->

- **探索空间**
    我们观察到 IcePop 的对数概率始终保持比 TIS 相对较低的值，这隐含地表明我们的方法避免了过度自信的预测，从而确保了更大的探索空间，其中低概率 token 更有可能被选择，最终增加响应的多样性。

    <figure>
    <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/11/U5HZjV.png" alt="token 的对数概率。基线快速增长然后跌至底部，而 IcePop 相对稳定。">
    <figcaption style="text-align: center;">图9：token 的对数概率。基线快速增长然后跌至底部，而 IcePop 相对稳定。</figcaption>
    </figure>

- **病态 Token（Ill-conditioned Tokens）**
    在我们的实验中，我们发现我们的掩码机制的裁剪比例保持在训练 token 的1-2‰左右。随着训练的进行，裁剪比例急剧上升，表明出现了越来越微妙但有害的梯度更新，需要更高的裁剪比例。我们还对裁剪的 token 进行了详细分析。下面的右图显示，与所有 token 相比，裁剪的 token 表现出更高的熵，表明裁剪的 token 在训练中起着重要作用。

    <figure>
    <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/11/gek10Y.png" alt="裁剪比例（Clipping ratio）。在我们的默认设置中，IcePop保持约1-2‰的token被裁剪。">
    <figcaption style="text-align: center;">图10：裁剪比例（Clipping ratio）。在我们的默认设置中，IcePop保持约1-2‰的token被裁剪。</figcaption>
    </figure>

    <figure>
    <img src="https://cdn.jsdelivr.net/gh/gongzitaiyi/picture@master/uPic/2025/11/SNDCAe.png" alt="所有 token 和裁剪 token 之间 token 熵的比较。与所有 token 相比，裁剪 token 显示出更高比例的高熵 token。">
    <figcaption style="text-align: center;">图11：所有 token 和裁剪 token 之间 token 熵的比较。与所有 token 相比，裁剪 token 显示出更高比例的高熵 token。</figcaption>
    </figure>


## 结论和未来工作

- 我们对MoE上的训练-推理概率不匹配问题提供了初步分析。在线策略 RL 训练的不稳定性可能源于训练和推理引擎之间不断增长的概率差异。**IcePop** 通过在损失级别纠正不匹配来解决这个问题。
- 一个重要的方向是正式表征*崩溃边界*，定义为在线策略训练变得不稳定

## Reference

[1] Feng Yao, Liyuan Liu, Dinghuai Zhang, Chengyu Dong, Jingbo Shang and Jianfeng Gao. [Your Efficient RL Framework Secretly Brings You Off-Policy RL Training](https://fengyao.notion.site/off-policy-rl). *Notion Blog*. 2025.
