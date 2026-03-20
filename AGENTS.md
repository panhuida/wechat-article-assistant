# AGENTS.md

本文件面向在本仓库内工作的AI Coding Agent，目标是减少无效探索，保证改动方式与项目现状一致。

## 项目概览

- 项目名称：`wechat-article-assistant`
- 技术栈：Python 3.12、Flask、SQLAlchemy、Playwright、pytest、Ruff、pyright
- 包目录：`src/wechat_article_assistant`
- Web 入口：`run.py`
- CLI 入口：`wechat-cli.py` 或 `python -m wechat_article_assistant.cli`
- 应用工厂：`create_app()`，定义于 `src/wechat_article_assistant/__init__.py`

## 目录约定

- `src/wechat_article_assistant/routes/`：Flask 蓝图与 HTTP 接口
- `src/wechat_article_assistant/services/`：核心业务逻辑
- `src/wechat_article_assistant/browser/`：Playwright 浏览器交互与登录态管理
- `src/wechat_article_assistant/models.py`：数据库模型与数据库初始化
- `src/wechat_article_assistant/templates/`：Jinja2 模板
- `src/wechat_article_assistant/static/`：静态资源
- `tests/unit/`：单元测试
- `tests/integration/`：集成测试
- `tests/contract/`：契约/样本驱动测试（当前可能为空）
- `tests/e2e/manual/`：手动 E2E，用例默认不自动运行
- `docs/`：设计说明、修复说明、开发文档
- `scripts/`：辅助脚本，例如诊断和 SQLite 到 PostgreSQL 迁移

## 推荐工作方式

1. 先阅读与任务直接相关的 `routes`、`services`、`browser` 或测试文件，不要先做大范围重构。
2. 新逻辑优先放在 `services/`，路由层保持轻量，只做参数解析、调用服务、返回响应。
3. 涉及浏览器登录、二维码、会话复用的改动，优先检查 `browser/` 下的现有抽象，不要重复造一套流程。
4. 涉及数据库行为的改动，同时检查 `models.py`、服务层调用点和对应测试夹具。
5. 除非任务明确要求，不要修改 `data/`、`logs/`、`htmlcov/`、`.env` 里的本地运行产物。
6. 若发现工作区已有删除、重命名或迁移中的文件，不要默认恢复；先基于当前工作区状态继续工作，除非任务明确要求恢复。

## 本地命令

优先使用 `uv`，其次再使用 `pip` 虚拟环境。

### 安装依赖

```bash
uv sync
```

如需直接使用 `pytest`、`ruff`、`pyright` 等命令，可先激活虚拟环境：

```bash
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Linux/macOS
source .venv/bin/activate
```



### 启动应用

```bash
uv run python run.py
```

### 运行 CLI

```bash
uv run python wechat-cli.py download <article_url>
uv run python wechat-cli.py download --file urls.txt
uv run python wechat-cli.py collect-recent
```

### 运行测试

```bash
uv run pytest
uv run pytest tests/unit/
uv run pytest tests/integration/
uv run pytest -m integration
uv run pytest -m "not slow"
```

说明：

- `pytest` 配置写在 `pyproject.toml`
- 默认覆盖率门槛为 `60`
- `tests/e2e/manual` 已在 pytest 配置中排除，除非任务明确要求，不要把手动测试加入默认测试流
- `tests/` 下的测试会按目录自动打 marker：`unit`、`integration`、`contract`、`manual`

### 代码质量检查

```bash
uv run ruff format .
uv run ruff check .
uv run ruff check . --fix
uv run pyright
```

## 编码约定

- 保持现有分层：路由层处理请求，服务层处理业务，工具模块处理通用能力。
- 新增代码默认使用类型标注，风格与现有 Python 3.12 语法保持一致。
- 项目文档与注释以中文为主；已有模块 docstring 也是中文，新增内容保持一致。
- 优先复用现有日志能力，例如 `src/wechat_article_assistant/utils/logger.py`。
- 变更 API 或页面行为时，同步补充对应测试；至少覆盖成功路径和一个失败路径。
- 改动导入路径时注意本项目通过 `src` 布局组织代码，测试夹具会手动注入 `src` 到 `sys.path`。

## 测试注意事项

- 测试夹具位于 `tests/conftest.py`，会为每个测试创建独立 SQLite 数据库和临时目录。
- 如果新增配置项，评估是否需要同步扩展 `test_config` fixture。
- 浏览器相关测试尽量保持可 mock；只有在必须验证真实 Playwright 行为时才放入手动或 E2E 测试。
- 若修改下载逻辑、HTML 清理、图片处理、文章解析逻辑，优先补 `unit` 或 `contract` 测试，而不是只做人工验证。
- 非必要不要在测试文件里重复手工添加目录 marker，优先复用 `tests/conftest.py` 中的自动标记机制。

## 提交前自检

在完成代码改动后，尽量执行与改动范围匹配的最小验证：

- Python 代码改动：`uv run ruff check .`，必要时 `uv run ruff format .`
- 业务逻辑改动：运行相关 `uv run pytest` 文件或目录
- 类型影响较大：补跑 `uv run pyright`
- 涉及路由：至少跑对应 `tests/integration/` 用例
- 涉及 CLI：至少跑对应 `tests/unit/test_cli.py`
- 若仓库存在 `.github/workflows/`，确保本次改动不会破坏其中的 `ruff`、`pyright`、`pytest` 检查链路

## 额外说明

- 仓库当前未显示使用 Alembic；若涉及数据库结构变化，先确认现有初始化与迁移策略，再决定是否直接修改模型和初始化逻辑。
- Playwright 浏览器依赖系统环境，若本地缺少浏览器或沙箱限制导致失败，应明确说明，不要伪造验证结果。
- `README.md` 和 `docs/` 中已有多份中文说明文档；当实现与文档不一致时，优先修正代码后再补文档，或明确记录差异。
