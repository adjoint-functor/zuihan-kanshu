# zuihan-kanshu

**Zuihan Kanshu (瑞般观珠)** is a plugin primarily for ChatGPT **Work**, supporting mathematical questions, sustained research, and mathematical writing.

[中文](README.md) · [Installation](INSTALL.md#english) · [Reproducible example](docs/examples/research-initialization.md) · [Design principles](docs/design-principles.md) · [History and migration](docs/history-and-migration.md)

**Use ChatGPT Work. Take your mathematics with you; leave server maintenance behind.**

Zuihan Kanshu supports mathematical questions, research, and writing in the cloud, without a remote machine or server of your own to maintain. Pick up your mathematics during a break at work, on a business trip, or while travelling.

If Codex seems a little too enthusiastic about working continuously, and you worry that Goal Mode might exhaust your allowance before your conjecture is settled, Work may offer just the right pace. Advance one round at a time, pause at useful points, review the progress, ask questions, and help choose what comes next. Human participation remains part of the specification.

## Advanced usage guide

**[Read the full advanced usage guide](skill/zuihan-kanshu/references/usage-guide.md)** for starting and continuing research, asking about details, and planning mathematical writing. The guide is written in Chinese; you can ask the plugin to explain it in English.

**Want to use it more effectively?** Type `@` in the conversation input, select **瑞般观珠**, and ask:

```text
How can I use this plugin more effectively?
```

**Built-in guide responses have been available since v8.4.0.** You can also read the full guide through the link above. The current source and guide describe unreleased v8.6.0; the published download remains v8.4.0.

| Scenario | Suggested approach |
| --- | --- |
| Mathematical questions | Ask directly, adding relevant background and the depth you want if useful. Answers stay in the conversation and can be concise or detailed as needed. |
| Start mathematical research | Upload a Markdown or PDF brief describing your goal, existing results, and reference material. Sufficient material lets research begin directly; a broad direction can be discussed first. |
| Continue research | After reading the progress brief, say: “Following @瑞般观珠's guidelines, use your judgment and continue the next research round.” |
| Pause and ask | Say: “Pause research rounds. Following @瑞般观珠's guidelines, first answer: …” Ask about details, reassess the direction, or discuss whether the results are ready for a manuscript. |
| Mathematical writing | Give the full requirements. By default, the plugin saves a plan and discusses it with you, then proceeds across rounds after you start execution. |

## Environment and models

Compatibility with Codex has not been tested.

**Recommended main agent:** choose **GPT-6 Astra with Max** when your budget allows; **GPT-6.1 Sol with Max** is the minimum recommended choice for this plugin. Built-in sub-agent assignments already cover exploration, proof, and verification in the research module. Max is normally sufficient; **Ultra is not recommended by default**.

In preliminary rough tests, the consumption ratio of GPT-6 Astra to GPT-6.1 Sol was about **4:1**. A simplified conversion assuming roughly five times the unit consumption gives an equivalent usage ratio of about **4:5**, with Sol accounting for more than half. This is a rough reference; task assignments vary. Users have reported that **Chinese, English, and Japanese all work correctly**.

## Install

This third-party plugin is distributed through GitHub. The current release is **v8.4.0**: [download the plugin ZIP](https://github.com/adjoint-functor/zuihan-kanshu/releases/download/v8.4.0/zuihan-kanshu-v8.4.0.zip). You do not need to build from source.

### First installation (recommended: upload the complete ZIP)

1. [Download the release plugin ZIP](https://github.com/adjoint-functor/zuihan-kanshu/releases/download/v8.4.0/zuihan-kanshu-v8.4.0.zip) and keep the complete `.zip` without extracting it.
2. Open ChatGPT's **Plugins** page, choose **Add → Upload plugin archive**, upload this ZIP, and follow the page's import/save prompts.
3. Complete **installation/enabling**, then start a new conversation, select **瑞般观珠** with `@`, and ask a mathematical question.

Users have reported successful first-time installation via archive upload. Controls and permissions may differ by account or client.

### Ask GPT to help install (optional)

In ChatGPT Chat or Work with **Plugin Creator** and permission to create and use plugins, start a conversation, type `@`, select **Plugin Creator**, and send the prompt below. After the private copy is saved, complete installation/enabling and verify it in a new conversation.

```text
Help me install the third-party plugin Zuihan Kanshu (瑞般观珠): https://github.com/adjoint-functor/zuihan-kanshu
Read the root INSTALL.md first. Use the published release plugin ZIP and import the complete package unchanged, preserving its name, version, skill, and assets, as my own private copy. Do not redesign or rewrite the plugin. Complete installation/enabling using this host's available capabilities, and report the stage actually reached.
```

The [full installation guide, including instructions for GPT](INSTALL.md#english), covers Plugins page upload, GPT tool availability troubleshooting, updates, local Codex installation, and source builds. GitHub's **Code → Download ZIP** and a release's **Source code** archives contain source code, not the installable plugin.

## Questions → research → writing

| Goal | Support | Entry point |
| --- | --- | --- |
| Answer a mathematical question | Choose depth from the question, explicit requests, and reliable relevant background; retain necessary reasoning, proofs, counterexamples, and sources in the conversation | [Mathematical inquiry](skill/zuihan-kanshu/references/mathematical-inquiry.md) |
| Continue a research project | Literature, exploration, proof, verification, progress records, and session recovery | [Research workbench](skill/zuihan-kanshu/references/research-workbench.md) |
| Mathematical writing | Plan, draft, and revise, with quality as the default priority. | [Working drafts](skill/zuihan-kanshu/references/working-draft.md) |

Built-in **mathematical research mini-agent** guidance covers explorers, proof authors, bounded problem solvers, independent verifiers, and mathematical editors. Actual delegation, model selection, and reasoning settings depend on host capabilities and user authorization; see [research roles](skill/zuihan-kanshu/references/research-roles.md).

[Chinese expression and terminology guidance](skill/zuihan-kanshu/references/chinese-translation.md) applies while composing intended Chinese output, including questions, planning, research briefs, and manuscripts. Mathematical answers and discussions also use [style guidance](skill/zuihan-kanshu/references/writing-style.md) from the start. Conversation can naturally use relevant context without starting a manuscript control or review workflow. Manuscripts retain translation, revision, and [finished-document support](skill/zuihan-kanshu/references/final-output.md); PDF compilation requires the toolchain described in the [build profile](skill/zuihan-kanshu/references/final-pdf-build-profile.md).

Internal research derivation, retrieval, and verification keep their existing workflow. Chinese and style guidance apply when composing the user report, preserving its established level of detail. Chinese tasks also use a [shared personal reference](skill/zuihan-kanshu/references/shared-chinese-reference.md) for verified additions and explicit user rules across projects; it does not replace manuscript terminology tables.

## Start a task

The plugin offers these three prompts:

```text
使用瑞般观珠解答以下数学问题，并按需要给出推导、证明或文献依据。问题：……。
```

```text
使用瑞般观珠，围绕以下目标开展数学研究，将研究记录与阶段成果保存在云端。研究目标：……。
```

```text
使用瑞般观珠，根据以下要求制定数学文稿的写作计划，并保存在云端。写作要求：……。
```

They request an answer, a research project, or a writing plan, respectively. New saved tasks default to a project folder under `瑞般观珠/` at the cloud Library root. Your explicit project name takes priority; otherwise the plugin chooses a name by topic and confirms the actual folder on the first save. An explicit destination wins, and existing projects keep their folder without automatic migration. Ordinary questions and usage help do not create manuscripts or research projects by default; the shared Chinese reference is maintained separately alongside project folders.

Other hosts use their available workspace, local storage, or file delivery and report the actual location. Without persistent storage, they should explain the limitation and provide usable content in the conversation. A successful local command does not establish a cloud save. The [workbench](skill/zuihan-kanshu/references/research-workbench.md) describes its five versioned files and persistence protocol.

## Source and checks

The runtime consists of on-demand skill instructions, reference modules, and Python utilities in `skill/zuihan-kanshu/`. `tools/runtime-files.txt` is its explicit file manifest. Repository checks and packaging live in `tools/`, tests in `tests/`, and public explanations and examples in `docs/`.

```sh
python tools/validate_repo.py
python tools/run_tests.py
```

Full PDF checks need TeX, fonts, and PDF tools. Read skips in the context of the available environment; structural validation does not prove mathematical correctness. See [contributing](CONTRIBUTING.md) for change-specific verification.

## Acknowledgments

Thanks to [Danus](https://github.com/frenzymath/Danus/tree/6d92e8d415933ca2ef52fd1a4da73fdfcd418f1c), [Rethlas](https://github.com/frenzymath/Rethlas/tree/e7e48a6d30e7f0ddf0ed1909a594a1f0cfe2c2b7), and [Bolzano (problem-solver)](https://github.com/vaclavrozhon/problem-solver/tree/ccc0f7185ef6a72b3b8f519b8efab3f386cf597f) for design references on research collaboration, proof verification, and failure feedback.

We thank Terence Tao for his public advice on mathematical writing, especially [“Describe the results accurately”](https://terrytao.wordpress.com/advice-on-writing-papers/describe-the-results-accurately/) and [“Give appropriate amounts of detail”](https://terrytao.wordpress.com/advice-on-writing-papers/give-appropriate-amounts-of-detail/), which informed the guidance on accurate statements of results and appropriate levels of detail.

The complete sources for methods, tools, services, and terminology, with their roles, are collected in [NOTICE](NOTICE). These acknowledgments do not imply inclusion of entire upstream projects or their authors' endorsement; see that file for licenses and usage boundaries.

## Name, icons, and help

The name is a phonetic wordplay on Japanese 「随伴関手」 (ずいはんかんしゅ, “adjoint functor”), rendered 「瑞般観珠」 and written 「瑞般观珠」 in Chinese. The technical identifier is `zuihan-kanshu`.

The [icon catalogue](docs/design/zuihan-icon/formula-catalogue.md) records the exact **22 formulas**, their conditions, sources, and mathematical status. See the [design notes](docs/design/zuihan-icon/README.md) for reproducible exports. Transparent PNGs: [light 256](skill/zuihan-kanshu/assets/icon-256.png), [dark 256](skill/zuihan-kanshu/assets/icon-dark-256.png), [light 1024](skill/zuihan-kanshu/assets/icon-1024.png), [dark 1024](skill/zuihan-kanshu/assets/icon-dark-1024.png).

See [LICENSE](LICENSE), [NOTICE](NOTICE), [support](SUPPORT.md), and [security and external data interactions](SECURITY.md).

