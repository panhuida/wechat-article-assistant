# 部署指南

## 环境准备

### 系统要求

- Python 3.12 或更高版本
- 至少 500MB 可用磁盘空间
- 互联网连接（用于下载依赖和访问微信公众平台）

### 依赖安装

#### 方式一：使用 pip

```bash
pip install -r requirements.txt
```

#### 方式二：使用 uv（推荐）

```bash
# 安装 uv
pip install uv

# 使用 uv 安装依赖
uv pip install -r requirements.txt
```

### Playwright 浏览器安装

```bash
playwright install chromium
```

## 配置

### 1. 环境变量配置

复制 `.env.example` 为 `.env`：

```bash
cp .env.example .env
```

编辑 `.env` 文件，根据需要修改配置：

```env
# Flask配置
SECRET_KEY=your-secret-key-here-change-this  # 修改为随机字符串
FLASK_DEBUG=False  # 生产环境设置为False

# 数据库配置
DATABASE_URL=sqlite:///data/wechat_assistant.db

# 日志配置
LOG_LEVEL=INFO

# 下载配置
DOWNLOAD_DIR=data/downloads
```

### 2. 数据库初始化

首次运行时会自动初始化数据库，也可以手动初始化：

```bash
python -c "from src.wechat_article_assistant.models import init_db; init_db()"
```

## 部署方式

### 方式一：开发环境运行

```bash
python run.py
```

访问：http://localhost:5000

### 方式二：生产环境部署

#### 使用 Gunicorn（Linux/macOS）

1. 安装 Gunicorn：

```bash
pip install gunicorn
```

2. 启动服务：

```bash
gunicorn -w 4 -b 0.0.0.0:5000 "src.wechat_article_assistant.app:app"
```

参数说明：
- `-w 4`: 4个工作进程
- `-b 0.0.0.0:5000`: 绑定到所有网络接口的5000端口
- `--timeout 300`: 超时时间（采集和下载可能需要较长时间）

#### 使用 Waitress（Windows）

1. 安装 Waitress：

```bash
pip install waitress
```

2. 启动服务：

```bash
waitress-serve --host=0.0.0.0 --port=5000 src.wechat_article_assistant.app:app
```

### 方式三：Docker 部署（可选）

创建 `Dockerfile`：

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安装 Playwright 浏览器
RUN playwright install chromium
RUN playwright install-deps chromium

COPY . .

# 初始化数据库
RUN python -c "from src.wechat_article_assistant.models import init_db; init_db()"

EXPOSE 5000

CMD ["python", "run.py"]
```

构建和运行：

```bash
docker build -t wechat-article-assistant .
docker run -d -p 5000:5000 -v ./data:/app/data wechat-article-assistant
```

## Nginx 反向代理配置

如果需要通过域名访问，可以配置 Nginx 反向代理：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时配置（采集和下载可能需要较长时间）
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
    }
}
```

## 系统服务配置

### Systemd 服务（Linux）

创建 `/etc/systemd/system/wechat-article-assistant.service`：

```ini
[Unit]
Description=Wechat Article Assistant
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/wechat-article-assistant
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 "src.wechat_article_assistant.app:app"
Restart=always

[Install]
WantedBy=multi-user.target
```

启用并启动服务：

```bash
sudo systemctl enable wechat-article-assistant
sudo systemctl start wechat-article-assistant
sudo systemctl status wechat-article-assistant
```

## 安全建议

1. **修改 SECRET_KEY**：在生产环境中务必修改为随机字符串
2. **防火墙配置**：只开放必要的端口
3. **HTTPS**：建议使用 HTTPS 访问，可以通过 Let's Encrypt 免费申请证书
4. **访问控制**：如需限制访问，可以配置 Nginx 的 basic auth 或其他认证方式
5. **备份**：定期备份 `data/` 目录

## 日志管理

日志文件位于 `logs/` 目录：

- `app.log`: 应用日志
- `collect.log`: 采集日志
- `download.log`: 下载日志

可以使用 logrotate 进行日志轮转管理。

## 故障排查

### 1. 数据库锁定错误

如果遇到 "database is locked" 错误，可能是因为 SQLite 不支持高并发。解决方案：

- 减少 worker 数量
- 考虑迁移到 PostgreSQL 或 MySQL

### 2. Playwright 浏览器问题

如果浏览器无法启动：

```bash
# 重新安装浏览器
playwright install --force chromium

# 安装系统依赖
playwright install-deps chromium
```

### 3. 端口被占用

如果 5000 端口被占用，可以修改端口：

```bash
# 修改 run.py 中的端口号
app.run(host="0.0.0.0", port=8080, debug=config.DEBUG)
```

## 性能优化

1. **使用生产级 WSGI 服务器**：Gunicorn 或 Waitress
2. **启用静态文件缓存**：通过 Nginx 配置静态文件缓存
3. **数据库优化**：定期清理不需要的数据
4. **异步任务**：对于耗时的采集和下载任务，可以考虑使用 Celery 等任务队列

## 升级

```bash
# 拉取最新代码
git pull

# 更新依赖
pip install -r requirements.txt

# 重启服务
sudo systemctl restart wechat-article-assistant
```
