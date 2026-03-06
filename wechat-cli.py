#!/usr/bin/env python
"""
微信公众号文章助手 - 命令行工具
使用方法:
  python wechat-cli.py download <article_url>
  python wechat-cli.py download --file <file_path>
  python wechat-cli.py download <article_url> --output <output_dir>
  python wechat-cli.py collect-recent
  python wechat-cli.py download-articles --start-time 2026-03-05 --end-time 2026-03-06
  python wechat-cli.py download-articles --start-time 2026-03-05 --end-time 2026-03-06 --nickname 测试公众号
  python wechat-cli.py download-articles --start-time 2026-03-05 --end-time 2026-03-06 --nickname 公众号A,公众号B
"""

import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from wechat_article_assistant.cli import main

if __name__ == "__main__":
    main()
