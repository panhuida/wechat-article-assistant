"""数据验证工具"""

import re


def validate_required(value: str | None, field_name: str) -> bool:
    """
    验证必填字段

    Args:
        value: 字段值
        field_name: 字段名称

    Returns:
        验证是否通过
    """
    return bool(value and str(value).strip())


def validate_url(url: str | None) -> bool:
    """
    验证URL格式

    Args:
        url: URL字符串

    Returns:
        验证是否通过
    """
    if not url:
        return False
    url_pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    return url_pattern.match(url) is not None


def validate_wechat_article_url(url: str | None) -> bool:
    """
    验证微信文章URL

    Args:
        url: URL字符串

    Returns:
        验证是否通过
    """
    if not url:
        return False
    return "mp.weixin.qq.com" in url
