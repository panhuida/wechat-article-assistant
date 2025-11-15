"""文章下载服务"""

import re
import requests
from pathlib import Path
from typing import Optional, List, Tuple
from bs4 import BeautifulSoup
from ..config import config
from ..utils.logger import download_logger
from ..utils.file_helper import sanitize_filename, ensure_dir, get_file_extension, get_unique_filename


class DownloadService:
    """文章下载服务"""

    def __init__(self):
        """初始化下载服务"""
        self.download_dir = config.DOWNLOAD_DIR

    def download_article(
        self,
        article_url: str,
        article_title: str,
        account_name: str = "未分类",
        save_dir: Path = None
    ) -> Tuple[bool, str]:
        """
        下载单篇文章

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
            images_dir = ensure_dir(account_dir / "images")

            # 获取文章HTML
            response = requests.get(article_url, timeout=30)
            response.encoding = "utf-8"
            html_content = response.text

            # 解析HTML
            soup = BeautifulSoup(html_content, "html.parser")

            # 下载图片并替换链接
            img_tags = soup.find_all("img")
            downloaded_images = []

            for idx, img_tag in enumerate(img_tags):
                img_url = img_tag.get("data-src") or img_tag.get("src")
                if not img_url:
                    continue

                # 处理相对URL
                if img_url.startswith("//"):
                    img_url = "https:" + img_url
                elif img_url.startswith("/"):
                    img_url = "https://mp.weixin.qq.com" + img_url

                # 下载图片
                try:
                    img_response = requests.get(img_url, timeout=30)
                    if img_response.status_code == 200:
                        ext = get_file_extension(img_url)
                        img_filename = f"img_{idx}{ext}"
                        img_path = images_dir / img_filename

                        with open(img_path, "wb") as f:
                            f.write(img_response.content)

                        # 替换图片链接为本地相对路径
                        img_tag["src"] = f"images/{img_filename}"
                        if img_tag.get("data-src"):
                            img_tag["data-src"] = f"images/{img_filename}"

                        downloaded_images.append(img_filename)
                        download_logger.info(f"下载图片: {img_filename}")
                except Exception as e:
                    download_logger.warning(f"下载图片失败 {img_url}: {e}")

            # 保存HTML文件
            html_filename = sanitize_filename(article_title) + ".html"
            html_path = get_unique_filename(account_dir, html_filename)

            with open(html_path, "w", encoding="utf-8") as f:
                f.write(str(soup))

            download_logger.info(f"文章下载成功: {html_path}")
            return True, f"下载成功，保存至: {html_path}"

        except Exception as e:
            error_msg = f"下载文章失败: {e}"
            download_logger.error(error_msg)
            return False, error_msg

    def download_articles_batch(
        self,
        articles: List[dict],
        save_dir: Path = None
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

    def download_from_file(self, file_path: str, save_dir: Path = None) -> Tuple[int, int, List[str]]:
        """
        从文件读取URL列表并下载

        Args:
            file_path: 文件路径（每行一个URL）
            save_dir: 保存目录（可选）

        Returns:
            (成功数量, 失败数量, 错误消息列表)
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                urls = [line.strip() for line in f if line.strip()]

            articles = []
            for idx, url in enumerate(urls):
                articles.append({
                    "url": url,
                    "title": f"文章_{idx + 1}",
                    "account_name": "批量下载"
                })

            return self.download_articles_batch(articles, save_dir)
        except Exception as e:
            download_logger.error(f"从文件下载失败: {e}")
            return 0, 0, [str(e)]
