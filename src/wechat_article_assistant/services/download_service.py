"""文章下载服务"""

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

from ..config import config
from ..utils.file_helper import (
    ensure_dir,
    sanitize_filename,
)
from ..utils.logger import get_module_logger

logger = get_module_logger(__name__)


class DownloadService:
    """文章下载服务"""

    def __init__(self):
        """初始化下载服务"""
        self.download_dir = config.DOWNLOAD_DIR

    def _download_and_replace_image(
        self, img_url: str, img_index: Any, article_url: str, download_dir: Path, assets_dir: Path
    ) -> str | None:
        """
        下载单张图片并返回本地相对路径

        Args:
            img_url: 图片URL
            img_index: 图片索引
            article_url: 文章URL（用于解析相对路径）
            download_dir: 文章下载目录
            assets_dir: 图片资源目录

        Returns:
            本地相对路径，失败返回None
        """
        try:
            # 处理相对URL
            full_img_url = urljoin(article_url, img_url)

            # 下载图片
            img_response = requests.get(full_img_url, timeout=15)
            img_response.raise_for_status()

            # 根据Content-Type确定扩展名
            content_type = img_response.headers.get("Content-Type", "")
            if "jpeg" in content_type or "jpg" in content_type:
                ext = ".jpg"
            elif "png" in content_type:
                ext = ".png"
            elif "gif" in content_type:
                ext = ".gif"
            elif "webp" in content_type:
                ext = ".webp"
            else:
                ext = Path(full_img_url).suffix or ".jpg"

            # 清理扩展名中的参数
            ext = ext.split("?")[0]

            img_filename = f"image_{img_index}{ext}"
            img_path = assets_dir / img_filename

            with img_path.open("wb") as f:
                for chunk in img_response.iter_content(1024):
                    f.write(chunk)

            # 返回相对于下载目录的路径
            relative_img_path = img_path.relative_to(download_dir)
            logger.info(f"下载图片成功: {img_filename}")
            return relative_img_path.as_posix()

        except Exception as e:
            logger.warning(f"下载图片失败: {img_url}, 错误: {e}")
            return None

    def _inject_publish_info(self, soup: BeautifulSoup, html_content: str, article_url: str) -> None:
        """
        从JavaScript中提取发布时间和地点信息，并注入到HTML元素中

        Args:
            soup: BeautifulSoup对象
            html_content: 原始HTML内容
            article_url: 文章原始URL
        """
        try:
            # 提取发布时间
            # 尝试多种格式：
            # 1. var createTime = '2025-11-18 22:24';
            # 2. create_time: JsDecode('...')
            # 3. create_time = "..."
            create_time = None
            
            # 格式1：var createTime = '...'
            create_time_match = re.search(r"var\s+createTime\s*=\s*['\"]([^'\"]+)['\"]", html_content)
            if create_time_match:
                create_time = create_time_match.group(1)
                logger.debug(f"从 var createTime 提取到发布时间: {create_time}")
            else:
                # 格式2：create_time: JsDecode('...')
                create_time_match = re.search(r'create_time.*?JsDecode\([\'"]([^\'"]+)', html_content)
                if create_time_match:
                    create_time = create_time_match.group(1)
                    logger.debug(f"从 create_time JsDecode 提取到发布时间: {create_time}")
                else:
                    # 格式3：create_time = "..." 或 create_time: "..."
                    create_time_match = re.search(r'create_time\s*[:=]\s*["\']([^"\']+)', html_content)
                    if create_time_match:
                        create_time = create_time_match.group(1)
                        logger.debug(f"从 create_time 提取到发布时间: {create_time}")
            
            if create_time:
                # 查找发布时间元素
                publish_time_elem = soup.find("em", id="publish_time")
                if isinstance(publish_time_elem, Tag):
                    publish_time_elem.string = create_time
                    logger.info(f"成功注入发布时间: {create_time}")
                else:
                    logger.warning("未找到 publish_time 元素")
            else:
                logger.warning("未能从JavaScript中提取发布时间")

            # 提取IP归属地 (ip_wording)
            # 尝试两种格式：
            # 1. 旧格式：ip_wording: JsDecode('北京')
            # 2. 新格式：ip_wording: { province_name: JsDecode('北京'), ... }
            ip_wording = None
            
            # 先尝试新格式（对象格式）
            province_match = re.search(r'province_name:\s*JsDecode\([\'"]([^\'"]+)', html_content)
            if province_match:
                ip_wording = province_match.group(1)
                logger.debug(f"从province_name提取到IP归属地: {ip_wording}")
            else:
                # 尝试旧格式（直接字符串）
                ip_wording_match = re.search(r'ip_wording:\s*JsDecode\([\'"]([^\'"]+)', html_content)
                if ip_wording_match:
                    ip_wording = ip_wording_match.group(1)
                    logger.debug(f"从ip_wording提取到IP归属地: {ip_wording}")
            
            if ip_wording:
                # 查找IP归属地元素
                ip_wording_elem = soup.find("span", id="js_ip_wording")
                if isinstance(ip_wording_elem, Tag):
                    ip_wording_elem.string = ip_wording
                    # 显示父容器元素
                    ip_wording_wrp = soup.find("em", id="js_ip_wording_wrp")
                    if isinstance(ip_wording_wrp, Tag):
                        # 移除 display: none 样式
                        if ip_wording_wrp.has_attr("style"):
                            style = ip_wording_wrp["style"]
                            if isinstance(style, str):
                                new_style = re.sub(r'display\s*:\s*none\s*;?', '', style).strip()
                                if new_style:
                                    ip_wording_wrp["style"] = new_style
                                else:
                                    del ip_wording_wrp["style"]
                    logger.info(f"成功注入IP归属地: {ip_wording}")
                else:
                    logger.warning("未找到 js_ip_wording 元素")
            else:
                logger.info("未找到IP归属地信息（某些文章可能没有此信息）")

            # 添加原文链接
            # 查找元信息容器
            meta_content_elem = soup.find("span", id="meta_content_hide_info")
            if isinstance(meta_content_elem, Tag):
                # 创建原文链接元素
                source_link_em = soup.new_tag("em", **{"class": "rich_media_meta rich_media_meta_text"})
                source_link_em["style"] = "margin-left: 10px;"
                
                # 创建链接
                source_link_a = soup.new_tag("a")
                source_link_a["href"] = article_url
                source_link_a["target"] = "_blank"
                source_link_a["style"] = "color: #576b95; text-decoration: none;"
                source_link_a.string = article_url
                
                source_link_em.append(source_link_a)
                meta_content_elem.append(source_link_em)
                logger.info(f"成功注入原文链接: {article_url}")
            else:
                logger.warning("未找到 meta_content_hide_info 元素")

        except Exception as e:
            logger.warning(f"注入发布信息时出错: {e}")

    def _clean_wechat_ui_elements(self, soup: BeautifulSoup) -> None:
        """
        清理微信特定的UI元素，保留文章核心内容

        Args:
            soup: BeautifulSoup对象
        """
        try:
            # 1. 移除底部的互动工具栏（点赞、分享、评论等）
            selectors_to_remove = [
                # 底部工具栏和互动区
                {"id": "js_bottom_ad_area"},
                {"class_": "rich_media_tool"},
                {"id": "js_pc_qr_code"},
                {"class_": "qr_code_pc"},
                {"class_": "rich_media_extra"},
                # 分享、点赞相关
                {"id": "js_share_bar"},
                {"id": "like"},
                {"class_": "reward_area"},
                {"id": "js_preview_reward_panel"},
                # 阅读原文、相关文章推荐
                {"id": "js_related_container"},
                {"id": "js_toobar3"},
                {"class_": "rich_media_area_extra"},
                # 页面遮罩和弹窗
                {"class_": "wx_tap_card"},
                {"class_": "profile_container"},
                {"class_": "wx_follow_area"},
                {"class_": "weui-desktop-popover"},  # 二维码弹窗
                {"class_": "weui-dialog"},  # 对话框
                {"class_": "jump_wx_qrcode_desc"},  # 扫码提示
                # 小程序卡片
                {"class_": "weapp_card"},
                {"class_": "miniprogram_card"},
                # 其他UI提示和按钮
                {"id": "js_tags"},
                {"class_": "rich_media_meta_nickname"},  # 可点击的公众号名称
                {"class_": "wx_stream_article_slide_tip"},  # 滑动提示
                {"class_": "stream_bottom"},  # 底部滑动区域
                {"id": "wx_expand_article_button"},  # 阅读原文按钮
            ]

            for selector in selectors_to_remove:
                elements = soup.find_all(**selector)
                for elem in elements:
                    if isinstance(elem, Tag):
                        elem.decompose()

            # 2. 清理所有 javascript: 链接
            for link in soup.find_all("a", href=True):
                if isinstance(link, Tag):
                    href = link.get("href", "")
                    if isinstance(href, str) and "javascript:" in href.lower():
                        # 将链接转换为span，保留文本
                        text_content = link.get_text()
                        new_span = soup.new_tag("span")
                        new_span.string = text_content
                        # 复制class等属性
                        if link.has_attr("class"):
                            new_span["class"] = link["class"]
                        link.replace_with(new_span)

            # 3. 移除包含特定UI提示的元素
            # 使用更精确的查找方式
            ui_patterns = [
                ("继续滑动看下一个", "div"),
                ("轻触阅读原文", "div"),
                ("向上滑动看下一个", "div"),
                ("知道了", "div"),
                ("微信扫一扫", "p"),
                ("关注该公众号", "p"),
                ("使用小程序", "p"),
                ("在小说阅读器中沉浸阅读", "p"),
            ]

            for pattern, tag_name in ui_patterns:
                elements = soup.find_all(tag_name, string=lambda s: s and pattern in str(s))
                for elem in elements:
                    if isinstance(elem, Tag):
                        # 检查父元素是否也应该被移除
                        parent = elem.parent
                        if isinstance(parent, Tag):
                            # 如果父元素内容很少，移除父元素
                            parent_text = parent.get_text(strip=True)
                            if len(parent_text) < 50 and pattern in parent_text:
                                parent.decompose()
                            else:
                                elem.decompose()

            # 4. 移除底部的多个空白或无用section/div
            # 保留主要内容区域
            main_content = soup.find("div", id="js_content")
            if main_content and isinstance(main_content, Tag):
                # 找到内容区域的父容器
                content_parent = main_content.parent
                if isinstance(content_parent, Tag):
                    # 移除内容区域之后的所有兄弟元素（通常是底部UI）
                    for sibling in list(main_content.find_next_siblings()):
                        if isinstance(sibling, Tag):
                            sibling.decompose()

            # 5. 清理空的div和section
            # 先收集要删除的元素，避免在迭代时修改
            elements_to_remove = []
            for elem in soup.find_all(["div", "section"]):
                if isinstance(elem, Tag):
                    # 跳过重要的内容容器
                    elem_id = elem.get("id")
                    if elem_id in ["js_content", "page-content"]:
                        continue
                    
                    elem_class = elem.get("class")
                    if elem_class and "rich_media_content" in elem_class:
                        continue
                    
                    # 如果元素为空或只包含空白
                    text = elem.get_text(strip=True)
                    if not text:
                        # 检查是否包含图片
                        if not elem.find("img"):
                            elements_to_remove.append(elem)
            
            # 批量删除
            for elem in elements_to_remove:
                elem.decompose()

            logger.info("成功清理微信UI元素")

        except Exception as e:
            import traceback
            logger.warning(f"清理微信UI元素时出错: {e}")
            logger.debug(f"详细错误: {traceback.format_exc()}")

    def _extract_picture_urls_from_js_array(self, html_content: str) -> list[str]:
        """
        从JavaScript的picture_page_info_list数组中提取图片URL
        只提取第一层对象中的cdn_url，不包括嵌套对象
        
        Args:
            html_content: HTML源代码
            
        Returns:
            图片URL列表
        """
        picture_urls = []
        
        # 查找picture_page_info_list数组
        list_start_pattern = r'picture_page_info_list\s*:\s*\['
        list_start_match = re.search(list_start_pattern, html_content)
        
        if not list_start_match:
            logger.debug("未找到picture_page_info_list")
            return picture_urls
        
        start_pos = list_start_match.end()
        
        # 查找数组结束：查找下一个顶级字段
        end_pattern = r'\n\s{0,8}\w+\s*:'
        temp_text = html_content[start_pos:start_pos+80000]
        end_match = re.search(end_pattern, temp_text)
        
        if end_match:
            end_pos = start_pos + end_match.start()
        else:
            end_pos = start_pos + 50000
        
        list_content = html_content[start_pos:end_pos]
        
        # 逐字符解析，找到每个顶层对象
        objects = []
        depth = 0
        current_obj_start = -1
        in_string = False
        escape_next = False
        i = 0
        
        while i < len(list_content):
            char = list_content[i]
            
            if escape_next:
                escape_next = False
            elif char == '\\':
                escape_next = True
            elif char in ('"', "'") and not escape_next:
                in_string = not in_string
            elif not in_string:
                if char == '{':
                    if depth == 0:
                        current_obj_start = i
                    depth += 1
                elif char == '}':
                    depth -= 1
                    if depth == 0 and current_obj_start >= 0:
                        obj_content = list_content[current_obj_start:i+1]
                        objects.append(obj_content)
                        current_obj_start = -1
            
            i += 1
        
        # 在每个对象中只提取第一个cdn_url
        for obj in objects:
            match = re.search(r"cdn_url:\s*JsDecode\(['\"]([^'\"]+)['\"]", obj)
            if match:
                picture_urls.append(match.group(1))
        
        if picture_urls:
            logger.info(f"从picture_page_info_list提取到 {len(picture_urls)} 个图片URL（仅第一层）")
        else:
            logger.warning("picture_page_info_list数组的第一层未找到cdn_url")
        
        return picture_urls

    def _process_text_only_article(
        self, 
        soup: BeautifulSoup, 
        article_title: str, 
        html_content: str,
        article_url: str
    ) -> None:
        """
        处理纯文字文章（item_show_type=10）
        这类文章没有正常的body内容，标题就是全部内容
        
        Args:
            soup: BeautifulSoup对象
            article_title: 文章标题（即内容）
            html_content: HTML源代码（用于提取发布信息）
            article_url: 文章原始URL
        """
        logger.info("处理纯文字文章，将标题内容注入到页面")
        
        # 提取发布信息
        publish_time_str = None
        ip_location_str = None
        
        time_match = re.search(r"var\s+createTime\s*=\s*['\"]([^'\"]+)['\"]", html_content)
        if time_match:
            publish_time_str = time_match.group(1)
            logger.debug(f"提取到发布时间: {publish_time_str}")
        
        province_match = re.search(r'province_name:\s*JsDecode\([\'"]([^\'"]+)', html_content)
        if province_match:
            ip_location_str = province_match.group(1)
            logger.debug(f"提取到IP归属地: {ip_location_str}")
        
        # 查找或创建 js_content 容器
        content_div = soup.find("div", id="js_content")
        if not isinstance(content_div, Tag):
            body = soup.find("body")
            if isinstance(body, Tag):
                content_div = soup.new_tag("div", id="js_content")
                body.append(content_div)
                logger.info("创建了 js_content 容器")
        
        if not isinstance(content_div, Tag):
            logger.warning("无法创建 js_content 容器")
            return
        
        # 清空原有内容
        content_div.clear()
        
        # 添加发布信息和原文链接
        if publish_time_str or ip_location_str or article_url:
            info_div = soup.new_tag("div")
            info_div["style"] = "color: #888; font-size: 14px; margin-bottom: 2em; padding-bottom: 1em; border-bottom: 1px solid #eee;"
            
            info_parts = []
            if publish_time_str:
                info_parts.append(publish_time_str)
            if ip_location_str:
                info_parts.append(ip_location_str)
            
            # 添加文本部分
            if info_parts:
                info_text = "  ".join(info_parts)
                info_div.append(info_text)
            
            # 添加原文链接
            if article_url:
                if info_parts:
                    info_div.append("  ")
                link_a = soup.new_tag("a")
                link_a["href"] = article_url
                link_a["target"] = "_blank"
                link_a["style"] = "color: #576b95; text-decoration: none;"
                link_a.string = article_url
                info_div.append(link_a)
            
            content_div.append(info_div)
            logger.info(f"已添加发布信息和原文链接")
        
        # 将标题内容格式化后插入
        processed_title = article_title.replace('\\n', '\n')
        processed_title = processed_title.replace('\r\n', '\n').replace('\r', '\n')
        paragraphs = processed_title.split('\n\n')
        
        for para in paragraphs:
            para = para.strip()
            if para:
                lines = para.split('\n')
                p_tag = soup.new_tag("p")
                p_tag["style"] = "margin: 1em 0; line-height: 1.8; font-size: 16px;"
                
                for i, line in enumerate(lines):
                    line = line.strip()
                    if line:
                        if i > 0:
                            p_tag.append(soup.new_tag("br"))
                        p_tag.append(line)
                
                content_div.append(p_tag)
        
        logger.info(f"已将标题内容注入到 js_content，共 {len(paragraphs)} 个段落")

    def _process_image_only_article(
        self, 
        soup: BeautifulSoup, 
        article_title: str, 
        html_content: str,
        article_url: str
    ) -> None:
        """
        处理纯图片文章（item_show_type=8）
        这类文章的HTML中可能没有js_content容器，需要特殊处理
        
        Args:
            soup: BeautifulSoup对象
            article_title: 文章标题
            html_content: HTML源代码
            article_url: 文章原始URL
        """
        logger.info("处理纯图片文章，创建完整内容容器")
        
        # 提取发布信息
        publish_time_str = None
        ip_location_str = None
        
        time_match = re.search(r"create_time:\s*JsDecode\(['\"]([^'\"]+)['\"]", html_content)
        if time_match:
            publish_time_str = time_match.group(1)
            logger.debug(f"提取到发布时间: {publish_time_str}")
        else:
            time_match = re.search(r"var\s+createTime\s*=\s*['\"]([^'\"]+)['\"]", html_content)
            if time_match:
                publish_time_str = time_match.group(1)
                logger.debug(f"提取到发布时间（备用格式）: {publish_time_str}")
        
        province_match = re.search(r'province_name:\s*JsDecode\([\'"]([^\'"]+)', html_content)
        if province_match:
            ip_location_str = province_match.group(1)
            logger.debug(f"提取到IP归属地: {ip_location_str}")
        
        # 提取标题（从og:title）
        image_title = article_title
        og_title_meta = soup.find("meta", property="og:title")
        if og_title_meta and isinstance(og_title_meta, Tag):
            og_title = og_title_meta.get("content", "")
            if og_title:
                image_title = og_title
                logger.debug(f"从og:title提取标题: {image_title}")
        
        # 提取描述（从og:description）
        description = ""
        og_desc_meta = soup.find("meta", property="og:description")
        if og_desc_meta and isinstance(og_desc_meta, Tag):
            description = og_desc_meta.get("content", "")
        
        # 提取滑动图片信息
        picture_urls = self._extract_picture_urls_from_js_array(html_content)
        
        # 检查是否有js_content
        content_div = soup.find("div", id="js_content")
        if not isinstance(content_div, Tag):
            body = soup.find("body")
            if not isinstance(body, Tag):
                logger.warning("未找到 body 标签，无法创建内容容器")
                return
            
            content_div = soup.new_tag("div", id="js_content")
            content_div["style"] = "padding: 20px; max-width: 800px; margin: 0 auto;"
            
            # 1. 添加标题
            title_h1 = soup.new_tag("h1")
            title_h1["style"] = "font-size: 24px; font-weight: bold; margin-bottom: 10px; line-height: 1.4;"
            title_h1.string = image_title
            content_div.append(title_h1)
            
            # 2. 添加发布信息和原文链接
            if publish_time_str or ip_location_str or article_url:
                info_div = soup.new_tag("div")
                info_div["style"] = "color: #888; font-size: 14px; margin-bottom: 20px;"
                
                info_parts = []
                if publish_time_str:
                    info_parts.append(publish_time_str)
                if ip_location_str:
                    info_parts.append(ip_location_str)
                
                # 添加文本部分
                if info_parts:
                    info_text = "  ".join(info_parts)
                    info_div.append(info_text)
                
                # 添加原文链接
                if article_url:
                    if info_parts:
                        info_div.append("  ")
                    link_a = soup.new_tag("a")
                    link_a["href"] = article_url
                    link_a["target"] = "_blank"
                    link_a["style"] = "color: #576b95; text-decoration: none;"
                    link_a.string = article_url
                    info_div.append(link_a)
                
                content_div.append(info_div)
            
            # 3. 添加描述（如果有）
            if description:
                desc_div = soup.new_tag("div")
                desc_div["style"] = "color: #000000; font-size: 15px; margin-bottom: 20px; line-height: 1.6;"
                
                import re as regex_module
                import html
                
                # 替换十六进制转义序列
                def hex_replace(match):
                    hex_str = match.group(1)
                    return chr(int(hex_str, 16))
                
                decoded_desc = regex_module.sub(r'\\x([0-9a-fA-F]{2})', hex_replace, description)
                decoded_desc = html.unescape(decoded_desc)
                decoded_desc = html.unescape(decoded_desc)
                decoded_desc = decoded_desc.replace('\n', '<br>')
                
                from bs4 import BeautifulSoup as BS
                temp_soup = BS(f'<div>{decoded_desc}</div>', 'html.parser')
                
                for child in list(temp_soup.div.children):
                    desc_div.append(child)
                
                content_div.append(desc_div)
            
            # 4. 添加分隔线
            hr = soup.new_tag("hr")
            hr["style"] = "border: none; border-top: 1px solid #eee; margin: 20px 0;"
            content_div.append(hr)
            
            # 5. 添加图片
            if picture_urls:
                logger.info(f"使用picture_page_info_list中的 {len(picture_urls)} 张图片")
                
                for idx, img_url in enumerate(picture_urls):
                    img_container = soup.new_tag("div")
                    img_container["style"] = "margin: 20px 0;"
                    
                    img_tag = soup.new_tag("img")
                    img_tag["src"] = img_url
                    img_tag["style"] = "max-width: 100%; height: auto; display: block; margin-bottom: 10px; cursor: pointer;"
                    img_tag["loading"] = "lazy"
                    img_container.append(img_tag)
                    
                    link_div = soup.new_tag("div")
                    link_div["style"] = "font-size: 12px; color: #999;"
                    
                    link_a = soup.new_tag("a")
                    link_a["href"] = img_url
                    link_a["target"] = "_blank"
                    link_a["style"] = "color: #576b95; text-decoration: none;"
                    
                    filename = img_url.split('/')[-1].split('?')[0]
                    link_a.string = f"📎 图片 {idx + 1}: {filename}"
                    
                    link_div.append(link_a)
                    img_container.append(link_div)
                    content_div.append(img_container)
            else:
                all_imgs = soup.find_all("img")
                if all_imgs:
                    logger.info(f"未找到picture_page_info_list，使用HTML中的 {len(all_imgs)} 张图片")
                    
                    for idx, img in enumerate(all_imgs):
                        img_container = soup.new_tag("div")
                        img_container["style"] = "margin: 20px 0;"
                        
                        img_copy = soup.new_tag("img")
                        for attr, value in img.attrs.items():
                            img_copy[attr] = value
                        img_copy["style"] = "max-width: 100%; height: auto; display: block; margin-bottom: 10px; cursor: pointer;"
                        img_container.append(img_copy)
                        
                        img_src = img.get("src", "")
                        if img_src:
                            link_div = soup.new_tag("div")
                            link_div["style"] = "font-size: 12px; color: #999;"
                            
                            link_a = soup.new_tag("a")
                            link_a["href"] = img_src
                            link_a["target"] = "_blank"
                            link_a["style"] = "color: #576b95; text-decoration: none;"
                            
                            filename = img_src.split('/')[-1].split('?')[0]
                            link_a.string = f"📎 图片 {idx + 1}: {filename}"
                            
                            link_div.append(link_a)
                            img_container.append(link_div)
                        
                        content_div.append(img_container)
            
            body.insert(0, content_div)
            logger.info("已创建 js_content 容器并添加完整内容")

    def _process_normal_article(self, soup: BeautifulSoup) -> None:
        """
        处理普通文章
        确保文章内容可见
        
        Args:
            soup: BeautifulSoup对象
        """
        content_div = soup.find("div", id="js_content")
        if isinstance(content_div, Tag) and content_div.has_attr("style"):
            del content_div["style"]
            logger.info("强制显示文章内容")

    def download_article(
        self,
        article_url: str,
        article_title: str,
        account_name: str = "未分类",
        save_dir: Path | None = None,
    ) -> tuple[bool, str]:
        """
        下载单篇文章（包含HTML、图片、CSS等资源）

        Args:
            article_url: 文章URL
            article_title: 文章标题
            account_name: 公众号名称
            save_dir: 保存目录（可选）

        Returns:
            (是否成功, 消息)
        """
        try:
            logger.info(f"开始下载文章: {article_title}")

            # 创建公众号目录
            base_dir = save_dir or self.download_dir
            account_dir = ensure_dir(base_dir / sanitize_filename(account_name))

            # 获取文章HTML
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            }
            response = requests.get(article_url, headers=headers, timeout=20)
            response.raise_for_status()

            # 使用 response.content 让 BeautifulSoup 自行处理编码
            soup = BeautifulSoup(response.content, "lxml")

            # === 自动提取文章真实标题 ===
            extracted_title = None

            # 优先尝试从 <title> 标签提取
            title_tag = soup.find("title")
            if isinstance(title_tag, Tag) and title_tag.string and title_tag.string.strip():
                extracted_title = title_tag.string.strip()
                logger.info(f"从 <title> 标签提取标题: {extracted_title[:50]}...")

            # 如果没有找到或标题为空，尝试从 og:title meta标签提取
            if not extracted_title:
                og_title = soup.find("meta", property="og:title")
                if isinstance(og_title, Tag) and og_title.get("content"):
                    extracted_title = og_title.get("content", "").strip()
                    logger.info(f"从 og:title 提取标题: {extracted_title[:50]}...")

            # 如果还没有找到，尝试从 <h1> 提取
            if not extracted_title:
                h1_tag = soup.find("h1")
                if h1_tag:
                    extracted_title = h1_tag.get_text().strip()
                    logger.info(f"从 <h1> 标签提取标题: {extracted_title[:50]}...")

            # 如果成功提取到标题，使用提取的标题替换传入的标题
            if extracted_title:
                article_title = extracted_title
                logger.info(f"使用提取的标题: {article_title[:50]}...")
            else:
                logger.warning(f"未能从页面提取标题，使用传入的标题: {article_title}")

            # === 提取 item_show_type 以确定文章类型和文件名长度 ===
            # item_show_type = 10: 纯文字文章（标题即内容）
            # item_show_type = 8: 纯图片文章（内容主要是图片）
            max_filename_length = 100  # 默认长度
            item_show_type_match = re.search(r'item_show_type["\']?\s*[:=]\s*["\']?(\d+)', response.text)
            is_text_only_article = False  # 标记是否为纯文字文章
            is_image_only_article = False  # 标记是否为纯图片文章
            
            if item_show_type_match:
                item_show_type = int(item_show_type_match.group(1))
                logger.info(f"检测到 item_show_type: {item_show_type}")
                if item_show_type == 10:
                    max_filename_length = 40
                    is_text_only_article = True
                    logger.info(f"item_show_type=10，这是纯文字文章（标题即内容），使用较短文件名长度: {max_filename_length}")
                elif item_show_type == 8:
                    is_image_only_article = True
                    logger.info(f"item_show_type=8，这是纯图片文章")

            # === 确保HTML头中有正确的编码声明 ===
            head = soup.find("head")
            if isinstance(head, Tag):
                # 移除旧的charset，避免冲突
                for meta_tag in head.find_all("meta", attrs={"charset": True}):
                    meta_tag.decompose()
                # 插入新的UTF-8 meta标签
                meta_charset_tag = soup.new_tag("meta", charset="UTF-8")
                head.insert(0, meta_charset_tag)
            else:
                logger.warning(f"文章 '{article_title}' 缺少 <head> 标签")

            # === 根据文章类型进行不同处理 ===
            if is_text_only_article:
                self._process_text_only_article(soup, article_title, response.text, article_url)
            elif is_image_only_article:
                self._process_image_only_article(soup, article_title, response.text, article_url)
            else:
                self._process_normal_article(soup)

            # 创建文章和图片文件夹
            base_filename = sanitize_filename(article_title, max_length=max_filename_length)
            article_path = account_dir / f"{base_filename}.html"
            assets_dir = ensure_dir(account_dir / f"{base_filename}.assets")

            # === 下载并替换CSS ===
            for link in soup.find_all("link", rel="stylesheet"):
                if isinstance(link, Tag):
                    css_url = link.get("href")
                    if not css_url or not isinstance(css_url, str):
                        continue

                    css_url = urljoin(article_url, css_url)
                    try:
                        css_response = requests.get(css_url, timeout=15)
                        if css_response.status_code == 200:
                            css_filename = Path(css_url).name or "style.css"
                            css_filename = f"{Path(css_filename).stem}_{hash(css_url) % 10000}{Path(css_filename).suffix}"
                            css_path = assets_dir / css_filename

                            with css_path.open("w", encoding="utf-8") as f:
                                f.write(css_response.text)

                            relative_css_path = css_path.relative_to(account_dir)
                            link["href"] = relative_css_path.as_posix()
                            logger.info(f"下载CSS成功: {css_filename}")
                    except Exception as e:
                        logger.warning(f"下载CSS失败: {css_url}, 错误: {e}")

            # === 下载并替换图片 ===
            img_tags = soup.find_all("img")
            for i, img in enumerate(img_tags):
                if isinstance(img, Tag):
                    # 优先处理 data-src，其次是 src
                    img_url = img.get("data-src") or img.get("src")
                    srcset = img.get("srcset")

                    if not img_url and not srcset:
                        continue

                    # 处理主图片 (src/data-src)
                    if isinstance(img_url, str):
                        local_img_path = self._download_and_replace_image(
                            img_url, i, article_url, account_dir, assets_dir
                        )
                        if local_img_path:
                            img["src"] = local_img_path
                            # 确保 data-src 也被更新或移除
                            if img.has_attr("data-src"):
                                img["data-src"] = local_img_path

                    # 处理 srcset
                    if isinstance(srcset, str):
                        new_srcset = []
                        for part in srcset.split(","):
                            part = part.strip()
                            if not part:
                                continue

                            url_part = part.split()[0]
                            descriptor = part.split()[1] if len(part.split()) > 1 else ""

                            local_path = self._download_and_replace_image(
                                url_part,
                                f"{i}_{descriptor.replace(' ', '')}",
                                article_url,
                                account_dir,
                                assets_dir,
                            )
                            if local_path:
                                new_srcset.append(f"{local_path} {descriptor}")

                        if new_srcset:
                            img["srcset"] = ", ".join(new_srcset)

            # === 提取并注入发布时间和地点信息 ===
            self._inject_publish_info(soup, response.text, article_url)

            # === 清理微信UI元素 ===
            self._clean_wechat_ui_elements(soup)

            # === 移除所有脚本（包括外部和内联） ===
            # 移除所有script标签，因为静态HTML不需要JavaScript
            for script in soup.find_all("script"):
                if isinstance(script, Tag):
                    script.decompose()

            # 保存修改后的HTML
            with article_path.open("w", encoding="utf-8") as f:
                f.write(str(soup))

            # 保存元数据文件
            meta_path = account_dir / f"{base_filename}.html.meta.json"
            meta_data = {"source_url": article_url}
            with meta_path.open("w", encoding="utf-8") as f:
                json.dump(meta_data, f, ensure_ascii=False, indent=4)

            logger.info(f"文章下载成功: {article_path}")
            return True, f"下载成功，保存至: {article_path}"

        except Exception as e:
            error_msg = f"下载文章失败: {e}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg

    def download_articles_batch(
        self, articles: list[dict[str, Any]], save_dir: Path | None = None
    ) -> tuple[int, int, list[str]]:
        """
        批量下载文章

        Args:
            articles: 文章列表，每项包含 url, title, account_name
            save_dir: 保存目录（可选）

        Returns:
            (成功数量, 失败数量, 错误消息列表)
        """
        success_count = 0
        fail_count = 0
        errors = []

        for article in articles:
            url = article.get("url") or article.get("article_link")
            title = article.get("title") or article.get("article_title")
            account = article.get("account_name") or article.get("nickname", "未分类")

            if not isinstance(url, str) or not isinstance(title, str):
                fail_count += 1
                errors.append(f"无效的文章数据: {article}")
                continue

            success, msg = self.download_article(url, title, account, save_dir)
            if success:
                success_count += 1
            else:
                fail_count += 1
                errors.append(f"{title}: {msg}")

        logger.info(f"批量下载完成: 成功 {success_count}, 失败 {fail_count}")
        return success_count, fail_count, errors

    def download_from_file(
        self, file_path: str, save_dir: Path | None = None
    ) -> tuple[int, int, list[str]]:
        """
        从文件读取URL列表并下载

        支持的文件格式：
        - 每行一个URL
        - 以 # 开头的行视为注释，会被忽略
        - 空行会被忽略

        Args:
            file_path: 文件路径（每行一个URL）
            save_dir: 保存目录（可选）

        Returns:
            (成功数量, 失败数量, 错误消息列表)
        """
        try:
            with Path(file_path).open(encoding="utf-8") as f:
                lines = f.readlines()

            # 过滤注释和空行
            urls = []
            for line in lines:
                line = line.strip()
                # 跳过空行和注释行
                if not line or line.startswith("#"):
                    continue
                urls.append(line)

            if not urls:
                logger.warning(f"文件中没有找到有效的URL: {file_path}")
                return 0, 0, ["文件中没有找到有效的URL"]

            logger.info(f"从文件读取到 {len(urls)} 个URL")

            articles = []
            for idx, url in enumerate(urls):
                articles.append(
                    {"url": url, "title": f"文章_{idx + 1}", "account_name": "批量下载"}
                )

            return self.download_articles_batch(articles, save_dir)
        except Exception as e:
            logger.error(f"从文件下载失败: {e}")
            return 0, 0, [str(e)]
