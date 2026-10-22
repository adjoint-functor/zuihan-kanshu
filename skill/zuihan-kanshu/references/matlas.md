# Matlas 定理检索

按 literature.md 选择检索时机、处理查询范围、核对原文和回收结果。Matlas 适合按数学对象、条件和结论寻找书籍及论文中的定理、引理、定义或证明机制；索引覆盖有边界，近期论文及未收录来源按需由其他检索补充。自动展开的陈述仍须回到来源核对，借用方法时阅读有关证明。

## 命令与候选范围

使用技能根目录中的标准库脚本，无需安装额外依赖。把技能根和当前项目路径替换为实际路径：

```bash
skill_root="/path/to/zuihan-kanshu"
project_root="/path/to/数学项目"
mkdir -p "$project_root/tmp"
python3 "$skill_root/scripts/matlas-client.py" search \
  "A continuous real-valued function on a compact space attains its maximum and minimum." \
  --num-results 50 \
  --output "$project_root/tmp/matlas-compact-extrema.json"
```

| 参数 | 本客户端默认与范围 | 用途 |
|---|---|---|
| --num-results | 默认 50；10–200 | 返回候选陈述数，不是文献数 |
| --preview | 默认 10；可取 0 | 本次显示的元数据数，不影响请求量和完整保存 |
| --timeout | 默认 30 秒；正数 | 单次 HTTP 超时，不是研究预算 |

官方接口默认返回 10 条；本技能采用 50 条作为增加候选覆盖的起点，不声称这是实证最优值。定位明确时可调小，较宽的机制搜索可调大；根据后续候选是否仍有信息调整，也可改变查询或来源，不设固定逐档增加流程。客户端不自动重试，不发送反馈。

只有显式传入 --output 才保存服务返回的完整数组；父目录须存在，已有文件不会覆盖。已有结果仍可用时直接复用，新查询用新的临时文件名。默认预览不显示定理正文；若需选读后续候选，例如查看第 11–20 项的元数据：

```bash
python3 "$skill_root/scripts/matlas-client.py" preview \
  "$project_root/tmp/matlas-compact-extrema.json" --start 11 --limit 10
python3 "$skill_root/scripts/matlas-client.py" show \
  "$project_root/tmp/matlas-compact-extrema.json" 13
```

preview 与 show 只读取本地 JSON，不再次联网。preview 默认从第 1 项显示 10 项；show 使用原数组从 1 开始的序号，显示该项完整 statement。分段筛选元数据、选读相关陈述及原文，不把前 10 项预览当作后续候选的筛选上限。

## 接口与失败含义

客户端调用 [Matlas 公开 API](https://matlas.ai/openapi.json) 的 `POST https://matlas.ai/api/search`，请求体只有 `query` 和 `num_results`。服务返回数组，每项的当前字段均为字符串：

| 字段 | 使用方式 |
|---|---|
| `type` | `book` 或 `paper` |
| `entity_name` | 服务给出的数学条目名称，用于定位 |
| `doi` | DOI 线索，仍需核对来源身份 |
| `title` | 作品题名 |
| `authors` | 服务给出的作者字符串 |
| `journal` | 服务给出的期刊或出版信息 |
| `year` | 服务给出的年份字符串，不自行改成数值 |
| `statement` | 待核对的数学陈述 |
| `candidate_id` | 服务候选标识，不当作文献版本或原文定理编号 |

保存服务返回的完整字段；额外返回的字段也保留在 JSON 文件中。

退出码 0 表示请求与结构校验成功，包括成功返回空数组。退出码 2 表示命令输入有误；退出码 1 表示请求、结果或本地文件操作失败。标准错误中的类别区分 `http`、`network`、`timeout`、`response` 和 `file`；其中 `response` 包括无效 UTF-8、非 JSON 或字段结构不符。失败不会伪装成成功空结果。
