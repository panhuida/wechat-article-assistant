param(
    [string]$SkillsDirectory = (Join-Path $env:USERPROFILE '.agents\skills')
)

$ErrorActionPreference = 'Stop'
$repoPath = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$pythonPath = Join-Path $repoPath '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw '请先在项目目录运行 uv sync。'
}
$launcherPath = Join-Path $PSScriptRoot 'wechat-cli.cmd'
$skillPath = Join-Path $SkillsDirectory 'huida-wechat-articles'
$installedSkill = Join-Path $skillPath 'SKILL.md'
$runtimePath = Join-Path $skillPath 'runtime.md'
$marker = 'wechat-article-assistant managed installation'
# 仅更新本安装器管理的技能，不修改 PATH。
if ((Test-Path -LiteralPath $skillPath) -and
    (-not (Test-Path -LiteralPath $runtimePath) -or -not ((Get-Content -LiteralPath $runtimePath -Raw).Contains($marker)))) {
    throw "已有非本项目管理的技能：$skillPath"
}
if (-not (Test-Path -LiteralPath $launcherPath)) { throw "项目启动器不存在：$launcherPath" }
New-Item -ItemType Directory -Path $skillPath -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $repoPath 'skills\huida-wechat-articles\SKILL.md') -Destination $installedSkill
$runtime = @"
<!-- $marker -->
# 本机运行位置

启动器：$launcherPath

PowerShell 调用示例：

``````powershell
& '$($launcherPath.Replace("'", "''"))' doctor --json
``````

应用数据目录：$repoPath

启动器根据自身位置定位仓库，使用仓库的 .env、数据库及登录态，调用方工作目录保持不变。
启动器依赖此仓库和 .venv；移动仓库后重新运行安装器，并手动更新用户 PATH 中的 scripts 目录。
"@
[IO.File]::WriteAllText($runtimePath, $runtime, [Text.UTF8Encoding]::new($false))
Write-Output "项目命令：$launcherPath"
Write-Output "已安装技能：$installedSkill"
Write-Output "请手动将此目录加入用户 PATH：$PSScriptRoot"
Write-Output '安装器未修改 PATH。配置后重新打开终端；也可直接通过启动器绝对路径调用。'
