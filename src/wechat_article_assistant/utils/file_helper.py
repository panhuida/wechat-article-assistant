"""文件操作辅助工具"""

import re
from pathlib import Path


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，替换非法字符

    Args:
        filename: 原始文件名

    Returns:
        清理后的文件名
    """
    # 替换Windows文件名非法字符
    illegal_chars = r'[/\\:*?"<>|]'
    return re.sub(illegal_chars, "_", filename)


def ensure_dir(path: Path) -> Path:
    """
    确保目录存在，不存在则创建

    Args:
        path: 目录路径

    Returns:
        目录路径
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_extension(url: str) -> str:
    """
    从URL获取文件扩展名

    Args:
        url: 文件URL

    Returns:
        文件扩展名（包含.）
    """
    path = url.split("?")[0]  # 移除查询参数
    ext = Path(path).suffix
    return ext if ext else ".jpg"  # 默认为jpg


def get_unique_filename(directory: Path, filename: str) -> Path:
    """
    获取唯一的文件名，如果文件已存在，添加数字后缀

    Args:
        directory: 目录路径
        filename: 文件名

    Returns:
        唯一的文件路径
    """
    path = directory / filename
    if not path.exists():
        return path

    p = Path(filename)
    name, ext = p.stem, p.suffix
    counter = 1
    while True:
        new_filename = f"{name}_{counter}{ext}"
        new_path = directory / new_filename
        if not new_path.exists():
            return new_path
        counter += 1
