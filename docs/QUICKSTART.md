# 快速开始指南

欢迎使用微信公众号文章阅读助手！本指南将帮助您快速上手使用本应用。

## 📦 安装步骤

### 方式一：使用 uv（推荐，更快）

```bash
# 安装 uv
pip install uv

# 自动安装所有依赖
uv sync


# 或使用脚本
# Windows
.\scripts\setup-uv.ps1

# Linux/macOS
./scripts/setup-uv.sh
```

### 方式二：使用传统 pip

```bash
# 安装项目依赖
pip install -e .

# 或使用 requirements.txt
pip install -r requirements.txt
```

### 安装 Playwright 浏览器

```bash
playwright install chromium
```

### 配置环境变量（可选）

```bash
cp .env.example .env
```

如需修改配置（如端口、日志级别等），编辑 `.env` 文件。常用配置：

```env
FLASK_DEBUG=True          # 开发模式
LOG_LEVEL=INFO           # 日志级别
DOWNLOAD_DIR=data/downloads  # 下载目录
```

## 🚀 启动应用

### Web 应用模式

```bash
python run.py
```

启动成功后，在浏览器中访问：**http://localhost:5000**

看到欢迎界面即表示启动成功！🎉

### 命令行模式

适合快速下载文章，无需启动 Web 服务：

```bash
# 下载单篇文章
python wechat-cli.py download "https://mp.weixin.qq.com/s/xxxxx"

# 批量下载
python wechat-cli.py download --file urls.txt
```

详见下方"命令行工具"部分。



## 💻 命令行工具

命令行工具适合快速下载文章，无需启动 Web 服务。

### 基本用法

```bash
# 查看帮助
python wechat-cli.py --help
python wechat-cli.py download --help
```

### 下载单篇文章

```bash
python wechat-cli.py download "https://mp.weixin.qq.com/s/xxxxx"
```

### 批量下载文章

1. 创建文本文件 `urls.txt`，每行一个文章链接：

```text
https://mp.weixin.qq.com/s/xxxxx
https://mp.weixin.qq.com/s/yyyyy
https://mp.weixin.qq.com/s/zzzzz
```

2. 执行批量下载：

```bash
python wechat-cli.py download --file urls.txt
```

或使用简写：

```bash
python wechat-cli.py download -f urls.txt
```

### 指定输出目录

```bash
# 下载到指定目录
python wechat-cli.py download "url" --output ./my_articles
python wechat-cli.py download -f urls.txt -o ./downloads
```

### 显示详细日志

```bash
# 查看详细的下载过程
python wechat-cli.py download "url" --verbose
python wechat-cli.py download -f urls.txt -v
```

### 组合使用

```bash
# 批量下载 + 自定义目录 + 详细日志
python wechat-cli.py download -f urls.txt -o ./articles -v
```

### 下载结果

命令行工具会显示：
- ✅ 成功下载的文章数量
- ❌ 失败的文章数量及错误信息
- 📁 文章保存路径
- ⏱️ 总耗时统计

示例输出：
```
============================================================
从文件读取URL: urls.txt
============================================================

[1/3] 正在下载: 文章标题1
✅ 下载成功: ./downloads/文章标题1.html

[2/3] 正在下载: 文章标题2
✅ 下载成功: ./downloads/文章标题2.html

[3/3] 正在下载: 文章标题3
✅ 下载成功: ./downloads/文章标题3.html

============================================================
下载完成!
============================================================
成功: 3 篇
失败: 0 篇
总耗时: 15.3 秒
```

## 🔑 重要提示

### 关于登录

1. **首次使用**需要扫码登录微信公众平台
   - 在添加公众号时点击"从公众平台获取"
   - 系统会显示二维码
   - 使用微信扫码登录

2. **登录会话**会自动保存
   - 会话文件：`data/wechat_session.json`
   - 会话有效期通常为几天到几周
   - 失效后会提示重新登录

3. **安全建议**
   - ⚠️ **不要分享会话文件**，它包含您的登录凭证
   - 不要在公共环境使用
   - 定期更新密码提高安全性





## ⚠️ 常见问题

### Q1: 启动时提示端口被占用

**问题**：`Address already in use` 或端口 5000 被占用

**解决方案**：
```bash
# 方案1: 修改端口（编辑 run.py）
app.run(host="0.0.0.0", port=5001, debug=config.DEBUG)

# 方案2: 查找并关闭占用端口的进程
# Windows
netstat -ano | findstr :5000
taskkill /PID <进程ID> /F

# Linux/macOS
lsof -i :5000
kill -9 <PID>
```

### Q2: 无法连接到微信公众平台

**问题**：采集时提示连接失败

**解决方案**：
1. 检查网络连接，确保可以访问 https://mp.weixin.qq.com
2. 检查是否有代理或防火墙拦截
3. 尝试在浏览器中手动访问该网站
4. 检查 hosts 文件是否有相关配置

### Q3: Playwright 浏览器无法启动

**问题**：`Executable doesn't exist` 或浏览器启动失败

**解决方案**：
```bash
# 重新安装浏览器
playwright install chromium

# 如果还不行，安装系统依赖（Linux）
playwright install-deps chromium

# 强制重新安装
playwright install --force chromium
```

### Q4: 采集时提示"请先登录"或"会话失效"

**问题**：之前登录过，但现在提示需要登录

**解决方案**：
1. 删除会话文件：`data/wechat_session.json`
2. 重新在界面上进行扫码登录
3. 确保扫码时使用正确的微信账号
4. 检查 `data` 目录是否有写入权限

### Q5: 下载的图片无法显示

**问题**：打开 HTML 文件后图片不显示

**解决方案**：
1. 确保 HTML 文件和 `images/` 目录在同一个文件夹
2. 不要移动文件位置，保持相对路径关系
3. 检查 `images/` 目录中是否有图片文件
4. 确保图片文件没有被防病毒软件删除

### Q6: 数据库锁定错误

**问题**：`database is locked` 错误

**解决方案**：
1. 不要同时进行多个采集或下载操作
2. SQLite 不支持高并发写操作
3. 等待当前操作完成后再进行下一个
4. 确保没有多个程序实例同时运行
5. 重启应用可以释放锁

### Q7: 采集到的文章数量为 0

**问题**：采集完成但没有新文章

**可能原因**：
1. 该公众号最近没有发布新文章
2. 所有文章都已经采集过（自动去重）
3. Fakeid 不正确，无法获取文章列表
4. 登录会话问题

**解决方案**：
1. 检查该公众号是否真的有文章
2. 查看日志文件了解详细信息：`logs/collect.log`
3. 确认 Fakeid 是否正确
4. 尝试重新登录

### Q8: 命令行工具无法使用

**问题**：`ModuleNotFoundError` 或导入错误

**解决方案**：
```bash
# 确保已经安装项目
pip install -e .

# 或者使用完整路径
python wechat-cli.py download "url"

# 检查 Python 环境
python --version  # 需要 3.12+
```

### Q9: 内存占用过高

**问题**：采集或下载时内存占用很大

**解决方案**：
1. 这是正常现象，Playwright 浏览器会占用内存
2. 采集完成后浏览器会自动关闭，释放内存
3. 减少批量操作的数量
4. 分批次进行采集和下载

### Q10: 日志文件过大

**问题**：`logs/` 目录占用空间过大

**解决方案**：
```bash
# 可以安全删除旧日志
# Windows
del logs\*.log

# Linux/macOS
rm logs/*.log

# 或者使用日志轮转（未来版本会支持）
```

## 📚 进一步学习

- 查看 [README.md](../README.md) 了解项目详情
- 查看 [DEVELOPMENT.md](./DEVELOPMENT.md) 了解开发指南
