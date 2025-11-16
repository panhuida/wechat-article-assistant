"""二维码生成工具"""

import base64
from io import BytesIO

import qrcode


def generate_qr_code(data: str, size: int = 300) -> str:
    """
    生成二维码并返回base64编码的图片

    Args:
        data: 二维码数据
        size: 图片大小

    Returns:
        base64编码的图片字符串
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # 转换为base64
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    return f"data:image/png;base64,{img_str}"
