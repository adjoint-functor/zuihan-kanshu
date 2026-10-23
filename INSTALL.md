# 安装 / Installation

[中文](#中文) · [English](#english) · [项目主页 / Project home](https://github.com/adjoint-functor/zuihan-kanshu)

瑞般观珠是通过 GitHub 分发的第三方插件。安装使用以下正式发布包，无需加入官方插件目录，也无需从源码编译。 / Zuihan Kanshu is a third-party plugin distributed through GitHub. Use the release package below; an official directory listing and a source build are not required.

| 项目 / Item | 当前发布 / Current release |
| --- | --- |
| 名称 / Name | 瑞般观珠 / Zuihan Kanshu (`zuihan-kanshu`) |
| 版本 / Version | **v8.7.0** |
| 插件 ZIP / Plugin ZIP | [zuihan-kanshu-v8.7.0.zip](https://github.com/adjoint-functor/zuihan-kanshu/releases/download/v8.7.0/zuihan-kanshu-v8.7.0.zip) · **不要选 Source code / Do not choose Source code** |
| 发布页 / Release page | [v8.7.0](https://github.com/adjoint-functor/zuihan-kanshu/releases/tag/v8.7.0) |
| 校验文件 / Checksums | [SHA256SUMS](https://github.com/adjoint-functor/zuihan-kanshu/releases/download/v8.7.0/SHA256SUMS) |
| ZIP SHA-256 | `476042ac469b9b7b997e3aef221cc01bf93d1e8ffed714efdfe394d25a0f90a7` |

当前正式版为 **v8.7.0**，新增按实际对话模式判断的默认停止规则和文稿后处理入口，并保留此前的质量优先写作与语言表达指导。上表提供含全部技能和资源的完整安装包，可用于首次安装或更新既有副本。 / The current release is **v8.7.0**, adding a conversation-mode check and a manuscript-refinement entry while retaining quality-first writing and language guidance. The table provides the complete plugin package, including all skill files and assets, for first-time installation or updating an existing copy.

未指定目的地的新任务默认保存在 Library 根目录 `瑞般观珠/` 下的项目子目录，用户明确项目名优先；首次保存确认实际目录，已有项目不自动迁移。共享中文参考与项目子目录并列。 / New saved tasks without an explicit destination use a project folder under `瑞般观珠/` at the Library root, preferring an explicit project name and confirming the actual folder on the first save. Existing projects are not migrated; the shared Chinese reference sits alongside project folders.

## 中文

### 在 ChatGPT 的 Chat 或 Work 中安装

推荐在 **Work** 中使用，在云端启动、查看和接续数学工作，无需自行准备远程主机或维护服务器。本分支除了智能体分工，还有适配 Work 的轮次与串行处理规则，目前不推荐在真正的 Codex 对话中运行，未来拟提供专用分支。从 Codex 客户端启动或打开的 Work 仍按 Work 处理。v8.7.0 只在明确识别为 Codex 对话时默认停止并提醒，不以客户端名称或底层运行时名称判断。下方本地安装步骤仅说明技术操作。使用方法见[进阶使用指南](skill/zuihan-kanshu/references/usage-guide.md)；指南问答自 v8.4.0 提供，链接指向当前源码的指南。

**Chat 也可使用部分功能**：数学问答、概念讨论和简单数学写作任务。按当前官方公布的支持范围，普通 Chat 暂不能使用本插件的子智能体分工；持续研究、长篇写作和多智能体核验仍推荐 Work。依据与说明见主页[使用环境与模型](README.md#使用环境与模型)。

#### 首次安装（推荐：上传完整 ZIP）

建议先确认 **Plugin Creator 已安装并启用**，便于需要时让 GPT 协助安装或更新。若已可用，可在新对话中用 `@` 选中它；也可以直接发送下方包含安装和启用授权的提示词。

1. [下载 zuihan-kanshu-v8.7.0.zip](https://github.com/adjoint-functor/zuihan-kanshu/releases/download/v8.7.0/zuihan-kanshu-v8.7.0.zip)（**不要选 Source code，也不要用 Code → Download ZIP**），保留完整 `.zip`，无需解压。
2. 打开 ChatGPT 的**插件**页面，选择 **添加 → 上传插件压缩包**，上传这个 ZIP，按页面提示完成完整插件的导入／保存。
3. **导入／保存**与**安装／启用**是不同步骤。保存成功后，按宿主实际提供的提示完成安装／启用。
4. 再新建 Work 对话，输入 `@` 并选择**瑞般观珠**，试问：“@瑞般观珠 数学问答：请证明素数有无穷多个。”确认能选中插件并使用其技能；回答了一道数学题本身不能证明插件已安装。每次发起或接续数学任务建议选中插件并说明任务类别，关键词辅助表达，不是固定口令。

已有用户反馈首次上传安装成功；具体入口和权限因账户或客户端而异。GitHub 的 **Code → Download ZIP** 和 Release 的 **Source code** 是源码包，不是这里所需的插件包。

#### 让 GPT 协助安装（可选）

这条路线需要当前账户／工作区允许使用 **Plugin Creator** 及创建插件。下方提示词已包含安装、启用和使用 Plugin Creator 的授权；助手应先发现可用能力并推进，遇到实际权限限制或必须由用户点击的步骤时再提示。文字授权不能替代平台要求的确认操作。

1. 新建 Chat 或 Work 对话，直接发送 [README 的安装提示词](README.md#安装)。若 **Plugin Creator** 已可用，也可输入 `@` 并选中它；提示词已包含授权并指向本安装说明，下载与核验步骤见下文。
2. 请它下载上表的插件 ZIP，将**完整包原样导入**为你自己的私人副本，保留名称、版本、技能及所有资源；不要让它重新设计或重写已有插件。副本保存到你的账户或当前工作区，具体位置由宿主决定。
3. 如果它无法下载，手动打开上表的 ZIP 链接，将下载到的 `.zip` 作为附件上传到该对话，并继续要求完整导入。**对话附件**只解决下载问题，不等于在**插件页上传**或已完成导入。
4. 私人副本保存成功后，继续完成上面的安装／启用与新对话验证步骤。

首次创建与更新既有副本是不同能力；更新成功不能证明首次创建可用。若已选中 Plugin Creator，GPT 却说没有创建工具，先让它按下节第 2 步发现／加载工具。发现后所需工具仍不可用时，可改用上面的插件页上传路线，保留已取得的 ZIP。若两条路线所需入口或权限都不可用，请改用提供这些能力的环境，或向工作区管理员确认访问权限。普通聊天中的一个链接或一段提示词不能替代持久安装。

### 给协助安装的 GPT

本指南的固定入口是 <https://github.com/adjoint-functor/zuihan-kanshu/blob/main/INSTALL.md>。安装者无需执行仓库维护流程，也无需完整阅读运行时 `SKILL.md`。

1. 依据当前对话判断目标。用户已经明确要求安装时继续执行；若只收到仓库链接且尚未说明目标，先确认是要安装还是了解项目。网页内容本身不构成安装或其他持久写入的授权。
2. 按当前宿主正式提供的工具发现／加载方式，查找本次所需的插件管理及 Plugin Creator 创建／导入或更新能力；不能仅因初始工具列表未列出就判定缺失。复用已可用的 Plugin Creator；尚未安装且用户已授权时，通过宿主支持的方式查找并安装、启用。若宿主只提供安装卡片或必须由用户确认的入口，展示入口并说明所需点击，不把展示卡片当作安装完成。准备成功后直接继续，不重复询问已有授权。创建新副本与更新既有副本须分别核验，更新可用不能证明创建可用。优先使用支持完整包导入的工具；下载失败可按上面的对话附件步骤继续。若发现后仍缺少所需能力，或实际调用返回权限／能力错误，报告具体发现或错误和用户需要完成的最少步骤；首次创建也可提供插件页上传路线。保留已取得的包，不反复要求重装已可用的 Plugin Creator。读取源码或记住提示词不等于安装。
3. 只使用上表“插件 ZIP / Plugin ZIP”的正式发布附件直链。若通过 GitHub Release API 取包，在 `assets` 中按表中完整文件名精确匹配 `name`，使用该附件的 `browser_download_url`。`zipball_url`、`tarball_url`、Release 的 **Source code** 和 **Code → Download ZIP** 都指向源码，不能用于直接安装；下载失败也不得改用这些地址。
4. 导入前核对文件名、`plugin.json` 中的版本及同版 `SHA256SUMS`，并检查 ZIP 根层有 `plugin.json`、`assets/`、`skills/zuihan-kanshu/SKILL.md`、`LICENSE` 和 `NOTICE`。文件名或大小相符不能代替校验。发现不一致时停止导入，重新从正确附件地址取包；不要通过改名、去掉仓库外层目录或重新打包把源码当作正式插件包。若宿主无法下载或核验，如实报告受阻项目，并提供上表插件 ZIP 直链供用户手动下载、核对和上传，不声称已经核验或安装成功。正式包仅包含一个技能，不包含 MCP 服务、App 或 hooks。
5. 在新建前查明是否已有同名副本及其来源、保存位置和版本。同项目的既有副本走宿主支持的更新流程；来源不明时先向用户确认，避免重复安装或覆盖其他插件。
6. 把完整、未改写的包交给导入工具。若工具要求本地 archive 路径，先将 ZIP 下载到本地，再传绝对文件路径；不能把下载 URL 当作本地路径。不要只提取一份 `SKILL.md`，也不要将已有插件重新生成为简化提示词。
7. 依据宿主返回结果区分“文件已下载”“私人副本已保存”“已安装／启用”和“新对话已验证”，报告实际完成阶段、插件名称、版本和来源。安装不包括公开发布或向他人分享副本。

### 更新已有副本

GitHub 发布与已经导入的私人副本**不会自动同步**。需要更新时，使用本指南顶部“插件 ZIP / Plugin ZIP”的下载直链（**不要选 Source code**）。若在本仓库 [Releases](https://github.com/adjoint-functor/zuihan-kanshu/releases) 查找其他版本，选择该版明确列出的 `zuihan-kanshu-v<版本号>.zip` 附件，并使用同版校验文件。确认是同一来源和目标副本后，通过宿主的插件更新功能更新原副本；让 GPT 协助时，同样遵守上一节的附件选择与核验步骤。自己修改过的内容应先比较差异，再决定如何保留。更新后重新完成宿主要求的启用与新对话验证。

### 桌面环境的本地安装（技术参考）

以下说明安装位置，不决定对话模式。本分支面向 Work，客户端即使名为 Codex，也不能据此排除其中的 Work 对话；真正的 Codex 对话则受上述默认停止规则约束。安装成功不代表已适配 Codex，也不绕过运行时的入口判断。

支持本地插件 marketplace 的 Codex／ChatGPT 桌面环境，可使用同一份 Release ZIP：将**完整内容**解压到本地插件目录，再按 OpenAI 的[本地插件安装说明](https://developers.openai.com/plugins/build/plugins#install-a-local-plugin-manually)建立 repo 或 personal marketplace，并在宿主中安装／启用。比如插件放在 marketplace 根目录下的 `plugins/zuihan-kanshu/` 时，入口是 `plugins/zuihan-kanshu/plugin.json`，目录条目的 `source.path` 为 `./plugins/zuihan-kanshu`；路径相对于 marketplace 根目录。

本仓库目前是源码仓库，没有可供直接注册的 marketplace 目录，也没有根层已构建的插件。不能直接把本仓库 URL 当作 marketplace 源安装。请按目标宿主的实际文档操作；插件已包含技能，同一宿主不要再重复安装独立技能。

宿主是否提供检索、子智能体、模型参数、云端文件和编译工具，以实际环境为准；安装插件不会添加这些能力。

### 仅在需要时从源码构建

取得源码后，在仓库根目录使用可用的 Python 3；本机命令为 `python3` 时相应替换：

```sh
python tools/build_release.py --check
python tools/build_release.py --format plugin --check
python tools/build_release.py --format plugin --zip --output-dir dist
```

当前 v8.7.0 源码输出为 `dist/plugin/zuihan-kanshu-v8.7.0/` 和 `dist/plugin/zuihan-kanshu-v8.7.0.zip`。自行构建只产生文件，之后仍需安装／启用；它不改变上表正式发布的版本。

若目标宿主只接受独立技能目录：

```sh
python tools/build_release.py --format skill --output-dir dist
```

当前 v8.7.0 源码输出为 `dist/skill/zuihan-kanshu-v8.7.0/`，根层有 `SKILL.md`。按宿主技能安装说明，将其内容安装到名为 `zuihan-kanshu` 的目录，去掉构建目录名中的版本后缀。独立技能沿用相同的模式与任务范围判断。已有输出目录不会被覆盖；重复构建另选空输出目录。

### 验证范围与帮助

本指南已核对正式发布资产、版本、校验值及下列官方说明。已有用户反馈通过插件页上传完整 ZIP 完成首次安装；此为用户反馈，未逐一验证所有账户或客户端，具体入口与权限须以当前宿主为准。安装遇到问题时，先记录实际完成阶段，再参考 [SUPPORT.md](SUPPORT.md)；安全与外部数据交互说明见 [SECURITY.md](SECURITY.md)。

## English

### Install in ChatGPT Chat or Work

**Work is recommended** to start, check, and continue mathematics in the cloud without maintaining a remote machine or server of your own. Besides agent assignments, this branch includes rounds and sequential steps designed for Work. Actual Codex conversations are not currently recommended; a dedicated branch is planned. Work started or opened from a Codex client is still Work. Version v8.7.0 defaults to stopping and warning only when the current conversation is clearly identified as Codex, not from a client or runtime name. The local steps below describe installation mechanics. See the [advanced usage guide](skill/zuihan-kanshu/references/usage-guide.md), which follows the current source. Built-in guide responses have been available since v8.4.0.

**Chat also supports some features:** mathematical questions, conceptual discussions, and simple mathematical writing tasks. Based on the currently documented support, ordinary Chat cannot run this plugin's subagent assignments. Work remains recommended for sustained research, long manuscripts, and verification by multiple agents. See [Environment and models](README.en.md#environment-and-models) for the sources and explanation.

#### First installation (recommended: upload the complete ZIP)

We recommend checking that **Plugin Creator is installed and enabled**, so GPT can help with installation or updates when needed. If available, you can select it with `@` in a new conversation; you can also send the prompt below directly, which authorizes installing and enabling it.

1. [Download zuihan-kanshu-v8.7.0.zip](https://github.com/adjoint-functor/zuihan-kanshu/releases/download/v8.7.0/zuihan-kanshu-v8.7.0.zip) (**do not choose Source code or Code → Download ZIP**) and keep the complete `.zip` without extracting it.
2. Open ChatGPT's **Plugins** page, choose **Add → Upload plugin archive**, upload this ZIP, and follow the page's prompts to import/save the complete plugin.
3. **Importing/saving** and **installing/enabling** are separate stages. After saving, complete the host's installation/enabling prompts.
4. Start a new Work conversation, select **瑞般观珠** with `@`, and ask: “@瑞般观珠 Mathematical Q&A: Prove that there are infinitely many primes.” Check that the plugin can be selected and its skill used; a mathematical answer alone is not proof of installation. Select it and state the task category whenever starting or continuing mathematical work; the labels clarify intent rather than acting as required commands.

Users have reported successful first-time installation via archive upload. Controls and permissions may differ by account or client. GitHub's **Code → Download ZIP** and release **Source code** archives are not the plugin package.

#### Ask GPT to help install (optional)

This route requires your account or workspace to allow **Plugin Creator** and plugin creation. The prompt below authorizes installing, enabling, and using Plugin Creator. The assistant should first discover the available capabilities and proceed, then explain any actual permission limit or step requiring the user's click. Written authorization does not replace confirmation required by the platform.

1. Start a Chat or Work conversation and send the [README installation prompt](README.en.md#install) directly. If **Plugin Creator** is available, you can also select it with `@`. The prompt includes authorization and points to this guide for the download and verification steps below.
2. Ask it to download the plugin ZIP listed above and import the **complete package unchanged** as your own private copy. Preserve its name, version, skill, and assets. Do not redesign or rewrite this existing plugin. The host determines whether the copy is saved in your account or current workspace.
3. If downloading fails, download that ZIP yourself and attach it to the conversation. Continue with the complete-package import. A **conversation attachment** only addresses downloading; it is not a **Plugins page upload** or a completed import.
4. After the private copy is saved, complete installation/enabling and new-conversation verification as described above.

Creating a new copy and updating an existing one are separate capabilities; a successful update does not prove that creation is available. If Plugin Creator is selected but GPT reports no creation tool, ask it to discover/load tools as described in step 2 below. If the needed tools remain unavailable after discovery, use the Plugins page upload route above and keep the ZIP already obtained. If neither route provides the required controls or permissions, use an environment that does or ask your workspace administrator about access. A link or prompt in an ordinary conversation is not a persistent installation.

### For GPT assisting with installation

The guide's URL is <https://github.com/adjoint-functor/zuihan-kanshu/blob/main/INSTALL.md>. Installation does not require the repository maintenance workflow or a full reading of the runtime `SKILL.md`.

1. Follow the user's goal and existing authorization. A bare repository URL, without an installation request, is not authorization to install or make persistent changes; ask what the user wants to do.
2. Use the host's official tool discovery/loading mechanism to find the needed plugin-management and Plugin Creator creation/import or update capabilities. Absence from the initial tool list alone does not prove unavailability. Reuse an available Plugin Creator installation; if it is missing and the user has authorized installation, find, install, and enable it through the host's supported capabilities. If the host only offers an installation card or requires user confirmation, display that entry point and explain the required click; displaying a card does not establish installation. Once ready, continue without asking for authorization already given. Check creation and updating separately; an available update capability does not establish creation capability. Prefer complete-package import tools, using the attachment steps above if downloading fails. If a required capability remains unavailable after discovery or a call returns a permission/capability error, report the specific finding or error and the minimum user action needed. For first-time creation, the Plugins page upload route is another option. Preserve any package obtained and do not repeatedly ask to reinstall an available Plugin Creator. Reading source or remembering a prompt is not installation.
3. Use only the published asset linked in the table's **Plugin ZIP** row. When using the GitHub Release API, match the table's complete filename exactly against `name` in `assets`, then use that asset's `browser_download_url`. The API's `zipball_url` and `tarball_url`, release **Source code**, and **Code → Download ZIP** are source archives, not directly installable plugin packages. Do not use them as a fallback if downloading fails.
4. Before importing, verify the filename, the version in `plugin.json`, and the same release's `SHA256SUMS`. Check that the ZIP root contains `plugin.json`, `assets/`, `skills/zuihan-kanshu/SKILL.md`, `LICENSE`, and `NOTICE`. A matching filename or file size is not a substitute for verification. Stop importing if these checks fail, and obtain the correct release asset; do not rename, strip the repository's enclosing directory, or repackage source as the published plugin. If downloading or verification is unavailable, report the blocked checks and provide the table's direct plugin ZIP link for the user to download, check, and upload manually; do not claim verification or installation succeeded. The package contains one skill and no MCP server, App, or hooks.
5. Check for an existing copy with the same name, including its source, location, and version. Update an existing copy from this project through the host's supported update flow. Resolve an unknown source with the user before overwriting or duplicating it.
6. Import the complete package unchanged. If a tool requires a local archive path, download the ZIP first and pass its absolute local path, not the URL. Do not replace the package with a lone `SKILL.md` or a rewritten prompt.
7. Report the stage actually reached: downloaded, private copy saved, installed/enabled, or verified in a new conversation. Include the plugin name, version, and source. Installation does not include publishing or sharing a copy.

### Updates

Imported private copies **do not automatically sync with GitHub**. To update, use the direct link in this guide's **Plugin ZIP** row (**do not choose Source code**). If selecting another version from [Releases](https://github.com/adjoint-functor/zuihan-kanshu/releases), choose that release's explicitly listed `zuihan-kanshu-v<version>.zip` asset and its matching checksums. Confirm the source and target copy, then use the host's update feature on that copy. GPT-assisted updates follow the same asset selection and verification steps above. Compare any personal modifications before replacing them. Complete any required enabling and new-conversation verification again.

### Local installation on desktop (technical reference)

These steps describe an installation location, not the current conversation mode. This branch targets Work, including Work opened from a Codex client. Actual Codex conversations remain subject to the default stop described above. Installation does not establish Codex compatibility or bypass the runtime entry check.

For Codex or ChatGPT desktop environments supporting local plugin marketplaces, extract the **complete release ZIP** into a plugin directory and follow OpenAI's [local plugin installation instructions](https://developers.openai.com/plugins/build/plugins#install-a-local-plugin-manually). For example, a plugin at `<marketplace-root>/plugins/zuihan-kanshu/` has its manifest at `plugins/zuihan-kanshu/plugin.json` and a catalog `source.path` of `./plugins/zuihan-kanshu`, relative to the marketplace root. Complete installation/enabling in the host.

This source repository does not currently contain a directly registrable marketplace or a built plugin at its root. Do not register its URL as a marketplace source. Follow the target host's documentation. The plugin already contains the skill; avoid a duplicate standalone skill installation in the same host.

Search, delegation, model parameters, cloud files, and compilation tools depend on the host. Installing the plugin does not add these capabilities.

### Build from source only when needed

From the source repository root, use Python 3 (`python3` may be the command on your system):

```sh
python tools/build_release.py --check
python tools/build_release.py --format plugin --check
python tools/build_release.py --format plugin --zip --output-dir dist
```

The current v8.7.0 source creates `dist/plugin/zuihan-kanshu-v8.7.0/` and `dist/plugin/zuihan-kanshu-v8.7.0.zip`. Building produces files; installation/enabling is still required, and the published version in the table remains unchanged.

For a host accepting only standalone skill directories:

```sh
python tools/build_release.py --format skill --output-dir dist
```

For the current v8.7.0 source, install the contents of `dist/skill/zuihan-kanshu-v8.7.0/` into a skill directory named `zuihan-kanshu`, without the version suffix, following that host's instructions. The output contains `SKILL.md` at its root and uses the same mode and task-scope rules. Existing output directories are not overwritten; use another empty output location when rebuilding.

### Verification scope and help

The release assets, version, checksum, and official documentation below have been checked. Users have reported successful first-time installation via archive upload through the Plugins page. This is user-reported success; not every account or client has been tested. Current host controls and permissions determine availability. Record the stage reached when asking for help; see [SUPPORT.md](SUPPORT.md) and [SECURITY.md](SECURITY.md).

## 官方参考 / Official references

- [ChatGPT: Build plugins](https://learn.chatgpt.com/docs/build-plugins)
- [OpenAI Developers: Package your plugin](https://developers.openai.com/plugins/build/plugins)
