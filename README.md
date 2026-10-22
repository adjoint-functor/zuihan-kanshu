# zuihan-kanshu

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="skill/zuihan-kanshu/assets/icon-dark-1024.png">
  <img src="skill/zuihan-kanshu/assets/icon-1024.png" width="256" height="256" alt="瑞般观珠：以数学微雕公式环绕的双叶图标">
</picture>

**瑞般观珠**是主要面向 ChatGPT **Chat 与 Work** 的数学问题解答、持续研究与写作插件。

[English](README.en.md) · [安装说明](INSTALL.md) · [可复现示例](docs/examples/research-initialization.md) · [设计原则](docs/design-principles.md) · [版本与迁移](docs/history-and-migration.md)

## 安装

本项目通过 GitHub 提供第三方插件。当前正式版为 **v8.3.1**：[下载插件 ZIP](https://github.com/adjoint-functor/zuihan-kanshu/releases/download/v8.3.1/zuihan-kanshu-v8.3.1.zip)，普通使用者无需从源码编译。

1. 在提供 **Plugin Creator**、允许创建和使用插件的 ChatGPT Chat 或 Work 中新建对话，输入 `@` 并选择 **Plugin Creator**。
2. 发送下面的提示词，让它取得正式插件 ZIP，将完整插件保存为你自己的私人副本。
3. 保存后，按宿主提示完成**安装／启用**；再新建对话，用 `@` 选择**瑞般观珠**并提出一个数学问题。

```text
请帮我安装第三方插件“瑞般观珠”：https://github.com/adjoint-functor/zuihan-kanshu
请先读根目录 INSTALL.md，使用正式 Release 插件 ZIP，原样导入完整插件并保留名称、版本、技能和资源，保存为我自己的私人副本。不要重新设计或改写插件；按当前宿主能力完成安装／启用，并说明实际完成到哪一步。
```

[完整安装说明（含给 GPT 的步骤）](INSTALL.md)提供工具能力排查、手动下载与插件页导入后备、已有副本更新、Codex 本地安装与源码构建方法。GitHub 的 **Code → Download ZIP** 和 Release 的 **Source code** 都是源码包，不能直接当作插件 ZIP。

## 问题 → 研究 → 写作

| 你要做的事 | 瑞般观珠提供的支持 | 详细入口 |
| --- | --- | --- |
| 解答数学问题 | 推导、证明、反例、计算核验与必要的文献依据；普通问答默认在对话中完成 | [数学问答](skill/zuihan-kanshu/references/mathematical-inquiry.md) |
| 开展持续研究 | 梳理文献、探索路线、证明与核验，保存进展并接续已有工作 | [研究工作台](skill/zuihan-kanshu/references/research-workbench.md) |
| 规划与制作文稿 | 写作计划、撰写、审阅、修订、中文翻译，以及 Markdown、TeX、PDF 制作 | [普通文稿](skill/zuihan-kanshu/references/working-draft.md) |

内置**数学研究迷你智能体**的角色与协作约定，包括探索者、证明者、做题者、独立核验者和数学编辑者，按研究需要启用。模型选择、推理强度与实际委派受宿主提供的能力和用户授权约束；具体职责见[研究角色](skill/zuihan-kanshu/references/research-roles.md)。

中文支持包括[翻译与术语](skill/zuihan-kanshu/references/chinese-translation.md)、[文风整理](skill/zuihan-kanshu/references/writing-style.md)及[成品制作](skill/zuihan-kanshu/references/final-output.md)。PDF 路径包含工具与字体检测、编译和预检；实际编译需要可用的工具链，见 [PDF 构建说明](skill/zuihan-kanshu/references/final-pdf-build-profile.md)。

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

在具备云端文件能力的宿主中，新建研究或文稿优先采用指定目录；仅要求“保存在云端”或未指定目录时，自动在云端库根目录下建立以主题命名的子目录，无需仅为目录命名再次询问。接续工作沿用已有目录。

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

感谢 [Danus](https://github.com/frenzymath/Danus/tree/6d92e8d415933ca2ef52fd1a4da73fdfcd418f1c)、[Rethlas](https://github.com/frenzymath/Rethlas/tree/e7e48a6d30e7f0ddf0ed1909a594a1f0cfe2c2b7) 与 [Bolzano（problem-solver）](https://github.com/vaclavrozhon/problem-solver/tree/ccc0f7185ef6a72b3b8f519b8efab3f386cf597f)，它们为研究协作、证明核验和失败反馈提供了设计参考。[Matlas](https://matlas.ai/docs) 提供数学检索服务与 API；[hrjtju/matlas-search](https://github.com/hrjtju/matlas-search) 为接口使用与候选文献阅读提供了参考。

这些致谢说明参考来源，不表示将上游项目整体纳入本插件，也不表示上游作者为本项目背书。具体来源、许可与使用边界见 [NOTICE](NOTICE)。

## 名称与图标

名称取意于数学术语「随伴関手」（ずいはんかんしゅ，Adjoint Functor），以其日语读音谐作「瑞般観珠」，中文写作「瑞般观珠」；技术标识为 `zuihan-kanshu`。

图标微雕保留正式 **22 条公式**，每条出现四次。其精确写法、适用条件、来源与定义／定理／猜想状态见[公式清单](docs/design/zuihan-icon/formula-catalogue.md)；源图与导出方法见[图标设计说明](docs/design/zuihan-icon/README.md)。四张透明 PNG 为：

| 尺寸 | 浅色背景 | 深色背景 |
| --- | --- | --- |
| 256 × 256 | [icon-256.png](skill/zuihan-kanshu/assets/icon-256.png) | [icon-dark-256.png](skill/zuihan-kanshu/assets/icon-dark-256.png) |
| 1024 × 1024 | [icon-1024.png](skill/zuihan-kanshu/assets/icon-1024.png) | [icon-dark-1024.png](skill/zuihan-kanshu/assets/icon-dark-1024.png) |

许可与来源说明见 [LICENSE](LICENSE) 和 [NOTICE](NOTICE)。使用问题与建议见 [SUPPORT.md](SUPPORT.md)，安全与外部数据交互说明见 [SECURITY.md](SECURITY.md)。

