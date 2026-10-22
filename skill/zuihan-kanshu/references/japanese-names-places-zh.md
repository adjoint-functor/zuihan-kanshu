# 日本人名、地名与机构名中文表

## 处理顺序

本表只处理中文读者正文中的具体日本实体和封闭列举的人名来源数学术语，不是罗马字字符串替换表。

1. 先划定保护区：参考文献条目、BibTeX/CSL 元数据、引用键、DOI、URL、文件名、代码及逐字保留的原文均不得改写。保护区可以用于消歧正文身份，但只能读、不能写。
2. 在正文中解析完整人物、地点或机构身份；也可以精确匹配“固定人名术语”表中的完整术语。
3. 只把已解析的日本实体部分改为本表规定的中文正文形式；数学通名照常翻译，非日本人名保持原文。
4. 裸姓、缩写、对象类别不明、同名身份或未列罗马字变体均不足以触发替换。不能唯一解析时保留来源形式。

表内简体形式是本技能采用的中文正文形式，不表示每一项都有独立的权威中文译名。日文旧字、新字、长音号和连字符变体只按表内明列形式匹配，不作模糊扩张。

## 人物实体

只有完整身份已经解析时才使用本表。表内日文形式也可帮助核对身份，但不得据相同姓氏反推人物。

| 完整身份 | 允许匹配的完整来源形式 | 中文正文形式 |
|---|---|---|
| Kenkichi Iwasawa | `Kenkichi Iwasawa`；`岩澤健吉`；`岩沢健吉` | 岩泽健吉 |
| Tsuneo Tamagawa | `Tsuneo Tamagawa`；`玉河恒夫` | 玉河恒夫 |
| Ichirō Satake | `Ichirō Satake`；`Ichiro Satake`；`佐武一郎` | 佐武一郎 |
| Nobuo Yoneda | `Nobuo Yoneda`；`米田信夫` | 米田信夫 |
| Yozō Matsushima | `Yozō Matsushima`；`Yozo Matsushima`；`松島与三` | 松岛与三 |
| Nagayoshi Iwahori | `Nagayoshi Iwahori`；`岩堀長慶` | 岩堀长庆 |
| Jun-ichi Igusa | `Jun-ichi Igusa`；`Junichi Igusa`；`井草準一` | 井草准一 |
| Mikio Sato | `Mikio Sato`；`佐藤幹夫` | 佐藤干夫 |
| Kiiti Morita | `Kiiti Morita`；`森田紀一` | 森田纪一 |
| Atsushi Ichino | `Atsushi Ichino`；`市野篤史` | 市野笃史 |
| Tamotsu Ikeda | `Tamotsu Ikeda`；`池田保` | 池田保 |
| Shunsuke Yamana | `Shunsuke Yamana`；`山名俊介` | 山名俊介 |
| Shuichiro Takeda | `Shuichiro Takeda`；`武田秀一郎` | 武田秀一郎 |
| Takashi Ono | `Takashi Ono`；`小野孝` | 小野孝 |
| Takurō Shintani | `Takurō Shintani`；`Takuro Shintani`；`新谷卓郎` | 新谷卓郎 |
| Hiroshi Saito, author in the Tunnell–Saito setting | `Hiroshi Saito`；`斎藤裕`；`齊藤裕`；`斉藤裕` | 斋藤裕 |
| Tetsuya Asai, mathematician associated with the Asai representation | `Tetsuya Asai`；`浅井哲也` | 浅井哲也 |

## 固定人名术语

下列完整术语可以直接命中；这项许可不扩张为对其中裸姓的全局替换。

| 来源术语 | 中文正文形式 |
|---|---|
| Iwasawa theory | 岩泽理论 |
| Iwasawa decomposition | 岩泽分解 |
| Iwasawa coordinates | 岩泽坐标 |
| Tamagawa number | 玉河数 |
| Tamagawa measure | 玉河测度 |
| Satake parameter | 佐武参数 |
| Satake isomorphism | 佐武同构 |
| Satake diagram | 佐武图 |
| Yoneda lemma | 米田引理 |
| Matsushima criterion | 松岛判据 |
| Iwahori subgroup | 岩堀子群 |
| Iwahori–Hecke algebra | 岩堀–Hecke 代数 |
| Igusa zeta function | 井草 zeta 函数 |
| Bernstein–Sato polynomial | Bernstein–佐藤多项式 |
| Morita equivalence | 森田等价 |
| Ichino–Ikeda formula | 市野–池田公式 |
| Ikeda lift | 池田提升 |
| Shintani formula | 新谷公式 |
| Tunnell–Saito theorem | Tunnell–斋藤定理 |
| Asai representation | 浅井表示 |
| Asai $L$-function | 浅井 $L$-函数 |

## 地名与机构实体

先解析完整对象，再使用中文形式。不得用子串匹配把另一机构或另一地点误认成表中对象。

| 实体 | 允许匹配的完整来源形式 | 中文正文形式 |
|---|---|---|
| 日本城市或都府：Tokyo | `Tokyo`；`東京` | 东京 |
| 日本城市或府：Kyoto | `Kyoto`；`京都` | 京都 |
| 日本城市或府：Osaka | `Osaka`；`大阪` | 大阪 |
| Waseda University | `Waseda University`；`早稲田大学` | 早稻田大学 |
| University of Tsukuba | `University of Tsukuba`；`筑波大学` | 筑波大学 |
| The University of Tokyo | `The University of Tokyo`；`東京大学` | 东京大学 |
| Kyoto University | `Kyoto University`；`京都大学` | 京都大学 |
| The University of Osaka | `The University of Osaka`；历史英文名 `Osaka University`；`大阪大学` | 大阪大学 |

## 歧义守卫

- `Saito`、`Sato`、`Ono`、`Ikeda`、`Ichino`、`Takeda`、`Asai` 等裸姓不得自动映射。正文较早位置的完整身份或只读参考文献可以提供消歧，但研究领域相似本身不是身份证据。
- `Takashi Tsukamoto` 保留来源形式；不得采用未经绑定的日文汉字候选。
- `Tokyo`、`Kyoto`、`Osaka`、`Tsukuba` 先确认是地点、机构还是名称的一部分。`Tokyo University of Science` 不属于东京大学；现代 `つくば市` 不因 `Tsukuba` 自动写成“筑波市”。
- 多人术语只转换本表精确命中的日本人名部分，其他人名保持原文。
