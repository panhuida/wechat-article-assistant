# 开发指南

## 开发环境设置

### 1. 克隆项目

```bash
git clone <repository-url>
cd wechat-article-assistant
```

### 2. 安装依赖

**推荐使用 uv：**

```bash
uv sync
```

如需手动激活虚拟环境：

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

**使用传统 pip：**

```bash
# 安装运行依赖
pip install -r requirements.txt

# 开发工具请按需单独安装
pip install pytest pytest-cov ruff pyright pytest-mock pytest-asyncio
```

### 3. 安装 Playwright 浏览器

```bash
# 安装浏览器驱动
playwright install chromium
```

### 4. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，根据需要修改配置：

```env
FLASK_APP=src.wechat_article_assistant.app
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here

DATABASE_URL=sqlite:///data/wechat_assistant.db
LOG_LEVEL=INFO
LOG_DIR=logs
DOWNLOAD_DIR=data/downloads

WECHAT_MP_URL=https://mp.weixin.qq.com
SESSION_FILE=data/wechat_session.json
```

### 5. 运行应用

```bash
# Web 应用
uv run python run.py

# 或使用命令行工具
uv run python wechat-cli.py download <article_url>
uv run python wechat-cli.py download --file urls.txt
```

## 项目结构说明

```
wechat-article-assistant/
├── src/wechat_article_assistant/
│   ├── __init__.py              # 包初始化
│   ├── config.py                # 配置管理
│   ├── models.py                # 数据模型
│   ├── cli.py                   # 命令行工具
│   │
│   ├── routes/                  # 路由层
│   │   ├── __init__.py
│   │   ├── wechat_routes.py     # 公众号管理路由
│   │   └── article_routes.py    # 文章管理路由
│   │
│   ├── services/                # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── wechat_service.py    # 公众号服务
│   │   ├── article_service.py   # 文章服务
│   │   └── download_service.py  # 下载服务
│   │
│   ├── browser/                 # 浏览器自动化
│   │   ├── __init__.py
│   │   ├── browser_manager.py   # 浏览器管理
│   │   ├── wechat_authenticator.py  # 微信认证
│   │   └── session_manager.py   # 会话管理
│   │
│   ├── utils/                   # 工具类
│   │   ├── __init__.py
│   │   ├── logger.py            # 日志工具
│   │   ├── file_helper.py       # 文件操作
│   │   ├── validators.py        # 数据验证
│   │   └── qr_code.py           # 二维码生成
│   │
│   ├── templates/               # HTML模板
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── wechat_list.html
│   │   └── article_list.html
│   │
│   └── static/                  # 静态资源
│       ├── favicon.png
│       ├── wechat.png
│       └── article.png
│
├── tests/                       # 测试
│   ├── conftest.py              # pytest配置
│   ├── unit/                    # 单元测试
│   ├── integration/             # 集成测试
│   ├── contract/                # 契约/样本驱动测试
│   ├── e2e/                     # 端到端与手动测试
│   ├── factories/               # 测试数据工厂
│   └── fixtures/                # 固定样本数据
│
├── scripts/                     # 工具脚本
│   ├── setup-uv.ps1             # Windows uv 安装脚本
│   ├── setup-uv.sh              # Linux/macOS uv 安装脚本
│   └── diagnose.py              # 诊断脚本
│
├── docs/                        # 文档
├── data/                        # 数据目录
├── logs/                        # 日志目录
├── pyproject.toml               # 项目配置
├── requirements.txt             # 依赖列表
├── run.py                       # Web应用启动脚本
├── wechat-cli.py                # 命令行工具入口
└── urls.txt.example             # URL列表示例
```

## 代码规范

### Python 代码风格

项目使用 Ruff 进行代码格式化和检查：

```bash
# 格式化代码
ruff format .

# 检查代码
ruff check .

# 自动修复
ruff check --fix .
```

### 类型检查

项目支持两种类型检查工具：

**使用 pyright：**
```bash
pyright
```

配置详见 `pyproject.toml` 中的 `[tool.pyright]` 部分。

### 注释规范

- 所有注释使用中文
- 函数和类使用文档字符串（docstring）
- 重要逻辑添加行内注释

示例：

```python
def example_function(param1: str, param2: int) -> bool:
    """
    函数说明

    Args:
        param1: 参数1说明
        param2: 参数2说明

    Returns:
        返回值说明
    """
    # 逻辑说明
    return True
```

## 测试

### 运行测试

```bash
# 运行所有测试（自动跳过 tests/e2e/manual）
uv run pytest

# 运行特定测试文件
uv run pytest tests/unit/test_models.py

# 运行特定测试目录
uv run pytest tests/integration/

# 显示详细输出
uv run pytest -v

# 生成覆盖率报告
uv run pytest --cov-report=html

# 当前覆盖率门槛
uv run pytest

# 运行标记的测试
uv run pytest -m "not slow"  # 排除慢速测试
uv run pytest -m integration  # 只运行集成测试
```

### 测试目录结构

- `tests/unit/` - 单元测试
- `tests/integration/` - 集成测试
- `tests/contract/` - 契约/样本驱动测试
- `tests/e2e/manual/` - 手动测试（不会自动运行）
- `tests/factories/` - 测试数据工厂
- `tests/fixtures/` - 固定样本

### 编写测试

测试文件放在 `tests/` 目录下，使用 pytest 框架。测试配置在 `pyproject.toml` 中。

**示例 - 路由测试：**

```python
def test_create_wechat_account(client):
    """测试创建公众号"""
    response = client.post('/api/wechat/accounts', json={
        'nickname': '测试公众号',
        'fakeid': 'test_fakeid'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
```

**示例 - 服务测试：**

```python
from wechat_article_assistant.services.article_service import ArticleService

def test_article_service(db_session):
    """测试文章服务"""
    service = ArticleService(db_session)
    articles = service.get_articles(limit=10)
    assert isinstance(articles, list)
```

**测试标记：**

```python
import pytest

@pytest.mark.slow
def test_slow_operation():
    """慢速测试"""
    pass

@pytest.mark.integration
def test_integration():
    """集成测试"""
    pass
```

## 数据库

### 模型定义

使用 SQLAlchemy ORM 定义数据模型，位于 `src/wechat_article_assistant/models.py`。

主要模型：
- `WeChatAccount` - 微信公众号账号
- `Article` - 文章信息

### 数据库操作

```python
from wechat_article_assistant.models import db_session, WeChatAccount, Article

# 查询
accounts = db_session.query(WeChatAccount).all()

# 创建
account = WeChatAccount(nickname="测试", fakeid="test123")
db_session.add(account)
db_session.commit()

# 更新
account.nickname = "新名称"
db_session.commit()

# 删除
db_session.delete(account)
db_session.commit()
```

### 数据库迁移

当前使用 SQLite，模型变更时：

1. 修改 `models.py` 中的模型定义
2. 开发环境可以删除数据库文件重建
3. 生产环境建议备份后手动迁移

**未来计划**：集成 Alembic 进行自动化迁移管理。

## API 设计

### RESTful API 规范

- 使用标准 HTTP 方法：GET、POST、PUT、DELETE
- 返回格式统一为 JSON
- 状态码使用标准 HTTP 状态码

响应格式：

```json
{
    "success": true,
    "message": "操作成功",
    "data": {}
}
```

### 错误处理

统一的错误响应格式：

```json
{
    "success": false,
    "message": "错误信息"
}
```

## 日志

### 日志配置

日志配置在 `src/wechat_article_assistant/utils/logger.py`。

### 日志级别

- DEBUG: 详细的调试信息
- INFO: 一般信息
- WARNING: 警告信息
- ERROR: 错误信息

### 使用示例

```python
from wechat_article_assistant.utils.logger import app_logger

app_logger.info("操作成功")
app_logger.error("操作失败", exc_info=True)
```

## 调试

### Flask 调试模式

在 `.env` 中设置：

```env
FLASK_DEBUG=True
FLASK_ENV=development
```

### 日志调试

设置日志级别为 DEBUG：

```env
LOG_LEVEL=DEBUG
```

查看日志文件：

```bash
# Windows
type logs\app.log

# Linux/macOS
tail -f logs/app.log
```

### IDE 调试

#### VS Code

创建 `.vscode/launch.json`：

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Flask",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/run.py",
            "console": "integratedTerminal",
            "justMyCode": true,
            "env": {
                "FLASK_DEBUG": "1"
            }
        },
        {
            "name": "Python: CLI",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/wechat-cli.py",
            "console": "integratedTerminal",
            "args": ["download", "--help"]
        }
    ]
}
```

#### PyCharm

1. 右键点击 `run.py` → Run 'run'
2. 或配置 Python 运行配置，脚本路径选择 `run.py`

### 诊断工具

运行诊断脚本检查环境：

```bash
python scripts/diagnose.py
```

## 贡献指南

### 提交代码

1. Fork 项目
2. 创建特性分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -am '添加某功能'`
4. 推送分支：`git push origin feature/your-feature`
5. 提交 Pull Request

### Commit 消息规范

遵循约定式提交规范：

- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

示例：

```
feat: 添加文章批量下载功能
fix: 修复采集时的编码问题
docs: 更新API文档
```

## 常见问题

### Q: 如何添加新的路由？

A: 
1. 在 `routes/` 目录创建或编辑路由文件
2. 定义 Blueprint 和路由处理函数
3. 在 `app.py` 中注册 Blueprint

示例：
```python
# routes/new_routes.py
from flask import Blueprint, jsonify

bp = Blueprint('new', __name__, url_prefix='/api/new')

@bp.route('/test')
def test():
    return jsonify({'message': 'success'})

# app.py
from .routes import new_routes
app.register_blueprint(new_routes.bp)
```

### Q: 如何添加新的数据模型？

A:
1. 在 `models.py` 中定义新的模型类
2. 继承 `Base` 类
3. 定义 `__tablename__` 和字段
4. 开发环境删除数据库文件重建

示例：
```python
class NewModel(Base):
    __tablename__ = "new_models"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
```

### Q: 如何修改前端页面？

A:
1. 编辑 `templates/` 目录下的 HTML 文件
2. 使用 Jinja2 模板语法
3. 使用 Tailwind CSS 类进行样式设置
4. JavaScript 代码写在 `<script>` 标签中

### Q: 如何添加新的业务逻辑？

A:
1. 在 `services/` 目录创建或编辑服务文件
2. 定义服务类和方法
3. 在路由中调用服务

示例：
```python
# services/new_service.py
class NewService:
    def __init__(self, db_session):
        self.db = db_session
    
    def do_something(self):
        # 业务逻辑
        pass

# routes/new_routes.py
from ..services.new_service import NewService
from ..models import db_session

@bp.route('/action')
def action():
    service = NewService(db_session)
    result = service.do_something()
    return jsonify(result)
```

### Q: 如何调试 Playwright 浏览器自动化？

A:
1. 设置环境变量 `PWDEBUG=1` 启用调试模式
2. 使用 `page.pause()` 暂停执行
3. 使用 `headless=False` 查看浏览器界面

```python
# 调试模式
import os
os.environ['PWDEBUG'] = '1'

# 非无头模式
browser = await playwright.chromium.launch(headless=False)
```

### Q: 如何处理依赖冲突？

A:
1. 使用 uv 管理依赖（推荐）：`uv sync`
2. 或使用虚拟环境隔离：`python -m venv venv`
3. 检查 `pyproject.toml` 中的版本约束
4. 运行 `scripts/diagnose.py` 检查环境

## 性能优化建议

1. **数据库查询优化**
   - 使用索引加速查询
   - 使用 `joinedload` 预加载关联数据，避免 N+1 查询
   - 对大量数据使用分页查询

2. **缓存策略**
   - 对频繁访问且不常变化的数据使用缓存
   - 可以考虑使用 Flask-Caching
   - 浏览器 Session 缓存复用

3. **异步任务**
   - 耗时操作（如文章下载）使用后台任务
   - 可以考虑集成 Celery 或 RQ

4. **前端优化**
   - 静态资源使用 CDN
   - 使用 Tailwind CSS 的生产构建
   - 启用 gzip 压缩

5. **Playwright 优化**
   - 复用浏览器上下文和页面
   - 使用 Session 持久化减少登录次数
   - 适当设置超时时间

## 安全建议

1. **输入验证**
   - 所有用户输入都要验证，使用 `validators.py` 工具
   - 验证 URL 格式和来源

2. **SQL 注入防护**
   - 使用 ORM 参数化查询
   - 避免拼接 SQL 字符串

3. **XSS 防护**
   - Jinja2 模板自动转义
   - 下载的文章内容做适当清理

4. **CSRF 防护**
   - 考虑使用 Flask-WTF 添加 CSRF 保护
   - API 接口使用 Token 认证

5. **密钥管理**
   - 不要在代码中硬编码密钥
   - 使用 `.env` 文件管理配置
   - `.env` 文件不要提交到版本控制

6. **文件操作安全**
   - 验证文件路径，防止路径遍历
   - 限制文件上传大小和类型
   - 下载文件路径使用白名单

## 工具脚本

### setup-uv 脚本

自动安装 uv 和项目依赖：

```bash
# Windows
.\scripts\setup-uv.ps1

# Linux/macOS
./scripts/setup-uv.sh
```

### diagnose 脚本

诊断开发环境：

```bash
python scripts/diagnose.py
```

检查内容：
- Python 版本
- 依赖安装情况
- 环境变量配置
- 数据库连接
- Playwright 浏览器

## 参考资源

### 框架和库文档
- [Flask 文档](https://flask.palletsprojects.com/) - Web 框架
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/) - ORM
- [Playwright 文档](https://playwright.dev/python/) - 浏览器自动化
- [Tailwind CSS 文档](https://tailwindcss.com/) - CSS 框架

### Python 工具
- [Ruff 文档](https://docs.astral.sh/ruff/) - 代码检查和格式化
- [pytest 文档](https://docs.pytest.org/) - 测试框架
- [uv 文档](https://docs.astral.sh/uv/) - Python 包管理器

### 相关资源
- [微信公众平台](https://mp.weixin.qq.com/) - 官方平台
- [Python 类型提示](https://docs.python.org/3/library/typing.html) - 官方文档
- [PEP 8](https://peps.python.org/pep-0008/) - Python 代码风格指南

## 开发工作流

### 典型开发流程

1. **创建功能分支**
```bash
git checkout -b feature/your-feature
```

2. **开发和测试**
```bash
# 编写代码
# 运行格式化
ruff format .

# 运行检查
ruff check --fix .

# 类型检查
pyright

# 运行测试
pytest
```

3. **提交代码**
```bash
git add .
git commit -m "feat: 添加某功能"
```

4. **推送和 PR**
```bash
git push origin feature/your-feature
# 在 GitHub 创建 Pull Request
```

### 版本发布流程

1. 更新版本号（`pyproject.toml`）
2. 更新 CHANGELOG
3. 运行完整测试套件
4. 创建 release 分支
5. 合并到 main 分支
6. 创建 Git tag

### 使用 pre-commit（可选）

安装 pre-commit hooks：

```bash
pip install pre-commit
pre-commit install
```

配置 `.pre-commit-config.yaml`：

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests, types-beautifulsoup4]
```

## 命令行工具使用

### wechat-cli.py

批量下载文章的命令行工具：

```bash
# 下载单篇文章
python wechat-cli.py download "https://mp.weixin.qq.com/s/..."

# 从文件批量下载
python wechat-cli.py download --file urls.txt

# 指定输出目录
python wechat-cli.py download --file urls.txt --output ./downloads

# 显示详细日志
python wechat-cli.py download --file urls.txt --verbose
```

URL 文件格式（每行一个 URL）：
```
https://mp.weixin.qq.com/s/article1
https://mp.weixin.qq.com/s/article2
https://mp.weixin.qq.com/s/article3
```
