# dingtalk-cli 测试计划与结果

## Test Inventory Plan

- `tests/test_core.py`: 17 个单测与命令测试
- `tests/test_full_e2e.py`: 4 个可选真实钉钉 E2E 场景

## Unit Test Plan

### `config.py`

- 配置读写
- 环境变量覆盖
- token 缓存读写

### `core/auth.py`

- `auth setup`
- `auth set-operator`
- `auth status`
- `userId -> unionId` 分支

### `core/documents.py`

- blocks 文本重建
- `.axls` 目标拦截
- 覆盖写入目标解析

### `core/workbooks.py`

- 默认取第一个工作表
- range 读取结构

### `core/members.py`

- add/update/remove payload

### `cli.py`

- `--json` 输出结构
- `--yes` 保护
- 参数互斥校验
- 子进程 `--help`
- 子进程 `--json auth status`

## E2E Test Plan

默认关闭，设置 `DINGTALK_CLI_E2E=1` 启用。

- `auth status` 真实 token 校验
- `workspace list/info` 真实读取
- `doc create -> read -> overwrite -> delete`
- 若配置了 workbook/member 环境变量，追加 `.axls` 读取与成员管理

## Realistic Workflow Scenarios

### 文档生命周期

- Simulates: 在知识库中创建一篇文档并立刻读写
- Operations chained: create -> read -> overwrite -> delete
- Verified: 文档创建成功、正文可读、覆盖后接口成功、删除成功

### 表格抽取

- Simulates: 读取 `.axls` 表格前几行数据
- Operations chained: sheets -> read range
- Verified: 至少返回一个工作表，且 `display_values` 为二维数组

## Test Results

### 默认本地测试

```text
============================= test session starts ==============================
platform linux -- Python 3.10.12, pytest-9.0.2, pluggy-1.6.0 -- /usr/bin/python3
cachedir: .pytest_cache
rootdir: /root/work/dingtalk-cli/.worktree/feat-dingtalk-cli-v1
plugins: anyio-4.12.1
collecting ... collected 19 items

tests/test_core.py::TestConfigHelpers::test_config_round_trip PASSED
tests/test_core.py::TestConfigHelpers::test_env_overrides_config PASSED
tests/test_core.py::TestAuthCommands::test_auth_setup_saves_config PASSED
tests/test_core.py::TestAuthCommands::test_auth_setup_with_user_id_resolves_union_id PASSED
tests/test_core.py::TestAuthCommands::test_auth_setup_rejects_both_operator_flags PASSED
tests/test_core.py::TestAuthCommands::test_auth_status_without_config PASSED
tests/test_core.py::TestDocumentLogic::test_extract_text_from_blocks PASSED
tests/test_core.py::TestDocumentLogic::test_doc_read_axls_returns_structured_error PASSED
tests/test_core.py::TestDocumentLogic::test_doc_delete_requires_yes PASSED
tests/test_core.py::TestDocumentLogic::test_doc_overwrite_reads_file PASSED
tests/test_core.py::TestWorkbookAndMembers::test_workbook_read_uses_first_sheet_when_sheet_id_missing PASSED
tests/test_core.py::TestWorkbookAndMembers::test_member_add_payload PASSED
tests/test_core.py::TestHttpClient::test_access_token_uses_cache PASSED
tests/test_core.py::TestCliSubprocess::test_help PASSED
tests/test_core.py::TestCliSubprocess::test_json_auth_status PASSED
tests/test_full_e2e.py::test_auth_status_live SKIPPED
tests/test_full_e2e.py::test_workspace_live SKIPPED
tests/test_full_e2e.py::test_document_lifecycle_live SKIPPED
tests/test_full_e2e.py::test_workbook_live SKIPPED

======================== 15 passed, 4 skipped in 0.48s =========================
```

## Summary Statistics

- Total tests: 19
- Passed: 15
- Skipped: 4
- Runtime: 0.48s

### 真实钉钉 E2E 验证

使用本机 `~/.dingtalk-skills/config` 中的 `APP_KEY / APP_SECRET / OPERATOR_ID`，并指定测试知识库 `workspace_id=9Bv51S4ZVjYEDgv3` 执行。

```text
tests/test_core.py: 17 passed
tests/test_full_e2e.py: 4 passed
```

说明：

- `test_auth_status_live` 通过
- `test_workspace_live` 通过
- `test_document_lifecycle_live` 通过
- `test_workbook_live` 通过

## Coverage Notes

- 本轮覆盖了配置、CLI 参数、JSON 输出、写操作保护、文档/表格类型分流、成员 payload 和子进程入口。
- 真实钉钉 API E2E 已完成认证、知识库读取、文档生命周期和 workbook 读取验证。
