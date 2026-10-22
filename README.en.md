# zuihan-kanshu

**Zuihan Kanshu (瑞般观珠)** is a plugin primarily for ChatGPT **Chat and Work**, supporting mathematical questions, sustained research, and mathematical writing.

[中文](README.md) · [Installation](INSTALL.md#english) · [Reproducible example](docs/examples/research-initialization.md) · [Design principles](docs/design-principles.md) · [History and migration](docs/history-and-migration.md)

## Install

This third-party plugin is distributed through GitHub. The current release is **v8.3.1**: [download the plugin ZIP](https://github.com/adjoint-functor/zuihan-kanshu/releases/download/v8.3.1/zuihan-kanshu-v8.3.1.zip). You do not need to build from source.

1. In ChatGPT Work with **Plugin Creator** and permission to create and use plugins, start a conversation, type `@`, and select **Plugin Creator**.
2. Send the prompt below to obtain the release ZIP and save the complete plugin as your own private copy.
3. After saving, follow the host's **install/enable** prompts. Start another conversation, select **瑞般观珠** with `@`, and ask a mathematical question.

```text
Help me install the third-party plugin Zuihan Kanshu (瑞般观珠): https://github.com/adjoint-functor/zuihan-kanshu
Read the root INSTALL.md first. Use the published release plugin ZIP and import the complete package unchanged, preserving its name, version, skill, and assets, as my own private copy. Do not redesign or rewrite the plugin. Complete installation/enabling using this host's available capabilities, and report the stage actually reached.
```

The [full installation guide, including instructions for GPT](INSTALL.md#english), covers manual download, updates, local Codex installation, and source builds. GitHub's **Code → Download ZIP** and a release's **Source code** archives contain source code, not the installable plugin.

## Questions → research → writing

| Goal | Support | Entry point |
| --- | --- | --- |
| Answer a mathematical question | Derivations, proofs, counterexamples, computational checks, and relevant literature | [Mathematical inquiry](skill/zuihan-kanshu/references/mathematical-inquiry.md) |
| Continue a research project | Literature, exploration, proof, verification, progress records, and session recovery | [Research workbench](skill/zuihan-kanshu/references/research-workbench.md) |
| Plan and produce a manuscript | Planning, drafting, review, revision, Chinese translation, Markdown, TeX, and PDF | [Working drafts](skill/zuihan-kanshu/references/working-draft.md) |

Built-in **mathematical research mini-agent** guidance covers explorers, proof authors, bounded problem solvers, independent verifiers, and mathematical editors. Actual delegation, model selection, and reasoning settings depend on host capabilities and user authorization; see [research roles](skill/zuihan-kanshu/references/research-roles.md).

Additional modules support [Chinese translation and terminology](skill/zuihan-kanshu/references/chinese-translation.md), [writing style](skill/zuihan-kanshu/references/writing-style.md), and [finished documents](skill/zuihan-kanshu/references/final-output.md). PDF compilation requires an available toolchain; the [build profile](skill/zuihan-kanshu/references/final-pdf-build-profile.md) covers compilation and preflight checks.

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

They request an answer, a cloud-saved research project, or a cloud-saved writing plan, respectively. In hosts with cloud file capabilities, a new task uses the requested folder or creates a topic-named subfolder at the cloud library root without asking only for a folder name. Existing tasks keep their established folder.

Other hosts use their available workspace, local storage, or file delivery and report the actual location. Without persistent storage, they should explain the limitation and provide usable content in the conversation. A successful local command does not establish a cloud save. The [workbench](skill/zuihan-kanshu/references/research-workbench.md) describes its five versioned files and persistence protocol.

## Source and checks

The runtime consists of on-demand skill instructions, reference modules, and Python utilities in `skill/zuihan-kanshu/`. `tools/runtime-files.txt` is its explicit file manifest. Repository checks and packaging live in `tools/`, tests in `tests/`, and public explanations and examples in `docs/`.

```sh
python tools/validate_repo.py
python tools/run_tests.py
```

Full PDF checks need TeX, fonts, and PDF tools. Read skips in the context of the available environment; structural validation does not prove mathematical correctness. See [contributing](CONTRIBUTING.md) for change-specific verification.

## Acknowledgments

Thanks to [Danus](https://github.com/frenzymath/Danus/tree/6d92e8d415933ca2ef52fd1a4da73fdfcd418f1c), [Rethlas](https://github.com/frenzymath/Rethlas/tree/e7e48a6d30e7f0ddf0ed1909a594a1f0cfe2c2b7), and [Bolzano (problem-solver)](https://github.com/vaclavrozhon/problem-solver/tree/ccc0f7185ef6a72b3b8f519b8efab3f386cf597f) for design references on research collaboration, proof verification, and failure feedback. [Matlas](https://matlas.ai/docs) provides mathematical search services and APIs; [hrjtju/matlas-search](https://github.com/hrjtju/matlas-search) provided references for API use and reading candidate literature.

These acknowledgments identify references, not the inclusion of entire upstream projects or their authors' endorsement. See [NOTICE](NOTICE) for provenance, licenses, and usage boundaries.

## Name, icons, and help

The name is a phonetic wordplay on Japanese 「随伴関手」 (ずいはんかんしゅ, “adjoint functor”), rendered 「瑞般観珠」 and written 「瑞般观珠」 in Chinese. The technical identifier is `zuihan-kanshu`.

The [icon catalogue](docs/design/zuihan-icon/formula-catalogue.md) records the exact **22 formulas**, their conditions, sources, and mathematical status. See the [design notes](docs/design/zuihan-icon/README.md) for reproducible exports. Transparent PNGs: [light 256](skill/zuihan-kanshu/assets/icon-256.png), [dark 256](skill/zuihan-kanshu/assets/icon-dark-256.png), [light 1024](skill/zuihan-kanshu/assets/icon-1024.png), [dark 1024](skill/zuihan-kanshu/assets/icon-dark-1024.png).

See [LICENSE](LICENSE), [NOTICE](NOTICE), [support](SUPPORT.md), and [security and external data interactions](SECURITY.md).

