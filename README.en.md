# zuihan-kanshu

**Zuihan Kanshu (瑞般观珠)** is a plugin primarily for ChatGPT **Work**, supporting mathematical questions, sustained research, and mathematical writing.

[中文](README.md) · [Installation](INSTALL.md#english) · [Reproducible example](docs/examples/research-initialization.md) · [Design principles](docs/design-principles.md) · [History and migration](docs/history-and-migration.md)

**Use ChatGPT Work. Take your mathematics with you; leave server maintenance behind.**

**Whenever you start or continue a mathematical task, select 瑞般观珠 with `@` and state the intent: “Mathematical Q&A,” “Mathematical research,” or “Mathematical writing.”** These labels help clarify your goal; the plugin still understands natural requests without fixed keywords, in Chinese, English, or Japanese.

Zuihan Kanshu supports mathematical questions, research, and writing in the cloud, without a remote machine or server of your own to maintain. Pick up your mathematics during a break at work, on a business trip, or while travelling.

If Codex seems a little too enthusiastic about working continuously, and you worry that Goal Mode might exhaust your allowance before your conjecture is settled, Work may offer just the right pace. Advance one round at a time, pause at useful points, review the progress, ask questions, and help choose what comes next. Human participation remains part of the specification.

When you need to step away, put **Dot on the editorial night shift**: whenever it sees that the current round's task is complete, have it send `@瑞般观珠 Mathematical writing: Following the plugin's guidelines and the specified plan, proceed with the next round.` to the specified **Work conversation**, and let Work moonlight as Codex. Label a research task “Mathematical research” instead. You can also ask Dot to read and follow the plan or limit how many rounds it advances.

[Official Dot tasks and memory documentation](https://learn.chatgpt.com/docs/dots/tasks-and-memory) · [Controls](https://learn.chatgpt.com/docs/dots/controls)

First confirm that Dot can access and continue the specified task; capabilities depend on the official documentation and what is actually available. A user reports completing a **200-page set of lecture notes** by starting the work in one step and letting it advance through the plan this way. **Continuous work can still exhaust your allowance, especially on open-ended research; agree on a round limit and stopping conditions first.**

## Advanced usage guide

**[Read the full advanced usage guide](skill/zuihan-kanshu/references/usage-guide.md)** for starting and continuing research, asking about details, planning mathematical writing, and refining existing manuscripts. The guide is written in Chinese; you can ask the plugin to explain it in English.

**Want to use it more effectively?** Type `@` in the conversation input, select **瑞般观珠**, and ask:

```text
@瑞般观珠 How can I use this plugin more effectively?
```

**Built-in guide responses have been available since v8.4.0.** The current release, **v8.7.0**, includes the conversation-mode check and manuscript-refinement entry. See the installation section for the download.

| Scenario | Suggested approach |
| --- | --- |
| Mathematical questions | Ask directly, adding relevant background and the depth you want if useful. Answers stay in the conversation and can be concise or detailed as needed. |
| Start mathematical research | Upload a Markdown or PDF brief describing your goal, existing results, and reference material. Sufficient material lets research begin directly; a broad direction can be discussed first. |
| Continue research | After reading the progress brief, say: “@瑞般观珠 Mathematical research: Follow the plugin's guidelines, use your judgment, and continue the next research round.” |
| Pause and ask | Say: “@瑞般观珠 Mathematical Q&A: Pause research rounds and first answer: …” Ask about details, reassess the direction, or discuss whether the results are ready for a manuscript. |
| Mathematical writing | Give the full requirements. By default, the plugin saves a plan and discusses it with you, then proceeds across rounds after you start execution. |
| Refine an existing manuscript | Identify the manuscript and the presentation or organization you want improved. The plugin proposes a plan for approval, then reviews the whole text, any appropriate introduction, and the language. This is part of mathematical writing. |

```text
@瑞般观珠 Mathematical writing task: Please polish the manuscript “...”. Its readers are ..., and I would like you to focus on ... .
```

Manuscript polishing improves structure and expression so existing mathematical content is clearer and easier to follow. You can request mathematical revisions, such as completing a proof or adjusting a conclusion, separately. If such issues arise during polishing, the plugin will discuss them with you first.

## Environment and models

**This branch targets Work; running it in an actual Codex conversation is not currently recommended.** Besides agent assignments, it includes Work-specific rounds and sequential steps: discuss the plan, draft according to dependencies, then complete the whole-manuscript and language reviews. A Codex-compatible branch is planned for the future.

**Save the plan so the next round has a clear starting point.** Codex reads applicable `AGENTS.md` project instructions before beginning work. For ongoing tasks, Zuihan Kanshu maintains changing task records: a separate `.control.md` for writing, and the continuation entry and other workbench files for research. These preserve the goal and main thread, current plan, progress, open decisions, and next steps; the assistant reports important arrangements in the conversation.

Whether you simply say “continue” or use Dot to coordinate further rounds, the assistant has a record to consult and should reassess the plan against current progress. This helps reduce forgotten agreements, duplicated work, and mechanical pursuit of stale tasks. **Persistent planning is an important part of this plugin's design and a general method. This branch's Work-oriented execution rhythm and its Codex compatibility are separate considerations.** See the [design principles](docs/design-principles.md).

The distinction is the **current conversation mode**. A Work conversation started or opened from a Codex client is still Work. The plugin defaults to stopping and warning when the conversation is clearly identified as Codex. A client name, a model's generic identity, or a Codex runtime label alone is insufficient. This is a skill-level execution rule, not a platform-enforced disable switch.

**Recommended main agent:** choose **GPT-6 Astra with Max** when your budget allows; **GPT-6.1 Sol with Max** is the minimum recommended choice for this plugin. Built-in sub-agent assignments already cover exploration, proof, and verification in the research module. Max is normally sufficient; **Ultra is not recommended by default**.

In preliminary rough tests, the consumption ratio of GPT-6 Astra to GPT-6.1 Sol was about **4:1**. A simplified conversion assuming roughly five times the unit consumption gives an equivalent usage ratio of about **4:5**, with Sol accounting for more than half. This is a rough reference; task assignments vary. Users have reported that **Chinese, English, and Japanese all work correctly**.

## Install

This third-party plugin is distributed through GitHub. The current release is **v8.7.0**: [download zuihan-kanshu-v8.7.0.zip](https://github.com/adjoint-functor/zuihan-kanshu/releases/download/v8.7.0/zuihan-kanshu-v8.7.0.zip) (**do not choose Source code or Code → Download ZIP**) · [SHA256SUMS](https://github.com/adjoint-functor/zuihan-kanshu/releases/download/v8.7.0/SHA256SUMS). You do not need to build from source.

We recommend checking that **Plugin Creator is installed and enabled**, so GPT can help with installation or updates when needed. If available, you can select it with `@` in a new conversation; you can also send the prompt below directly, which authorizes installing and enabling it.

### First installation (recommended: upload the complete ZIP)

1. [Download zuihan-kanshu-v8.7.0.zip](https://github.com/adjoint-functor/zuihan-kanshu/releases/download/v8.7.0/zuihan-kanshu-v8.7.0.zip) (**do not choose Source code**) and keep the complete `.zip` without extracting it.
2. Open ChatGPT's **Plugins** page, choose **Add → Upload plugin archive**, upload this ZIP, and follow the page's import/save prompts.
3. Complete **installation/enabling**, then start a new Work conversation, select **瑞般观珠** with `@`, and ask, for example: “@瑞般观珠 Mathematical Q&A: Prove that there are infinitely many primes.”

Users have reported successful first-time installation via archive upload. Controls and permissions may differ by account or client.

### Ask GPT to help install (optional)

Start a new ChatGPT Chat or Work conversation and send the prompt below directly. If **Plugin Creator** is available, you can also select it with `@` to make the intended plugin explicit. The prompt authorizes preparing Plugin Creator; the assistant should check available capabilities first and explain any required clicks or permission limits when encountered. After the private copy is saved, complete installation/enabling and verify it in a new conversation.

```text
Help me install the third-party plugin Zuihan Kanshu (瑞般观珠), following the instructions at:
https://github.com/adjoint-functor/zuihan-kanshu/blob/main/INSTALL.md

I authorize you to enable and use Plugin Creator and, if it is not installed, to install it through this host's supported capabilities. First discover and load the available plugin-management and Plugin Creator tools. Reuse an available installation and proceed within this authorization without asking for it again. When preparing Plugin Creator, ask me to intervene only if permissions are insufficient, the required capability is unavailable, or a step requires my click; explain the specific blocker and action needed.
```

The [full installation guide, including instructions for GPT](INSTALL.md#english), covers Plugins page upload, GPT tool availability troubleshooting, updates, local installation as a technical reference, and source builds. GitHub's **Code → Download ZIP** and a release's **Source code** archives contain source code, not the installable plugin.

## Questions → research → writing

| Goal | Support | Entry point |
| --- | --- | --- |
| Answer a mathematical question | Choose depth from the question, explicit requests, and reliable relevant background; retain necessary reasoning, proofs, counterexamples, and sources in the conversation | [Mathematical inquiry](skill/zuihan-kanshu/references/mathematical-inquiry.md) |
| Continue a research project | Literature, exploration, proof, verification, progress records, and session recovery | [Research workbench](skill/zuihan-kanshu/references/research-workbench.md) |
| Mathematical writing | Plan, draft, revise, and refine existing manuscripts, with quality as the default priority. | [Working drafts](skill/zuihan-kanshu/references/working-draft.md) · [Manuscript refinement](skill/zuihan-kanshu/references/manuscript-refinement.md) |

Built-in **mathematical research mini-agent** guidance covers explorers, proof authors, bounded problem solvers, independent verifiers, and mathematical editors. Actual delegation, model selection, and reasoning settings depend on host capabilities and user authorization; see [research roles](skill/zuihan-kanshu/references/research-roles.md).

[Language and writing guidance](skill/zuihan-kanshu/references/writing-style.md) supports clear, accurate mathematical conversation, answers, new drafts, and revisions from composition, in the task's language. Conversation naturally uses relevant context, manuscripts retain applicable planning and independent reviews, and research reports keep their established level of detail.

[Chinese guidance](skill/zuihan-kanshu/references/chinese-translation.md) improves Chinese expression. Explicitly adopted Chinese translation preferences are recorded accurately and applied within their scope; see the [usage guide](skill/zuihan-kanshu/references/usage-guide.md) for details.

[Document preparation and delivery](skill/zuihan-kanshu/references/final-output.md) separately provides Markdown, PDF, and optional TeX. Actual compilation and checks need the toolchain described in the [build profile](skill/zuihan-kanshu/references/final-pdf-build-profile.md).

## Start a task

Use these prompts, or describe the same goals in your own words:

```text
@瑞般观珠 Mathematical Q&A: Please answer ..., with derivations, proofs, or references as needed.
```

```text
@瑞般观珠 Mathematical research: Please investigate ..., saving research records and intermediate results in the cloud.
```

```text
@瑞般观珠 Mathematical writing task: Please write a manuscript with the following requirements: ... .
```

Writing begins with a saved plan and discussion by default; drafting starts after approval. Here, `@瑞般观珠` means actually selecting the plugin in the composer; pasting its name alone is not the same action. New saved tasks default to a project folder under `瑞般观珠/` at the cloud Library root. Your explicit project name takes priority; otherwise the plugin chooses a name by topic and confirms the actual folder on the first save. An explicit destination wins, and existing projects keep their folder without automatic migration. Ordinary questions and usage help do not create manuscripts or research projects by default.

Once the entry's mode check permits the task, saving uses the available cloud, local, or workspace capabilities and reports the actual location. A storage fallback does not override the default stop in Codex conversations. A successful local command does not establish a cloud save. The [workbench](skill/zuihan-kanshu/references/research-workbench.md) describes its five versioned files and persistence protocol.

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

