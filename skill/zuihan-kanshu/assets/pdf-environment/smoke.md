---
title: 中文数学环境样稿
date: ""
---

# 正交投影

设 $V$ 是有限维实内积空间，$W$ 是其子空间，$P:V\to W$ 是正交投影。对每个 $v\in V$，向量 $Pv$ 与 $v-Pv$ 正交。因此
\begin{equation}
  \|v\|^2=\|Pv\|^2+\|v-Pv\|^2. \label{eq:projection}
\end{equation}
由式 \eqref{eq:projection} 可知 $\|Pv\|\leq\|v\|$，等号成立当且仅当 $v\in W$。

**粗体中文用于检查字体嵌入。** 本样稿还检查正文中的中文文字提取、目录书签与公式交叉引用。取 $V=\mathbb{R}^2$，沿第一坐标轴投影时，标准基下的矩阵为
$$
P=\begin{pmatrix}1&0\\0&0\end{pmatrix},\qquad
\|P(x,y)\|^2=x^2\leq x^2+y^2.
$$

\textsf{无衬线中文用于辅助说明，\textbf{黑体粗字也应清晰。}} 行内代码 `等宽中文：投影 P(x,y) = (x,0)` 用于检查中文代码字体。

```text
等宽中文：输入向量 (x, y)，输出 (x, 0)。
```

# 数学字形

对 $a,b>0$，Cauchy–Schwarz 不等式给出
$$
\left(\int_0^1 (a+bt)\,dt\right)^2
\leq \int_0^1 (a+bt)^2\,dt
=a^2+ab+\frac{b^2}{3}.
$$
记号 $\mathbb{A},\mathbb{B},\mathbb{C},\mathbb{N},\mathbb{Q},\mathbb{R},\mathbb{Z}$ 用于检查 AMS 空心大写字形；根式 $\sqrt{1+x^2}$、上下标 $a_{i_j}^{n+1}$、求和 $\sum_{k=1}^{n}k$ 与乘积 $\prod_{k=1}^{n}k$ 用于人工检查数学排版。

| 对象 | 性质 |
|:---|:---|
| 正交投影 $P$ | $P^2=P$ |
| 恒等算子 $I$ | $\|Iv\|=\|v\|$ |

: 投影与恒等算子的基本性质。

这份样稿只验证环境与排版链，不代替实际文稿的编译和视觉检查。
