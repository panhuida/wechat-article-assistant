"""文章下载服务"""

import re
import json
import requests
from pathlib import Path
from typing import Optional, List, Tuple
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from ..config import config
from ..utils.logger import download_logger
from ..utils.file_helper import (
    sanitize_filename,
    ensure_dir,
    get_file_extension,
    get_unique_filename,
)


class DownloadService:
    """文章下载服务"""

    def __init__(self):
        """初始化下载服务"""
        self.download_dir = config.DOWNLOAD_DIR

    def _download_and_replace_image(
        self, img_url: str, img_index: int, article_url: str, download_dir: Path, assets_dir: Path
    ) -> Optional[str]:
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

            with open(img_path, "wb") as f:
                for chunk in img_response.iter_content(1024):
                    f.write(chunk)

            # 返回相对于下载目录的路径
            relative_img_path = img_path.relative_to(download_dir)
            download_logger.info(f"下载图片成功: {img_filename}")
            return relative_img_path.as_posix()

        except Exception as e:
            download_logger.warning(f"下载图片失败: {img_url}, 错误: {e}")
            return None

    def download_article(
        self,
        article_url: str,
        article_title: str,
        account_name: str = "未分类",
        save_dir: Path = None,
    ) -> Tuple[bool, str]:
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
            download_logger.info(f"开始下载文章: {article_title}")

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
            if title_tag and title_tag.string:
                extracted_title = title_tag.string.strip()
                download_logger.info(f"从 <title> 标签提取标题: {extracted_title}")

            # 如果没有找到或标题为空，尝试从 <h1> 提取
            if not extracted_title:
                h1_tag = soup.find("h1")
                if h1_tag:
                    extracted_title = h1_tag.get_text().strip()
                    download_logger.info(f"从 <h1> 标签提取标题: {extracted_title}")

            # 如果成功提取到标题，使用提取的标题替换传入的标题
            if extracted_title:
                article_title = extracted_title
                download_logger.info(f"使用提取的标题: {article_title}")
            else:
                download_logger.warning(f"未能从页面提取标题，使用传入的标题: {article_title}")

            # === 确保HTML头中有正确的编码声明 ===
            head = soup.find("head")
            if head:
                # 移除旧的charset，避免冲突
                for meta_tag in head.find_all("meta", attrs={"charset": True}):
                    meta_tag.decompose()
                # 插入新的UTF-8 meta标签
                meta_charset_tag = soup.new_tag("meta", charset="UTF-8")
                head.insert(0, meta_charset_tag)
            else:
                download_logger.warning(f"文章 '{article_title}' 缺少 <head> 标签")

            # === 强制显示文章内容 ===
            content_div = soup.find("div", id="js_content")
            if content_div and content_div.has_attr("style"):
                del content_div["style"]
                download_logger.info(f"强制显示文章内容")

            # 创建文章和图片文件夹
            base_filename = sanitize_filename(article_title)
            article_path = account_dir / f"{base_filename}.html"
            assets_dir = ensure_dir(account_dir / f"{base_filename}.assets")

            # === 下载并替换CSS ===
            for link in soup.find_all("link", rel="stylesheet"):
                css_url = link.get("href")
                if not css_url:
                    continue

                css_url = urljoin(article_url, css_url)
                try:
                    css_response = requests.get(css_url, timeout=15)
                    if css_response.status_code == 200:
                        css_filename = Path(css_url).name or "style.css"
                        css_filename = f"{Path(css_filename).stem}_{hash(css_url) % 10000}{Path(css_filename).suffix}"
                        css_path = assets_dir / css_filename

                        with open(css_path, "w", encoding="utf-8") as f:
                            f.write(css_response.text)

                        relative_css_path = css_path.relative_to(account_dir)
                        link["href"] = relative_css_path.as_posix()
                        download_logger.info(f"下载CSS成功: {css_filename}")
                except Exception as e:
                    download_logger.warning(f"下载CSS失败: {css_url}, 错误: {e}")

            # === 下载并替换图片 ===
            img_tags = soup.find_all("img")
            for i, img in enumerate(img_tags):
                # 优先处理 data-src，其次是 src
                img_url = img.get("data-src") or img.get("src")
                srcset = img.get("srcset")

                if not img_url and not srcset:
                    continue

                # 处理主图片 (src/data-src)
                if img_url:
                    local_img_path = self._download_and_replace_image(
                        img_url, i, article_url, account_dir, assets_dir
                    )
                    if local_img_path:
                        img["src"] = local_img_path
                        # 确保 data-src 也被更新或移除
                        if img.has_attr("data-src"):
                            img["data-src"] = local_img_path

                # 处理 srcset
                if srcset:
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

            # === 移除所有外部脚本，保留内联脚本 ===
            for script in soup.find_all("script"):
                if script.has_attr("src"):
                    script.decompose()

            # 保存修改后的HTML
            with open(article_path, "w", encoding="utf-8") as f:
                f.write(str(soup))

            # 保存元数据文件
            meta_path = account_dir / f"{base_filename}.html.meta.json"
            meta_data = {"source_url": article_url}
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta_data, f, ensure_ascii=False, indent=4)

            download_logger.info(f"文章下载成功: {article_path}")
            return True, f"下载成功，保存至: {article_path}"

        except Exception as e:
            error_msg = f"下载文章失败: {e}"
            download_logger.error(error_msg, exc_info=True)
            return False, error_msg

    def download_articles_batch(
        self, articles: List[dict], save_dir: Path = None
    ) -> Tuple[int, int, List[str]]:
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

            success, msg = self.download_article(url, title, account, save_dir)
            if success:
                success_count += 1
            else:
                fail_count += 1
                errors.append(f"{title}: {msg}")

        download_logger.info(f"批量下载完成: 成功 {success_count}, 失败 {fail_count}")
        return success_count, fail_count, errors

    def download_from_file(
        self, file_path: str, save_dir: Path = None
    ) -> Tuple[int, int, List[str]]:
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
            with open(file_path, "r", encoding="utf-8") as f:
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
                download_logger.warning(f"文件中没有找到有效的URL: {file_path}")
                return 0, 0, ["文件中没有找到有效的URL"]

            download_logger.info(f"从文件读取到 {len(urls)} 个URL")

            articles = []
            for idx, url in enumerate(urls):
                articles.append(
                    {"url": url, "title": f"文章_{idx + 1}", "account_name": "批量下载"}
                )

            return self.download_articles_batch(articles, save_dir)
        except Exception as e:
            download_logger.error(f"从文件下载失败: {e}")
            return 0, 0, [str(e)]
