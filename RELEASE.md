# dingtalk-cli 发布说明

## 目标

本项目按标准 Python 包对外分发，主要分发形式：

- PyPI: `pip install dingtalk-cli`
- 源码分发包: `sdist`
- 二进制分发包: `wheel`

## 发布前检查

```bash
python3 -m pip install -e .[dev]
python3 -m pytest -q tests/test_core.py
python3 -m pytest -q tests/test_full_e2e.py
```

如需真实 E2E，请准备：

- `DINGTALK_CLI_E2E=1`
- `DINGTALK_APP_KEY`
- `DINGTALK_APP_SECRET`
- `DINGTALK_OPERATOR_ID`
- `DINGTALK_TEST_WORKSPACE_ID`
- `DINGTALK_TEST_WORKBOOK_NODE_ID`

## 本地构建

```bash
python3 -m build
python3 -m twine check dist/*
```

构建产物：

- `dist/dingtalk_cli-<version>.tar.gz`
- `dist/dingtalk_cli-<version>-py3-none-any.whl`

## 上传到 PyPI

### 方式一：手工上传

```bash
python3 -m twine upload dist/*
```

### 方式二：GitHub Actions Trusted Publishing

仓库接入 GitHub 后，可使用 `.github/workflows/publish.yml`：

- 推送 `v*` tag 时自动构建
- 使用 PyPI Trusted Publisher 发布

## 版本发布建议

1. 更新 `dingtalk_cli/__init__.py` 版本号
2. 更新 `CHANGELOG.md`
3. 提交发布变更
4. 打 tag，如 `v1.0.0`
5. 构建并上传
