# 成品 PDF 构建配置

## 目录

- [支持范围与输入](#支持范围与输入)
- [配置位置与结构](#配置位置与结构)
- [字段约束](#字段约束)
- [空心字体契约](#空心字体契约)
- [构建](#构建)

## 支持范围与输入

本构建器支持一个当前正文 Markdown、一个独立控制稿，以及声明的本地资源；不是多 Markdown 文件交叉引用或原生 TeX 工程的通用构建器。混合输入的判断与整理、来源保存及版本流程见 `working-draft.md`；成品排版和检查见 `final-output.md`。正文现有 metadata 和数学宏继续作为输入，控制稿的自由说明不参与排版。

## 配置位置与结构

独立控制稿的“来源与构建”中包含且只包含一个构建配置块，必须通过 `--control` 指定。构建器只解析该块，不把整篇控制稿、计划或历史作为正文；正文中同时存在配置时拒绝歧义。块的规范结构如下；尖括号值必须替换为实际使用的内容。

~~~markdown
- PDF 构建配置如下。

<!-- BEGIN:BUILD_PROFILE -->
```yaml
build_profile:
  schema: final-pdf-build/v1
  profile: zh-math-xelatex/v1
  engine: xelatex
  fonts:
    latin_main: <Latin text font family>
    cjk_main: <CJK text font family>
    cjk_sans: <CJK sans-serif font family>
    cjk_mono: <CJK monospace font family>
    math_main: <OpenType math font family>
  layout:
    paper: a4
    margins:
      top: 25mm
      right: 25mm
      bottom: 25mm
      left: 25mm
  resources:
    figures: []
    bibliography: null
  document:
    class: article
    fontsize: 11pt
    toc: false
    number_sections: true
  typography:
    mathbb_uppercase: ams-msbm
    mathbb_nonuppercase: explicit-only
```
<!-- END:BUILD_PROFILE -->
~~~

该块是构建输入，不是读者正文；最终 PDF 中必须完全消失。自然语言构建记录不能替代它。

## 字段约束

- `schema`、`profile` 与 `engine` 必须分别为 `final-pdf-build/v1`、`zh-math-xelatex/v1` 与 `xelatex`。未知 profile 或 engine 直接失败。
- `fonts` 必填 `latin_main`、`cjk_main`、`math_main`，可另填 `cjk_sans`、`cjk_mono`，均使用精确字体族名。中文文稿检查正文、无衬线和等宽三个通道，分别传给 Pandoc 的 `CJKmainfont`、`CJKsansfont`、`CJKmonofont`。未指定的辅助通道先保留正文 metadata 中的选择，再从现有合适字族中选择；实际结果写入检查报告。控制配置与正文 metadata 的显式选择冲突时失败，先统一配置。不可用的明确字族不静默替换；没有合适候选时按 `pdf-environment.md` 补齐后重查。字体下载只在环境恢复时进行，构建器本身不安装。
- 新稿建议将确认的三个中文字族写入控制稿，便于环境重建。正文中直接调用字体命令、局部字族、字体选项或额外文字系统时，还要检查实际编译日志与输出；字体族探测不证明每个字重、字形或字符均可用。
- `paper` 只允许 `a4` 或 `letter`。四个边距必须完整给出，并使用正数 `mm`、`cm`、`in` 或 `pt` 长度。
- `resources.figures` 是相对于输出目录根的本地资源文件或目录列表，可包含图像及正文使用的宏依赖；`bibliography` 是相对书目文件或 `null`。候选 Markdown 位于 `tmp/` 时，输出目录根是 `tmp/` 的父目录。绝对路径、`..` 越界和缺失的声明资源均失败；正文实际用到的本地资源也应在配置中登记，不把配置检查当成任意 TeX 的依赖证明。
- `document.class` 只允许 `article`、`report` 或 `book`；`fontsize` 只允许 `10pt`、`11pt` 或 `12pt`；`toc` 与 `number_sections` 必须为布尔值。
- `typography` 两项固定为 `ams-msbm` 与 `explicit-only`。构建配置不接受任意覆盖键、额外 header、临时模板或未登记 filter。正文已有的数学宏及 metadata 仍是正文输入；外置宏按实际资源登记并随需要交付。
- 所有映射拒绝未知键和重复键；不得用自由 `overrides` 绕过上述白名单。
- 正文含中文且未显式指定 metadata `lang` 时，采用 `zh-CN`，使目录等生成标签与中文正文一致；显式语言设定保留。明确日期原样使用，不为了排版擅自填写内容日期。

`inspect` 解析配置、验证路径和字体，通过 Pandoc AST 检查数学与 raw TeX，并列出短陈列公式和按需标题候选；候选只供编辑判断，不自动改写。公式陈列与断行规则、调用示例见 `final-output.md`。

## 空心字体契约

- `\mathbb{A}` 至 `\mathbb{Z}` 由 AMSFonts 原版 `msbm` 字形提供。主数学字体可以由文档选择，但不得重新接管这些大写字母。
- `\mathbb` 只接受单个拉丁大写字母。直接使用 `\mathbb{1}`、`\mathbb{k}`、多字符参数或不透明宏参数均阻断构建。
- 上述检查针对 Pandoc AST 中实际排版的数学和 raw TeX；行内代码、围栏代码及缩进代码中的字面示例不触发限制，也不要求 `MSBM10`。标为 `{=latex}` 或 `{=tex}` 的原始内容仍参与检查。外置宏等间接依赖还需结合实际编译和 PDF 检查，AST 扫描不等于展开任意 TeX。
- 空心小写和数字没有默认回退。确有需要时先建立独立命名的宏、字体通道和样张测试，再通过技能维护扩展；不得把它们塞入 `msbm` 的非字母槽位。
- 构建资产 `assets/final-pdf/v1/ams-mathbb.tex` 必须在最后一次主数学字体设置之后接管 `\mathbb`。
- 文稿实际含大写 `\mathbb` 时，PDF 预检必须要求嵌入 `MSBM10`，同时保持无 Type 3 字体和无缺字。没有使用 `\mathbb` 的文稿不要求出现该字体。文本提取能否返回 Unicode 双线字只作提示，不单独判失败。

## 构建

构建以当前正文、控制配置、声明资源和技能资产为输入，不读取同目录旧 PDF、旧 LaTeX 来恢复正文。依赖 Pandoc、PyYAML、XeLaTeX、latexmk、Fontconfig、所用宏包与配置字体；预检和渲染另需 Poppler、Pillow 与 pypdf。确认真实可用的字体和资源后，按 `final-output.md` 的命令检查与构建。

Work 云端环境被清理、工具缺失或字体不可用时，按 `pdf-environment.md` 检测与恢复。环境配置负责工具路径及可用字体，本文档的 `BUILD_PROFILE` 仍负责每份文稿的具体排版；二者不互相代替。

构建器拒绝覆盖输出；reader、PDF、日志和报告先放输出目录的 `tmp/`。生成用 TeX 的 basename（指定 `--tex` 时取该文件名，否则取 PDF 的同名 `.tex`）不得含空白、`{}\\%#$&^~"` 或以 `-` 开头；资源搜索目录名不得含空白及 TeX 特殊字符。遇到不适用名称时，在保留来源的候选副本中整理名称和引用，不直接改写来源。

Pandoc 生成 standalone TeX，latexmk 用它完成引用收敛和 PDF 编译。声明资源先按原相对位置复制到临时构建目录，无需创建目录符号链接；图像和外置宏须登记其文件或所在目录。按需追加 `--tex tmp/finished_v1.0.1.tex` 时，导出的就是实际编译用 TeX，并仅将编译实际打开的项目资源复制到同名 `.resources/`，随 TeX 一起保存、移动和归档。构建使用的 AMS 字体设置内联在该 TeX；citeproc 已内联的书目不重复打包；系统宏包与字体仍需在重编环境中准备。

构建成功后按 `final-output.md` 完成机械与视觉检查；日志保留失败诊断与最终 XeLaTeX 轮次。配置检查不代替实际重编和阅读成品。
