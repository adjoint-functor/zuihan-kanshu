# 英文数学术语中文规范表

## 目录

- [使用协议](#使用协议)
- [关键义项路由](#关键义项路由)
- [一般代数、代数几何与群论](#一般代数代数几何与群论)
- [域、局部—整体与测度](#域局部整体与测度)
- [线性代数、形式与经典群](#线性代数形式与经典群)
- [表示论、Langlands 与 theta 对应](#表示论langlands-与-theta-对应)
- [自守形式、解析与一般数学写作](#自守形式解析与一般数学写作)
- [专业扩展条目](#专业扩展条目)
- [默认保留的来源词形](#默认保留的来源词形)

## 使用协议

本表是已经完成义项限定的技能默认表，不是逐词替换词典，也不宣称每个译名都是国家统一审定名词。

仅在英文源词、数学义项、对象类型和语法功能同时命中表项时采用默认形式。译名优先级依次为：用户明确的译法指示、用户已明确采用且同一义项适用的项目译名、本次适用的源文双语约定、本表默认；源文双语约定按 `chinese-translation.md` 所述翻译目的处理。数学对象及源文定义决定义项，译名优先级不改变数学内容，普通英文讨论也不构成双语约定。

明确采用按语义判断，无需固定口令；随口讨论、临时简称、提问用词、模型重复用法和助手自写术语表不自动成为项目约定，也不能覆盖本表的精确义项。无需逐词追索无冲突旧用法的批准凭据，也不批量改写历史材料。精确命中时无需为该词再次专门联网；出现新词、义项变化、对象不明、项目冲突或表内未覆盖的多义性时，返回 `chinese-translation.md` 的查证流程。

逐字保留的原文引文、参考文献字段、引用键、DOI、URL 和文件名不应用本表。每份译文只把实际采用且对读者有帮助的条目写入自己的术语表，不复制整张技能表。

## 关键义项路由

- `character` 先区分群的一维表示、代数群同态、代数或 Lie 代数的特征标及表示的迹函数；都可使用“特征标”，但定义和语法角色不得混同。域或环的 `characteristic` 是“特征”，算子的 `eigenvalue` 是“特征值”。
- 集合的 `indicator / characteristic function` 译“示性函数”；概率论中以 Fourier 变换定义的 `characteristic function` 译“特征函数”。两者均不作为群特征标处理。
- 对环面 $T$，固定 $X^*(T)=\operatorname{Hom}(T,\mathbb G_m)$ 为特征格，$X_*(T)=\operatorname{Hom}(\mathbb G_m,T)$ 为余特征格。`cocharacter` 默认“余特征标”，`coweight` 默认“余权”；这是一项保持术语可逆区分的技能约定。来源若明确把 $X_*(T)$ 的元素称为 coweights，按源词译“余权”。
- `one-parameter subgroup` 默认“单参数子群”。代数群中的余特征标特指 $\mathbb G_m\to G$；$\mathbb G_a\to G$ 以及 Lie 群中的 $\mathbb R\to G$ 都不自动称为余特征标。
- 表示论中修饰诱导、Jacquet 函子或交织算子的 `normalized` 默认“归一化”；测度或向量的数值规范也用“归一化”。代数几何的 `normal/normalization` 是“正规／正规化”，共轭保持子群的 `normalize/normalizer` 是“正规化／正规化子”，分析中的 `regularization` 是“正则化”；不得跨义项替换。
- `section` 先区分诱导表示族或丛的截面与商映射的右逆；同名不表示相同对象，也不自动具备连续性或等变性。`jet` 是“射流”，不译成截面。
- 张量积、连续对偶及余不变量保留来源范畴与拓扑；限制张量积不自动完备化，连续对偶不自动取光滑部分，余商不自动对关系空间取闭包。大小 theta 提升的技术义项也不由群对大小或实际实现像决定。
- 数学复合词已经确定为 `pseudo-X` 时，前缀 `pseudo-` 默认译“伪”，后接人名保持原文；不得只凭词形推断对象定义或臆造一个尚未核实的复合术语。

## 一般代数、代数几何与群论

| 英文术语 | 默认中文 | 精确适用范围 |
|---|---|---|
| affine group scheme | 仿射群概形 | 代数几何中的群概形 |
| Brauer group | Brauer 群 | 中心单代数的 Brauer 群 |
| canonical conjugation | 典范共轭 | 四元数代数上的标准共轭 |
| central isogeny | 中心同源 | 代数群的中心核同源 |
| central simple algebra | 中心单代数 | 有限维中心单代数 |
| additive character | 加性特征标 | 加法群的一维表示；值域及连续、光滑等条件依来源 |
| algebraic character | 代数特征标 | 代数群同态 $G\to\mathbb G_m$；无歧义时可简称“特征标” |
| character | 特征标 | 群到指定乘法群的一维表示；若指表示的迹函数，改用 `character of a representation` 的义项 |
| character of an algebra | 代数的特征标 | 含幺代数到指定系数域的含幺代数同态，如 Hecke 代数的特征标；不同于代数群的代数特征标或 idèle 类群的 Hecke 特征标，也不等于某个算子的特征值 |
| character of a representation | 表示的特征标 | $g\mapsto\operatorname{tr}\pi(g)$，或 Lie 群表示的相应广义函数／分布；一般不是群同态 |
| character group | 特征标群 | 由指定类别的特征标组成的群；须说明代数、连续或有理等范畴 |
| character lattice $X^*(T)$ | 特征格 | $X^*(T)=\operatorname{Hom}(T,\mathbb G_m)$；来源明确采用权语言时可随源称“权格”，但不得与完整权格无条件等同 |
| characteristic of a field / ring | 域／环的特征 | 如特征零；不写成“特征标零” |
| coboundary | 余边 | 群上同调及标准复形 |
| cocycle | 余圈 | 群上同调及标准复形；`n-cocycle` 写作“$n$-余圈” |
| component group | 连通分支群 | 代数群或拓扑群中由连通分支形成的群；须核对 $\pi_0(G)$、$G/G^\circ$ 及所用范畴，不用于任意几何分支集合 |
| cocharacter | 余特征标 | 代数群同态 $\mathbb G_m\to G$；不作为 `coweight` 的同义词 |
| cocharacter lattice $X_*(T)$ | 余特征格 | $X_*(T)=\operatorname{Hom}(\mathbb G_m,T)$；与抽象余权格分列 |
| coroot | 余根 | 根数据中的 coroot |
| coweight | 余权 | 根数据或对偶根系中的 coweight；不作为 `cocharacter` 的无条件替换 |
| coweight lattice | 余权格 | 抽象根系或来源定义的 coweight lattice；与 $X_*(T)$ 同现时保留各自记号 |
| discriminant | 判别式 | 代数、二次型或 Hermitian 分类；具体归一化另说明 |
| faithfully flat | 忠实平坦 | 态射或模的 faithfully flat 性质 |
| finite étale algebra | 有限平展代数 | 有限平展底代数 |
| identity component | 单位连通分支 | 代数群或拓扑群中的 $G^\circ$ |
| inner form | 内形式 | 代数群或表示论 |
| involution | 对合 | 阶为 $2$ 的自同构或反自同构；按对象与源文定义判断 |
| involution of the first kind | 第一类对合 | 在中心上恒等的对合 |
| involution of the second kind | 第二类对合 | 在中心上非平凡的对合 |
| isogeny | 同源 | 代数群、阿贝尔簇等语境 |
| Lie algebra character | Lie 代数特征标 | 一维 Lie 代数表示，即消去 Lie 括号的线性泛函；不与群表示的迹函数混同 |
| normalize a subgroup / normalizer | 正规化一个子群／正规化子 | 共轭保持指定子群；不同于调整数值因子的归一化 |
| one-parameter subgroup | 单参数子群 | 按源词翻译；$\mathbb G_a\to G$ 与 Lie 群的 $\mathbb R\to G$ 不自动称为余特征标 |
| opposite algebra | 反代数 | $D^{\mathrm{op}}$ |
| orthogonal involution | 正交型对合 | 第一类对合的正交型 |
| proper action | 正常作用 | 拓扑群或离散群的 proper action；不用于 proper morphism |
| pure inner form | 纯内形式 | pure inner twist/form 语境 |
| pure quaternion | 纯四元数 | 约化迹为零的四元数 |
| quaternion algebra | 四元数代数 | 中心单代数语境 |
| rational character | 有理特征标 | 定义在指定底域上的代数特征标；“有理”不表示值域为 $\mathbb Q$ |
| reduced norm | 约化范数 | 中心单代数的 reduced norm |
| reduced trace | 约化迹 | 中心单代数的 reduced trace |
| reductive dual pair | 约化对偶对 | theta 对应 |
| restriction of scalars | 限制标量 | Weil restriction |
| root | 根 | 根系或根数据 |
| root datum | 根数据 | 代数群或根系 |
| split | 分裂 | 代数群；其他对象中的 `split` 另行判断 |
| quasi-split | 拟分裂 | 代数群 |
| symplectic involution | 辛型对合 | 第一类对合的辛型 |
| torsor | 挠子 | $G$-torsor；首次出现可释为“主齐性空间” |
| unipotent | 幂幺 | 代数群或群元素 |
| unipotent radical | 幂幺根基 | 抛物子群或代数群 |
| weight | 权 | 表示论、根数据或模形式 |
| weight lattice | 权格 | 抽象根系的 weight lattice，或来源明确采用权语言的 $X^*(T)$ |

## 域、局部—整体与测度

| 英文术语 | 默认中文 | 精确适用范围 |
|---|---|---|
| adèle | adèle | 保留重音拼写 |
| idèle | idèle | 保留重音拼写 |
| Archimedean | Archimedean | 人名来源术语保留原文 |
| non-Archimedean | 非 Archimedean | 人名来源部分保留原文 |
| completed $L$-function | 完备化 $L$-函数 | 加入无穷处等因子的 $L$-函数 |
| different | 不同理想 | 数域或局部域扩张的 different；源文定义为分式理想时可简称“不同” |
| finite adèle | 有限 adèle | adèle 环的有限部分 |
| finite place | 有限位 | 整体域的非 Archimedean 位 |
| infinite place | 无穷位 | 整体域的 Archimedean 位 |
| global | 整体 | 仅限数论及 Langlands 的整体—局部结构；一般语篇仍译“全局” |
| local | 局部 | 数论、局部域及 Langlands 的局部对象；一般语篇按对象另译 |
| global field | 整体域 | 数域或一元函数域 |
| Haar measure | Haar 测度 | 局部紧群上的不变测度 |
| Hecke character | Hecke 特征标 | idèle 类群上的特征标；不同于 Hecke 代数的特征标，附加条件依来源 |
| hyperspecial | 超特殊 | Bruhat–Tits 理论中的顶点或紧开子群 |
| indicator function / characteristic function of a set | 示性函数 | 集合的 $0$—$1$ 函数；不用于概率论的 characteristic function |
| invariant top differential form | 最高次不变微分形式 | 代数群测度构造 |
| inverse different | 逆不同理想 | different 的逆分式理想 |
| leading Laurent coefficient | Laurent 首项系数 | Laurent 展开存在最低次非零幂时，该项的系数；本质奇点等情形不命中 |
| leading Laurent term | Laurent 首项 | 首项系数连同相应幂次 |
| local Artin map | 局部 Artin 映射 | 局部类域论；Frobenius 规范另说明 |
| local field | 局部域 | 标准数论语境中的局部紧非离散拓扑域，包括 Archimedean 与非 Archimedean 情形 |
| modulus character | 模特征标 | 抛物子群的 $\delta_P$ |
| place | 位 | 数论中由绝对值等价类描述的位；`at v` 写作“在位 $v$ 处” |
| probability Haar measure | 概率 Haar 测度 | 总体积归一化为 $1$ |
| ramified | 分歧 | 域扩张、表示或特征标；对象须写明 |
| unramified | 非分歧 | 域扩张、表示或特征标；对象须写明 |
| residue field | 剩余域 | 赋值环的 residue field |
| restricted product | 限制直积 | adèle 或局部群 |
| restricted tensor product | 限制张量积 | 相对于指定参考向量等资料的张量构造；几乎处处条件、代数形式及拓扑完备形式依来源分别说明 |
| self-dual measure | 自对偶测度 | 相对于固定加性特征标或 Fourier 配对 |
| uniformizer | 一致化元 | 离散赋值环中赋值为 $1$ 的元素；`prime element` 才译“素元” |
| valuation ring | 赋值环 | 非 Archimedean 局部域的赋值环 |

## 线性代数、形式与经典群

| 英文术语 | 默认中文 | 精确适用范围 |
|---|---|---|
| anisotropic | 非迷向 | 二次型、Hermitian 形式、向量、子空间或代数群；对象须写明 |
| anisotropic kernel | 非迷向核 | Witt 分解 |
| Gram matrix | Gram 矩阵 | 双线性或 Hermitian 形式 |
| Hermitian form | Hermitian 形式 | 保留人名部分 |
| Hermitian space | Hermitian 空间 | 保留人名部分 |
| hyperbolic plane | 双曲平面 | Witt 理论中的二维双曲平面 |
| isometry | 等距 | 保持给定形式的映射或群 |
| isotropic | 迷向 | 二次型、Hermitian 形式、向量、子空间或代数群；对象须写明 |
| sesquilinear | 半双线性 | 半双线性形式或映射 |
| signature, defined as $p-q$ | 符号差 | $p,q$ 为正、负惯性指数；不得改写为有序对 |
| signature, defined as $(p,q)$ | 正负惯性指数对 | 保留有序对及源文约定；不得改写为 $p-q$ |
| similitude | 相似 | 经典群中按标量缩放形式的映射或群 |
| skew-Hermitian form | 斜 Hermitian 形式 | $\epsilon=-1$ 等相应语境 |
| totally isotropic | 全迷向 | 子空间上的形式恒为零 |
| Witt decomposition | Witt 分解 | 形式空间 |
| Witt index | Witt 指数 | 通常在非退化形式空间中指极大全迷向子空间的维数，等价地为 Witt 分解中的双曲平面数 |
| Witt tower | Witt 塔 | theta 或 Witt 理论 |

## 表示论、Langlands 与 theta 对应

| 英文术语 | 默认中文 | 精确适用范围 |
|---|---|---|
| $(\mathfrak g,K)$-module | $(\mathfrak g,K)$-模 | 带相容 $\mathfrak g$ 与 $K$ 作用的模；不自动成为 Harish-Chandra 模 |
| admissible representation | 可容许表示 | 局部群表示论 |
| automorphic representation | 自守表示 | 自守表示论 |
| big theta lift | 大 theta 提升 | theta 对应中的 big theta lift；保留源文的输入范畴与商空间定义，不自动取不可约商 |
| branching law | 分支律 | 表示限制到子群后的分解或重数规律 |
| Casselman–Wallach representation | Casselman–Wallach 表示 | 实约化群的光滑 Fréchet 表示范畴 |
| central character | 中心特征标 | 中心通过一个特征标作用的情形；不可约性常保证这一性质，但不是词义本身的必要条件 |
| coinvariants | 余不变量 | 对群作用关系取商；关系空间是否取闭包及商拓扑依来源范畴，不由“余商”一词补入 |
| conductor | 导子 | 特征标、表示或 $L$-函数 |
| constant term | 常数项 | 自守形式沿幂幺根基的常数项 |
| contragredient representation | 逆步表示 | $\pi^\vee$；按来源区分光滑逆步及相应拓扑范畴的逆步，不无条件等同整个连续对偶 |
| degenerate principal series representation | 退化主系列表示 | 通常从非极小抛物子群、常以特征标为数据诱导；“退化”不等于可约 |
| discrete series representation | 离散系列表示 | 实约化群或局部群；与自守离散谱分开 |
| first occurrence | 首次出现 | theta 对应 |
| first occurrence index | 首次出现指标 | theta 对应 |
| genuine representation | 真表示 | 亚辛覆盖群；具体中心作用条件依来源 |
| generalized infinitesimal character | 广义无穷小特征标 | 相应中心极大理想的幂按来源规定的范围消去向量或模；保留幂次与量词，不改成中心逐点标量作用 |
| Harish-Chandra character | Harish-Chandra 特征标 | 实约化群可容许表示的特征标分布及其函数实现 |
| Harish-Chandra module | Harish-Chandra 模 | 满足有限生成、$K$-有限等条件的 $(\mathfrak g,K)$-模 |
| induced representation | 诱导表示 | 一般群、Lie 群或局部紧群；诱导范畴和左右约定另说明 |
| infinitesimal character | 无穷小特征标 | $Z(U(\mathfrak g))$ 通过一个特征标作用的情形；不可约性不是词义本身的必要条件 |
| inner type | 内型 | 实约化群中按伴随作用定义的 inner type 条件；具体条件依来源，与 inner form“内形式”分开 |
| intertwining operator | 交织算子 | 表示之间的 intertwiner 或标准交织积分算子 |
| Jacquet module | Jacquet 模 | 表示的 Jacquet module |
| $K$-type | $K$-型 | 限制到指定紧子群 $K$ 后的不可约类型；不与下列 type 或 Type I／II 分类混同 |
| Langlands correspondence | Langlands 对应 | 局部或整体对应 |
| Langlands functoriality | Langlands 函子性 | 与 Langlands 对应、纲领分开 |
| Langlands program | Langlands 纲领 | 猜想与结构性框架 |
| limit of discrete series | 离散系列的极限 | 实约化群表示；本身不自动属于离散系列 |
| minimal principal series representation | 极小主系列表示 | 从极小抛物子群诱导；“极小”不表示表示空间维数最小 |
| metaplectic | 亚辛 | metaplectic 群、覆盖、提升或中心扩张；底群、覆盖次数与中心核依来源，不由译名推定 |
| mixed model | 混合模型 | Weil 表示或 theta 对应 |
| monodromy operator | 单值算子 | 本表只覆盖 Weil–Deligne 对中的幂零算子 $N$；其他领域重新核对 |
| normalized induction | 归一化诱导 | 吸收规定的模特征标修正；忠实保留原文给出的指数和约定，不自行补写 |
| normalized intertwining operator | 归一化交织算子 | 经规定归一化因子校正；忠实保留原文给出的因子和乘除约定，不自行补写 |
| normalized Jacquet functor | 归一化 Jacquet 函子 | 与归一化抛物诱导配套的约定 |
| normalized Jacquet module | 归一化 Jacquet 模 | 与归一化抛物诱导配套的约定 |
| normalized parabolic induction | 归一化抛物诱导 | 抛物诱导的归一化版本 |
| open Bruhat cell | 开 Bruhat 胞 | Bruhat 分解中的开胞 |
| parabolic induction | 抛物诱导 | 从 $P=MN$ 的 Levi 数据诱导；不自动称为主系列 |
| period functional | 周期泛函 | 抽象 Hom 泛函 |
| period integral | 周期积分 | 整体积分 |
| principal series representation | 主系列表示 | 约化 Lie 群或局部约化群中由极小抛物子群诱导的系列；一般抛物诱导不自动命中 |
| relative trace formula | 相对迹公式 | 相对表示论或自守形式 |
| residual spectrum | 剩余谱 | 自守谱分解 |
| root number | 根数 | 函数方程中由 $\epsilon$-因子归一化得到的局部或整体常数；精确规范随来源 |
| small theta lift | 小 theta 提升 | 局部不可约输入语境中按来源定义的小 theta 提升，允许为零；不把较小群对的配对或实际实现像自动视为此对象 |
| smooth representation | 光滑表示 | 非 Archimedean 群取局部常值意义；Archimedean 群按来源采用光滑 Fréchet 等设定 |
| section of an induced representation | 诱导表示的截面 | 诱导表示族中的截面；标准、平坦、球等限定依来源，不同于任意商映射的右逆 |
| spherical section | 球截面 | 诱导表示中的极大紧子群不变截面 |
| standard intertwining operator | 标准交织算子 | 主系列或抛物诱导间由 Weyl 元给出的标准交织算子；不表示已归一化 |
| standard section | 标准截面 | 诱导表示族 |
| supercuspidal representation | 超尖表示 | 局部群表示论 |
| tempered representation | 柔曼表示 | 局部约化群表示论的 tempered 性，按来源范畴定义；“柔曼”为技能默认，不宣称统一定译，也不据此新增柔曼性假设 |
| type | 型 | Bushnell–Kutzko 等型理论中的紧开子群及其表示数据，精确定义依来源；不用于 Type I／II 分类，也不等同 $K$-型 |
| unitary character | 酉特征标 | 拓扑群、局部域乘法群或 adèle 类群 |
| unnormalized induction | 未归一化诱导 | 未吸收规定的模特征标修正 |
| Weil–Deligne representation | Weil–Deligne 表示 | $WD_F$ 表示 |

## 自守形式、解析与一般数学写作

| 英文术语 | 默认中文 | 精确适用范围 |
|---|---|---|
| automorphic form | 自守形式 | 经典或 adèlic 语境 |
| Banach contraction mapping theorem | Banach 压缩映射定理 | 固定点定理 |
| characteristic function of a probability distribution | 特征函数 | 概率分布的 Fourier 变换，如 $t\mapsto\mathbb E(e^{itX})$；符号约定依来源，不用于集合的 $0$—$1$ 函数 |
| completed projective tensor product | 完备投射张量积 | 按指定投射张量拓扑完备化；不同于限制张量积或未完备的代数张量积 |
| completion | 完备化 | 按给定拓扑完成；不自动代替取关系闭包或其他余商操作 |
| congruence subgroup | 同余子群 | 模形式 |
| continuous dual | 连续对偶 | 给定拓扑向量空间上的连续线性泛函；所用对偶拓扑依来源，不自动取群作用的光滑部分 |
| cusp | 尖点 | 模曲线或模形式 |
| cusp form | 尖点形式 | 模形式或自守形式 |
| de Rham cohomology | de Rham 上同调 | 微分几何或代数几何 |
| factor of automorphy | 自守因子 | 模形式变换律 |
| Fourier expansion | Fourier 展开 | 保留人名部分 |
| Fourier transform | Fourier 变换 | 保留人名部分 |
| jet / normal jet / jet filtration | 射流／法向射流／射流滤过 | 记录来源指定阶数与方向的 Taylor 数据；所有阶法向射流为零不削弱为仅函数值为零 |
| modular form | 模形式 | 经典模形式 |
| moderate growth | 缓增长 | 函数或表示的增长条件；高度、连续半范数及量词依来源，不与 Nash 语境的 tempered 无条件等同 |
| Neumann series | Neumann 级数 | 泛函分析 |
| normalization of a measure / vector | 测度／向量的归一化 | 按来源调整总体积、指定取值等规范；不同于正则化或代数几何正规化 |
| nuclear Fréchet space | 核 Fréchet 空间 | 拓扑向量空间的核性；不指某个线性映射的核 |
| partition of unity / subordinate partition of unity | 单位分解／从属单位分解 | 保留从属的开覆盖及来源规定的函数类别；不自动声称其存在 |
| Poisson distribution | Poisson 分布 | 概率论 |
| projective tensor seminorm | 投射张量半范数 | 指定空间上的投射张量半范数；名称不包含完备化 |
| proper map | 逆紧映射 | 拓扑语境：紧集的逆像仍紧 |
| proper morphism | 固有态射 | 代数几何 |
| regularization / regularized period | 正则化／正则化周期 | 分析或自守理论的 regularization；具体方法依来源，不与归一化混同 |
| Schwartz function / space / seminorm | Schwartz 函数／空间／半范数 | 保留人名及来源范畴，不自动缩为紧支或有限型输入 |
| section of a bundle | 丛的截面 | 指定丛的截面，所用几何或函数类别依来源；不与射流混同 |
| section of a quotient map | 商映射的截面 | 指定商映射的右逆；线性、连续或等变等性质仅在来源给出时采用 |
| slash operator | 斜线算子 | 模形式中的 slash action/operator |
| strong approximation | 强近似 | 代数群或数论 |
| tempered function / bundle / partition of unity | 柔曼函数／柔曼丛／柔曼单位分解 | 仅限 Nash–Schwartz 语境，各对象依来源定义；“柔曼”为技能默认，不宣称公认定译，不与柔曼表示或一般缓增长混同 |
| uniform moderate growth | 一致缓增长 | 按来源保留各阶微分共用增长指数等量词；跨参数或跨输入的一致性不能由译名补入 |
| upper half-plane | 上半平面 | 复分析或模形式 |

## 专业扩展条目

| 英文术语 | 默认中文 | 精确适用范围 |
|---|---|---|
| associate class | 相伴类 | Eisenstein 谱或抛物子群 |
| boundary degeneration | 边界退化 | 球簇或相对 Langlands |
| doubling method | 加倍方法 | 自守 $L$-函数或 theta 语境 |
| first term identity | 首项恒等式 | Siegel–Weil 公式 |
| invariant functional | 不变泛函 | 表示论中的 Hom 泛函 |
| mixed truncation | 混合截断 | 自守形式的截断方法 |
| normal variety | 正规簇 | 代数几何 |
| normalization | 正规化 | 代数几何中的代数簇、概形或环；不受表示论 `normalized` 规则影响 |
| open orbit | 开轨道 | 代数群作用 |
| pseudo-Eisenstein operator | 伪Eisenstein算子 | 以测试数据作抛物求和的算子；保留人名 |
| pseudo-Eisenstein series | 伪Eisenstein级数 | 由测试数据作抛物求和并形成普通 Eisenstein 族波包的对象 |
| rapidly decreasing | 速降 | 函数或截断后的自守形式 |
| relative invariant | 相对不变量 | 预齐次向量空间或球簇 |
| residual representation | 剩余表示 | 自守谱 |
| scattering operator | 散射算子 | 相对谱理论 |
| second term identity | 次项恒等式 | Siegel–Weil 公式 |
| spherical root | 球根 | 球簇理论 |
| spherical variety | 球簇 | 代数群作用或相对 Langlands |
| stabilizer | 稳定子 | 群作用 |
| wave packet | 波包 | 谱分解 |
| zeta distribution | zeta 分布 | 相对或预齐次 zeta 理论 |
| zeta integral | zeta 积分 | Rankin–Selberg 等积分表示 |

## 默认保留的来源词形

| 来源词 | 正文处理 | 适用范围 |
|---|---|---|
| Borel | 保留人名，加中文通名 | Borel 子群等 |
| Levi | 保留人名，加中文通名 | Levi 子群、Levi 分解等 |
| Bruhat | 保留人名，加中文通名 | Bruhat 分解、Bruhat 胞等 |
| Eisenstein | 保留人名，加中文通名 | Eisenstein 级数、截面、算子和族等；不改为中文音译 |
| Fourier | 保留人名，加中文通名 | Fourier 变换、Fourier 展开等 |
| Mellin | 保留人名，加中文通名 | Mellin 变换等 |
| Hecke | 保留人名，加中文通名 | Hecke 算子、Hecke 代数等 |
| Jacquet | 保留人名，加中文通名 | Jacquet 模、Jacquet 函子等 |
| Weil | 保留人名，加中文通名 | Weil 表示、Weil 群等 |
| Langlands | 保留人名，加中文通名 | 对应、函子性和纲领须分开 |
| generic | 保留 `generic` | 多个表示论义项；先核对来源定义，覆盖默认时按使用协议的明确采用规则 |
| relevant | 保留 `relevant` | GGP 等语境中的精确定义 |
| distinguished | 保留 `distinguished` | 相对表示论中的 Hom 非零性质 |
| parahoric | 保留 `parahoric`，加中文通名 | parahoric 子群等；连通性等定义约定依来源，不译为“抛物子群” |
| seesaw | 保留 `seesaw` | theta 对应中的 seesaw 结构；覆盖默认时按使用协议的明确采用规则 |
| theta | 保留 `theta`，加中文通名 | theta 对应、核、级数和提升等；大小 theta 提升依上表的技术义项 |
| Arthur string | 保留 `Arthur string` | 高度专门的参数结构 |
| pinning | 保留 `pinning` | 约化群及根数据语境；覆盖默认时按使用协议的明确采用规则 |
