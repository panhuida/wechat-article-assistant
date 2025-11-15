# 命令行工具快速入门

## 快速开始（3分钟上手）

### 1. 下载单篇文章

**Windows用户**（推荐）：
```bash
wechat-cli download https://mp.weixin.qq.com/s/你的文章链接
```

**其他系统**：
```bash
python wechat-cli.py download https://mp.weixin.qq.com/s/你的文章链接
```

### 2. 批量下载文章

**步骤1**：创建一个 `urls.txt` 文件，每行一个链接：
```
https://mp.weixin.qq.com/s/文章1
https://mp.weixin.qq.com/s/文章2
https://mp.weixin.qq.com/s/文章3
```

**步骤2**：执行批量下载：
```bash
# Windows
wechat-cli download --file urls.txt

# 其他系统
python wechat-cli.py download --file urls.txt
```

### 3. 自定义下载位置

```bash
# Windows - 下载到指定文件夹
wechat-cli download 文章链接 --output E:\我的文档\公众号

# 其他系统
python wechat-cli.py download 文章链接 --output /path/to/folder
```

或者在 `.env` 文件中配置默认路径：
```
DOWNLOAD_PATH=E:/documents/文摘/公众号
```

## 常用命令速查

| 功能 | Windows命令 | 其他系统命令 |
|------|------------|--------------|
| 下载单篇 | `wechat-cli download <url>` | `python wechat-cli.py download <url>` |
| 批量下载 | `wechat-cli download --file urls.txt` | `python wechat-cli.py download --file urls.txt` |
| 指定目录 | `wechat-cli download <url> -o 路径` | `python wechat-cli.py download <url> -o 路径` |
| 详细日志 | `wechat-cli download <url> -v` | `python wechat-cli.py download <url> -v` |
| 查看帮助 | `wechat-cli --help` | `python wechat-cli.py --help` |

## 下载的文件在哪里？

- **默认位置**：项目目录下的 `data/downloads/命令行下载/`
- **自定义位置**：使用 `--output` 参数或配置 `.env` 文件

## 更多帮助

- 详细文档：查看 `docs/CLI_GUIDE.md`
- 查看日志：`logs/download.log`
- 遇到问题：提交 GitHub Issue
