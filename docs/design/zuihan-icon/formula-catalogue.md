# 瑞般观珠：微雕公式精确清单（正式 22 条）

本清单列出图标中正式采用的 22 条微雕公式，说明其精确写法、适用条件与来源。每条公式在图标中出现 4 次，共 88 处。

其中，1 条为定义性表述，18 条为定理，3 条为猜想：Riemann 猜想、Birch–Swinnerton-Dyer（BSD）猜想的秩断言，以及 $`\mathsf P\ne\mathsf{NP}`$ 猜想。

本清单约定：闭流形指紧致且无边界的流形。第 09、10 项的 Fourier 变换统一采用 $`\widehat f(\xi)=\int_{\mathbb R}f(x)e^{-2\pi i x\xi}\,dx`$；第 11 项的热迹采用非负 Laplace 算子。

## 01. 伴随关系

**领域**：范畴论　**状态**：定义／自然双射表述

```math
\mathop{\mathrm{Hom}}\nolimits_{\mathcal D}(FX,Y)\cong\mathop{\mathrm{Hom}}\nolimits_{\mathcal C}(X,GY)
```

**条件与记号**：$`\mathcal C`$、$`\mathcal D`$ 为局部小范畴，$`F:\mathcal C\to\mathcal D`$、$`G:\mathcal D\to\mathcal C`$ 为函子，$`F`$ 是 $`G`$ 的左伴随。所示双射对 $`X\in\mathcal C`$ 和 $`Y\in\mathcal D`$ 都自然；这一自然双射是伴随数据的一部分。

**来源**：[Emily Riehl, Category Theory in Context](https://emilyriehl.github.io/files/context.pdf)，作者公开版，Definition 4.1.1 与式 (4.1.2)。

## 02. 米田引理

**领域**：范畴论　**状态**：定理

```math
\mathop{\mathrm{Nat}}\nolimits\!\left(\mathop{\mathrm{Hom}}\nolimits_{\mathcal C}(-,X),F\right)\cong F(X)
```

**条件与记号**：$`\mathcal C`$ 为局部小范畴，$`X\in\mathcal C`$，$`F:\mathcal C^{\mathrm{op}}\to\mathrm{Set}`$ 为集合值反变函子。该双射将自然变换 $`\eta`$ 映为 $`\eta_X(\mathrm{id}_X)`$，并且对 $`X`$ 和 $`F`$ 都自然。

**来源**：[Emily Riehl, Category Theory in Context](https://emilyriehl.github.io/files/context.pdf)，Theorem 2.2.4 的对偶形式，亦见 Exercise 2.2.i。

## 03. Riemann 曲面的 Riemann–Roch 公式

**领域**：复几何／代数几何　**状态**：定理

```math
h^0(X,L)-h^1(X,L)=\deg L+1-g
```

**条件与记号**：$`X`$ 为亏格 $`g`$ 的紧致连通 Riemann 曲面，$`L`$ 为 $`X`$ 上的全纯线丛。记 $`h^q(X,L)=\dim_{\mathbb C}H^q(X,\mathcal O(L))`$，其中 $`\mathcal O(L)`$ 是 $`L`$ 的全纯截面层，$`H^q`$ 表示层上同调。

**来源**：[Xianzhe Dai, Lectures on Dirac Operators and Index Theory](https://web.math.ucsb.edu/~dai/book.pdf)，§3.5，印刷页 62（PDF 第 62 页），经典 Riemann–Roch 公式。

## 04. Atiyah–Singer 指标定理（扭曲自旋 Dirac 型）

**领域**：指标理论／微分几何　**状态**：定理

```math
\mathop{\mathrm{ind}}\nolimits D_E^+=\left\langle\widehat A(TM)\mathop{\mathrm{ch}}\nolimits(E),[M]\right\rangle
```

**条件与记号**：$`M`$ 为闭的偶数维光滑 Riemann 自旋流形，定向由自旋结构给出。$`E`$ 为带酉联络的复 Hermitian 向量丛；$`D_E^+:\Gamma(S^+\otimes E)\to\Gamma(S^-\otimes E)`$ 为正手征扭曲自旋 Dirac 算子。

指标为 $`\mathop{\mathrm{ind}}\nolimits D_E^+=\dim\ker D_E^+-\dim\ker D_E^-`$。$`\widehat A(TM)`$ 与 $`\mathop{\mathrm{ch}}\nolimits(E)`$ 为相应的有理特征类；右端取乘积的最高次分量，与基本类 $`[M]`$ 配对。

**来源**：[Xianzhe Dai, Lectures on Dirac Operators and Index Theory](https://web.math.ucsb.edu/~dai/book.pdf)，Theorem 3.3.4；此处将其 Chern–Weil 积分写成有理特征类配对。

## 05. Gauss–Bonnet 公式

**领域**：曲面几何／拓扑　**状态**：定理

```math
\int_M K\,dA=2\pi\chi(M)
```

**条件与记号**：$`M`$ 为闭的定向光滑二维 Riemann 流形。$`K`$ 为 Gauss 曲率，$`dA`$ 为 Riemann 面积元，$`\chi(M)`$ 为 Euler 示性数。

**来源**：[Oliver Knill, Math 136, Lecture 17: Global Gauss-Bonnet（Harvard，2025）](https://people.math.harvard.edu/~knill/teaching/math136_2025/handouts/lecture17.pdf)，亦为 Dai §3.5 的 Gauss–Bonnet–Chern 公式在二维的情形。

## 06. Poincaré 对偶

**领域**：代数拓扑　**状态**：定理

```math
H^k(M;\mathbb R)\cong H_{n-k}(M;\mathbb R)
```

**条件与记号**：$`M`$ 为闭的定向 $`n`$ 维流形，$`0\leq k\leq n`$。两端分别为实系数奇异上同调与奇异同调；同构由与所选定向的基本类 $`[M]`$ 作帽积给出。

**来源**：[Allen Hatcher, Algebraic Topology](https://pi.math.cornell.edu/~hatcher/AT/AT.pdf)，Theorem 3.30，印刷页 239；取系数环 $`R=\mathbb R`$。

## 07. Hodge 分解

**领域**：几何分析　**状态**：定理

```math
\Omega^k(M)=\mathcal H^k(M)\oplus d\Omega^{k-1}(M)\oplus d^*\Omega^{k+1}(M)
```

**条件与记号**：$`M`$ 为闭的定向光滑 $`n`$ 维 Riemann 流形，$`\Omega^k(M)`$ 为光滑实微分 $`k`$-形式的空间，$`0\leq k\leq n`$。$`d^*`$ 是 $`d`$ 关于 $`L^2`$ 内积的形式伴随，$`\Delta=dd^*+d^*d`$，$`\mathcal H^k(M)=\ker(\Delta|_{\Omega^k(M)})`$。

所示分解为 $`L^2`$ 正交直和。当 $`k=0`$ 或 $`k=n`$ 时，次数超出 $`0,\ldots,n`$ 的形式空间按零空间处理。

**来源**：[Denis Auroux, MIT 18.966, Lecture 15](https://ocw.mit.edu/courses/18-966-geometry-of-manifolds-spring-2007/d6848bb391c032ef27993e984fef4558_lect15.pdf)，Theorem 2（Hodge decomposition）；此处用 $`d^*`$ 记余微分。

## 08. Stokes 公式

**领域**：微分拓扑／分析　**状态**：定理

```math
\int_M d\omega=\int_{\partial M}\omega
```

**条件与记号**：$`M`$ 为紧致定向光滑 $`n`$ 维带边界流形，$`n\geq1`$，$`\omega`$ 为光滑 $`(n-1)`$-形式。边界采用外法向优先的诱导定向；右端的 $`\omega`$ 表示沿边界包含映射的拉回。

**来源**：[Victor Guillemin and Peter J. Haine, Differential Forms](https://math.mit.edu/classes/18.952/2018SP/files/18.952_book.pdf)，§4.6（Stokes’ theorem），印刷页 128–130。

## 09. Plancherel 恒等式

**领域**：调和分析　**状态**：定理

```math
\int_{\mathbb R}|f(x)|^2\,dx=\int_{\mathbb R}|\widehat f(\xi)|^2\,d\xi
```

**条件与记号**：$`f\in L^2(\mathbb R)`$。Fourier 变换采用本清单开头约定的归一化：先在 $`L^1(\mathbb R)\cap L^2(\mathbb R)`$ 上按积分定义，再连续延拓至 $`L^2(\mathbb R)`$。

**来源**：[Richard Melrose, Functional Analysis（MIT 18.102）](https://ocw.mit.edu/courses/18-102-introduction-to-functional-analysis-spring-2021/3d4cc88026d44a01f936cd6a0aa995cb_MIT18_102s20_lec_FA.pdf)，Chapter 4 §9，印刷页 143–144；此处将其 $`e^{-ix\xi}`$ 归一化换为 $`2\pi`$ 归一化，使两端无额外常数因子。

## 10. Poisson 求和公式

**领域**：调和分析／数论　**状态**：定理

```math
\sum_{n\in\mathbb Z}f(n)=\sum_{m\in\mathbb Z}\widehat f(m)
```

**条件与记号**：$`f`$ 为 $`\mathbb R`$ 上的 Schwartz 函数，Fourier 变换的归一化与第 09 项一致。两端级数均绝对收敛。

**来源**：[Richard Melrose, Functional Analysis](https://ocw.mit.edu/courses/18-102-introduction-to-functional-analysis-spring-2021/3d4cc88026d44a01f936cd6a0aa995cb_MIT18_102s20_lec_FA.pdf)，Chapter 4 §13，Proposition 4.10；将其 $`2\pi`$ 周期化公式换为周期 $`1`$，并在 $`x=0`$ 处取值。

## 11. 热迹的短时主项

**领域**：谱几何／偏微分方程　**状态**：定理

```math
\mathop{\mathrm{Tr}}\nolimits(e^{-t\Delta})\sim\frac{\mathop{\mathrm{Vol}}\nolimits(M)}{(4\pi t)^{n/2}}
```

**条件与记号**：$`M`$ 为闭的光滑 $`n`$ 维 Riemann 流形，$`n\geq1`$；$`\Delta=d^*d`$ 为标量函数上的非负 Laplace–Beltrami 算子。当 $`t\downarrow0`$ 时，符号 $`\sim`$ 表示两端之比趋于 $`1`$。迹等于 $`\sum_j e^{-t\lambda_j}`$，其中 $`\lambda_j`$ 为 $`\Delta`$ 的特征值，按重数计。

**来源**：[Xianzhe Dai, Lectures on Dirac Operators and Index Theory](https://web.math.ucsb.edu/~dai/book.pdf)，Theorem 3.6.2 的局部热核展开；标量 Laplace 算子的情形有 $`a_0(x)=1`$，沿对角线积分即得此主项。

## 12. Riemann zeta 函数的 Euler 乘积

**领域**：解析数论　**状态**：定理

```math
\zeta(s)=\prod_{p\ {\rm prime}}(1-p^{-s})^{-1}
```

**条件与记号**：$`s\in\mathbb C`$ 且 $`\Re s>1`$，$`\zeta(s)=\sum_{n\geq1}n^{-s}`$。$`p`$ 遍历正素数；级数与 Euler 乘积在此半平面内均绝对收敛。

**来源**：[Noam D. Elkies, Math 229: Elementary methods II: The Euler product](https://people.math.harvard.edu/~elkies/M229.26/euler.pdf)，开头公式及复参数的绝对收敛讨论。

## 13. 二次互反律

**领域**：初等数论／代数数论　**状态**：定理

```math
\left(\frac pq\right)\left(\frac qp\right)=(-1)^{(p-1)(q-1)/4}
```

**条件与记号**：$`p`$、$`q`$ 为互不相同的奇素数，圆括号内的分式表示 Legendre 符号。

**来源**：[Ben Lynn, Number Theory: Quadratic Reciprocity](https://crypto.stanford.edu/pbc/notes/numbertheory/quadrecip.html)，Law of Quadratic Reciprocity；作者在 Stanford 托管的笔记。

## 14. 素数定理

**领域**：解析数论　**状态**：定理

```math
\pi(x)\sim\frac{x}{\log x}
```

**条件与记号**：$`x\to+\infty`$，$`\pi(x)`$ 为不超过 $`x`$ 的正素数个数，$`\log`$ 表示自然对数。符号 $`\sim`$ 表示两端之比趋于 $`1`$。

**来源**：[NIST Digital Library of Mathematical Functions](https://dlmf.nist.gov/27.12)，§27.12，式 (27.12.4) 的首项；$`\pi(x)`$ 的定义见该节开头。

## 15. 独立同分布中心极限定理

**领域**：概率论　**状态**：定理

```math
\frac{\sum_{i=1}^{n}X_i-n\mu}{\sigma\sqrt n}\xrightarrow{\ d\ }\mathcal N(0,1)
```

**条件与记号**：$`X_1,X_2,\ldots`$ 为独立同分布的实随机变量，$`\mathbb E[X_1]=\mu`$，$`\mathop{\mathrm{Var}}\nolimits(X_1)=\sigma^2\in(0,\infty)`$。当 $`n\to\infty`$ 时，箭头表示依分布收敛。

**来源**：[Jeremy Orloff and Jonathan Bloom, MIT 18.05, Class 6: Central Limit Theorem and the Law of Large Numbers](https://ocw.mit.edu/courses/18-05-introduction-to-probability-and-statistics-spring-2022/mit18_05_s22_class06-prep-b.pdf)，此处采用标准化后的等价写法。

## 16. 伊藤公式（Brown 运动型）

**领域**：随机分析　**状态**：定理

```math
df(t,B_t)=\left(f_t+\tfrac12 f_{xx}\right)dt+f_x\,dB_t
```

**条件与记号**：$`B_t`$ 为一维标准 Brown 运动，二次变差为 $`[B]_t=t`$，$`f\in C^{1,2}(\mathbb R\times\mathbb R)`$。右端偏导数均在 $`(t,B_t)`$ 处取值；$`dB_t`$ 按伊藤积分理解，公式表示相应的局部随机积分恒等式。

**来源**：[David Gamarnik, MIT 15.070J, Lecture 17: Ito process and formula](https://www.ocw.mit.edu/courses/15-070j-advanced-stochastic-processes-fall-2013/d9d7372cbf65d56aa8aa9d59ba0ab2e8_MIT15_070JF13_Lec17.pdf)，伊藤过程公式在 $`X=B`$、漂移为 $`0`$、扩散系数为 $`1`$ 时的特例。

## 17. 矩阵树定理

**领域**：组合数学／图论　**状态**：定理

```math
\tau(G)=\det L^{(v)}
```

**条件与记号**：$`G`$ 为至少有两个顶点的有限连通无向简单图，$`\tau(G)`$ 为其生成树数目。$`L=\mathop{\mathrm{diag}}\nolimits(\deg v)-A`$ 为无权图的 Laplace 矩阵，其中 $`A`$ 为邻接矩阵。删除 $`L`$ 中顶点 $`v`$ 对应的行和列，所得矩阵记为 $`L^{(v)}`$；$`v`$ 可任取。

**来源**：[Richard P. Stanley, Topics in Algebraic Combinatorics](https://math.mit.edu/~rstan/algcomb/algcomb.pdf)，Chapter 9，Theorem 9.8；将其生成树记号 $`\kappa(G)`$ 改记为 $`\tau(G)`$。

## 18. 不可约特征标的正交关系

**领域**：有限群表示论　**状态**：定理

```math
\frac1{|G|}\sum_{g\in G}\chi_i(g)\overline{\chi_j(g)}=\delta_{ij}
```

**条件与记号**：$`G`$ 为有限群，$`\chi_i`$、$`\chi_j`$ 来自一组两两不同构的有限维不可约复表示。$`\delta_{ij}`$ 为 Kronecker 符号；横线表示复共轭，归一化系数为 $`1/|G|`$。

**来源**：[Pavel Etingof et al., Introduction to Representation Theory](https://math.mit.edu/~etingof/reprbook.pdf)，§4.5，Theorem 4.5.1；此处取基域 $`\mathbb C`$。

## 19. 留数定理

**领域**：复分析　**状态**：定理

```math
\oint_{\partial D}f(z)\,dz=2\pi i\sum_{a\in D}\mathop{\mathrm{Res}}\nolimits_{z=a}f(z)
```

**条件与记号**：$`D\subset\mathbb C`$ 为有界 Jordan 域，边界分段 $`C^1`$，取正向（逆时针）。$`f`$ 在闭包 $`\overline D`$ 的某邻域内亚纯，且边界上无极点。求和只需遍历 $`D`$ 中有限多个极点，其余点的留数为零。

**来源**：[Jeremy Orloff, MIT 18.04, Topic 8: Residue Theorem](https://ocw.mit.edu/courses/18-04-complex-variables-with-applications-spring-2018/3c58ce71ec6f7573804221d76158a0bd_MIT18_04S18_topic8.pdf)，§8.5 Cauchy’s residue theorem；此处取简单闭曲线的情形。

## 20. Riemann 猜想

**领域**：解析数论　**状态**：猜想（一般尚未解决）

```math
\zeta(\rho)=0,\quad0<\Re\rho<1\quad\Longrightarrow\quad\Re\rho=\tfrac12
```

**条件与记号**：$`\zeta`$ 为 Riemann zeta 函数在 $`\mathbb C`$ 上的亚纯延拓。$`\rho\in\mathbb C`$；公式的前提要求 $`\rho`$ 为开临界带 $`0<\Re\rho<1`$ 内的零点。

**来源**：[Enrico Bombieri, Problems of the Millennium: The Riemann Hypothesis](https://www.claymath.org/wp-content/uploads/2022/05/riemann.pdf)，Clay 官方问题说明。原清单于 2026-10-22 核查时，Clay 问题页标为 Unsolved。

## 21. Birch–Swinnerton-Dyer 猜想（秩断言）

**领域**：算术几何　**状态**：猜想（一般尚未解决）

```math
\mathop{\mathrm{ord}}\nolimits_{s=1}L(E,s)=\mathop{\mathrm{rank}}\nolimits E(\mathbb Q)
```

**条件与记号**：$`E/\mathbb Q`$ 为椭圆曲线，$`L(E,s)`$ 为包含所有有限素数处局部因子的 Hasse–Weil $`L`$-函数，采用中心点为 $`s=1`$ 的算术归一化。$`\mathop{\mathrm{ord}}\nolimits_{s=1}`$ 表示在 $`s=1`$ 处的零点阶数；右端为有限生成群 $`E(\mathbb Q)`$ 的自由秩。

本条只列出 BSD 猜想的秩断言；完整猜想还包括首项系数等断言。

**来源**：[Andrew Wiles, The Birch and Swinnerton-Dyer Conjecture](https://www.claymath.org/wp-content/uploads/2022/05/birchswin.pdf)，印刷页 2 的猜想及 Remark 1；此处使用标准 Hasse–Weil $`L`$-函数，补入的有限多个局部因子在 $`s=1`$ 处正则且非零。原清单于 2026-10-22 核查时，Clay 问题页标为 Unsolved。

## 22. P≠NP 猜想

**领域**：理论计算机科学／计算复杂性　**状态**：猜想（一般尚未解决）

```math
\mathsf P\ne\mathsf{NP}
```

**条件与记号**：$`\mathsf P`$、$`\mathsf{NP}`$ 是有限字母表上判定问题（语言）的复杂性类，采用标准 Turing 机模型和最坏情形时间。$`\mathsf P`$ 中的问题可由确定性 Turing 机在多项式时间内判定；$`\mathsf{NP}`$ 中的问题可由非确定性 Turing 机在多项式时间内判定，等价地，肯定实例具有多项式长度、可在多项式时间内验证的证书。

**来源**：[Stephen Cook, The P Versus NP Problem](https://www.claymath.org/wp-content/uploads/2022/06/pvsnp.pdf)，§1 的类定义与 §3 的 $`\mathsf P\ne\mathsf{NP}`$ 猜想。原清单于 2026-10-22 核查时，Clay 问题页标为 Unsolved。
