# dingtalk-cli AGENTS

## 项目目标

`dingtalk-cli` 是一个面向 agent 的钉钉文档 CLI，提供知识库、节点、文档、`.axls` workbook 和成员管理能力。

## 开发约定

- 命令名固定为 `dingtalk-cli`
- Python 包固定为 `dingtalk_cli`
- 默认输出支持人类可读和 `--json`
- 写操作必须显式传 `--yes`
- 普通文档走 `doc` 命令
- `.axls` 表格走 `workbook` 命令

## 配置约定

- 默认配置目录：`~/.dingtalk-cli/`
- 支持环境变量：
  - `DINGTALK_APP_KEY`
  - `DINGTALK_APP_SECRET`
  - `DINGTALK_OPERATOR_ID`
  - `DINGTALK_CLI_CONFIG_DIR`

## 测试约定

- 单测：`python3 -m pytest -q tests/test_core.py`
- 真实 E2E：设置 `DINGTALK_CLI_E2E=1` 后执行 `python3 -m pytest -q tests/test_full_e2e.py`
- 真实 E2E 至少覆盖：
  - `auth status`
  - `workspace list/info`
  - `doc create -> read -> overwrite -> delete`
  - `workbook live`

## 交付约定

- 合并前至少完成一次安装验证：`python3 -m pip install -e .`
- 合并时同步维护 `README.md`、`AGENTS.md`、`tests/TEST.md`
