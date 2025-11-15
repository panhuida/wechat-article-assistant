# 命令行工具使用指南

## 简介

微信公众号文章助手提供了灵活的命令行工具，支持快速下载单个或批量文章。

## 安装前准备

确保已安装项目依赖：
```bash
pip install -r requirements.txt
```

## 使用方式

### 方式一：使用简化脚本（最简单，推荐）

#### Windows用户

直接在项目目录下使用 `wechat-cli.bat` 批处理文件：

```bash
# 下载单个文章
wechat-cli download https://mp.weixin.qq.com/s/xxxxx

# 批量下载（从文件读取URL列表）
wechat-cli download --file urls.txt

# 指定输出目录
wechat-cli download https://mp.weixin.qq.com/s/xxxxx --output E:\documents\文摘\公众号

# 显示详细日志
wechat-cli download https://mp.weixin.qq.com/s/xxxxx --verbose
```

**提示**：可以将项目目录添加到系统PATH环境变量，这样在任何位置都可以直接使用 `wechat-cli` 命令。

#### Linux/Mac用户

使用 Python 脚本：

```bash
# 下载单个文章
python wechat-cli.py download https://mp.weixin.qq.com/s/xxxxx

# 批量下载
python wechat-cli.py download --file urls.txt

# 指定输出目录
python wechat-cli.py download https://mp.weixin.qq.com/s/xxxxx --output /path/to/output

# 显示详细日志
python wechat-cli.py download https://mp.weixin.qq.com/s/xxxxx --verbose
```

### 方式二：使用Python模块

```bash
# 下载单个文章
python -m wechat_article_assistant download https://mp.weixin.qq.com/s/xxxxx

# 批量下载
python -m wechat_article_assistant download --file urls.txt

# 指定输出目录
python -m wechat_article_assistant download https://mp.weixin.qq.com/s/xxxxx --output /path/to/output

# 显示详细日志
python -m wechat_article_assistant download https://mp.weixin.qq.com/s/xxxxx --verbose
```

### 方式三：安装为系统命令

将包安装到Python环境后，可以直接使用命令：

```bash
# 安装包（开发模式）
pip install -e .

# 之后可以在任何位置使用
wechat-article-assistant download https://mp.weixin.qq.com/s/xxxxx
wechat-article-assistant download --file urls.txt
```

## 批量下载

### 创建URL列表文件

创建一个文本文件（如 `urls.txt`），每行一个文章链接：

```
https://mp.weixin.qq.com/s/xxx
https://mp.weixin.qq.com/s/yyy
https://mp.weixin.qq.com/s/zzz
```

### 执行批量下载

```bash
# Windows用户
wechat-cli download --file urls.txt

# Linux/Mac用户
python wechat-cli.py download --file urls.txt

# 使用Python模块
python -m wechat_article_assistant download --file urls.txt
```

## 配置输出目录

### 使用命令行参数指定

```bash
wechat-cli download <url> --output E:\documents\文摘\公众号
```

### 使用环境变量配置（推荐）

在项目根目录的 `.env` 文件中配置默认下载路径：

```
DOWNLOAD_PATH=E:/documents/文摘/公众号
```

配置后，不使用 `--output` 参数时会自动使用此路径。

## 常见问题

### Q: Windows下如何在任何位置使用 wechat-cli 命令？

**A**: 将项目目录添加到系统PATH环境变量：
1. 右键"此电脑" -> "属性" -> "高级系统设置"
2. 点击"环境变量"
3. 在"系统变量"中找到"Path"，点击"编辑"
4. 点击"新建"，输入项目完整路径，如 `E:\study\code\github\wechat-article-assistant`
5. 点击"确定"保存
6. 重新打开命令行窗口

### Q: Linux/Mac下如何快速使用？

**A**: 可以创建一个软链接或别名：

```bash
# 创建别名（添加到 ~/.bashrc 或 ~/.zshrc）
alias wechat-cli='python /path/to/wechat-article-assistant/wechat-cli.py'

# 或创建软链接
sudo ln -s /path/to/wechat-article-assistant/wechat-cli.py /usr/local/bin/wechat-cli
chmod +x /path/to/wechat-article-assistant/wechat-cli.py
```

### Q: 下载的文件保存在哪里？

**A**: 默认保存在项目的 `data/downloads/` 目录下。可以通过以下方式修改：
1. 使用 `--output` 参数指定
2. 在 `.env` 文件中配置 `DOWNLOAD_PATH`

### Q: 如何查看详细的下载日志？

**A**: 使用 `--verbose` 或 `-v` 参数：
```bash
wechat-cli download <url> --verbose
```

同时可以查看日志文件 `logs/download.log`

## 示例

### 示例1：下载单篇文章

```bash
wechat-cli download https://mp.weixin.qq.com/s/abc123xyz
```

### 示例2：批量下载并指定输出目录

```bash
wechat-cli download --file articles.txt --output E:\我的文档\公众号文章
```

### 示例3：下载并显示详细日志

```bash
wechat-cli download https://mp.weixin.qq.com/s/abc123xyz --verbose
```

## 高级用法

### 结合其他命令使用

```bash
# 从剪贴板获取URL并下载（Windows）
powershell -command "Get-Clipboard" | wechat-cli download

# 下载后自动打开文件夹
wechat-cli download <url> && start data\downloads
```

## 技术支持

如遇问题，请查看：
1. 日志文件：`logs/download.log`
2. 项目文档：`docs/` 目录
3. 提交Issue：GitHub Issues

## 更新日志

- v0.1.0: 初始版本，支持单个和批量下载功能
