# zuihan-kanshu

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="skill/zuihan-kanshu/assets/icon-dark-1024.png">
  <img src="skill/zuihan-kanshu/assets/icon-1024.png" width="256" height="256" alt="瑞般观珠：以数学微雕公式环绕的双叶图标">
</picture>

**瑞般观珠**是主要面向 ChatGPT **Work** 的数学问题解答、持续研究与写作插件。

[English](README.en.md) · [安装说明](INSTALL.md) · [可复现示例](docs/examples/research-initialization.md) · [设计原则](docs/design-principles.md) · [版本与迁移](docs/history-and-migration.md)

**请在 ChatGPT Work 中使用。数学可以随身携带，服务器不必。**

瑞般观珠在云端开展数学问答、研究与写作，无需自行准备远程主机或维护服务器。工作间隙、出差途中、旅行路上，都可以打开 Work，接着做数学。

如果觉得 Codex 的连续工作能力过于充沛，担心目标模式一开，额度先于猜想告终，那么 Work 的节奏或许刚刚好：按轮次推进，在适合讨论时停下来，看看进展、追问细节，再决定下一步。本插件为人类保留参与数学的席位。

需要暂时离席时，可以请 **Dot 担任值班编辑**：每当它看到本轮任务完成，就向指定 **Work 对话**发送 `根据 @瑞般观珠 规范，按指定计划，进行下一轮。`，让 Work 也客串一回 Codex。还可以请它先读计划照着推进，或限定推进多少轮。

[Dot 官方任务与记忆说明](https://learn.chatgpt.com/docs/dots/tasks-and-memory) · [控制说明](https://learn.chatgpt.com/docs/dots/controls)

先确认 Dot 能访问并续接指定任务，具体能力以官方说明及实际可用范围为准。有用户反馈，以这种方式一键启动、按计划连续推进，完成了 **200 页讲义**的写作。**研究等开放任务连续推进仍可能耗尽额度，可先约定轮数与停止条件。**

## 进阶使用指南

**[阅读完整进阶指南](skill/zuihan-kanshu/references/usage-guide.md)**，了解怎样开题、接续研究、追问细节和规划写作。

**想用得更有效率？** 在对话输入框中输入 `@`，选中实际的**瑞般观珠**插件，然后直接问：

```text
告诉我怎么用得更有效率。
```

**自 v8.4.0 起已内置指南问答**；也可以通过上方链接直接阅读完整指南。当前源码与指南对应待发布的 v8.6.0，正式下载仍为 v8.4.0。

| 使用场景 | 进阶用法 |
| --- | --- |
| 数学问答 | 直接提出疑问，可说明相关基础与想要的深度；默认在对话中给出简洁充分或按需展开的回答。 |
| 数学科研开题 | 上传 Markdown 或 PDF 说明文件，集中交代目标、已有结果和参考线索；材料充分可直接开始，只有大方向时可先讨论。 |
| 接续研究 | 看完对话简报后，可以说“依照 @瑞般观珠 的规范，按照你的判断，继续下一轮研究”。 |
| 暂停与追问 | 先说“暂停研究轮次，依照 @瑞般观珠 的规范，先回答我：……”，再追问细节、研判方向或判断是否适合阶段成文。 |
| 数学写作 | 说清完整需求；默认先制定并保存计划，在对话中讨论，启动后按质量分轮推进。 |

## 使用环境与模型

目前不推荐在 Codex 中使用，未来拟推出适配 Codex 的分支版本。

**主智能体建议：**预算充足时选 **GPT-6 Astra／Max**，最低建议 **GPT-6.1 Sol／Max**。插件已内置子智能体分配方案，数学研究模组有专门的探索、证明与核验安排；通常使用 Max 即可，**默认不建议 Ultra**。

初步粗测中，GPT-6 Astra 与 GPT-6.1 Sol 的消耗占比约为 **4∶1**；按约 5 倍单位消耗作简化折算，等价用量约为 **4∶5**，Sol 占一半以上。这是粗测参考，实际分工随任务而变。已有用户实测**中文、英文和日语均可正确运行**。

## 安装

本项目通过 GitHub 提供第三方插件。当前正式版为 **v8.4.0**：[下载插件 ZIP](https://github.com/adjoint-functor/zuihan-kanshu/releases/download/v8.4.0/zuihan-kanshu-v8.4.0.zip)，普通使用者无需从源码编译。

### 首次安装（推荐：上传完整 ZIP）

1. [下载正式插件 ZIP](https://github.com/adjoint-functor/zuihan-kanshu/releases/download/v8.4.0/zuihan-kanshu-v8.4.0.zip)，保留完整 `.zip`，无需解压。
2. 打开 ChatGPT 的**插件**页面，选择 **添加 → 上传插件压缩包**，上传这个 ZIP，按页面提示完成导入／保存。
3. 按提示完成**安装／启用**；再新建对话，用 `@` 选择**瑞般观珠**并提出一个数学问题。

已有用户反馈首次上传安装成功；具体入口和权限因账户或客户端而异。

### 让 GPT 协助安装（可选）

在提供 **Plugin Creator**、允许创建和使用插件的 ChatGPT Chat 或 Work 中新建对话，输入 `@` 并选择 **Plugin Creator**，发送下面的提示词。保存私人副本后，仍需完成安装／启用与新对话验证。

```text
请帮我安装第三方插件“瑞般观珠”：https://github.com/adjoint-functor/zuihan-kanshu
请先读根目录 INSTALL.md，使用正式 Release 插件 ZIP，原样导入完整插件并保留名称、版本、技能和资源，保存为我自己的私人副本。不要重新设计或改写插件；按当前宿主能力完成安装／启用，并说明实际完成到哪一步。
```

[完整安装说明（含给 GPT 的步骤）](INSTALL.md)提供插件页上传、GPT 工具能力排查、已有副本更新、Codex 本地安装与源码构建方法。GitHub 的 **Code → Download ZIP** 和 Release 的 **Source code** 都是源码包，不能直接当作插件 ZIP。

## 问题 → 研究 → 写作

| 你要做的事 | 瑞般观珠提供的支持 | 详细入口 |
| --- | --- | --- |
| 解答数学问题 | 按问题、明确要求和可靠相关背景选择解释深度，保留必要推导、证明、反例与文献依据；默认在对话中完成 | [数学问答](skill/zuihan-kanshu/references/mathematical-inquiry.md) |
| 开展持续研究 | 梳理文献、探索路线、证明与核验，保存进展并接续已有工作 | [研究工作台](skill/zuihan-kanshu/references/research-workbench.md) |
| 数学写作 | 支持规划、撰写与修订，默认以质量为先。 | [普通文稿](skill/zuihan-kanshu/references/working-draft.md) |

内置**数学研究迷你智能体**的角色与协作约定，包括探索者、证明者、做题者、独立核验者和数学编辑者，按研究需要启用。模型选择、推理强度与实际委派受宿主提供的能力和用户授权约束；具体职责见[研究角色](skill/zuihan-kanshu/references/research-roles.md)。

[语言表达与写作指导](skill/zuihan-kanshu/references/writing-style.md)覆盖数学对话、问答、文稿新写与修订，从组织表达时就帮助把内容说清楚、说准确，适用于各任务语言。普通对话自然承接相关上下文，文稿保留适用的规划与独立审读，研究报告沿用既有简报详略。

中文输出另用[中文指导](skill/zuihan-kanshu/references/chinese-translation.md)改善中文表现；中文翻译习惯会按你的明确需求准确记录，并在相应范围沿用。具体用法见[进阶使用指南](skill/zuihan-kanshu/references/usage-guide.md)。

[成品制作与交付](skill/zuihan-kanshu/references/final-output.md)另提供 Markdown、PDF 和按需 TeX；实际编译与检查需要可用工具链，见 [PDF 构建说明](skill/zuihan-kanshu/references/final-pdf-build-profile.md)。

## 从这三句话开始

```text
使用瑞般观珠解答以下数学问题，并按需要给出推导、证明或文献依据。问题：……。
```

```text
使用瑞般观珠，围绕以下目标开展数学研究，将研究记录与阶段成果保存在云端。研究目标：……。
```

```text
使用瑞般观珠，根据以下要求制定数学文稿的写作计划，并保存在云端。写作要求：……。
```

研究记录、写作计划与文稿默认保存在云端 Library 的 `瑞般观珠/` 下：用户明确的项目名优先，否则自主按主题命名，首次保存确认实际目录。指定目的地优先，接续已有项目沿用原目录，不自动迁移。普通问答和使用帮助不自动建立稿件或研究项目。

其他宿主按实际可用的本地、工作区或文件交付能力保存，并说明实际保存位置；没有持久保存能力时，说明限制并在对话中提供可用内容。脚本在本地成功不代表已经保存到云端。研究工作台的五文件协议与保存步骤见[研究工作台](skill/zuihan-kanshu/references/research-workbench.md)。

## 仓库与检查

运行时由可按需加载的技能说明、参考模组和 Python 脚本组成。

| 路径 | 用途 |
| --- | --- |
| [`skill/zuihan-kanshu/`](skill/zuihan-kanshu/) | 唯一运行时源码，包含技能、参考、脚本与资源 |
| [`tools/runtime-files.txt`](tools/runtime-files.txt) | 精确的运行时文件清单 |
| [`tools/`](tools/) 与 [`tests/`](tests/) | 源码检查、打包与测试 |
| [`docs/`](docs/) | 公开设计说明、迁移记录与可复现示例 |

```sh
python tools/validate_repo.py
python tools/run_tests.py
```

涉及 PDF 的完整验收需要 TeX、字体及 PDF 工具。测试报告中的跳过项应按实际环境理解；结构检查通过不等于数学证明正确。贡献时按改动范围选择验证，见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 致谢

感谢 [Danus](https://github.com/frenzymath/Danus/tree/6d92e8d415933ca2ef52fd1a4da73fdfcd418f1c)、[Rethlas](https://github.com/frenzymath/Rethlas/tree/e7e48a6d30e7f0ddf0ed1909a594a1f0cfe2c2b7) 与 [Bolzano（problem-solver）](https://github.com/vaclavrozhon/problem-solver/tree/ccc0f7185ef6a72b3b8f519b8efab3f386cf597f)，它们为研究协作、证明核验和失败反馈提供了设计参考。

感谢 Terence Tao 公开的数学写作建议，尤其是[《Describe the results accurately》](https://terrytao.wordpress.com/advice-on-writing-papers/describe-the-results-accurately/)和[《Give appropriate amounts of detail》](https://terrytao.wordpress.com/advice-on-writing-papers/give-appropriate-amounts-of-detail/)，为本插件关于准确陈述数学结果、合理安排论证详略的写作指导提供了参考。

完整的方法、工具服务与术语来源及其用途集中列在 [NOTICE](NOTICE)。这些致谢不表示将上游项目整体纳入本插件，也不表示上游作者为本项目背书；许可与使用边界以该说明为准。

## 名称与图标

名称取意于数学术语「随伴関手」（ずいはんかんしゅ，Adjoint Functor），以其日语读音谐作「瑞般観珠」，中文写作「瑞般观珠」；技术标识为 `zuihan-kanshu`。

图标微雕保留正式 **22 条公式**，每条出现四次。其精确写法、适用条件、来源与定义／定理／猜想状态见[公式清单](docs/design/zuihan-icon/formula-catalogue.md)；源图与导出方法见[图标设计说明](docs/design/zuihan-icon/README.md)。四张透明 PNG 为：

| 尺寸 | 浅色背景 | 深色背景 |
| --- | --- | --- |
| 256 × 256 | [icon-256.png](skill/zuihan-kanshu/assets/icon-256.png) | [icon-dark-256.png](skill/zuihan-kanshu/assets/icon-dark-256.png) |
| 1024 × 1024 | [icon-1024.png](skill/zuihan-kanshu/assets/icon-1024.png) | [icon-dark-1024.png](skill/zuihan-kanshu/assets/icon-dark-1024.png) |

许可与来源说明见 [LICENSE](LICENSE) 和 [NOTICE](NOTICE)。使用问题与建议见 [SUPPORT.md](SUPPORT.md)，安全与外部数据交互说明见 [SECURITY.md](SECURITY.md)。

