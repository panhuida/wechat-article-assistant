# 开发指南

## 开发环境设置

### 1. 克隆项目

```bash
git clone <repository-url>
cd wechat-article-assistant
```

### 2. 创建虚拟环境

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### 3. 安装依赖

```bash
# 安装运行依赖
pip install -r requirements.txt

# 安装开发依赖
pip install ruff mypy pytest pytest-cov
```

### 4. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置 `FLASK_DEBUG=True`。

## 项目结构说明

```
wechat-article-assistant/
├── src/wechat_article_assistant/
│   ├── __init__.py              # 包初始化
│   ├── app.py                   # Flask应用入口
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
│   │   ├── wechat_login.py      # 微信登录
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
│
├── tests/                       # 测试
├── docs/                        # 文档
├── data/                        # 数据目录
└── logs/                        # 日志目录
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

### 类型提示

使用类型提示并通过 mypy 进行检查：

```bash
mypy src
```

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
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_models.py

# 显示详细输出
pytest -v

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

### 编写测试

测试文件放在 `tests/` 目录下，使用 pytest 框架。

示例：

```python
def test_create_account(client):
    """测试创建公众号"""
    response = client.post('/api/wechat/create', json={
        'nickname': '测试公众号',
        'begin': 0,
        'count': 5
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
```

## 数据库

### 模型定义

使用 SQLAlchemy ORM 定义数据模型，位于 `src/wechat_article_assistant/models.py`。

### 数据库迁移

当前使用 SQLite，模型变更时需要：

1. 修改 `models.py` 中的模型定义
2. 删除现有数据库文件（开发环境）
3. 重新运行应用以创建新表结构

未来可以考虑使用 Alembic 进行数据库迁移管理。

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
```

### 日志调试

设置日志级别为 DEBUG：

```env
LOG_LEVEL=DEBUG
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
            "type": "python",
            "request": "launch",
            "module": "flask",
            "env": {
                "FLASK_APP": "src.wechat_article_assistant.app",
                "FLASK_DEBUG": "1"
            },
            "args": [
                "run",
                "--no-debugger",
                "--no-reload"
            ],
            "jinja": true
        }
    ]
}
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
1. 在 `routes/` 目录创建新的路由文件
2. 定义 Blueprint 和路由处理函数
3. 在 `app.py` 中注册 Blueprint

### Q: 如何添加新的数据模型？

A:
1. 在 `models.py` 中定义新的模型类
2. 继承 `Base` 类
3. 定义表名和字段
4. 重新初始化数据库

### Q: 如何修改前端页面？

A:
1. 编辑 `templates/` 目录下的 HTML 文件
2. 使用 Tailwind CSS 类进行样式设置
3. JavaScript 代码直接写在 `{% block scripts %}` 中

## 性能优化建议

1. **数据库查询优化**：使用索引、避免 N+1 查询
2. **缓存**：对频繁访问的数据使用缓存
3. **异步任务**：耗时操作使用后台任务队列
4. **静态资源**：使用 CDN 加载静态资源

## 安全建议

1. **输入验证**：所有用户输入都要验证
2. **SQL 注入防护**：使用 ORM 参数化查询
3. **XSS 防护**：模板自动转义
4. **CSRF 防护**：使用 Flask-WTF
5. **密钥管理**：不要在代码中硬编码密钥

## 参考资源

- [Flask 文档](https://flask.palletsprojects.com/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
- [Playwright 文档](https://playwright.dev/python/)
- [Tailwind CSS 文档](https://tailwindcss.com/)
