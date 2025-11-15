"""应用启动脚本"""

import sys
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from wechat_article_assistant.app import app
from wechat_article_assistant.config import config

if __name__ == "__main__":
    print("=" * 60)
    print("微信公众号文章阅读助手")
    print("=" * 60)
    print(f"服务地址: http://127.0.0.1:5000")
    print(f"调试模式: {config.DEBUG}")
    print("=" * 60)
    print()

    app.run(host="0.0.0.0", port=5000, debug=config.DEBUG)
