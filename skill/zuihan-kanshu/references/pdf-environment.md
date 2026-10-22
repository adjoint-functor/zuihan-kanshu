# Work 云端 PDF 环境恢复

在 Work 云端开始 PDF 工作、环境被清理或依赖检查失败时使用。目录：先确认环境；按缺失项恢复；验收与日常构建；定制与故障定位。文稿排版由 `final-pdf-build-profile.md` 决定。

## 先确认实际运行环境

环境目录是可重建的缓存。持久保存文稿、控制稿中的字体／额外宏包选择和实际验收记录；清理后重新发现工具，不把上一会话的绝对路径当作环境保证。

先确认当前执行端是否确实在目标 Work 云端，并查明操作系统、架构、可写目录、可用 Python 和预装工具。本地或 CI 只提供对应环境的验证，不能代替真实 Work。

下例面向 Linux Work shell。`MATH_DOC_SKILL_DIR` 为实际技能目录；`PDF_PYTHON` 优先采用能运行的 `CODEX_PRIMARY_RUNTIME_PYTHON`，否则使用实际确认可用的 Python 3.11.8 以上解释器。先执行其 `--version`。

```bash
"$PDF_PYTHON" "$MATH_DOC_SKILL_DIR/scripts/pdf-environment.py" check
```

`check` 不下载、安装或编译；加 `--report <新路径>` 才写报告。它检查工具、Python 模块、TeX 文件和指定字体，并列出 TeX 年度／核心文件与现有中文字体。默认字体缺失不表示系统没有其他中文字体；`dependencies-found` 只表示依赖探测通过。

## 按缺失项恢复

**优先使用 Work 现有版本，通过调整本技能调用和文稿配置实现目标。** 不因工具比备用配方旧、或 Poppler 各组件版本不完全相同而重装；依据实际功能、编译与验收结果判断。

| 用途 | 需要的能力 |
|---|---|
| 正文与配置 | Python、PyYAML、Pandoc |
| 编译 | XeLaTeX、latexmk、Perl、当前文稿使用的宏包 |
| 字体 | Fontconfig、确定的中文／拉丁／数学字体、AMSFonts |
| PDF 验收 | Poppler 工具与相应 CMap 数据、Pillow、pypdf |

在当前可写、路径简短且无空格的工作目录中选择新目录：

```bash
"$PDF_PYTHON" "$MATH_DOC_SKILL_DIR/scripts/pdf-environment.py" restore \
  --prefix "$PDF_ENV_DIR"
```

默认行为：

- 复用现有 Pandoc、可导入的 Python 包和可用 TeX。只有缺失的非 TeX 组件才使用备用下载配方。
- XeLaTeX 已有而普通宏包缺失时，在本次目录的独立用户 TEXMF 树内安装已探测缺失或明确指定的包，保留共享 TeX 树和引擎。为避免发行版包数据库差异导致递归拉入另一套核心，不自动递归安装依赖；基本配方按实际文件检查所需组件，额外宏包的依赖按具体编译诊断补齐。安装后核对核心文件仍来自宿主。`tlmgr` 用户模式受可迁移包及核心依赖条件限制；失败会保留诊断，不自动转成整套下载。现有引擎缺少 latexmk 时，先补这个小组件；格式或核心不兼容时按诊断处理。
- 仓库匹配实际 TeX 年度。默认按配方中的当前或历史年度来源进行有限尝试；可用 `--tex-repository <URL>` 明确指定匹配仓库。镜像故障只处理来源问题，不借此升级其他工具。
- 中文正文、无衬线、等宽三个通道分别检查与复用。未指定时选择已有的合适候选；缺失时只下载相应的静态 Noto Serif CJK SC、Noto Sans CJK SC 或 Noto Sans Mono CJK SC 常规／粗体及许可，按通道存放。采用字体记录在 `environment.json`，仍需通过实际 PDF 验收。技能保留官方下载配方，不内置字体二进制。

已有文稿先读取其字体约定，并用 `--latin-main`、`--cjk-main`、`--cjk-sans`、`--cjk-mono`、`--math-main` 传入；明确指定的字族不会被候选替换。新文稿可根据现有字体和排版目标选择，再写入 `BUILD_PROFILE`。`--font-dir` 可重复，用于提供另行取得的字体。

只有引擎缺失、确有核心不兼容、最小扩展不可行或明确需要独立环境时，采用私有 TeX：

```bash
"$PDF_PYTHON" "$MATH_DOC_SKILL_DIR/scripts/pdf-environment.py" restore \
  --prefix "$PDF_ENV_DIR" --private-tex
```

`--private-tex` 只选择独立 TeX，仍复用其他可用组件；`--baseline-tools` 则显式选择整套私有 Pandoc／TeX／Python 包。私有 TeX 可以更新自己的包，用户树路径不对共享发行版执行更新。两种模式的 Linux 原生依赖都由宿主提供。

`assets/pdf-environment/baseline.json` 中的版本号是缺失时的备用配方，不是所有工具必须达到的版本，也不是任意数学文稿的宏包全集。`environment.json` 记录本次实际选择；`check.json`、TeX 安装／仓库日志记录检查和失败原因。重复对已成功目录调用 `restore` 只复查；旧路径失效时先重新检测，然后使用新目录恢复。失败目录保留，便于判断原因。

## 验收与日常构建

```bash
"$PDF_PYTHON" "$MATH_DOC_SKILL_DIR/scripts/pdf-environment.py" smoke \
  --config "$PDF_ENV_DIR/environment.json" --output tmp/pdf-env-smoke-01
```

样稿实际调用构建器和预检器，检查中文正文常规／粗体、无衬线常规／粗体、行内与围栏等宽中文代码、编号回引、AMS 大写黑板体、矩阵、积分、表格、中文提取、书签／内部链接及无附件，渲染全部页面。样稿要求预检零错误、零警告；最终日志中的 LaTeX／Package／Class 警告包括 xeCJK 字体族警告都应处理，不能只看进程返回码。随后打开全部页图核对字形、公式和布局。`sample-built` 表示机械检查通过，视觉检查仍需实际完成；它不能代替文稿自身或长文分页的验收。

日常构建通过所选环境运行：

```bash
"$PDF_PYTHON" "$MATH_DOC_SKILL_DIR/scripts/pdf-environment.py" check \
  --config "$PDF_ENV_DIR/environment.json" --control tmp/finished_v1.0.1.control.md
"$PDF_PYTHON" "$MATH_DOC_SKILL_DIR/scripts/pdf-environment.py" run \
  --config "$PDF_ENV_DIR/environment.json" -- \
  python "$MATH_DOC_SKILL_DIR/scripts/final-pdf-build.py" inspect \
  tmp/finished_v1.0.1.md --control tmp/finished_v1.0.1.control.md
```

将 `inspect` 换成 `final-output.md` 的完整构建或预检命令。`run` 后的 `python` 使用配置记录的解释器。预检通过 pypdf 检查必要的 PDF 对象；mutool、pdfdetach 可用于补充诊断，不因缺少它们而另外安装，解析失败和未完成的检查仍须处理。

## 定制与故障定位

- 新建环境时用 `--extra-tex-package <包名>` 补充实际需要的宏包，可重复，无需选择整套私有基线。将包名及实际需要补充的依赖记入项目控制稿；变更时仍保留字体选择。用户树只适合可迁移包，含二进制／格式等需求另作判断。
- Linux 原生依赖确实缺失时，在环境已有权限内用发行版对应包补齐。Debian／Ubuntu 常见包为 `perl`、`fontconfig`、`poppler-utils`、`poppler-data` 和 `latexmk`，只安装检查发现缺少的部分。无权限时使用平台可用能力或报告具体缺口；不要求改装个人电脑。
- 字体存在不保证正确嵌入或提取。结合编译日志、字体／文本检查和页图判断，处理具体的 CMap、可变字体或粗体问题；不静默改变已定文稿字体。
- 自动配方覆盖 Linux x86_64／aarch64；Windows 分支用于相应执行端，不定义 Work 云端。其他平台可手动准备后检查；某平台通过不代表其他平台已测。
- 记录实际位置、版本、字体、额外包及验收结果。环境变化后重查受影响部分；稳定会话内复用有效证据。目录失效模拟与平台真实清理分开记录。
