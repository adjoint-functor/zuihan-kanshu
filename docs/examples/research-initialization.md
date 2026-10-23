# 可复现示例：初始化有限等比和工作台

本例从仓库源码创建本地研究工作台，检查文件结构并恢复下一次入口。只使用 Python 标准库和内置模板，不需要网络、外部检索服务、代理或 TeX。例子中的数学证明完整列出，便于区分结构检查与数学核验。

## 1. 创建与检查

在仓库根目录选择一个尚未使用的输出位置，运行：

```sh
python skill/zuihan-kanshu/scripts/research-workbench.py init-project .example-work/geometric-sum --name geometric-sum --goal "Prove the finite geometric-sum identity and treat r = 1 separately."
python skill/zuihan-kanshu/scripts/research-workbench.py inspect-project .example-work/geometric-sum
python skill/zuihan-kanshu/scripts/research-workbench.py validate-project .example-work/geometric-sum --json
python skill/zuihan-kanshu/scripts/research-workbench.py prepare-session .example-work/geometric-sum --format markdown
```

命令中的 `python` 可换成本机可用的 `python3`。初始化会拒绝覆盖已有研究文件；再次尝试时改用另一个空目录。示例产物无需提交到仓库。

工作台包含以下五文件，项目初始版本为 `v1.0.0`，独立于技能版本号：

| 文件 | 内容职责 |
| --- | --- |
| `geometric-sum_数学主稿_v1.0.0.md` | 目标、定义、命题、证明与未决问题 |
| `geometric-sum_计算草稿_v1.0.0.md` | 试算、局部推导与反例检查 |
| `geometric-sum_研究日志_v1.0.0.md` | 只追加的研究过程记录 |
| `geometric-sum_下一次入口_v1.0.0.md` | 当前状态、近期计划和必要定位 |
| `geometric-sum_参考资料台账_v1.0.0.md` | 资料来源与适用性状态 |

另有 `download/`、`tmp/`、`old/` 三个目录。`inspect-project` 应报告 `current_version` 为 `1.0.0`；`validate-project --json` 应报告 `valid: true` 和空的 `issues`；`prepare-session` 输出当前下一次入口。生成日期随运行日期变化。

这些结果表示本地结构已建立并通过检查。模板仍有待补充内容，初始化没有完成数学研究，也没有将文件保存到云端。

## 2. 自含数学样例

可将以下内容作为数学主稿中“已建立的数学内容”的起点，并在草稿中核对边界情形。

**命题【已建立】。** 设 $n$ 为正整数，$r\in\mathbb C$，定义

$$
S_n(r)=\sum_{k=0}^{n-1}r^k.
$$

则

$$
S_n(r)=
\begin{cases}
\dfrac{1-r^n}{1-r},&r\ne1,\\[4pt]
n,&r=1.
\end{cases}
$$

**证明。** 由有限和直接相减，

$$
(1-r)S_n(r)
=\sum_{k=0}^{n-1}r^k-\sum_{k=1}^{n}r^k
=1-r^n.
$$

当 $r\ne1$ 时，$1-r\ne0$，可以相除。$r=1$ 时，每项均为 $1$，共有 $n$ 项，故和为 $n$。证毕。

例如 $n=4,r=2$ 时，$1+2+4+8=15=(1-2^4)/(1-2)$；$r=0$ 时和为 $1$。上述有限恒等式无需 $|r|<1$；把它延伸为无穷级数则是另一个需要收敛条件的问题。

## 3. 留下可接续状态

将命题与证明放入主稿；将边界核对放入草稿；在入口写明本例目标已完成或当前仍需核对的具体问题。若进行版本修订，按[研究工作台命令](../../skill/zuihan-kanshu/references/research-workbench.md#本地工作台命令)建立候选、追加日志、验证并发布本地版本，不直接改写旧日志。

在具备云端文件能力的宿主中，再按实际请求保存这些文件：指定目录优先，否则默认放入 Library 根目录 `瑞般观珠/` 下的项目子目录，用户明确项目名优先，并在首次保存时确认实际目录。接续已有项目沿用原目录，不自动迁移；本地命令不会替代云端保存步骤。
