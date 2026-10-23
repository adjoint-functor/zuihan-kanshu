# 设计原则

瑞般观珠把数学判断、研究记录与文稿制作放在相互连接的工作流中。这些原则解释公开源码的组织方式；实际执行规则以[技能入口](../skill/zuihan-kanshu/SKILL.md)及其按需引用的模组为准。

## 先辨认当前目标

问题解答、持续研究与文稿制作有不同的恢复和交付需要。普通问题可以在对话中完成；持续研究保存可接续状态；文稿制作维护正文与控制信息。[语言表达与写作指导](../skill/zuihan-kanshu/references/writing-style.md)从组织内容时用于数学对话、问答、文稿新写与修订，适用于各任务语言。[中文表达、术语与翻译](../skill/zuihan-kanshu/references/chinese-translation.md)另指导预期中文的生成及真实来源翻译；[成品制作与交付](../skill/zuihan-kanshu/references/final-output.md)负责 Markdown、PDF 等产物。单独的语言或版式变换不暗中改变结论。

问答按当前问题、最新明确要求与可靠相关背景选择深度和先备，可以自然承接上下文。共享指导不把对话变成独立文章，不自动要求稿件控制、术语附录、审查轮次或 PDF；实际文稿仍完成其专门审读。研究内部过程不受中文润色规则干预，报告阶段采用适用指导，保留既有简报详略。

三条数学路径按完整意图选择，显式选择插件和任务类别只帮助澄清意图，不构成必需关键词。结合语言、上下文、否定与暂停指令，以及实际来源和修改范围判断；用“润色”“整理”等词并不自动授权整稿处理。已有文稿的表达与组织改善使用写作下的[文稿后处理入口](../skill/zuihan-kanshu/references/manuscript-refinement.md)，复用普通文稿的计划与顺序，不另建同权流程。

## 以对话模式判断适用性

本分支的智能体分工、轮次和串行审查流程面向 Work。入口在明确识别为真正的 Codex 对话时默认停止并提醒；从 Codex 客户端启动的 Work 仍适用，通用模型身份、工具或路径中的 Codex 字样不足以判断当前模式。不确定但没有 Codex 模式证据时不凭猜测拦截；实际模式信息冲突且影响执行时再针对性澄清。

这是技能规则，不能假称为平台硬拦截。`agents/openai.yaml` 保留既有 `CHAT`、`CODEX` 产品值与隐式调用，避免在尚未验证 Work 的产品映射时将其一并排除。源码检查和情境试用不等于真实宿主中的模式识别验收；仓库维护也不等于调用本插件执行数学任务。

## 用持久化计划支持接续

持续维护任务状态是本插件的重要设计之一。Codex 在开始工作前按发现规则加载适用的 `AGENTS.md`，用于提供项目约定；本插件的任务控制文件还承载随工作变化的目标、主线、计划、进展、待决问题、证据定位与下一步。普通写作使用独立的 `.control.md`，持续研究将计划与恢复入口保存在“下一次入口”，并与其他工作台文件保持一致。普通对话问答仍不默认建立这些文件。

控制文件由技能流程定位和读取，不假设宿主会自动发现任意 Markdown 文件。接续时先恢复有效目标与当前安排，结合用户最新指示和必要材料判断下一步；推进后更新实际进展、决定与计划，在规划、重要调整和轮次收束时向用户报告关键安排。已有且仍有效的上下文和核验可以复用；陈旧待办应调整或撤下，达到完成尺度后可以结束。控制记录服务于判断，不替代对实际材料的检查。

这使简短的继续指令或 Dot 辅助接续有具体依据，有助于减少重复摸索、遗忘约定和按失效计划机械推进。计划待批准、出现需用户决定的取舍或受到暂停限制时，继续指令仍按实际授权处理；持久化文件本身不会产生新的执行权限。它也不保证无人值守任务的结果或额度消耗。

持久化指令与持续更新计划都有公开实践，适用于多种智能体环境。本项目的具体工作台、写作控制、恢复顺序与用户汇报安排面向数学任务组织；不能仅凭这项通用方法推断 Codex 不适用，也不能据此宣称当前分支已经适配 Codex。当前 Work 轮次与串行安排，以及未来其他环境的兼容验证，分别按实际能力处理。

## 让结论与证据相匹配

准确保留对象、量词、适用假设、依赖与证明。已建立、条件成立、猜想、待验证与不成立分别表达；成熟文献的公开身份与当前命题是否适用分开判断。有限计算、数值证据和结构检查只支持各自覆盖的结论。

## 保留可恢复的当前状态

研究工作台用数学主稿、计算草稿、只追加日志、下一次入口和资料台账区分正文、探索、过程、计划与来源。每一版五文件保持一致；候选先检查并完整保存，再归档上一版。必要代码、数据与证书作为证据保存，五文件约定不排斥复现材料。

普通文稿将来源、偏好与构建记录放在控制稿，让正文可独立阅读。恢复时先读有效入口，再按当前问题补读必要材料；局部编辑从完整来源副本开始。

新建需保存任务在未指定目的地时，默认使用 Library 根目录 `瑞般观珠/` 下的项目子目录，用户明确项目名优先，首次保存确认实际目录；已有项目不自动迁移。全项目共享的个人中文参考与项目子目录并列，独立保存已查证补充及用户明确的中文用词、个性化翻译习惯和保留词规则，保留作用域与来源；随口用词不构成授权，共享参考不替代单篇文稿的术语说明。

写作计划先说明文章主线与范围，正文按内容与依赖灵活分轮。全稿结构与一致性由当前实际主智能体通读并实际修订，再完成适用的导语和语言审读。中间轮保存可接续材料，最终轮按交付目标制作 PDF，避免成品构建挤占尚未完成的实质写作。

## 以实际问题组织协作

探索、证明、计算、核验与编辑是可按需分配的职责。独立核验要接触实际论证，整合者保留最终接纳责任。分工须服从宿主工具、实际模型参数与用户授权；缺少能力时如实说明并继续可行工作，不把角色说明当作已经运行的代理。

## 按需加载，适度验证

技能入口集中说明环境边界、路径选择与通用约定，详细规则留在参考模组。按当前工作读取必要部分，复用仍适用的来源、证明与核验。验证围绕剩余风险选择：数学问题检查论证，脚本变化检查对应行为，PDF 变化检查真实编译与成品。

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
| OpenAI：[Skills](https://developers.openai.com/plugins/concepts/skills)、[Plugin architecture](https://developers.openai.com/plugins/concepts/plugins)与[Use ChatGPT](https://learn.chatgpt.com/docs/use-chatgpt) | 语义匹配与显式调用、技能和执行能力的边界，以及对话模式与共享运行时的区分。 |
| OpenAI：[Rethinking skills and prompts for GPT-6 Astra](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra) | 简洁入口、按需加载，说明目标与完成尺度，清理不再适用的规则。 |
| OpenAI：[Using PLANS.md for multi-hour problem solving](https://developers.openai.com/cookbook/articles/codex_exec_plans) | 持续更新当前计划、进展与重要决定，保留可恢复状态。 |
| OpenAI：[Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md) | 说明项目指令的发现与加载方式；与本插件持续维护的任务状态、计划及用户汇报安排区分。 |
| Anthropic：[Effective context engineering for AI agents](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents) | 外部保存必要状态，按当前问题读取相关材料。 |
| [Pandoc 手册](https://pandoc.org/MANUAL.html)与 [Quarto 的 LaTeX 输出说明](https://quarto.org/docs/output-formats/pdf-basics.html#latex-output) | 区分正文、配置、生成的 TeX 与实际依赖；以真实编译结果检查兼容性。 |
| [TinyTeX FAQ](https://yihui.org/tinytex/faq/) | 按需准备可扩展的 TeX 环境，考虑版本与依赖的实际可获得性。 |

写作体裁默认、主智能体职责、独立轮次和可选导语页数预算是本插件的设计；参考材料不构成跨体裁的固定导语占比规范。

完整的方法、检索工具、工程依赖、术语与标准来源及用途集中在 [NOTICE](../NOTICE)，并随运行包提供；上表保留设计与来源的对应关系。问答的上下文适配、写作轮次和具体路由由本插件定义。进一步阅读：[版本与迁移](history-and-migration.md)、[研究初始化示例](examples/research-initialization.md)、[图标设计](design/zuihan-icon/README.md)。
