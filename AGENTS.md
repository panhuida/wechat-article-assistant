# AGENTS.md

本文件面向 AI Coding Agent。目标是减少无效探索，约束改动边界，并让代码、测试、文档保持一致。


## 项目概览

`wechat-article-assistant` 是一个微信公众号文章阅读助手，用于集中管理公众号、采集历史文章，并下载文章及图片到本地。

- 主要技术栈：Python 3.12+、Flask、SQLAlchemy、Playwright、pytest、Ruff、ty、uv
- 主要包目录：`src/wechat_article_assistant`
- Web 入口：`run.py`
- CLI 入口：`wechat-cli.py`

优先从代码、测试和 `pyproject.toml` 判断真实约定；README 和 docs 可能滞后，发现不一致时应说明并同步修正。


## 仓库结构

```shell
src/wechat_article_assistant/
├── routes/        # HTTP 参数解析、响应组织，薄封装，不含业务逻辑
├── services/      # 业务逻辑主体，新功能优先放这里
├── browser/       # Playwright 封装、登录态、二维码、会话复用
├── models.py      # SQLAlchemy 模型与数据库初始化
├── config.py      # 环境变量与配置
├── utils/         # 无状态通用工具
├── templates/     # Jinja2 页面模板
└── static/        # 静态资源

tests/
├── unit/          # 单元测试
└── integration/   # 路由与跨层行为测试

docs/
├── 产品文档/      # 需求、样本、UI 参考
├── 参考文档/      # 实现过程说明
└── 开发笔记/     # 开发笔记（YYYY-MM-DD-<topic>.md）
```


## 常用命令

### 启动 Web 应用

```shell
uv run python run.py
```

### 代码格式化与检查

```shell
uv run ruff format .
uv run ruff check .
```

### 类型检查

```shell
uv run ty check
```

### 测试

```shell
uv run pytest
uv run pytest tests/unit/
uv run pytest tests/integration/
```

说明：

- pytest 配置位于 `pyproject.toml`。
- 除非任务明确要求，不要把手动 E2E 加入默认测试流。


## 编码规范

- 命名清晰，前后一致。

- 注释、日志、docstring 使用中文；标识符遵循 PEP 8 英文命名。
- 新增或修改函数应写参数和返回值类型注解。
- Service 层公开输入/输出优先使用 `dataclass`、`TypedDict` 或明确类型，不要裸传复杂 `dict`。
- 避免使用 `Any`；第三方库封装层无法避免时，需要使用局部注释说明原因。
- 使用 `pathlib.Path` 处理路径。
- 日志使用 `logging.getLogger(__name__)` 或项目已有日志工具，不要用 `print()` 表达运行时行为。
- 重构时清理无用旧代码，不留下死分支、重复实现或过期注释。


## 架构原则

- `routes/` 只做参数解析与响应组织，业务逻辑下沉到 `services/`。
- Service 层抛出的业务异常，必须由 Routes / CLI 转换为可读输出，不允许直接返回 500。
- 涉及浏览器/登录态的逻辑统一放在 `browser/`，不要在其他层直接操作 Playwright。


## 测试要求

- 新增或修改功能时，默认补写对应测试。
- 若未补测试，最终说明中必须写明原因与潜在风险。


## 禁止事项

- 不覆盖、恢复或删除用户未提交的修改。


## 开发笔记

解决非显而易见的问题、引入新依赖、做出架构决策或踩坑后，可在 `docs/开发笔记/YYYY-MM-DD-<topic>.md` 记录。

文档应简洁、准确、面向未来读者。