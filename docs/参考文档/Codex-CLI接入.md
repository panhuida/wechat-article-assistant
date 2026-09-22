# 在 Codex 中使用微信公众号 CLI

项目提供 `wechat-cli` 和兼容入口 `wechat-article-assistant`，均指向相同实现。
用户级 Skill 源码在 `skills/huida-wechat-articles`，负责选择命令、处理错误和读取下载文件。

## Windows 本机安装

在项目目录执行：

```powershell
uv sync
powershell -ExecutionPolicy Bypass -File scripts/install-codex-skill.ps1
.\scripts\wechat-cli.cmd doctor --json
```

启动器保存在项目的 `scripts/wechat-cli.cmd`，随 Git 管理。安装器仅将技能复制到 `~/.agents/skills/huida-wechat-articles` 并生成本机路径说明，不修改环境变量。可用 `-SkillsDirectory` 指定其他技能根目录。

手动打开 Windows「编辑账户的环境变量」，在当前用户的 `Path` 中新增项目的 `scripts` 目录，例如：

```text
D:\study\code\github\wechat-article-assistant\scripts
```

添加目录，不是 `.cmd` 文件；无需修改系统级 PATH。重新打开终端后，可运行 `Get-Command wechat-cli` 检查是否指向项目启动器，再运行 `wechat-cli doctor --json`。未配置 PATH 时仍可通过绝对路径调用。

启动器通过自身位置定位仓库，使用本仓库 `.venv`，为每次调用设置 `WECHAT_ASSISTANT_HOME` 指向本仓库，与 Web 端共用现有 `.env`、数据库及登录态。启动器不改变调用方当前目录，所以相对 `--output` 和 `--file` 相对于任务目录。源码更新即时生效；依赖变化后运行 `uv sync`，技能更新或仓库移动后重新运行安装器；移动仓库还需手动更新 PATH。

这属于本地开发安装，依赖仓库和 `.venv` 持续存在。已打开的 Codex 可能需要重启以读取新 PATH 和新技能；技能的 `runtime.md` 也记录了可直接调用的绝对启动器路径。

在 Codex 中可使用 `$huida-wechat-articles` 指定该技能。从旧方案迁移时，应移除旧的 `.local/bin/wechat-cli.cmd` 和 `.codex/skills/wechat-articles`，避免重复入口；保留 `.local/bin` 的 PATH 项供其他工具使用。安装器不会自动删除旧版本。

## 独立工具环境

不依赖项目虚拟环境时，可另行安装：

```powershell
uv tool install 'D:\path\to\wechat-article-assistant'
$env:WECHAT_ASSISTANT_HOME = 'D:\path\to\shared-data'
wechat-cli doctor --json
```

此方式需要单独设置共享数据目录并安装 Skill。不要同时在同一命令目录保留两种安装方式，以免 PATH 优先级造成混淆。需要浏览器扫码登录时，在实际运行 CLI 的 Python 环境安装 Playwright Chromium（源码环境可用 `uv run playwright install chromium`）。

## 配置路径

`WECHAT_ASSISTANT_HOME` 必须在进程启动前设置为应用目录，读取该目录的 `.env`，显式环境变量优先。未设置时，源码运行使用仓库根目录，安装包使用 `~/.wechat-article-assistant`。不会搜索调用方目录的 `.env`。

相对 SQLite 文件路径、`LOG_DIR`、`DOWNLOAD_DIR`、`DOWNLOAD_PATH` 和 `SESSION_FILE` 均相对于应用目录；绝对路径保持原位置。内存 SQLite 和 PostgreSQL URL 保持原语义。不同工具环境只要使用相同应用目录和配置即可共享数据。

`doctor` 仅输出非敏感的路径和存在性信息，不验证网络连接或会话有效性。首次使用空数据库仍需通过 Web 应用初始化并添加公众号。

## 命令示例

```powershell
wechat-cli download 'https://mp.weixin.qq.com/s/...' --output 'D:\文章' --json
wechat-cli download --file 'D:\urls.txt' --format html --output 'D:\文章' --json
wechat-cli collect-recent --json
wechat-cli download-articles --start-time 2026-09-21 --end-time 2026-09-21 --nickname '公众号A,公众号B' --output 'D:\文章' --json
wechat-cli login
```

`collect-recent` 获取所有已配置公众号最近 5 次群发，更新数据库；下载命令才保存正文。它不保证覆盖指定日期范围内的全部历史。`download-articles` 仅筛选库内文章，名称精确匹配。默认 Markdown，纯日期结束时间包含当天；日期按本机时间解释。

采集默认仅复用现有登录态，失效时立即返回需要登录。`login` 或 `collect-recent --interactive` 允许打开浏览器扫码。Web 原有交互认证流程保持兼容。

## 输出协议

`--json` 可放在子命令前或后。stdout 仅输出一个 JSON 对象，日志写入 stderr；帮助文本仍为普通文本。

字段为 `schema_version=1`、`command`、`status`、`exit_code`、`message`、`success_count`、`failure_count`、`items` 和 `details`。下载项包含实际标题、URL、成功状态、消息、文件绝对路径、错误代码和可选数据库文章 ID。路径在文件写入成功后返回，不通过日志解析或扫描目录推测。

| 退出码 | 含义 |
| --- | --- |
| 0 | 成功，允许空匹配 |
| 1 | 执行失败 |
| 2 | 参数错误或空链接文件 |
| 3 | 部分失败 |
| 4 | 需要登录 |
| 5 | 全部下载项被微信环境验证拦截 |

下载计数单位为文章；采集计数单位为公众号，文章数在 `details.total_articles`。部分失败应处理成功项并仅重试失败项。文件正文成功不保证每张远程图片都下载成功，图片失败仍按原有逻辑保留远程引用并记录日志。

兼容变化：单篇下载失败不再返回退出码 0；部分失败使用 3，参数错误统一使用 2。CLI 批量下载仅标记实际成功的数据库文章。原 Python 下载服务二元组及批量三元组接口保留，Web 调用方无需迁移。
