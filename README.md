# 微信公众号文章阅读助手

一个功能完善的Web应用，用于管理、采集和下载微信公众号历史文章。

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

### 1. 克隆项目

```bash
git clone <repository-url>
cd wechat-article-assistant
```

### 2. 安装依赖

使用 pip:
```bash
pip install -r requirements.txt
```

或使用 uv (推荐):
```bash
uv pip install -r requirements.txt
```

### 3. 安装Playwright浏览器

```bash
playwright install chromium
```

### 4. 配置环境变量

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

### 5. 启动应用

```bash
python run.py
```

访问 http://localhost:5000

## 📖 使用说明

### Web界面使用

#### 1. 添加公众号

- 访问"公众号管理"页面
- 点击"新增公众号"按钮
- 选择"手工录入"或"自动获取"方式添加公众号

**手工录入**：
- 填写公众号名称（必填）
- 填写其他信息（可选）
- 点击"保存"

**自动获取**：
- 首次使用需要扫码登录微信公众平台
- 输入公众号名称关键词
- 点击"搜索"
- 从搜索结果中选择目标公众号
- 确认后保存

#### 2. 采集文章

- 在公众号列表中找到目标公众号
- 点击"单页采集"：采集一页文章（根据配置的数量）
- 点击"全部采集"：循环采集所有历史文章

#### 3. 管理和下载文章

- 访问"文章列表"页面
- 使用搜索框或筛选条件查找文章
- 勾选要下载的文章
- 点击"下载选中"按钮批量下载

### 命令行工具使用

#### 下载单个文章

```bash
python -m wechat_article_assistant download <article_url>
```

#### 批量下载

创建一个文本文件（如 `urls.txt`），每行一个文章链接：

```
https://mp.weixin.qq.com/s/xxx
https://mp.weixin.qq.com/s/yyy
https://mp.weixin.qq.com/s/zzz
```

然后执行：

```bash
python -m wechat_article_assistant download --file urls.txt
```

#### 指定输出目录

```bash
python -m wechat_article_assistant download <article_url> --output /path/to/output
```

#### 显示详细日志

```bash
python -m wechat_article_assistant download <article_url> --verbose
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

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

### 代码格式化和检查

```bash
ruff format .
ruff check .
```

### 类型检查

```bash
mypy src
```

### 运行测试

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
