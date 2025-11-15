"""测试下载路径配置"""

import sys
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from wechat_article_assistant.config import config

print("=" * 60)
print("下载路径配置测试")
print("=" * 60)
print()

print("配置信息:")
print(f"  DOWNLOAD_DIR = {config.DOWNLOAD_DIR}")
print(f"  类型: {type(config.DOWNLOAD_DIR)}")
print(f"  是否为绝对路径: {config.DOWNLOAD_DIR.is_absolute()}")
print(f"  路径存在: {config.DOWNLOAD_DIR.exists()}")
print()

# 检查是否是目标路径
expected_path = Path("E:/documents/文摘/公众号")
if config.DOWNLOAD_DIR == expected_path:
    print("✅ 配置正确！下载路径已设置为: E:/documents/文摘/公众号")
else:
    print(f"⚠️  当前路径: {config.DOWNLOAD_DIR}")
    print(f"   期望路径: {expected_path}")

print()
print("=" * 60)

# 尝试创建目录
try:
    config.DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    print("✅ 下载目录创建成功（或已存在）")
except Exception as e:
    print(f"❌ 创建目录失败: {e}")
