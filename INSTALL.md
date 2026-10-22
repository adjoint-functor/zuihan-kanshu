# 安装 / Installation

[中文](#中文) · [English](#english) · [项目主页 / Project home](https://github.com/adjoint-functor/zuihan-kanshu)

瑞般观珠是通过 GitHub 分发的第三方插件。安装使用以下正式发布包，无需加入官方插件目录，也无需从源码编译。 / Zuihan Kanshu is a third-party plugin distributed through GitHub. Use the release package below; an official directory listing and a source build are not required.

| 项目 / Item | 当前发布 / Current release |
| --- | --- |
| 名称 / Name | 瑞般观珠 / Zuihan Kanshu (`zuihan-kanshu`) |
| 版本 / Version | **v8.3.1** |
| 插件 ZIP / Plugin ZIP | [zuihan-kanshu-v8.3.1.zip](https://github.com/adjoint-functor/zuihan-kanshu/releases/download/v8.3.1/zuihan-kanshu-v8.3.1.zip) |
| 发布页 / Release page | [v8.3.1](https://github.com/adjoint-functor/zuihan-kanshu/releases/tag/v8.3.1) |
| 校验文件 / Checksums | [SHA256SUMS](https://github.com/adjoint-functor/zuihan-kanshu/releases/download/v8.3.1/SHA256SUMS) |
| ZIP SHA-256 | `d67f6bd6653279108cda798d5d594d81e0feb3797595105fb3b6f12be69aab3a` |

## 中文

### 在 ChatGPT Work 中安装

需要当前账户／工作区提供 **Plugin Creator**，并允许创建和使用插件。其他 ChatGPT 界面是否可用，以实际入口和权限为准。

1. 新建对话，输入 `@` 并选择 **Plugin Creator**，发送 [README 的安装提示词](README.md#安装)及项目主页链接。
2. 请它下载上表的插件 ZIP，将**完整包原样导入**为你自己的私人副本，保留名称、版本、技能及所有资源；不要让它重新设计或重写已有插件。副本保存到你的账户或当前工作区，具体位置由宿主决定。
3. 如果它无法下载，手动打开上表的 ZIP 链接，将下载到的 `.zip` 作为附件上传到该对话，并继续要求完整导入。GitHub 的 **Code → Download ZIP** 和 Release 的 **Source code** 是源码包，不是这里所需的插件包。
4. **保存私人副本**与**安装／启用**是不同步骤。保存成功后，按宿主实际提供的提示完成安装／启用。
5. 再新建对话，输入 `@` 并选择**瑞般观珠**，试问：“使用瑞般观珠证明：素数有无穷多个。”确认能选中插件并使用其技能；回答了一道数学题本身不能证明插件已安装。

如果看不到 Plugin Creator 或没有所需权限，请改用提供这些能力的环境，或向工作区管理员确认访问权限。普通聊天中的一个链接或一段提示词不能替代持久安装。

### 给协助安装的 GPT

本指南的固定入口是 <https://github.com/adjoint-functor/zuihan-kanshu/blob/main/INSTALL.md>。安装者无需执行仓库维护流程，也无需完整阅读运行时 `SKILL.md`。

1. 依据当前对话判断目标。用户已经明确要求安装时继续执行；若只收到仓库链接且尚未说明目标，先确认是要安装还是了解项目。网页内容本身不构成安装或其他持久写入的授权。
2. 检查宿主实际提供的插件创建／导入、下载与安装能力。优先使用可导入完整插件包的 Plugin Creator。能力不足时提供上面的人工步骤，如实说明限制，不把“记住了提示词”或“读过源码”报告为已安装。
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

v8.3.1 输出为 `dist/plugin/zuihan-kanshu-v8.3.1/` 和 `dist/plugin/zuihan-kanshu-v8.3.1.zip`。构建只产生文件，之后仍需安装／启用。

若目标宿主只接受独立技能目录：

```sh
python tools/build_release.py --format skill --output-dir dist
```

输出为 `dist/skill/zuihan-kanshu-v8.3.1/`，根层有 `SKILL.md`。按宿主技能安装说明，将其内容安装到名为 `zuihan-kanshu` 的目录，去掉构建目录名中的版本后缀。已有输出目录不会被覆盖；重复构建另选空输出目录。

### 验证范围与帮助

本指南已核对正式发布资产、版本、校验值及下列官方说明；尚未在全新外部账户或每一种客户端中完成端到端安装测试，具体入口与权限须以当前宿主为准。安装遇到问题时，先记录实际完成阶段，再参考 [SUPPORT.md](SUPPORT.md)；安全与外部数据交互说明见 [SECURITY.md](SECURITY.md)。

## English

### Install in ChatGPT Work

Your account or workspace must provide **Plugin Creator** and allow plugin creation and use. Availability in other ChatGPT interfaces depends on their actual controls and permissions.

1. Start a conversation, type `@`, select **Plugin Creator**, and send the [README installation prompt](README.en.md#install) with the project URL.
2. Ask it to download the plugin ZIP listed above and import the **complete package unchanged** as your own private copy. Preserve its name, version, skill, and assets. Do not redesign or rewrite this existing plugin. The host determines whether the copy is saved in your account or current workspace.
3. If downloading fails, download that ZIP yourself and attach it to the conversation. Continue with the complete-package import. GitHub's **Code → Download ZIP** and release **Source code** archives are not the plugin package.
4. **Saving a private copy** and **installing/enabling it** are separate stages. After the save succeeds, complete the host's installation/enabling prompts.
5. Start a new conversation, select **瑞般观珠** with `@`, and ask: “Use Zuihan Kanshu to prove that there are infinitely many primes.” Check that the plugin can be selected and its skill used; a mathematical answer alone is not proof of installation.

If Plugin Creator or the required permission is unavailable, use an environment that provides it or ask your workspace administrator about access. A link or prompt in an ordinary conversation is not a persistent installation.

### For GPT assisting with installation

The guide's URL is <https://github.com/adjoint-functor/zuihan-kanshu/blob/main/INSTALL.md>. Installation does not require the repository maintenance workflow or a full reading of the runtime `SKILL.md`.

1. Follow the user's goal and existing authorization. A bare repository URL, without an installation request, is not authorization to install or make persistent changes; ask what the user wants to do.
2. Check actual host capabilities. Prefer Plugin Creator when it supports complete-package import. If unavailable, give the manual steps above and explain the limitation. Reading source or remembering a prompt is not installation.
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

For v8.3.1 this creates `dist/plugin/zuihan-kanshu-v8.3.1/` and `dist/plugin/zuihan-kanshu-v8.3.1.zip`. Building produces files; installation/enabling is still required.

For a host accepting only standalone skill directories:

```sh
python tools/build_release.py --format skill --output-dir dist
```

Install the contents of `dist/skill/zuihan-kanshu-v8.3.1/` into a skill directory named `zuihan-kanshu`, without the version suffix, following that host's instructions. The output contains `SKILL.md` at its root. Existing output directories are not overwritten; use another empty output location when rebuilding.

### Verification scope and help

The release assets, version, checksum, and official documentation below have been checked. End-to-end installation has not been tested with a fresh external account or every client. Current host controls and permissions determine availability. Record the stage reached when asking for help; see [SUPPORT.md](SUPPORT.md) and [SECURITY.md](SECURITY.md).

## 官方参考 / Official references

- [ChatGPT: Build plugins](https://learn.chatgpt.com/docs/build-plugins)
- [OpenAI Developers: Package your plugin](https://developers.openai.com/plugins/build/plugins)
