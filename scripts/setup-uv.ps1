# 快速设置脚本 - 使用 uv (Windows PowerShell)

Write-Host "🚀 开始设置 wechat-article-assistant 项目..." -ForegroundColor Cyan
Write-Host ""

# 检查 uv 是否安装
$uvInstalled = Get-Command uv -ErrorAction SilentlyContinue

if (-not $uvInstalled) {
    Write-Host "❌ 未检测到 uv，正在安装..." -ForegroundColor Yellow
    Write-Host ""
    
    # 安装 uv
    Invoke-Expression "& {$(Invoke-RestMethod https://astral.sh/uv/install.ps1)} -NoModifyPath"
    
    Write-Host ""
    Write-Host "✅ uv 安装完成！" -ForegroundColor Green
    Write-Host ""
    
    # 刷新环境变量
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
} else {
    $version = uv --version
    Write-Host "✅ 检测到 $version" -ForegroundColor Green
    Write-Host ""
}

# 创建虚拟环境并安装依赖
Write-Host "📦 正在安装项目依赖..." -ForegroundColor Cyan
uv sync
Write-Host ""
Write-Host "✅ 依赖安装完成！" -ForegroundColor Green
Write-Host ""

# 检查 .env 文件
if (-not (Test-Path .env)) {
    Write-Host "📝 创建 .env 配置文件..." -ForegroundColor Cyan
    Copy-Item .env.example .env
    Write-Host "✅ .env 文件已创建，请根据需要修改配置" -ForegroundColor Green
    Write-Host ""
}

# 安装 Playwright 浏览器
Write-Host "🌐 正在安装 Playwright 浏览器..." -ForegroundColor Cyan
.\.venv\Scripts\playwright.exe install chromium
Write-Host ""
Write-Host "✅ Playwright 浏览器安装完成！" -ForegroundColor Green
Write-Host ""

Write-Host "🎉 项目设置完成！" -ForegroundColor Green
Write-Host ""
Write-Host "接下来的步骤：" -ForegroundColor Yellow
Write-Host "  1. 激活虚拟环境："
Write-Host "     .venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  2. 启动应用："
Write-Host "     uv run python run.py" -ForegroundColor White
Write-Host "  3. 访问 http://localhost:5000"
Write-Host ""
Write-Host "📚 更多信息请查看 docs\UV_GUIDE.md" -ForegroundColor Cyan
