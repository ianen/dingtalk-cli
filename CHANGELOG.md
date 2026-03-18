# CHANGELOG

## Unreleased

- 调整公开 `SKILL.md` 安装说明，默认走 `pip install dingtalk-cli`
- 补充 `skills.sh` / `ClawHub` 分发与验证文档

## V1.0.0

- 首次发布 `dingtalk-cli`
- 支持知识库、节点、普通文档、`.axls` workbook 和成员管理
- 支持 `--json` 结构化输出、默认 REPL、内置 `SKILL.md`
- 完成真实钉钉 E2E 验证：
  - `auth status`
  - `workspace list/info`
  - `doc create -> read -> overwrite -> delete`
  - `workbook live`
