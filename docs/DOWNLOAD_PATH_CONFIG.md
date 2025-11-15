# 下载路径配置说明

## 配置方法

### 方式1：使用绝对路径（推荐）

在 `.env` 文件中配置 `DOWNLOAD_PATH`：

```ini
# 自定义下载路径（绝对路径）
DOWNLOAD_PATH=E:/documents/文摘/公众号
```

### 方式2：使用相对路径（默认）

在 `.env` 文件中配置 `DOWNLOAD_DIR`：

```ini
# 项目内下载路径（相对路径）
DOWNLOAD_DIR=data/downloads
```

## 配置优先级

```
DOWNLOAD_PATH（绝对路径）> DOWNLOAD_DIR（相对路径）> 默认值
```

- 如果设置了 `DOWNLOAD_PATH`，将使用该绝对路径
- 如果没有设置 `DOWNLOAD_PATH`，将使用 `DOWNLOAD_DIR`（相对于项目根目录）
- 如果都没有设置，默认使用 `项目根目录/data/downloads`

## 路径格式

### Windows系统
```ini
# 使用正斜杠（推荐）
DOWNLOAD_PATH=E:/documents/文摘/公众号

# 或使用双反斜杠
DOWNLOAD_PATH=E:\\documents\\文摘\\公众号
```

### Linux/Mac系统
```ini
DOWNLOAD_PATH=/home/user/documents/wechat_articles
```

## 配置示例

### 示例1：个人文档目录
```ini
DOWNLOAD_PATH=C:/Users/YourName/Documents/微信公众号
```

### 示例2：网盘同步目录
```ini
DOWNLOAD_PATH=D:/OneDrive/文摘/公众号
```

### 示例3：移动硬盘
```ini
DOWNLOAD_PATH=F:/备份/公众号文章
```

### 示例4：网络共享目录
```ini
DOWNLOAD_PATH=//NAS/share/wechat_articles
```

## 验证配置

### 方法1：使用测试脚本

```bash
python test_download_path.py
```

输出示例：
```
============================================================
下载路径配置测试
============================================================

配置信息:
  DOWNLOAD_DIR = E:\documents\文摘\公众号
  类型: <class 'pathlib.WindowsPath'>
  是否为绝对路径: True
  路径存在: True

✅ 配置正确！下载路径已设置为: E:/documents/文摘/公众号

============================================================
✅ 下载目录创建成功（或已存在）
```

### 方法2：在Python中检查

```python
from wechat_article_assistant.config import config

print(f"下载路径: {config.DOWNLOAD_DIR}")
print(f"是否为绝对路径: {config.DOWNLOAD_DIR.is_absolute()}")
```

## 注意事项

1. **路径必须存在或可创建**
   - 应用启动时会自动创建不存在的目录
   - 确保有足够的权限创建和写入目录

2. **中文路径支持**
   - ✅ 支持中文目录名
   - 确保系统编码正确设置

3. **路径分隔符**
   - Windows: 使用 `/` 或 `\\`（推荐使用 `/`）
   - Linux/Mac: 使用 `/`

4. **空格处理**
   - 路径中可以包含空格
   - 不需要使用引号

5. **配置重载**
   - 修改 `.env` 后需要重启应用
   - 配置在应用启动时加载

## 下载文件结构

无论使用哪种路径配置，下载的文件结构都是一样的：

```
配置的下载路径/
└── 公众号名称/
    ├── 文章标题.html
    ├── 文章标题.html.meta.json
    └── 文章标题.assets/
        ├── image_0.jpg
        ├── image_1.png
        └── style_0.css
```

### 示例

如果配置：
```ini
DOWNLOAD_PATH=E:/documents/文摘/公众号
```

下载"段永朝读书"公众号的文章后，文件结构为：
```
E:/documents/文摘/公众号/
└── 段永朝读书/
    ├── 2024年终总结.html
    ├── 2024年终总结.html.meta.json
    └── 2024年终总结.assets/
        ├── image_0.jpg
        ├── image_1.jpg
        └── style_0.css
```

## 迁移现有下载

如果要迁移已下载的文章到新路径：

1. **停止应用**
   ```bash
   # 按 Ctrl+C 停止
   ```

2. **复制文件**
   ```bash
   # 从旧路径复制到新路径
   xcopy "项目目录\data\downloads" "E:\documents\文摘\公众号" /E /I /Y
   ```

3. **修改配置**
   ```ini
   # .env
   DOWNLOAD_PATH=E:/documents/文摘/公众号
   ```

4. **重启应用**
   ```bash
   python run.py
   ```

## 常见问题

### Q1: 路径不存在会怎样？
A: 应用启动时会自动创建目录，前提是有足够的权限。

### Q2: 可以使用网络路径吗？
A: 可以，但需要确保网络稳定且有访问权限。

### Q3: 修改路径后旧文件怎么办？
A: 旧文件不会自动迁移，需要手动复制到新路径。

### Q4: 路径包含中文会有问题吗？
A: 不会，程序使用 UTF-8 编码，完全支持中文路径。

### Q5: 可以在运行时更改路径吗？
A: 不可以，配置在应用启动时加载，修改后需要重启应用。

## 配置文件位置

```
项目根目录/
├── .env                    # 配置文件
├── .env.example            # 配置模板（可选）
└── src/
    └── wechat_article_assistant/
        └── config.py       # 配置类
```

## 环境变量说明

| 变量名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `DOWNLOAD_PATH` | 字符串 | 无 | 自定义下载路径（绝对路径），优先级最高 |
| `DOWNLOAD_DIR` | 字符串 | `data/downloads` | 相对路径，相对于项目根目录 |

## 完整配置示例

`.env` 文件：
```ini
# Flask配置
FLASK_APP=src.wechat_article_assistant.app
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here

# 数据库配置
DATABASE_URL=sqlite:///data/wechat_assistant.db

# 日志配置
LOG_LEVEL=INFO
LOG_DIR=logs

# 下载配置
# 方式1：使用绝对路径（推荐）
DOWNLOAD_PATH=E:/documents/文摘/公众号

# 方式2：使用相对路径（如果不设置 DOWNLOAD_PATH）
# DOWNLOAD_DIR=data/downloads

# 微信公众平台配置
WECHAT_MP_URL=https://mp.weixin.qq.com
SESSION_FILE=data/wechat_session.json
```

---

**更新日期**: 2025-11-15  
**适用版本**: v1.0+
