# 阿里云 ODPS Query

面向当前机器本地使用的 ODPS / MaxCompute 只读查询工具，适合 OpenClaw agents 和人工终端调试共同使用。

## 安装

```bash
pip install pyodps pandas openpyxl
```

如果需要本地命令入口：

```bash
pip install -e .
```

## 给 OpenClaw Agent 的安装指引

如果要让当前机器上的 OpenClaw agent 使用这个技能，按下面步骤安装：

```bash
mkdir -p ~/.openclaw/workspace/skills
cp -R /Users/huangyuzhao/gitproject/aliyun-odps-query ~/.openclaw/workspace/skills/aliyun-odps-query
cd ~/.openclaw/workspace/skills/aliyun-odps-query
pip install -e .
pip install pyodps pandas openpyxl
```

安装后 agent 可以直接参考 `SKILL.md` 调用，推荐命令：

```bash
odps-skill list --project my_project --output json
odps-skill describe --project my_project --table order_detail --output json
odps-skill query --project my_project --sql "SELECT * FROM order_detail LIMIT 10" --output json
```

如果 agent 仍走旧脚本入口，也可以使用：

```bash
python scripts/odps_query.py list --project my_project --output json
```

## 环境配置

```bash
export ALIBABA_ACCESSKEY_ID="your_access_key_id"
export ALIBABA_ACCESSKEY_SECRET="your_access_key_secret"
export ALIBABA_ODPS_ENDPOINT="http://service.odps.aliyun.com/api"
export ALIBABA_ODPS_PROJECT="your_project_name"
```

## 常用命令

列出表：

```bash
odps-skill list --project my_project --output json
```

查看表结构：

```bash
odps-skill describe --project my_project --table order_detail --output json
```

执行只读 SQL：

```bash
odps-skill query --project my_project --sql "SELECT * FROM order_detail LIMIT 10" --output json
```

对结果做摘要：

```bash
odps-skill summarize --input-json '{"columns":["id"],"rows":[{"id":1}],"count":1}' --output json
```

生成诊断建议：

```bash
odps-skill diagnose --error-type empty_result --output json
```

## 输出格式

支持：

- `json`，默认，适合 agent 调用
- `text`，适合快速查看
- `table`，适合终端中的表格式输出

## 兼容旧入口

旧脚本路径仍然可用，但现在只是 CLI 兼容壳：

```bash
python scripts/odps_query.py list --project my_project --output json
```

## 限制

- 仅支持本机使用
- 不做 SQL 生成
- 不支持写操作和删表类 SQL
- 不暴露远程服务
