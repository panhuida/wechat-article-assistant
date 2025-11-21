#!/usr/bin/env bash
# 快速设置脚本 - 使用 uv

set -e

echo "🚀 开始设置 wechat-article-assistant 项目..."
echo ""

# 检查 uv 是否安装
if ! command -v uv &> /dev/null; then
    echo "❌ 未检测到 uv，正在安装..."
    echo ""
    
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        # Windows
        powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    else
        # Linux/macOS
        curl -LsSf https://astral.sh/uv/install.sh | sh
    fi
    
    echo ""
    echo "✅ uv 安装完成！"
    echo ""
else
    echo "✅ 检测到 uv $(uv --version)"
    echo ""
fi

# 创建虚拟环境并安装依赖
echo "📦 正在安装项目依赖..."
uv sync
echo ""
echo "✅ 依赖安装完成！"
echo ""

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "📝 创建 .env 配置文件..."
    cp .env.example .env
    echo "✅ .env 文件已创建，请根据需要修改配置"
    echo ""
fi

# 安装 Playwright 浏览器
echo "🌐 正在安装 Playwright 浏览器..."
.venv/bin/playwright install chromium 2>/dev/null || .venv/Scripts/playwright.exe install chromium 2>/dev/null
echo ""
echo "✅ Playwright 浏览器安装完成！"
echo ""

echo "🎉 项目设置完成！"
echo ""
echo "接下来的步骤："
echo "  1. 激活虚拟环境："
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "     .venv\\Scripts\\activate"
else
    echo "     source .venv/bin/activate"
fi
echo "  2. 启动应用："
echo "     uv run python run.py"
echo "  3. 访问 http://localhost:5000"
echo ""
echo "📚 更多信息请查看 docs/UV_GUIDE.md"
