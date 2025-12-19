"""文件操作辅助工具"""

import re
from pathlib import Path

__all__ = ["sanitize_filename", "ensure_dir", "get_file_extension", "get_unique_filename"]


def sanitize_filename(filename: str, max_length: int = 100) -> str:
    """
    清理文件名，替换非法字符并限制长度

    Args:
        filename: 原始文件名
        max_length: 文件名最大长度（默认100字符）

    Returns:
        清理后的文件名
    """
    # 移除换行符（直接删除，不替换为空格，避免标题过长）
    filename = re.sub(r"[\r\n]+", "", filename)
    # 移除多余空白
    filename = re.sub(r"\s+", " ", filename).strip()

    # 替换Windows文件名非法字符
    illegal_chars = r'[/\\:*?"<>|]'
    filename = re.sub(illegal_chars, "_", filename)

    # 限制文件名长度
    if len(filename) > max_length:
        # 保留前部分，避免截断时产生不完整的字符
        filename = filename[:max_length].rstrip()
        # 如果被截断，添加省略号标记
        # if filename:
        #     filename = filename + "..."

    # 确保文件名不为空
    if not filename:
        filename = "未命名文章"

    return filename


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
