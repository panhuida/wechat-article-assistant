<h1 align="center"><img src="src/wechat_article_assistant/static/favicon.png" alt="icon" width="48" height="48" style="vertical-align: text-bottom; margin-right: 8px;"/>微信公众号文章阅读助手</h1>

<p align="center">
  <strong>一个可以自动获取公众号所有文章并可以下载所有文章的工具</strong>
</p>

首页
<p align="center">
  <img src="docs\UI\首页.png" alt="首页">
</p>
公众号管理


<p align="center">
  <img src="docs\UI\公众号管理.png" alt="公众号管理">
</p>
公众号文章


<p align="center">
  <img src="docs\UI\公众号文章.png" alt="公众号文章">
</p>



**注：这个项目的代码由 AI 生成，README 文档也主要由 AI 生成。**





## ✨ 功能特点

- 📚 **公众号管理**：支持手工录入和自动搜索添加公众号
- 🔍 **文章采集**：单页或全部采集公众号历史文章
- ⬇️ **批量下载**：支持批量下载文章及图片到本地
- 🔎 **搜索筛选**：支持按公众号、作者、时间等条件筛选文章
- 💻 **命令行工具**：提供CLI工具快速下载指定文章
- 🎨 **友好界面**：基于Tailwind CSS的现代化UI设计



## 📋 系统要求

- Python 3.12 或更高版本
- 支持的操作系统：Windows、macOS、Linux



## 🚀 快速开始

### 方式一：使用 uv（推荐⚡）

[uv](https://github.com/astral-sh/uv) 是一个极快的 Python 包管理器，比 pip 快 10-100 倍。

#### 1. 安装 uv

**Windows（PowerShell）**：
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Linux/macOS**：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### 2. 克隆项目并初始化

```bash
git clone <repository-url>
cd wechat-article-assistant

# 创建虚拟环境并安装依赖（一条命令完成）
uv sync

# 激活虚拟环境
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
```

#### 3. 安装Playwright浏览器

```bash
playwright install chromium
```

#### 4. 配置环境变量

```bash
# Windows
copy .env.example .env
# Linux/macOS
cp .env.example .env
```

#### 5. 启动应用

```bash
# 使用 uv 运行（推荐）
uv run python run.py

# 或在激活虚拟环境后运行
python run.py
```

访问 http://localhost:5000

---

### 方式二：使用传统 pip

#### 1. 克隆项目

```bash
git clone <repository-url>
cd wechat-article-assistant
```

#### 2. 创建虚拟环境

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python -m venv venv
source venv/bin/activate
```

#### 3. 安装依赖

```bash
pip install -r requirements.txt
```

#### 4. 安装Playwright浏览器

```bash
playwright install chromium
```

#### 5. 配置环境变量

```bash
# Windows
copy .env.example .env
# Linux/macOS
cp .env.example .env
```

#### 6. 启动应用

```bash
python run.py
```

访问 http://localhost:5000



## 📖 使用说明

### 命令行工具使用

本工具提供多种使用方式，任选其一即可。

#### 方式一：使用简化脚本（推荐）

**Windows用户**：

```bash
# 下载单个文章
wechat-cli download <article_url>

# 批量下载
wechat-cli download --file urls.txt

# 指定输出目录
wechat-cli download <article_url> --output E:\documents\文摘\公众号

# 显示详细日志
wechat-cli download <article_url> --verbose
```

**Linux/Mac用户**：
```bash
# 下载单个文章
python wechat-cli.py download <article_url>

# 批量下载
python wechat-cli.py download --file urls.txt

# 指定输出目录
python wechat-cli.py download <article_url> --output /path/to/output

# 显示详细日志
python wechat-cli.py download <article_url> --verbose
```

#### 批量下载文件格式

创建一个文本文件（如 `urls.txt`），每行一个文章链接：

```
https://mp.weixin.qq.com/s/xxx
https://mp.weixin.qq.com/s/yyy
https://mp.weixin.qq.com/s/zzz
```



## 🗂️ 项目结构

```
wechat-article-assistant/
├── src/wechat_article_assistant/    # 主要代码
│   ├── routes/                      # 路由层
│   ├── services/                    # 业务逻辑层
│   ├── browser/                     # 浏览器自动化
│   ├── utils/                       # 工具类
│   ├── templates/                   # HTML模板
│   ├── static/                      # 静态资源
│   ├── models.py                    # 数据模型
│   ├── config.py                    # 配置管理
│   ├── app.py                       # Flask应用
│   └── cli.py                       # 命令行工具
├── data/                            # 数据目录
│   ├── downloads/                   # 下载文件
│   └── wechat_assistant.db          # SQLite数据库
├── logs/                            # 日志目录
├── tests/                           # 测试目录
├── docs/                            # 文档目录
├── requirements.txt                 # 依赖列表
├── pyproject.toml                   # 项目配置
├── run.py                           # 启动脚本
└── README.md                        # 项目说明
```





## 🔧 开发

### 方式一：使用 uv（推荐）

#### 安装开发依赖

```bash
# 同步所有依赖（包括开发依赖）
uv sync --all-extras

# 或者单独安装开发依赖
uv pip install -e ".[dev]"
```

#### 添加新依赖

```bash
# 添加生产依赖
uv add <package-name>

# 添加开发依赖
uv add --dev <package-name>

# 移除依赖
uv remove <package-name>
```

#### 运行命令

```bash
# 使用 uv run 在虚拟环境中运行命令
uv run python run.py
uv run pytest
uv run ruff check .
uv run mypy src
```

#### 代码格式化和检查

```bash
uv run ruff format .
uv run ruff check . --fix
```

#### 类型检查

```bash
uv run mypy src
uv run pyright
```

#### 运行测试

```bash
uv run pytest
uv run pytest --cov
```

---



### 方式二：使用传统 pip

#### 安装开发依赖

```bash
pip install -e ".[dev]"
```

#### 代码格式化和检查

```bash
ruff format .
ruff check .
```

#### 类型检查

```bash
mypy src
```

#### 运行测试

```bash
pytest
```



## 📝 注意事项

1. **登录会话**：微信公众平台的登录会话有效期有限，失效后需要重新扫码登录
2. **采集频率**：建议不要过于频繁地采集文章，避免被微信限制
3. **文章下载**：下载的HTML文件中的图片链接已替换为本地相对路径
4. **数据备份**：建议定期备份 `data/` 目录下的数据库和下载文件



## 🤝 贡献

欢迎提交Issue和Pull Request！



## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。



## 📧 联系方式

如有问题或建议，请提交Issue或联系项目维护者。



## 🙏 致谢

感谢所有为本项目做出贡献的开发者！
