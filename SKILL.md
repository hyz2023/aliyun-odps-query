---
name: aliyun-odps-query
description: "本机 OpenClaw agents 使用的阿里云 ODPS/MaxCompute 只读查询技能。适合表发现、schema 查看、只读 SQL 查询、结果摘要和失败诊断。"
---

# Aliyun ODPS Query Skill

## 适用场景

当 OpenClaw agent 需要在当前机器上对阿里云 ODPS / MaxCompute 做以下操作时，使用这个技能：

- 列出项目中的表或视图
- 查看表结构、分区和基础元数据
- 执行只读 SQL 查询
- 对已有结果做简短摘要
- 对常见失败或空结果做规则化诊断

## 明确不做的事情

这个技能不会：

- 生成 SQL
- 执行写操作或删表类操作
- 作为远程服务对其他机器暴露
- 替代更高层的分析 agent 做复杂解释

## 推荐调用流程

1. 先用 `list` 找表
2. 用 `describe` 看 schema 和分区
3. 用 `query` 执行只读 SQL
4. 需要快速概括时，用 `summarize`
5. 失败或空结果时，用 `diagnose`

## CLI 入口

推荐入口：

```bash
odps-skill <command> ...
```

兼容旧入口：

```bash
python scripts/odps_query.py <command> ...
```

## 命令说明

### `list`

```bash
odps-skill list --project my_project --output json
odps-skill list --project my_project --pattern order --output text
```

### `describe`

```bash
odps-skill describe --project my_project --table order_detail --output json
```

### `query`

```bash
odps-skill query --project my_project --sql "SELECT * FROM order_detail LIMIT 10" --output json
```

只支持只读 SQL。包含 `INSERT`、`UPDATE`、`DELETE`、`DROP`、`ALTER`、`TRUNCATE`、`CREATE` 或明显多语句输入的请求会被拒绝。

### `summarize`

```bash
odps-skill summarize --input-json '{"columns":["id"],"rows":[{"id":1}],"count":1}' --output json
```

### `diagnose`

```bash
odps-skill diagnose --error-type empty_result --output json
odps-skill diagnose --error-type invalid_query --output json
```

## 输出约定

默认输出是 `json`。可选：

- `json`
- `text`
- `table`

所有命令都尽量遵循统一 envelope：

```json
{
  "ok": true,
  "action": "list",
  "project": "my_project",
  "target": null,
  "data": {},
  "summary": "",
  "diagnostics": [],
  "meta": {}
}
```

失败时会返回：

- `ok: false`
- `error.type`
- `error.message`
- `diagnostics`

## 环境变量

```bash
export ALIBABA_ACCESSKEY_ID="your_access_key_id"
export ALIBABA_ACCESSKEY_SECRET="your_access_key_secret"
export ALIBABA_ODPS_ENDPOINT="http://service.odps.aliyun.com/api"
export ALIBABA_ODPS_PROJECT="your_project_name"
```

## 对 agent 的建议

- 默认优先 `--output json`
- 查询前优先 `describe`
- 遇到 `invalid_query` 不要重试写操作
- 遇到空结果，优先检查分区和时间条件
