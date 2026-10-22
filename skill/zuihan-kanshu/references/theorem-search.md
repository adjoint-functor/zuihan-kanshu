# TheoremSearch 与非形式化 TheoremGraph

按 literature.md 选择检索时机、查询范围与来源核验。TheoremSearch 按数学陈述找候选，TheoremGraph 可继续定位 arXiv 非形式化陈述及抽取的引用、依赖关系。普通问答、研究和文稿均可按需使用；不要求先搜陈述再查图，也不接入形式化库。

## 检索与本地选读

使用标准库脚本 scripts/theorem-search-client.py，无需安装依赖或配置全局 MCP。替换下列路径；输出父目录须已存在。

```bash
skill_root="/path/to/zuihan-kanshu"
project_root="/path/to/数学项目"
python3 "$skill_root/scripts/theorem-search-client.py" search \
  "Every doubly stochastic matrix is a convex combination of permutation matrices." \
  --num-results 50 --output "$project_root/tmp/theorem-search.json"
python3 "$skill_root/scripts/theorem-search-client.py" preview \
  "$project_root/tmp/theorem-search.json" --start 11 --limit 10
python3 "$skill_root/scripts/theorem-search-client.py" show \
  "$project_root/tmp/theorem-search.json" 13
```

search 调用 POST /search；graph-search 使用同类查询调用 GET /graph/embedding，可直接定位图中的 statement_id。两者默认请求 50 个候选、仅预览 10 项元数据。官方默认 10；50 是本技能的初始覆盖设置，按问题调整，不是官方最佳值。preview 分段查看更多元数据，show 选读一项完整响应；二者不联网。候选条数不等于独立文献数，预览范围不是阅读上限。

显式 --output 保存完整请求信息和原始响应，顶层为 operation、request、response；额外字段也保留，已有文件不覆盖。新查询另取临时文件名，已有可用结果直接复用。--preview 可改显示数或取 0；--timeout 默认 30 秒。客户端不自动重试。

## 按需参数

| 参数 | 使用方式与边界 |
|---|---|
| --num-results | 返回数量；graph-search 为 1–100，search 要求正整数，当前公开契约未声明上限 |
| --source | 可重复；search 支持 arXiv、Stacks Project、ProofWiki 等公开来源，完整选项见 --help；图只用 arXiv |
| --author / --type | 可重复；按作者或 Statement 类型缩小范围，勿因不必要的过滤漏掉跨领域结果 |
| --category | 可重复；search 对应 tags，graph-search 对应 categories，如 math.CO |
| --paper-filter | search 为题名子串；graph-search 按论文标识前缀或题名关键词过滤；异常空结果时去除过滤再定位 |
| --citation-weight | 默认 0；仅在明确希望按引用量调整排序时提高，不把引用量当作适用性或正确性 |
| --db-top-k | 仅 search；向量检索候选池大小，不是最终返回量或预览量；省略时交给服务默认策略 |

当前文档把 db_top_k 的默认描述为返回量的两倍；客户端不固化该服务端策略。先根据对象、条件和机制形成有辨识力的查询，再按覆盖和命中质量调参。不把别的智能体客户端、旧接口或社区单次故障当成当前接口契约。

## 图定位与方向

从 graph-search 的结果取得 UUID 形式的 statement_id，再按需要查邻接关系。/search 的数字 theorem_id 不能直接当作图的 statement_id；不能凭编号猜出关联。已知论文时也可直接查 paper。

```bash
python3 "$skill_root/scripts/theorem-search-client.py" graph-search \
  "Hall marriage theorem for a bipartite graph" \
  --output "$project_root/tmp/graph-search.json"
python3 "$skill_root/scripts/theorem-search-client.py" neighbors \
  "<返回的 statement_id>" --direction both \
  --output "$project_root/tmp/graph-neighbors.json"
python3 "$skill_root/scripts/theorem-search-client.py" show \
  "$project_root/tmp/graph-neighbors.json" --section root
python3 "$skill_root/scripts/theorem-search-client.py" preview \
  "$project_root/tmp/graph-neighbors.json" --section edges
python3 "$skill_root/scripts/theorem-search-client.py" paper \
  "<返回论文的 arXiv 标识>" --output "$project_root/tmp/graph-paper.json"
```

| neighbors --direction | 含义 |
|---|---|
| src（默认） | 当前根陈述使用了哪些陈述或引用 |
| dep | 哪些陈述使用了当前根陈述 |
| both | 两个方向的并集 |

客户端对图检索和邻接请求固定 formality=informal、mode=full，论文图固定来源 arXiv。当前返回结构：search 为 theorems，graph-search 为 results，neighbors 为 root / nodes / edges，paper 为 paper / statements / edges。show --section root 或 paper 可读根陈述或论文；preview 与 show 的 --section edges 可定位边。

一条边的 src_id 使用 dep_id，不能将方向反读。目标可能只有 cite_id、cite_key，或仍未解析；保留这些信息及实际返回的 methods、location、edge_type 等注释，不补造缺失类型或目标。图未返回某依赖不证明它不存在，也不能仅据图边认定其承担数学证明。

slogan 是自动摘要；body、proof、页面定位及图关系也可能抽取错误或错配。采用结论和证明前阅读原文，核对量词、条件及证明实际属于哪个陈述；结构校验通过只表示响应可读取。

## 接口与失败含义

契约核对 [官方 OpenAPI](https://api.theoremsearch.com/openapi.json)，阅读入口见 [官方文档](https://www.theoremsearch.com/docs)。当前客户端仅使用 search、graph/embedding、graph/statement 与 graph/paper 的非形式化用途。

退出码 0 表示请求与结构校验成功，包括空结果；2 为输入错误；1 为 HTTP、网络、超时、响应或文件错误，标准错误分别标为 http、network、timeout、response、file。失败不伪装成成功空结果。保存格式保留完整原始字段；据此选择原文和后续查询，数学使用及长期记录仍按 literature.md 处理。
