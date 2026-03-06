from pathlib import Path
from unittest.mock import Mock, patch

from bs4 import BeautifulSoup

from wechat_article_assistant.services.download_service import DownloadService


def test_build_markdown_content_from_article_body():
    """测试根据文章正文生成 Markdown 内容"""
    service = DownloadService()
    soup = BeautifulSoup(
        """
        <html>
          <body>
            <div id="js_content">
              <h2>小标题</h2>
              <p>第一段 <strong>加粗</strong> <a href="https://example.com">链接</a></p>
              <ul><li>项目A</li><li>项目B</li></ul>
              <blockquote><p>引用内容</p></blockquote>
              <pre>print("hello")</pre>
            </div>
          </body>
        </html>
        """,
        "html.parser",
    )

    markdown = service._build_markdown_content(
        soup,
        article_title="测试文章",
        article_url="https://mp.weixin.qq.com/s/test",
    )

    assert "# 测试文章" in markdown
    assert "> 原文链接: https://mp.weixin.qq.com/s/test" in markdown
    assert "## 小标题" in markdown
    assert "第一段 **加粗** [链接](https://example.com)" in markdown
    assert "- 项目A" in markdown
    assert "> 引用内容" in markdown
    assert '```\nprint("hello")\n```' in markdown


def test_build_markdown_content_falls_back_to_body():
    """测试缺少 js_content 时回退到 body"""
    service = DownloadService()
    soup = BeautifulSoup(
        """
        <html>
          <body>
            <p>只有 body 内容</p>
          </body>
        </html>
        """,
        "html.parser",
    )

    markdown = service._build_markdown_content(
        soup,
        article_title="回退测试",
        article_url="https://mp.weixin.qq.com/s/fallback",
    )

    assert "# 回退测试" in markdown
    assert "只有 body 内容" in markdown


def test_inline_image_tag_to_markdown():
    """测试图片节点转换为 Markdown 图片语法"""
    service = DownloadService()
    soup = BeautifulSoup('<img src="https://img.test/cover.png" alt="封面图">', "html.parser")

    markdown = service._inline_tag_to_markdown(soup.img)

    assert markdown == "![封面图](https://img.test/cover.png)"


def test_inject_publish_info_updates_time_ip_and_source_link():
    """测试注入发布时间、IP 归属地和原文链接"""
    service = DownloadService()
    soup = BeautifulSoup(
        """
        <html>
          <body>
            <em id="publish_time"></em>
            <em id="js_ip_wording_wrp" style="display: none;">
              <span id="js_ip_wording"></span>
            </em>
            <span id="meta_content_hide_info"></span>
          </body>
        </html>
        """,
        "html.parser",
    )
    html_content = """
        <script>
            var createTime = '2026-03-06 12:30';
            var data = { province_name: JsDecode('上海') };
        </script>
    """

    service._inject_publish_info(soup, html_content, "https://mp.weixin.qq.com/s/source")

    assert soup.find("em", id="publish_time").text == "2026-03-06 12:30"
    assert soup.find("span", id="js_ip_wording").text == "上海"
    assert soup.find("em", id="js_ip_wording_wrp").get("style") in (None, "")

    source_link = soup.find("a")
    assert source_link is not None
    assert source_link["href"] == "https://mp.weixin.qq.com/s/source"
    assert source_link.text == "https://mp.weixin.qq.com/s/source"


def test_inject_publish_info_tolerates_missing_fields():
    """测试缺少发布时间和 IP 信息时不会报错，并仍注入原文链接"""
    service = DownloadService()
    soup = BeautifulSoup(
        """
        <html>
          <body>
            <span id="meta_content_hide_info"></span>
          </body>
        </html>
        """,
        "html.parser",
    )

    service._inject_publish_info(soup, "<script>var noop = true;</script>", "https://x.test")

    source_link = soup.find("a")
    assert source_link is not None
    assert source_link["href"] == "https://x.test"


def test_download_and_replace_image_success(tmp_path: Path):
    """测试下载图片成功时返回相对路径并写入文件"""
    service = DownloadService()
    download_dir = tmp_path / "article"
    assets_dir = download_dir / "assets"
    assets_dir.mkdir(parents=True)

    mock_response = Mock()
    mock_response.headers = {"Content-Type": "image/png"}
    mock_response.iter_content.return_value = [b"chunk1", b"chunk2"]
    mock_response.raise_for_status.return_value = None

    with patch(
        "wechat_article_assistant.services.download_service.requests.get",
        return_value=mock_response,
    ) as mock_get:
        relative_path = service._download_and_replace_image(
            img_url="/images/test",
            img_index=1,
            article_url="https://mp.weixin.qq.com/s/test",
            download_dir=download_dir,
            assets_dir=assets_dir,
        )

    assert relative_path == "assets/image_1.png"
    assert (assets_dir / "image_1.png").read_bytes() == b"chunk1chunk2"
    mock_get.assert_called_once_with("https://mp.weixin.qq.com/images/test", timeout=15)


def test_download_and_replace_image_returns_none_on_request_failure(tmp_path: Path):
    """测试下载图片失败时返回 None"""
    service = DownloadService()
    download_dir = tmp_path / "article"
    assets_dir = download_dir / "assets"
    assets_dir.mkdir(parents=True)

    with patch(
        "wechat_article_assistant.services.download_service.requests.get",
        side_effect=RuntimeError("boom"),
    ):
        relative_path = service._download_and_replace_image(
            img_url="https://img.test/x.jpg",
            img_index=2,
            article_url="https://mp.weixin.qq.com/s/test",
            download_dir=download_dir,
            assets_dir=assets_dir,
        )

    assert relative_path is None
    assert list(assets_dir.iterdir()) == []


def test_clean_wechat_ui_elements_removes_known_ui_nodes():
    """测试清理微信 UI 元素时移除互动区和脚本链接"""
    service = DownloadService()
    soup = BeautifulSoup(
        """
        <html>
          <body>
            <!-- comment -->
            <div id="js_content"><p>正文内容</p></div>
            <div class="rich_media_tool">工具栏</div>
            <div id="js_share_bar">分享栏</div>
            <a href="javascript:void(0)" class="js_link">按钮</a>
            <div>继续滑动看下一个</div>
            <link rel="stylesheet" href="bad.css" />
          </body>
        </html>
        """,
        "html.parser",
    )

    service._clean_wechat_ui_elements(soup)

    assert soup.find("div", class_="rich_media_tool") is None
    assert soup.find("div", id="js_share_bar") is None
    assert soup.find(string=lambda text: text and "继续滑动看下一个" in text) is None
    assert soup.find("link") is None
    assert soup.find("a", href=lambda href: href and "javascript:" in href.lower()) is None


def test_clean_wechat_ui_elements_removes_empty_non_content_containers():
    """测试清理空容器时保留正文中的图片容器"""
    service = DownloadService()
    soup = BeautifulSoup(
        """
        <html>
          <body>
            <div id="js_content">
              <div id="image-box"><img src="https://img.test/1.jpg" /></div>
            </div>
            <div id="empty"></div>
            <section id="empty-section">   </section>
          </body>
        </html>
        """,
        "html.parser",
    )

    service._clean_wechat_ui_elements(soup)

    assert soup.find("div", id="js_content") is not None
    assert soup.find("div", id="empty") is None
    assert soup.find("section", id="empty-section") is None
    assert soup.find("div", id="image-box") is not None


def test_download_article_markdown_writes_article_and_meta_files(tmp_path: Path):
    """测试单篇下载 markdown 时写入正文和元数据文件"""
    service = DownloadService()
    service.download_dir = tmp_path

    html = """
        <html>
          <head><title>页面标题</title></head>
          <body>
            <div id="js_content">
              <p>正文内容</p>
              <script>window.alert('x')</script>
            </div>
          </body>
        </html>
    """
    response = Mock()
    response.content = html.encode("utf-8")
    response.text = html
    response.raise_for_status.return_value = None

    with patch(
        "wechat_article_assistant.services.download_service.requests.get",
        return_value=response,
    ), patch.object(service, "_inject_publish_info") as mock_inject, patch.object(
        service, "_clean_wechat_ui_elements"
    ) as mock_clean, patch.object(
        service, "_download_and_replace_image", return_value=None
    ):
        success, message = service.download_article(
            article_url="https://mp.weixin.qq.com/s/test-md",
            article_title="传入标题",
            account_name="测试公众号",
            save_dir=tmp_path,
            output_format="markdown",
        )

    article_path = tmp_path / "测试公众号" / "页面标题.md"
    meta_path = tmp_path / "测试公众号" / "页面标题.md.meta.json"

    assert success is True
    assert "下载成功" in message
    assert article_path.exists() is True
    assert meta_path.exists() is True
    assert "# 页面标题" in article_path.read_text(encoding="utf-8")
    assert "正文内容" in article_path.read_text(encoding="utf-8")
    assert "source_url" in meta_path.read_text(encoding="utf-8")
    mock_inject.assert_called_once()
    mock_clean.assert_called_once()


def test_download_article_rejects_unsupported_format(tmp_path: Path):
    """测试不支持的保存格式直接返回失败"""
    service = DownloadService()
    response = Mock()
    html = "<html><head><title>标题</title></head><body></body></html>"
    response.content = html.encode("utf-8")
    response.text = html
    response.raise_for_status.return_value = None

    with patch(
        "wechat_article_assistant.services.download_service.requests.get",
        return_value=response,
    ):
        success, message = service.download_article(
            article_url="https://mp.weixin.qq.com/s/test-invalid",
            article_title="标题",
            account_name="测试公众号",
            save_dir=tmp_path,
            output_format="pdf",
        )

    assert success is False
    assert message == "不支持的保存格式: pdf"


def test_download_articles_batch_aggregates_success_and_errors(tmp_path: Path):
    """测试批量下载汇总成功数、失败数和错误信息"""
    service = DownloadService()

    with patch.object(
        service,
        "download_article",
        side_effect=[(True, "ok"), (False, "网络失败")],
    ) as mock_download:
        success_count, fail_count, errors = service.download_articles_batch(
            [
                {"article_link": "https://a.test", "article_title": "文章A", "nickname": "号A"},
                {"article_link": "https://b.test", "article_title": "文章B", "nickname": "号B"},
                {"bad": "data"},
            ],
            save_dir=tmp_path,
            output_format="markdown",
        )

    assert success_count == 1
    assert fail_count == 2
    assert errors == ["文章B: 网络失败", "无效的文章数据: {'bad': 'data'}"]
    assert mock_download.call_count == 2


def test_download_from_file_skips_comments_and_blank_lines(tmp_path: Path):
    """测试从文件下载时忽略注释和空行"""
    service = DownloadService()
    input_file = tmp_path / "urls.txt"
    input_file.write_text(
        "\n# 注释\nhttps://mp.weixin.qq.com/s/1\n\nhttps://mp.weixin.qq.com/s/2\n",
        encoding="utf-8",
    )

    with patch.object(
        service,
        "download_articles_batch",
        return_value=(2, 0, []),
    ) as mock_batch:
        success_count, fail_count, errors = service.download_from_file(
            str(input_file),
            save_dir=tmp_path,
            output_format="markdown",
        )

    assert (success_count, fail_count, errors) == (2, 0, [])
    mock_batch.assert_called_once()
    articles = mock_batch.call_args.args[0]
    assert articles == [
        {"url": "https://mp.weixin.qq.com/s/1", "title": "文章_1", "account_name": "批量下载"},
        {"url": "https://mp.weixin.qq.com/s/2", "title": "文章_2", "account_name": "批量下载"},
    ]


def test_process_text_only_article_injects_paragraphs_and_meta_info():
    """测试纯文字文章处理会注入发布信息和段落内容"""
    service = DownloadService()
    soup = BeautifulSoup(
        """
        <html>
          <head>
            <meta property="og:title" content="第一段\\n第二行\\n\\n第二段" />
          </head>
          <body></body>
        </html>
        """,
        "html.parser",
    )
    html_content = """
        <script>
            var createTime = '2026-03-06 09:00';
            var data = { province_name: JsDecode('北京') };
        </script>
    """

    service._process_text_only_article(
        soup,
        article_title="传入标题",
        html_content=html_content,
        article_url="https://mp.weixin.qq.com/s/text-only",
    )

    content_div = soup.find("div", id="js_content")
    assert content_div is not None
    assert "2026-03-06 09:00" in content_div.get_text()
    assert "北京" in content_div.get_text()
    assert "https://mp.weixin.qq.com/s/text-only" in content_div.get_text()
    paragraphs = content_div.find_all("p")
    assert len(paragraphs) == 2
    assert "第一段" in paragraphs[0].get_text()
    assert paragraphs[0].find("br") is not None
    assert "第二段" in paragraphs[1].get_text()


def test_process_image_only_article_creates_content_from_picture_urls():
    """测试纯图片文章优先使用 JS 中的图片列表构建内容"""
    service = DownloadService()
    soup = BeautifulSoup(
        """
        <html>
          <head>
            <meta property="og:title" content="图片文章标题" />
            <meta property="og:description" content="描述\\x20内容" />
          </head>
          <body></body>
        </html>
        """,
        "html.parser",
    )
    html_content = """
        <script>
            var createTime = '2026-03-06 10:00';
            var data = { province_name: JsDecode('上海') };
            var picture_page_info_list = [
                {"url":"https://img.test/1.jpg"},
                {"url":"https://img.test/2.jpg"}
            ];
        </script>
    """

    with patch.object(
        service,
        "_extract_picture_urls_from_js_array",
        return_value=["https://img.test/1.jpg", "https://img.test/2.jpg"],
    ):
        service._process_image_only_article(
            soup,
            article_title="回退标题",
            html_content=html_content,
            article_url="https://mp.weixin.qq.com/s/image-only",
        )

    content_div = soup.find("div", id="js_content")
    assert content_div is not None
    assert "图片文章标题" in content_div.get_text()
    assert "2026-03-06 10:00" in content_div.get_text()
    assert "上海" in content_div.get_text()
    assert "描述 内容" in content_div.get_text()
    images = content_div.find_all("img")
    assert len(images) == 2
    assert images[0]["src"] == "https://img.test/1.jpg"


def test_process_image_only_article_falls_back_to_existing_images():
    """测试纯图片文章在无 JS 图片列表时回退到 HTML 图片"""
    service = DownloadService()
    soup = BeautifulSoup(
        """
        <html>
          <body>
            <img src="https://img.test/a.jpg" data-x="1" />
            <img src="https://img.test/b.jpg" />
          </body>
        </html>
        """,
        "html.parser",
    )

    with patch.object(service, "_extract_picture_urls_from_js_array", return_value=[]):
        service._process_image_only_article(
            soup,
            article_title="图片回退",
            html_content="<script></script>",
            article_url="https://mp.weixin.qq.com/s/image-fallback",
        )

    content_div = soup.find("div", id="js_content")
    assert content_div is not None
    images = content_div.find_all("img")
    assert len(images) == 2
    assert images[0]["src"] == "https://img.test/a.jpg"
    assert images[0]["data-x"] == "1"
    assert "📎 图片 1: a.jpg" in content_div.get_text()


def test_process_normal_article_removes_hidden_style():
    """测试普通文章处理时移除 js_content 的隐藏样式"""
    service = DownloadService()
    soup = BeautifulSoup(
        """
        <html>
          <body>
            <div id="js_content" style="display:none">正文</div>
          </body>
        </html>
        """,
        "html.parser",
    )

    service._process_normal_article(soup)

    content_div = soup.find("div", id="js_content")
    assert content_div is not None
    assert content_div.has_attr("style") is False
