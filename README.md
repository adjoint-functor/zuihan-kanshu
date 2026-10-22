# zuihan-kanshu

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="skill/zuihan-kanshu/assets/icon-dark-1024.png">
  <img src="skill/zuihan-kanshu/assets/icon-1024.png" width="256" height="256" alt="瑞般观珠：以数学微雕公式环绕的双叶图标">
</picture>

**瑞般观珠**是面向 ChatGPT 与 Codex 的数学问题解答、持续研究与写作插件。

[English](README.en.md) · [可复现示例](docs/examples/research-initialization.md) · [设计原则](docs/design-principles.md) · [版本与迁移](docs/history-and-migration.md)

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

## 取得与安装

当前源码版本为 **v8.3.0**，这是整理后的公开源码起点。预构建插件 ZIP 尚未发布，插件目录条目也尚未上架。发布后可从本仓库的 [GitHub Releases](https://github.com/adjoint-functor/zuihan-kanshu/releases) 下载插件 ZIP；目前可从源码构建。

在取得源码后，从仓库根目录运行以下命令。需要可用的 Python 3；若本机命令名为 `python3`，相应替换 `python`。

```sh
python tools/build_release.py --check
python tools/build_release.py --format plugin --check
python tools/build_release.py --format plugin --zip --output-dir dist
```

插件输出为：

- 目录：`dist/plugin/zuihan-kanshu-v8.3.0/`
- ZIP：`dist/plugin/zuihan-kanshu-v8.3.0.zip`

插件 ZIP 根层含 `plugin.json`、图标和 `skills/zuihan-kanshu/`，可交给支持该格式的宿主导入。GitHub 的 **Download ZIP 是源码 ZIP**，需要先执行构建命令，不能直接当作插件 ZIP 使用。构建不会自动安装；在宿主提供的导入或安装入口完成操作。

同一宿主优先安装插件；插件已经包含技能，请勿再重复安装独立技能。若宿主只使用独立技能目录，可构建纯技能：

```sh
python tools/build_release.py --format skill --output-dir dist
```

输出为 `dist/skill/zuihan-kanshu-v8.3.0/`，其根层包含 `SKILL.md`。按目标宿主的技能安装方式，将其内容安装到名为 `zuihan-kanshu` 的技能目录；构建产物目录上的版本后缀不属于最终安装名。两种目标来自同一份运行时源码，已有输出目录会拒绝覆盖；重复构建可另选空输出目录。

插件元数据面向 `CHAT` / `CODEX`。各宿主是否提供插件导入、外部检索、子智能体、模型参数、云端文件和编译工具，以实际环境为准；安装技能本身不会添加这些能力。

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

## 名称与图标

名称取意于数学术语「随伴関手」（ずいはんかんしゅ，Adjoint Functor），以其日语读音谐作「瑞般観珠」，中文写作「瑞般观珠」；技术标识为 `zuihan-kanshu`。

图标微雕保留正式 **22 条公式**，每条出现四次。其精确写法、适用条件、来源与定义／定理／猜想状态见[公式清单](docs/design/zuihan-icon/formula-catalogue.md)；源图与导出方法见[图标设计说明](docs/design/zuihan-icon/README.md)。四张透明 PNG 为：

| 尺寸 | 浅色背景 | 深色背景 |
| --- | --- | --- |
| 256 × 256 | [icon-256.png](skill/zuihan-kanshu/assets/icon-256.png) | [icon-dark-256.png](skill/zuihan-kanshu/assets/icon-dark-256.png) |
| 1024 × 1024 | [icon-1024.png](skill/zuihan-kanshu/assets/icon-1024.png) | [icon-dark-1024.png](skill/zuihan-kanshu/assets/icon-dark-1024.png) |

许可与来源说明见 [LICENSE](LICENSE) 和 [NOTICE](NOTICE)。使用问题与建议见 [SUPPORT.md](SUPPORT.md)，安全与外部数据交互说明见 [SECURITY.md](SECURITY.md)。
