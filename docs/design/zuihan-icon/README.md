# 瑞般观珠图标

本目录保存已批准图标的维护源与导出方法。原始珠心、青绿双叶和材质由 OpenAI ImageGen 根据用户指导生成；精确公式随后作为独立路径叠加。22 条微雕公式各出现 4 次，共 88 个实例。公式的写法、条件、公开来源及定义／定理／猜想状态见[公式清单](formula-catalogue.md)。

`source/approved-master.svg` 是嵌入原始 PNG 材质与公式路径的复合 SVG，并非纯矢量图。它包含完整布局，不依赖外部图片或本机数学字体。该母图、公式清单与四张正式 PNG 在本次公开整理中保持原字节。

在项目作者能够授权的范围内，图标的构图、合成与排布按仓库 [MIT 许可](../../../LICENSE) 提供；第三方字形保留各自许可。来源与许可范围集中记录于 [NOTICE](../../../NOTICE)。项目名称和图标用于标识本项目，提及相关工具与参考项目不表示其作者或 OpenAI 为本项目背书。

## 正式资产与引用

四张透明 PNG 的唯一源码位置为 `skill/zuihan-kanshu/assets/`；插件构建按 manifest 引用逐字复制到包根 `assets/`。

| 用途 | 资产 | 像素 | 引用 |
| --- | --- | --- | --- |
| 浅色小图 | `icon-256.png` | 256 × 256 | 插件 `composerIcon`、技能 `icon_small` |
| 浅色大图 | `icon-1024.png` | 1024 × 1024 | 插件 `logo`、技能 `icon_large` |
| 深色小图 | `icon-dark-256.png` | 256 × 256 | 插件 `composerIconDark` |
| 深色大图 | `icon-dark-1024.png` | 1024 × 1024 | 插件 `logoDark` |

主强调色为 `#087F79`，插件深色强调色为 `#64D5C7`；技能 `brand_color` 使用主强调色。主页通过 HTML `picture` 的 `prefers-color-scheme` 媒体条件选择深浅 PNG。小图用于识别主体，不承诺微雕公式可读。

## 导出

使用 Node.js 20.9 或更新版本与 `sharp`；现有 PNG 的导出记录为 Node.js 24.19.0、Sharp 0.35.5、libvips 8.18.7。从仓库根目录执行：

```bash
node docs/design/zuihan-icon/scripts/build-icons.cjs --out-dir skill/zuihan-kanshu/assets --png-only --skip-review --report ../zuihan-icon-build-report.json
```

脚本默认读取相邻 `source/approved-master.svg`；可用 `--source` 指定源文件，用 `--out-dir` 指定输出位置。省略 `--png-only` 可另导出浅／深 SVG；这两份可再生文件不重复提交。`--review-dir` 和 `--report` 可将预览、报告放到仓库外。批准母图的 SHA-256 记录于 `source/approved-master.sha256`。

导出保留母图的原始材质与透明边缘。深色版仅调整材质 RGB 的 gamma；公式路径与布局不变。同尺寸深浅 PNG 使用相同 alpha 字节，公式不受材质滤镜影响。脚本不生成新图、不联网，也不重新排版数学。

Sharp 按 Apache 2.0 分发；本次使用的 Windows 原生分发包声明为 `Apache-2.0 AND LGPL-3.0-or-later`。它们是外部制作工具，没有随本仓库或运行包附带。维护工具时应核对对应版本的 [Sharp 许可](https://github.com/lovell/sharp/blob/v0.35.5/LICENSE)和 [Sharp libvips 第三方声明](https://github.com/lovell/sharp-libvips/blob/main/THIRD-PARTY-NOTICES.md)；不能把制作工具的许可误作图标全部组成部分的许可。

## 发布边界

运行包使用显式文件清单。构建器核对图标相对路径、清单成员、PNG 签名、256／1024 像素尺寸与每文件 5 MiB 上限，并拒绝覆盖已有发布目录。设计母图、公式清单、导出脚本和审阅图仅保留在源码仓库，不进入运行包；运行包携带适用的 `LICENSE` 与 `NOTICE`。
