# Windows用户全局使用指南

本指南帮助Windows用户在任意位置使用 `wechat-cli` 命令。

## 方法一：添加到系统PATH（推荐）

### 步骤说明

1. **右键点击"此电脑"** → 选择"属性"

2. **点击"高级系统设置"**

3. **点击"环境变量"按钮**

4. **在"系统变量"区域找到"Path"变量** → 点击"编辑"

5. **点击"新建"按钮**，添加项目路径：
   ```
   E:\study\code\github\wechat-article-assistant
   ```
   （请替换为你的实际项目路径）

6. **点击"确定"保存所有更改**

7. **重新打开命令提示符或PowerShell**
   - 注意：必须重新打开，已打开的窗口不会生效

### 验证配置

打开新的命令提示符，输入：
```bash
wechat-cli --help
```

如果显示帮助信息，说明配置成功！

### 使用方法

配置成功后，可以在任意目录下使用：

```bash
# 在任意位置下载文章
C:\Users\YourName> wechat-cli download https://mp.weixin.qq.com/s/xxxxx

# 在桌面上批量下载
C:\Users\YourName\Desktop> wechat-cli download --file article_list.txt
```

## 方法二：创建桌面快捷方式

### 创建批处理文件

在桌面或其他常用位置创建 `wechat-download.bat`：

```batch
@echo off
echo ========================================
echo 微信公众号文章下载工具
echo ========================================
echo.

REM 切换到项目目录
cd /d E:\study\code\github\wechat-article-assistant

REM 提示输入URL
set /p article_url="请输入文章URL: "

REM 执行下载
wechat-cli download %article_url%

echo.
echo 下载完成！按任意键退出...
pause > nul
```

### 使用方法

双击 `wechat-download.bat`，按提示输入URL即可下载。

## 方法三：右键菜单集成

### 下载URL文件时自动处理

创建注册表文件 `add_to_context_menu.reg`：

```registry
Windows Registry Editor Version 5.00

[HKEY_CLASSES_ROOT\txtfile\shell\WechatDownload]
@="使用微信助手批量下载"

[HKEY_CLASSES_ROOT\txtfile\shell\WechatDownload\command]
@="\"E:\\study\\code\\github\\wechat-article-assistant\\wechat-cli.bat\" download --file \"%1\""
```

**注意**：
1. 将路径中的 `E:\\study\\code\\github\\wechat-article-assistant` 替换为你的实际路径
2. 路径中的反斜杠 `\` 需要写两次 `\\`

**安装步骤**：
1. 双击 `.reg` 文件
2. 确认添加到注册表
3. 之后右键点击 `.txt` 文件，会出现"使用微信助手批量下载"选项

## 方法四：使用别名（PowerShell）

### 添加PowerShell配置

1. 打开PowerShell配置文件：
   ```powershell
   notepad $PROFILE
   ```
   如果文件不存在，会提示创建。

2. 添加以下内容：
   ```powershell
   # 微信公众号文章助手别名
   function wechat-cli {
       python E:\study\code\github\wechat-article-assistant\wechat-cli.py $args
   }
   ```

3. 保存并重新加载配置：
   ```powershell
   . $PROFILE
   ```

### 使用方法

在PowerShell中可以直接使用：
```powershell
wechat-cli download <url>
```

## 方法五：创建快速启动脚本

### 在用户目录创建脚本

在 `C:\Users\YourName\` 目录下创建 `wechat-cli.bat`：

```batch
@echo off
python E:\study\code\github\wechat-article-assistant\wechat-cli.py %*
```

### 添加到用户PATH

1. 将 `C:\Users\YourName` 添加到用户PATH（不是系统PATH）
2. 这样不需要管理员权限

## 验证和测试

配置完成后，测试以下命令：

```bash
# 测试1：查看帮助
wechat-cli --help

# 测试2：查看下载命令帮助
wechat-cli download --help

# 测试3：实际下载（使用测试URL）
wechat-cli download https://mp.weixin.qq.com/s/test_article
```

## 常见问题

### Q1: 提示 'wechat-cli' 不是内部或外部命令

**原因**：PATH配置未生效或配置错误

**解决**：
1. 检查PATH中的路径是否正确
2. 确保重新打开了命令行窗口
3. 尝试使用完整路径测试

### Q2: 提示找不到Python

**原因**：Python未安装或未添加到PATH

**解决**：
1. 确认Python已安装：
   ```bash
   python --version
   ```
2. 如果未显示版本号，需要安装Python或将Python添加到PATH

### Q3: 命令执行了但没有效果

**原因**：工作目录不正确

**解决**：
使用完整路径指定输出目录：
```bash
wechat-cli download <url> --output E:\Downloads
```

### Q4: 权限不足无法修改系统PATH

**解决**：使用方法四或方法五，只修改用户级别的配置

## 推荐配置

根据使用频率推荐：

- **偶尔使用**：方法二（桌面快捷方式）
- **经常使用**：方法一（系统PATH）+ 方法二
- **重度使用**：方法一 + 方法三（右键菜单）
- **PowerShell用户**：方法四
- **无管理员权限**：方法五

## 配置成功标志

成功配置后，你应该能够：

1. ✓ 在任意目录运行 `wechat-cli --help`
2. ✓ 快速下载单篇文章
3. ✓ 右键.txt文件批量下载
4. ✓ 不需要记住项目路径

## 备份和迁移

如果需要迁移到其他电脑：

1. **导出配置**：
   - 记录PATH配置
   - 备份 `.reg` 文件（如果使用方法三）
   - 备份PowerShell配置（如果使用方法四）

2. **迁移项目**：
   - 复制整个项目文件夹
   - 在新电脑上重新配置PATH
   - 导入注册表（如果需要）

## 高级技巧

### 技巧1：创建多个快捷命令

创建不同的批处理文件用于不同场景：

**快速下载到桌面.bat**：
```batch
@echo off
set /p url="URL: "
wechat-cli download %url% --output %USERPROFILE%\Desktop
```

**批量下载.bat**：
```batch
@echo off
set /p file="文件路径: "
wechat-cli download --file %file%
```

### 技巧2：结合Total Commander或其他文件管理器

在文件管理器中配置快捷键，选中txt文件后按快捷键自动批量下载。

### 技巧3：使用任务栏固定

将常用的批处理文件固定到任务栏，随时可以一键打开。

## 结语

选择适合自己的方法配置后，就可以享受便捷的命令行下载体验了！

如果遇到问题，请查看：
- 项目文档：`docs/TROUBLESHOOTING.md`
- 完整指南：`docs/CLI_GUIDE.md`
