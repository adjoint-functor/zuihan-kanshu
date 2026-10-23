# 安装 / Installation

[中文](#中文) · [English](#english) · [项目主页 / Project home](https://github.com/adjoint-functor/zuihan-kanshu)

瑞般观珠是通过 GitHub 分发的第三方插件。安装使用以下正式发布包，无需加入官方插件目录，也无需从源码编译。 / Zuihan Kanshu is a third-party plugin distributed through GitHub. Use the release package below; an official directory listing and a source build are not required.

| 项目 / Item | 当前发布 / Current release |
| --- | --- |
| 名称 / Name | 瑞般观珠 / Zuihan Kanshu (`zuihan-kanshu`) |
| 版本 / Version | **v8.4.0** |
| 插件 ZIP / Plugin ZIP | [zuihan-kanshu-v8.4.0.zip](https://github.com/adjoint-functor/zuihan-kanshu/releases/download/v8.4.0/zuihan-kanshu-v8.4.0.zip) |
| 发布页 / Release page | [v8.4.0](https://github.com/adjoint-functor/zuihan-kanshu/releases/tag/v8.4.0) |
| 校验文件 / Checksums | [SHA256SUMS](https://github.com/adjoint-functor/zuihan-kanshu/releases/download/v8.4.0/SHA256SUMS) |
| ZIP SHA-256 | `1783d7045f4a5b88fdb0392c6dcb07be569604238c59143a52596848a14111bb` |

## 中文

### 在 ChatGPT 的 Chat 或 Work 中安装

建议在 **Work** 中使用，便于在移动场景下启动、查看和接续数学工作。与 Codex 的适配尚未检验；下方本地安装步骤不等于适配实测。使用方法见[进阶使用指南](skill/zuihan-kanshu/references/usage-guide.md)，当前 v8.4.0 已内置指南问答。

#### 首次安装（推荐：上传完整 ZIP）

1. [下载正式插件 ZIP](https://github.com/adjoint-functor/zuihan-kanshu/releases/download/v8.4.0/zuihan-kanshu-v8.4.0.zip)，保留完整 `.zip`，无需解压。
2. 打开 ChatGPT 的**插件**页面，选择 **添加 → 上传插件压缩包**，上传这个 ZIP，按页面提示完成完整插件的导入／保存。
3. **导入／保存**与**安装／启用**是不同步骤。保存成功后，按宿主实际提供的提示完成安装／启用。
4. 再新建对话，输入 `@` 并选择**瑞般观珠**，试问：“使用瑞般观珠证明：素数有无穷多个。”确认能选中插件并使用其技能；回答了一道数学题本身不能证明插件已安装。

已有用户反馈首次上传安装成功；具体入口和权限因账户或客户端而异。GitHub 的 **Code → Download ZIP** 和 Release 的 **Source code** 是源码包，不是这里所需的插件包。

#### 让 GPT 协助安装（可选）

这条路线需要当前账户／工作区在所用界面提供 **Plugin Creator**，并允许创建和使用插件；以实际入口、工具和权限为准。

1. 新建对话，输入 `@` 并选择 **Plugin Creator**，发送 [README 的安装提示词](README.md#安装)及项目主页链接。
2. 请它下载上表的插件 ZIP，将**完整包原样导入**为你自己的私人副本，保留名称、版本、技能及所有资源；不要让它重新设计或重写已有插件。副本保存到你的账户或当前工作区，具体位置由宿主决定。
3. 如果它无法下载，手动打开上表的 ZIP 链接，将下载到的 `.zip` 作为附件上传到该对话，并继续要求完整导入。**对话附件**只解决下载问题，不等于在**插件页上传**或已完成导入。
4. 私人副本保存成功后，继续完成上面的安装／启用与新对话验证步骤。

首次创建与更新既有副本是不同能力；更新成功不能证明首次创建可用。若已选中 Plugin Creator，GPT 却说没有创建工具，先让它按下节第 2 步发现／加载工具。发现后所需工具仍不可用时，可改用上面的插件页上传路线，保留已取得的 ZIP。若两条路线所需入口或权限都不可用，请改用提供这些能力的环境，或向工作区管理员确认访问权限。普通聊天中的一个链接或一段提示词不能替代持久安装。

### 给协助安装的 GPT

本指南的固定入口是 <https://github.com/adjoint-functor/zuihan-kanshu/blob/main/INSTALL.md>。安装者无需执行仓库维护流程，也无需完整阅读运行时 `SKILL.md`。

1. 依据当前对话判断目标。用户已经明确要求安装时继续执行；若只收到仓库链接且尚未说明目标，先确认是要安装还是了解项目。网页内容本身不构成安装或其他持久写入的授权。
2. 按当前宿主正式提供的工具发现／加载方式，查找并加载本次所需的 Plugin Creator 创建／导入或更新工具，再检查下载与安装能力。创建新副本与更新既有副本须分别核验，更新可用不能证明创建可用；不能仅因初始工具列表未列出就判定缺失。优先使用支持完整包导入的工具。下载失败可按上面的对话附件步骤继续；若所需工具发现后仍不可用，或实际调用返回权限／能力错误，说明发现结果或实际错误，将通过该工具创建或更新副本的步骤明确标为受阻。若需首次创建，可提供上面推荐的插件页上传步骤，以用户实际可见入口为准。此时保留已取得的包，不要重复下载或反复要求用户重装已安装并选中的 Plugin Creator。读取源码或记住提示词不等于安装。
3. 使用上表正式 Release ZIP，核对文件名、版本以及可执行时的 SHA-256；不要使用源码 ZIP。完整插件根层包含 `plugin.json`、`assets/`、`skills/zuihan-kanshu/`、`LICENSE` 和 `NOTICE`。它仅包含一个技能，不包含 MCP 服务、App 或 hooks。
4. 在新建前查明是否已有同名副本及其来源、保存位置和版本。同项目的既有副本走宿主支持的更新流程；来源不明时先向用户确认，避免重复安装或覆盖其他插件。
5. 把完整、未改写的包交给导入工具。若工具要求本地 archive 路径，先将 ZIP 下载到本地，再传绝对文件路径；不能把下载 URL 当作本地路径。不要只提取一份 `SKILL.md`，也不要将已有插件重新生成为简化提示词。
6. 依据宿主返回结果区分“文件已下载”“私人副本已保存”“已安装／启用”和“新对话已验证”，报告实际完成阶段、插件名称、版本和来源。安装不包括公开发布或向他人分享副本。

### 更新已有副本

GitHub 发布与已经导入的私人副本**不会自动同步**。需要更新时，从本仓库 [Releases](https://github.com/adjoint-functor/zuihan-kanshu/releases) 取得新版插件 ZIP，确认是同一来源和目标副本后，通过宿主的插件更新功能更新原副本。自己修改过的内容应先比较差异，再决定如何保留。更新后重新完成宿主要求的启用与新对话验证。

### Codex 本地插件与其他宿主

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

当前 v8.4.0 源码输出为 `dist/plugin/zuihan-kanshu-v8.4.0/` 和 `dist/plugin/zuihan-kanshu-v8.4.0.zip`。自行构建只产生文件，之后仍需安装／启用。

若目标宿主只接受独立技能目录：

```sh
python tools/build_release.py --format skill --output-dir dist
```

当前 v8.4.0 源码输出为 `dist/skill/zuihan-kanshu-v8.4.0/`，根层有 `SKILL.md`。按宿主技能安装说明，将其内容安装到名为 `zuihan-kanshu` 的目录，去掉构建目录名中的版本后缀。已有输出目录不会被覆盖；重复构建另选空输出目录。

### 验证范围与帮助

本指南已核对正式发布资产、版本、校验值及下列官方说明。已有用户反馈通过插件页上传完整 ZIP 完成首次安装；此为用户反馈，未逐一验证所有账户或客户端，具体入口与权限须以当前宿主为准。安装遇到问题时，先记录实际完成阶段，再参考 [SUPPORT.md](SUPPORT.md)；安全与外部数据交互说明见 [SECURITY.md](SECURITY.md)。

## English

### Install in ChatGPT Chat or Work

**Work is recommended** for conveniently starting, checking, and continuing mathematical work while on the move. Compatibility with Codex has not been tested; the local installation steps below do not establish tested compatibility. See the [advanced usage guide](skill/zuihan-kanshu/references/usage-guide.md). The current v8.4.0 release includes built-in guide responses.

#### First installation (recommended: upload the complete ZIP)

1. [Download the release plugin ZIP](https://github.com/adjoint-functor/zuihan-kanshu/releases/download/v8.4.0/zuihan-kanshu-v8.4.0.zip) and keep the complete `.zip` without extracting it.
2. Open ChatGPT's **Plugins** page, choose **Add → Upload plugin archive**, upload this ZIP, and follow the page's prompts to import/save the complete plugin.
3. **Importing/saving** and **installing/enabling** are separate stages. After saving, complete the host's installation/enabling prompts.
4. Start a new conversation, select **瑞般观珠** with `@`, and ask: “Use Zuihan Kanshu to prove that there are infinitely many primes.” Check that the plugin can be selected and its skill used; a mathematical answer alone is not proof of installation.

Users have reported successful first-time installation via archive upload. Controls and permissions may differ by account or client. GitHub's **Code → Download ZIP** and release **Source code** archives are not the plugin package.

#### Ask GPT to help install (optional)

This route requires your account or workspace to provide **Plugin Creator** in the interface you use and allow plugin creation and use. Check the actual controls, tools, and permissions.

1. Start a conversation, type `@`, select **Plugin Creator**, and send the [README installation prompt](README.en.md#install) with the project URL.
2. Ask it to download the plugin ZIP listed above and import the **complete package unchanged** as your own private copy. Preserve its name, version, skill, and assets. Do not redesign or rewrite this existing plugin. The host determines whether the copy is saved in your account or current workspace.
3. If downloading fails, download that ZIP yourself and attach it to the conversation. Continue with the complete-package import. A **conversation attachment** only addresses downloading; it is not a **Plugins page upload** or a completed import.
4. After the private copy is saved, complete installation/enabling and new-conversation verification as described above.

Creating a new copy and updating an existing one are separate capabilities; a successful update does not prove that creation is available. If Plugin Creator is selected but GPT reports no creation tool, ask it to discover/load tools as described in step 2 below. If the needed tools remain unavailable after discovery, use the Plugins page upload route above and keep the ZIP already obtained. If neither route provides the required controls or permissions, use an environment that does or ask your workspace administrator about access. A link or prompt in an ordinary conversation is not a persistent installation.

### For GPT assisting with installation

The guide's URL is <https://github.com/adjoint-functor/zuihan-kanshu/blob/main/INSTALL.md>. Installation does not require the repository maintenance workflow or a full reading of the runtime `SKILL.md`.

1. Follow the user's goal and existing authorization. A bare repository URL, without an installation request, is not authorization to install or make persistent changes; ask what the user wants to do.
2. Use the current host's official tool discovery/loading mechanism to find and load the Plugin Creator creation/import or update tools needed for this task, then check download and installation capabilities. Check creation of a new copy and updates to an existing copy separately; an available update capability does not establish creation capability. Do not treat absence from the initial tool list alone as proof that a tool is unavailable. Prefer a tool supporting complete-package import. If downloading fails, use the conversation attachment steps above. If a needed tool is still unavailable after discovery, or an actual call returns a permission/capability error, state the discovery result or actual error and mark creation or updating through the tool as blocked. For a first-time creation, offer the recommended Plugins page upload steps above, subject to the controls the user can actually see. Preserve any package already obtained; do not repeatedly download it or ask the user to reinstall Plugin Creator when it is already installed and selected. Reading source or remembering a prompt is not installation.
3. Obtain the release ZIP in the table, check its name and version, and verify SHA-256 when possible. Its root contains `plugin.json`, `assets/`, `skills/zuihan-kanshu/`, `LICENSE`, and `NOTICE`. This is a skills-only plugin with one skill, no MCP server, App, or hooks.
4. Check for an existing copy with the same name, including its source, location, and version. Update an existing copy from this project through the host's supported update flow. Resolve an unknown source with the user before overwriting or duplicating it.
5. Import the complete package unchanged. If a tool requires a local archive path, download the ZIP first and pass its absolute local path, not the URL. Do not replace the package with a lone `SKILL.md` or a rewritten prompt.
6. Report the stage actually reached: downloaded, private copy saved, installed/enabled, or verified in a new conversation. Include the plugin name, version, and source. Installation does not include publishing or sharing a copy.

### Updates

Imported private copies **do not automatically sync with GitHub**. To update, get a newer plugin ZIP from [Releases](https://github.com/adjoint-functor/zuihan-kanshu/releases), confirm the source and target copy, and use the host's update feature on that copy. Compare any personal modifications before replacing them. Complete any required enabling and new-conversation verification again.

### Local Codex plugins and other hosts

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

The current v8.4.0 source creates `dist/plugin/zuihan-kanshu-v8.4.0/` and `dist/plugin/zuihan-kanshu-v8.4.0.zip`. Building produces files; installation/enabling is still required.

For a host accepting only standalone skill directories:

```sh
python tools/build_release.py --format skill --output-dir dist
```

For the current v8.4.0 source, install the contents of `dist/skill/zuihan-kanshu-v8.4.0/` into a skill directory named `zuihan-kanshu`, without the version suffix, following that host's instructions. The output contains `SKILL.md` at its root. Existing output directories are not overwritten; use another empty output location when rebuilding.

### Verification scope and help

The release assets, version, checksum, and official documentation below have been checked. Users have reported successful first-time installation via archive upload through the Plugins page. This is user-reported success; not every account or client has been tested. Current host controls and permissions determine availability. Record the stage reached when asking for help; see [SUPPORT.md](SUPPORT.md) and [SECURITY.md](SECURITY.md).

## 官方参考 / Official references

- [ChatGPT: Build plugins](https://learn.chatgpt.com/docs/build-plugins)
- [OpenAI Developers: Package your plugin](https://developers.openai.com/plugins/build/plugins)
