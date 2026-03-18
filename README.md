# dingtalk-cli

`dingtalk-cli` 是一个面向 agent 的钉钉文档 CLI，覆盖知识库、节点、文档读写、`.axls` 表格读取和成员管理，并内置可发现的 `SKILL.md`。

## 安装

```bash
pip install dingtalk-cli
```

从源码开发安装：

```bash
pip install -e .
```

安装后可用命令：

```bash
dingtalk-cli --help
dingtalk-cli
```

## 配置

推荐直接通过命令写入本地配置：

```bash
dingtalk-cli auth setup \
  --app-key <APP_KEY> \
  --app-secret <APP_SECRET> \
  --operator-union-id <UNION_ID>
```

如果只知道 `userId`，可以让 CLI 自动换取 `unionId`：

```bash
dingtalk-cli auth setup \
  --app-key <APP_KEY> \
  --app-secret <APP_SECRET> \
  --operator-user-id <USER_ID>
```

配置文件位于 `~/.dingtalk-cli/`，可通过 `DINGTALK_CLI_CONFIG_DIR` 覆盖。

## 主要命令

- `auth setup|set-operator|status`
- `workspace list|info`
- `node list|info|resolve-url`
- `doc create|read|overwrite|delete`
- `workbook sheets|info|read`
- `member add|update|remove`

所有命令支持 `--json`，便于 agent 解析。

## 示例

```bash
# 查看知识库
dingtalk-cli --json workspace list --all

# 通过 URL 读取文档正文
dingtalk-cli doc read --url "https://alidocs.dingtalk.com/i/nodes/xxx"

# 覆盖写入文档
dingtalk-cli doc overwrite --doc-key <DOC_KEY> --content-file /abs/path/content.md --yes

# 若已知 create 返回的 workspace_id + node_id，可直接删除
dingtalk-cli doc delete --workspace-id <WORKSPACE_ID> --node-id <NODE_ID> --yes

# 读取钉钉表格
dingtalk-cli workbook read --node-id <NODE_ID> --range A1:Z80
```

## 给 Agent 的约定

- 优先使用 `--json`
- 写命令都需要显式 `--yes`
- `doc read` 遇到 `.axls` 会返回结构化错误并指向 `workbook` 命令
- REPL 启动横幅会展示内置 `SKILL.md` 的绝对路径

## 对外分发

标准构建命令：

```bash
python3 -m build
python3 -m twine check dist/*
```

详细发布流程见 [RELEASE.md](RELEASE.md)。
