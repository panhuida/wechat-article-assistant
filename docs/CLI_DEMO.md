# 命令行工具使用演示

## 场景1：下载单篇文章

### Windows用户

```bash
# 打开命令提示符（CMD）或PowerShell
# 切换到项目目录
cd E:\study\code\github\wechat-article-assistant

# 执行下载命令
wechat-cli download https://mp.weixin.qq.com/s/xxxxx
```

**预期输出**：
```
============================================================
下载文章: https://mp.weixin.qq.com/s/xxxxx
============================================================

正在下载文章...

============================================================
✓ 下载成功，保存至: E:\study\code\github\wechat-article-assistant\data\downloads\命令行下载\文章标题.html
============================================================
```

### Linux/Mac用户

```bash
# 打开终端
# 切换到项目目录
cd /path/to/wechat-article-assistant

# 执行下载命令
python wechat-cli.py download https://mp.weixin.qq.com/s/xxxxx
```

## 场景2：批量下载文章

### 步骤1：创建URL列表文件

创建一个名为 `my_articles.txt` 的文件：

```
# 技术文章
https://mp.weixin.qq.com/s/article1
https://mp.weixin.qq.com/s/article2

# 生活分享
https://mp.weixin.qq.com/s/article3
https://mp.weixin.qq.com/s/article4
https://mp.weixin.qq.com/s/article5
```

### 步骤2：执行批量下载

**Windows**：
```bash
wechat-cli download --file my_articles.txt
```

**Linux/Mac**：
```bash
python wechat-cli.py download --file my_articles.txt
```

**预期输出**：
```
============================================================
从文件读取URL: my_articles.txt
============================================================

正在下载第 1/5 篇...
正在下载第 2/5 篇...
正在下载第 3/5 篇...
正在下载第 4/5 篇...
正在下载第 5/5 篇...

============================================================
下载完成!
============================================================
成功: 5 篇
失败: 0 篇
============================================================
```

## 场景3：指定下载目录

```bash
# Windows
wechat-cli download https://mp.weixin.qq.com/s/xxxxx --output E:\我的文档\公众号文章

# Linux/Mac
python wechat-cli.py download https://mp.weixin.qq.com/s/xxxxx --output ~/Documents/公众号文章
```

## 场景4：查看详细日志

当下载遇到问题时，使用 `--verbose` 参数查看详细信息：

```bash
# Windows
wechat-cli download https://mp.weixin.qq.com/s/xxxxx --verbose

# Linux/Mac
python wechat-cli.py download https://mp.weixin.qq.com/s/xxxxx --verbose
```

## 场景5：组合使用多个选项

```bash
# 批量下载 + 指定目录 + 详细日志
wechat-cli download --file urls.txt --output E:\文章收藏 --verbose
```

## 常见问题处理

### 问题1：命令未找到

**Windows错误**：
```
'wechat-cli' 不是内部或外部命令，也不是可运行的程序
```

**解决方法**：
1. 确保在项目目录下执行
2. 或者使用完整路径：
   ```bash
   E:\study\code\github\wechat-article-assistant\wechat-cli download <url>
   ```
3. 或者添加项目目录到系统PATH

### 问题2：文件找不到

**错误**：
```
FileNotFoundError: [Errno 2] No such file or directory: 'urls.txt'
```

**解决方法**：
- 使用文件的完整路径：
  ```bash
  wechat-cli download --file E:\文档\urls.txt
  ```
- 或者确保在正确的目录下

### 问题3：下载失败

**错误**：
```
✗ 下载文章失败: HTTP 404
```

**解决方法**：
1. 检查URL是否正确
2. 检查网络连接
3. 查看日志文件：`logs/download.log`
4. 使用 `--verbose` 参数查看详细错误

## 高级技巧

### 技巧1：快速下载剪贴板中的链接（Windows）

```powershell
# PowerShell中执行
$url = Get-Clipboard
wechat-cli download $url
```

### 技巧2：批量下载后自动打开目录

```bash
# Windows
wechat-cli download --file urls.txt && explorer data\downloads

# Mac
python wechat-cli.py download --file urls.txt && open data/downloads

# Linux
python wechat-cli.py download --file urls.txt && xdg-open data/downloads
```

### 技巧3：定时批量下载

**Windows任务计划程序**：
1. 创建批处理文件 `auto_download.bat`：
   ```batch
   cd E:\study\code\github\wechat-article-assistant
   wechat-cli download --file daily_articles.txt
   ```
2. 在任务计划程序中设置定时运行

**Linux Cron**：
```bash
# 编辑crontab
crontab -e

# 添加定时任务（每天早上8点执行）
0 8 * * * cd /path/to/project && python wechat-cli.py download --file daily_articles.txt
```

### 技巧4：下载并转换格式

```bash
# 下载后使用其他工具转换为PDF
wechat-cli download <url> && wkhtmltopdf data/downloads/xxx.html xxx.pdf
```

## 性能优化建议

1. **批量下载**：一次性下载多篇文章比多次单独下载更高效
2. **本地网络**：在网络条件好的环境下载
3. **合理间隔**：避免频繁请求导致被限制
4. **日志清理**：定期清理日志文件释放空间

## 配置文件说明

在项目根目录的 `.env` 文件中配置：

```env
# 默认下载路径
DOWNLOAD_PATH=E:/documents/文摘/公众号

# 日志级别
LOG_LEVEL=INFO

# 请求超时（秒）
REQUEST_TIMEOUT=30
```

## 查看帮助

任何时候遇到问题，都可以查看帮助信息：

```bash
# 查看主帮助
wechat-cli --help

# 查看下载命令帮助
wechat-cli download --help
```

## 获取支持

- 查看文档：`docs/` 目录
- 查看日志：`logs/download.log`
- 提交Issue：GitHub Issues
- 邮件支持：[填写你的邮箱]
