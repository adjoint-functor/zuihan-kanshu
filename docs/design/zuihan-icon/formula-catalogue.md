# 瑞般观珠：微雕公式精确清单（正式 22 条）

本清单保存已批准图标中 22 条正式微雕公式的精确写法、适用条件及来源；每条出现 4 次，共 88 个实例，供项目主页查阅。

共 1 条定义性表述、18 条定理、3 条猜想。黎曼猜想、BSD 秩断言及 P≠NP 均明确保留猜想状态；BSD 仅列秩断言。闭流形指紧致且无边界。

傅里叶变换两项统一采用 $\widehat f(\xi)=\int_{\mathbb R}f(x)e^{-2\pi i x\xi}\,dx$；热迹项采用非负拉普拉斯算子。

## 01. 随伴关系

**领域：**范畴论　**状态：**定义／自然双射表述

$$
\operatorname{Hom}_{\mathcal D}(FX,Y)\cong\operatorname{Hom}_{\mathcal C}(X,GY)
$$

**条件与记号：**C、D 为局部小范畴，F:C→D、G:D→C；F 是 G 的左随伴。 所示为对 X∈C、Y∈D 都自然的集合间双射；随伴数据包括这一自然双射。

**来源：**[Emily Riehl, Category Theory in Context，作者公开版，Definition 4.1.1 与式 (4.1.2)。](https://emilyriehl.github.io/files/context.pdf)

## 02. 米田引理

**领域：**范畴论　**状态：**定理

$$
\operatorname{Nat}\!\left(\operatorname{Hom}_{\mathcal C}(-,X),F\right)\cong F(X)
$$

**条件与记号：**C 为局部小范畴，X∈C，F:Cᵒᵖ→Set 为集合值反变函子。 双射将自然变换 η 送到 η_X(id_X)，且对 X、F 自然。

**来源：**[Emily Riehl, Category Theory in Context，Theorem 2.2.4 的对偶形式；该形式亦见 Exercise 2.2.i。](https://emilyriehl.github.io/files/context.pdf)

## 03. 黎曼曲面的黎曼–罗赫公式

**领域：**复几何／代数几何　**状态：**定理

$$
h^0(X,L)-h^1(X,L)=\deg L+1-g
$$

**条件与记号：**X 为紧致连通黎曼曲面，g 为其亏格，L 为 X 上的全纯线丛。 h^q(X,L)=dim_C H^q(X,O(L))；这里的 H^q 是全纯截面层的上同调。

**来源：**[Xianzhe Dai, Lectures on Dirac Operators and Index Theory，§3.5、印刷页 62（PDF 第 62 页），经典黎曼–罗赫公式。](https://web.math.ucsb.edu/~dai/book.pdf)

## 04. 阿蒂亚–辛格指标定理（扭曲自旋狄拉克型）

**领域：**指标理论／微分几何　**状态：**定理

$$
\operatorname{ind}D_E^+=\left\langle\widehat A(TM)\operatorname{ch}(E),[M]\right\rangle
$$

**条件与记号：**M 为闭的偶数维光滑黎曼自旋流形，带自旋结构给出的定向；闭指紧致且无边界。 E 为复厄米向量丛，带酉联络；D_E^+:Γ(S⁺⊗E)→Γ(S⁻⊗E) 为正手征扭曲自旋狄拉克算子。 ind 为 dim ker D_E⁺−dim ker D_E⁻；Â、ch 为标准有理特征类，右侧只取最高次数后与基本类配对。

**来源：**[Xianzhe Dai, Lectures on Dirac Operators and Index Theory，Theorem 3.3.4；以有理特征类配对表述其 Chern–Weil 积分。](https://web.math.ucsb.edu/~dai/book.pdf)

## 05. 高斯–博内公式

**领域：**曲面几何／拓扑　**状态：**定理

$$
\int_M K\,dA=2\pi\chi(M)
$$

**条件与记号：**M 为闭的定向光滑黎曼二维流形。 K 为高斯曲率，dA 为黎曼面积元，χ(M) 为欧拉示性数。

**来源：**[Oliver Knill, Math 136, Lecture 17: Global Gauss-Bonnet（Harvard，2025）；亦为 Dai §3.5 的 Gauss–Bonnet–Chern 公式在二维的情形。](https://people.math.harvard.edu/~knill/teaching/math136_2025/handouts/lecture17.pdf)

## 06. 庞加莱对偶

**领域：**代数拓扑　**状态：**定理

$$
H^k(M;\mathbb R)\cong H_{n-k}(M;\mathbb R)
$$

**条件与记号：**M 为闭的定向 n 维流形，0≤k≤n；上下同调均为奇异理论、实系数。 同构由选定定向的基本类 [M] 作帽积给出。

**来源：**[Allen Hatcher, Algebraic Topology，Theorem 3.30，印刷页 239；取系数环 R=ℝ。](https://pi.math.cornell.edu/~hatcher/AT/AT.pdf)

## 07. 霍奇分解

**领域：**几何分析　**状态：**定理

$$
\Omega^k(M)=\mathcal H^k(M)\oplus d\Omega^{k-1}(M)\oplus d^*\Omega^{k+1}(M)
$$

**条件与记号：**M 为闭的定向光滑黎曼 n 维流形，Ω^k(M) 为光滑实微分 k 形式，0≤k≤n。 d* 为 d 关于 L² 内积的形式伴随，Δ=dd*+d*d，ℋ^k(M)=ker Δ；各项为 L² 正交直和。 当 k=0 或 n 时，越出 0,…,n 的形式空间按零空间处理。

**来源：**[Denis Auroux, MIT 18.966, Lecture 15，Theorem 2（Hodge decomposition）；用 d* 记余微分。](https://ocw.mit.edu/courses/18-966-geometry-of-manifolds-spring-2007/d6848bb391c032ef27993e984fef4558_lect15.pdf)

## 08. 斯托克斯公式

**领域：**微分拓扑／分析　**状态：**定理

$$
\int_M d\omega=\int_{\partial M}\omega
$$

**条件与记号：**M 为紧致定向光滑 n 维带边界流形，n≥1，ω 为光滑 (n−1) 形式。 边界采用外法向优先的诱导定向；右侧的 ω 表示沿边界包含映射的拉回。

**来源：**[Victor Guillemin and Peter J. Haine, Differential Forms，§4.6（Stokes’ theorem），印刷页 128–130。](https://math.mit.edu/classes/18.952/2018SP/files/18.952_book.pdf)

## 09. 普朗歇雷恒等式

**领域：**调和分析　**状态：**定理

$$
\int_{\mathbb R}|f(x)|^2\,dx=\int_{\mathbb R}|\widehat f(\xi)|^2\,d\xi
$$

**条件与记号：**f∈L²(ℝ)，使用傅里叶规范化 f̂(ξ)=∫ℝ f(x)e^(−2πixξ)dx。 傅里叶变换先在 L¹∩L² 上按该积分定义，再连续延拓至 L²。

**来源：**[Richard Melrose, Functional Analysis（MIT 18.102），Chapter 4 §9，印刷页 143–144；此处由其 e^(−ixξ) 规范化换元为 2π 规范化，使两端无常数。](https://ocw.mit.edu/courses/18-102-introduction-to-functional-analysis-spring-2021/3d4cc88026d44a01f936cd6a0aa995cb_MIT18_102s20_lec_FA.pdf)

## 10. 泊松求和公式

**领域：**调和分析／数论　**状态：**定理

$$
\sum_{n\in\mathbb Z}f(n)=\sum_{m\in\mathbb Z}\widehat f(m)
$$

**条件与记号：**f 为 ℝ 上的 Schwartz 函数。 傅里叶规范化与普朗歇雷项一致：f̂(ξ)=∫ℝ f(x)e^(−2πixξ)dx；两级数均绝对收敛。

**来源：**[Richard Melrose, Functional Analysis，Chapter 4 §13，Proposition 4.10；将其 2π 周期化公式换为周期 1，并在 x=0 处取值。](https://ocw.mit.edu/courses/18-102-introduction-to-functional-analysis-spring-2021/3d4cc88026d44a01f936cd6a0aa995cb_MIT18_102s20_lec_FA.pdf)

## 11. 热迹的短时主项

**领域：**谱几何／偏微分方程　**状态：**定理

$$
\operatorname{Tr}(e^{-t\Delta})\sim\frac{\operatorname{Vol}(M)}{(4\pi t)^{n/2}}
$$

**条件与记号：**M 为闭的光滑 n 维黎曼流形，n≥1；Δ=d*d 为标量函数上的非负拉普拉斯–贝尔特拉米算子。 t↓0；符号 ∼ 表示两边之比趋于 1。迹等于按重数计的 Σ_j e^(−tλ_j)，其中 λ_j 为 Δ 的特征值。

**来源：**[Xianzhe Dai, Lectures on Dirac Operators and Index Theory，Theorem 3.6.2 的局部热核展开；标量拉普拉斯情形 a₀(x)=1，沿对角线积分得到此主项。](https://web.math.ucsb.edu/~dai/book.pdf)

## 12. 黎曼泽塔函数的欧拉乘积

**领域：**解析数论　**状态：**定理

$$
\zeta(s)=\prod_{p\ {\rm prime}}(1-p^{-s})^{-1}
$$

**条件与记号：**s∈ℂ 且 Re(s)>1；ζ(s)=Σ_{n≥1}n^(−s)。 p 遍历正素数；级数与欧拉乘积在该半平面绝对收敛。

**来源：**[Noam D. Elkies, Math 229: Elementary methods II: The Euler product，开头公式及复参数绝对收敛讨论。](https://people.math.harvard.edu/~elkies/M229.26/euler.pdf)

## 13. 二次互反律

**领域：**初等数论／代数数论　**状态：**定理

$$
\left(\frac pq\right)\left(\frac qp\right)=(-1)^{(p-1)(q-1)/4}
$$

**条件与记号：**p、q 为互不相同的奇素数。 括号表示勒让德符号。

**来源：**[Ben Lynn, Number Theory: Quadratic Reciprocity，Law of Quadratic Reciprocity；作者在 Stanford 托管的笔记。](https://crypto.stanford.edu/pbc/notes/numbertheory/quadrecip.html)

## 14. 素数定理

**领域：**解析数论　**状态：**定理

$$
\pi(x)\sim\frac{x}{\log x}
$$

**条件与记号：**x→+∞，π(x)=#{p 为正素数:p≤x}；log 为自然对数。 符号 ∼ 表示比值趋于 1。

**来源：**[NIST Digital Library of Mathematical Functions，§27.12，式 (27.12.4) 的首项；π(x) 的定义见该节开头。](https://dlmf.nist.gov/27.12)

## 15. 独立同分布中心极限定理

**领域：**概率论　**状态：**定理

$$
\frac{\sum_{i=1}^{n}X_i-n\mu}{\sigma\sqrt n}\xrightarrow{\ d\ }\mathcal N(0,1)
$$

**条件与记号：**X₁,X₂,… 为独立同分布的实随机变量，E[X₁]=μ，Var(X₁)=σ²∈(0,∞)。 n→∞，箭头表示依分布收敛。

**来源：**[Jeremy Orloff and Jonathan Bloom, MIT 18.05, Class 6: Central Limit Theorem and the Law of Large Numbers；采用标准化后的等价写法。](https://ocw.mit.edu/courses/18-05-introduction-to-probability-and-statistics-spring-2022/mit18_05_s22_class06-prep-b.pdf)

## 16. 伊藤公式（布朗运动型）

**领域：**随机分析　**状态：**定理

$$
df(t,B_t)=\left(f_t+\tfrac12 f_{xx}\right)dt+f_x\,dB_t
$$

**条件与记号：**B_t 为一维标准布朗运动，二次变差 [B]_t=t；f∈C^{1,2}(ℝ×ℝ)。 右端偏导数均在 (t,B_t) 处取值；dB 按伊藤意义，公式表示相应的局部随机积分恒等式。

**来源：**[David Gamarnik, MIT 15.070J, Lecture 17: Ito process and formula，伊藤过程公式在 X=B、漂移 0、扩散系数 1 时的特例。](https://www.ocw.mit.edu/courses/15-070j-advanced-stochastic-processes-fall-2013/d9d7372cbf65d56aa8aa9d59ba0ab2e8_MIT15_070JF13_Lec17.pdf)

## 17. 矩阵树定理

**领域：**组合数学／图论　**状态：**定理

$$
\tau(G)=\det L^{(v)}
$$

**条件与记号：**G 为有至少两个顶点的有限连通无向简单图，τ(G) 为其生成树数目。 L=diag(deg v)−A 为无权图拉普拉斯矩阵；L^(v) 由 L 删除同一顶点 v 对应的行和列，v 可任取。

**来源：**[Richard P. Stanley, Topics in Algebraic Combinatorics，Chapter 9，Theorem 9.8；将其生成树记号 κ(G) 改记 τ(G)。](https://math.mit.edu/~rstan/algcomb/algcomb.pdf)

## 18. 不可约特征标的正交关系

**领域：**有限群表示论　**状态：**定理

$$
\frac1{|G|}\sum_{g\in G}\chi_i(g)\overline{\chi_j(g)}=\delta_{ij}
$$

**条件与记号：**G 为有限群；χ_i、χ_j 来自一组两两不同构的有限维不可约复表示。 δ_ij 为克罗内克符号；横线为复共轭，归一化系数为 1/|G|。

**来源：**[Pavel Etingof et al., Introduction to Representation Theory，§4.5，Theorem 4.5.1；此处取基域 ℂ。](https://math.mit.edu/~etingof/reprbook.pdf)

## 19. 留数定理

**领域：**复分析　**状态：**定理

$$
\oint_{\partial D}f(z)\,dz=2\pi i\sum_{a\in D}\operatorname{Res}_{z=a}f(z)
$$

**条件与记号：**D⊂ℂ 为有界 Jordan 域，边界分段 C¹ 并取正向（逆时针）。 f 在闭包 D̄ 的某邻域内亚纯，边界上无极点；求和只遍历 D 中有限多个极点，其余点留数为零。

**来源：**[Jeremy Orloff, MIT 18.04, Topic 8: Residue Theorem，§8.5 Cauchy’s residue theorem；取简单闭曲线情形。](https://ocw.mit.edu/courses/18-04-complex-variables-with-applications-spring-2018/3c58ce71ec6f7573804221d76158a0bd_MIT18_04S18_topic8.pdf)

## 20. 黎曼猜想

**领域：**解析数论　**状态：**猜想（一般尚未解决）

$$
\zeta(\rho)=0,\quad0<\Re\rho<1\quad\Longrightarrow\quad\Re\rho=\tfrac12
$$

**条件与记号：**ζ 为黎曼泽塔函数在 ℂ 上的亚纯延拓；ρ∈ℂ，前提将零点限制在开临界带。 ρ 位于开临界带；此项为一般尚未解决的猜想。

**来源：**[Enrico Bombieri, Problems of the Millennium: The Riemann Hypothesis，Clay 官方问题说明；Clay 当前问题页标为 Unsolved（核查日期 2026-10-22）。](https://www.claymath.org/wp-content/uploads/2022/05/riemann.pdf)

## 21. 伯奇–斯温纳顿-戴尔猜想（秩断言）

**领域：**算术几何　**状态：**猜想（一般尚未解决）

$$
\operatorname{ord}_{s=1}L(E,s)=\operatorname{rank}E(\mathbb Q)
$$

**条件与记号：**E/ℚ 为椭圆曲线，L(E,s) 为含各有限素数处局部因子的 Hasse–Weil L 函数，采用中心点 s=1 的算术规范化。 ord 为在 s=1 的零点阶数；右侧为有限生成群 E(ℚ) 的自由秩。 本条仅表示 BSD 的秩断言，一般情形尚未解决；完整 BSD 还包括首项系数等断言。

**来源：**[Andrew Wiles, The Birch and Swinnerton-Dyer Conjecture，印刷页 2 的猜想及 Remark 1；此处写标准 Hasse–Weil L 函数，其有限多个补入因子在 s=1 正则且非零。Clay 当前问题页标为 Unsolved（2026-10-22）。](https://www.claymath.org/wp-content/uploads/2022/05/birchswin.pdf)

## 22. P≠NP 猜想

**领域：**理论计算机科学／计算复杂性　**状态：**猜想（一般尚未解决）

$$
\mathsf P\ne\mathsf{NP}
$$

**条件与记号：**P、NP 是有限字母表上判定问题（语言）的复杂性类，采用标准图灵机模型和最坏情形时间。 P 可由确定性图灵机在多项式时间判定；NP 可由非确定性图灵机在多项式时间判定，等价地具有多项式长度、可在多项式时间验证的证书。 P≠NP 为尚未解决的猜想。

**来源：**[Stephen Cook, The P Versus NP Problem，§1 的类定义与 §3 的 P≠NP 猜想。Clay 当前问题页标为 Unsolved（2026-10-22）。](https://www.claymath.org/wp-content/uploads/2022/06/pvsnp.pdf)
