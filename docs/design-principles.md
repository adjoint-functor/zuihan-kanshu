# 设计原则

瑞般观珠把数学判断、研究记录与文稿制作放在相互连接的工作流中。这些原则解释公开源码的组织方式；实际执行规则以[技能入口](../skill/zuihan-kanshu/SKILL.md)及其按需引用的模组为准。

## 先辨认当前目标

问题解答、持续研究与文稿制作有不同的恢复和交付需要。普通问题可以在对话中完成；持续研究保存可接续状态；文稿制作维护正文与控制信息。跨路径工作先判断数学内容，再按需翻译、整理文风和编译，避免语言或版式变化暗中改变结论。

## 让结论与证据相匹配

准确保留对象、量词、适用假设、依赖与证明。已建立、条件成立、猜想、待验证与不成立分别表达；成熟文献的公开身份与当前命题是否适用分开判断。有限计算、数值证据和结构检查只支持各自覆盖的结论。

## 保留可恢复的当前状态

研究工作台用数学主稿、计算草稿、只追加日志、下一次入口和资料台账区分正文、探索、过程、计划与来源。每一版五文件保持一致；候选先检查并完整保存，再归档上一版。必要代码、数据与证书作为证据保存，五文件约定不排斥复现材料。

普通文稿将来源、偏好与构建记录放在控制稿，让正文可独立阅读。恢复时先读有效入口，再按当前问题补读必要材料；局部编辑从完整来源副本开始。

写作计划先说明文章主线与范围，正文按内容与依赖灵活分轮。全稿结构与一致性由当前实际主智能体通读并实际修订，再完成适用的导语和语言审读。中间轮保存可接续材料，最终轮按交付目标制作 PDF，避免成品构建挤占尚未完成的实质写作。

## 以实际问题组织协作

探索、证明、计算、核验与编辑是可按需分配的职责。独立核验要接触实际论证，整合者保留最终接纳责任。分工须服从宿主工具、实际模型参数与用户授权；缺少能力时如实说明并继续可行工作，不把角色说明当作已经运行的代理。

## 按需加载，适度验证

技能入口只做路径选择，详细规则留在参考模组。按当前工作读取必要部分，复用仍适用的来源、证明与核验。验证围绕剩余风险选择：数学问题检查论证，脚本变化检查对应行为，PDF 变化检查真实编译与成品。

## 源码与分发保持清楚边界

运行时只维护一份源码，以精确清单构建纯技能和插件。设计说明、版本沿革、测试与构建工具留在仓库层；发布包保留运行所需材料及许可声明。安装、云端保存、外部查询与编译各自以实际成功结果为准。

## 公开参考

以下公开材料保留了写作与工程设计的依据。表中说明本项目借鉴的方向；具体协议由本项目定义，数学结论的可靠性仍须由实际论证与核验判断。

| 参考材料 | 对应设计 |
| --- | --- |
| Terence Tao：[准确描述结果](https://terrytao.wordpress.com/advice-on-writing-papers/describe-the-results-accurately/)与[适度提供细节](https://terrytao.wordpress.com/advice-on-writing-papers/give-appropriate-amounts-of-detail/) | 如实说明条件、贡献与未证内容；关键论证和不常见依赖给出足够细节与定位。 |
| [UW–Madison Writing Center：Reverse Outlines](https://writing.wisc.edu/handbook/processandstructure/reverseoutlines/) | 从实际成稿反推提纲，检查每部分怎样推进主线。 |
| Terence Tao：[Organise the paper](https://terrytao.wordpress.com/advice-on-writing-papers/organise-the-paper/)与[Use good notation](https://terrytao.wordpress.com/advice-on-writing-papers/use-good-notation/) | 结构层次、支线安置、记号负担和一致性。 |
| Terence Tao：[导语中的关键内容](https://terrytao.wordpress.com/advice-on-writing-papers/use-the-introduction-to-%E2%80%9Csell%E2%80%9D-the-key-points-of-your-paper/)；[Bjorn Poonen：Practical suggestions for mathematical writing](https://math.mit.edu/~poonen/papers/writing.pdf) | 尽早说明有意义的结果，以准确简化和分层表达降低阅读负担。 |
| [Igor Pak：How to Write a Clear Math Paper](https://www.math.ucla.edu/~pak/papers/how-to-write1.pdf)；[Steven Kleiman：Writing a Math Phase Two Paper](https://web.mit.edu/mathp2/www/piil.html) | 完稿后重审导语、长导语分层和全篇／局部背景安置；保留个人及课程建议的适用边界。 |
| OpenAI：[Rethinking skills and prompts for GPT-6 Astra](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra) | 简洁入口、按需加载，说明目标与完成尺度，清理不再适用的规则。 |
| OpenAI：[Using PLANS.md for multi-hour problem solving](https://developers.openai.com/cookbook/articles/codex_exec_plans) | 持续更新当前计划、进展与重要决定，保留可恢复状态。 |
| Anthropic：[Effective context engineering for AI agents](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents) | 外部保存必要状态，按当前问题读取相关材料。 |
| [Pandoc 手册](https://pandoc.org/MANUAL.html)与 [Quarto 的 LaTeX 输出说明](https://quarto.org/docs/output-formats/pdf-basics.html#latex-output) | 区分正文、配置、生成的 TeX 与实际依赖；以真实编译结果检查兼容性。 |
| [TinyTeX FAQ](https://yihui.org/tinytex/faq/) | 按需准备可扩展的 TeX 环境，考虑版本与依赖的实际可获得性。 |

写作体裁默认、主智能体职责、独立轮次和可选导语页数预算是本插件的设计；参考材料不构成跨体裁的固定导语占比规范。

研究系统、检索工具及其他项目的公开来源与许可说明见 [NOTICE](../NOTICE)。进一步阅读：[版本与迁移](history-and-migration.md)、[研究初始化示例](examples/research-initialization.md)、[图标设计](design/zuihan-icon/README.md)。
