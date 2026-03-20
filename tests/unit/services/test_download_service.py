from pathlib import Path
from unittest.mock import Mock, patch

from bs4 import BeautifulSoup

from wechat_article_assistant.services.download_service import DownloadService


def _make_response(html: str, content_type: str = "text/html; charset=utf-8") -> Mock:
    response = Mock()
    response.text = html
    response.content = html.encode("utf-8")
    response.headers = {"Content-Type": content_type}
    response.raise_for_status.return_value = None
    return response


def test_load_session_cookies_filters_invalid_values():
    """测试加载会话 cookies 时过滤无效项"""
    service = DownloadService()
    service.session_manager.load_session = Mock(
        return_value={
            "cookies": [
                {"name": "token", "value": "abc"},
                {"name": "empty", "value": ""},
                {"name": "zero", "value": 0},
                {"name": "", "value": "skip"},
                {"name": "missing"},
                "not-a-dict",
            ]
        }
    )

    cookies = service._load_session_cookies()

    assert cookies == {"token": "abc", "empty": "", "zero": 0}


def test_fetch_article_response_retries_with_session_when_verification_page():
    """测试命中验证页时会复用本地会话重试"""
    service = DownloadService()
    first = _make_response("<html><body>环境异常</body></html>")
    second = _make_response("<html><body><div id='js_content'><p>正文</p></div></body></html>")

    with patch.object(service, "_load_session_cookies", return_value={"pass_ticket": "cookie"}), patch(
        "wechat_article_assistant.services.download_service.requests.get",
        side_effect=[first, second],
    ) as mock_get:
        response, blocked = service._fetch_article_response("https://mp.weixin.qq.com/s/test", {})

    assert response is second
    assert blocked is False
    assert mock_get.call_count == 2
    assert mock_get.call_args_list[1].kwargs["cookies"] == {"pass_ticket": "cookie"}


def test_build_markdown_content_supports_common_blocks():
    """测试 Markdown 构建支持常见块级结构"""
    service = DownloadService()
    soup = BeautifulSoup(
        """
        <html><body>
          <div id="js_content">
            <h2>小标题</h2>
            <p>包含<a href="https://example.com">链接</a>和<strong>加粗</strong></p>
            <ul><li>项目一</li><li>项目二</li></ul>
            <blockquote><p>引用内容</p></blockquote>
            <pre>print("ok")</pre>
            <img src="https://img.test/1.png" alt="封面" />
          </div>
        </body></html>
        """,
        "lxml",
    )

    markdown = service._build_markdown_content(
        soup, "测试文章", "https://mp.weixin.qq.com/s/markdown"
    )

    assert "# 测试文章" in markdown
    assert "> 原文链接: https://mp.weixin.qq.com/s/markdown" in markdown
    assert "## 小标题" in markdown
    assert "[链接](https://example.com)" in markdown
    assert "**加粗**" in markdown
    assert "- 项目一" in markdown
    assert "> 引用内容" in markdown
    assert 'print("ok")' in markdown
    assert "![封面](https://img.test/1.png)" in markdown


def test_inject_publish_info_updates_meta_fields():
    """测试注入发布时间、地区和原文链接"""
    service = DownloadService()
    soup = BeautifulSoup(
        """
        <html><body>
          <em id="publish_time"></em>
          <em id="js_ip_wording_wrp" style="display:none;">
            <span id="js_ip_wording"></span>
          </em>
          <span id="meta_content_hide_info"></span>
        </body></html>
        """,
        "lxml",
    )
    html_content = """
    <script>
      var createTime = '2026-03-20 12:00';
      province_name: JsDecode('上海')
    </script>
    """

    service._inject_publish_info(soup, html_content, "https://mp.weixin.qq.com/s/source")

    assert soup.find("em", id="publish_time").get_text() == "2026-03-20 12:00"
    assert soup.find("span", id="js_ip_wording").get_text() == "上海"
    assert "display" not in soup.find("em", id="js_ip_wording_wrp").attrs.get("style", "")
    source_link = soup.find("span", id="meta_content_hide_info").find("a")
    assert source_link is not None
    assert source_link["href"] == "https://mp.weixin.qq.com/s/source"


def test_clean_wechat_ui_elements_removes_ui_and_rewrites_javascript_links():
    """测试清理微信 UI 元素时移除无关节点并重写脚本链接"""
    service = DownloadService()
    soup = BeautifulSoup(
        """
        <html><body>
          <div id="js_content"><p>正文保留</p></div>
          <div id="js_bottom_ad_area">广告</div>
          <a href="javascript:void(0)" class="fake-link">按钮文本</a>
          <div><span>赞</span></div>
          <!-- remove me -->
        </body></html>
        """,
        "lxml",
    )

    service._clean_wechat_ui_elements(soup)

    assert soup.find(id="js_bottom_ad_area") is None
    assert soup.find("a", href=lambda href: href and "javascript:" in href) is None
    assert "正文保留" in soup.get_text()


def test_extract_picture_urls_from_js_array_returns_first_level_urls():
    """测试只提取 picture_page_info_list 第一层图片地址"""
    service = DownloadService()
    html_content = """
    picture_page_info_list: [
      {cdn_url: JsDecode('https://img.test/1.jpg'), nested: {cdn_url: JsDecode('https://img.test/nested.jpg')}},
      {cdn_url: JsDecode('https://img.test/2.jpg')}
    ]
    next_field: "done"
    """

    urls = service._extract_picture_urls_from_js_array(html_content)

    assert urls == ["https://img.test/1.jpg", "https://img.test/2.jpg"]


def test_process_text_only_article_creates_content_blocks():
    """测试纯文字文章会创建正文和元信息"""
    service = DownloadService()
    soup = BeautifulSoup("<html><body></body></html>", "lxml")
    html_content = """
    <script>
      var createTime = '2026-03-20';
      province_name: JsDecode('北京')
      content_noencode: JsDecode('第一段\\n\\n第二段')
    </script>
    """

    service._process_text_only_article(
        soup, "纯文字文章", html_content, "https://mp.weixin.qq.com/s/text"
    )

    content_div = soup.find("div", id="js_content")
    assert content_div is not None
    paragraphs = content_div.find_all("p")
    assert len(paragraphs) == 2
    assert paragraphs[0].get_text() == "第一段"
    assert paragraphs[1].get_text() == "第二段"
    assert "2026-03-20" in content_div.get_text()
    assert "北京" in content_div.get_text()
    assert content_div.find("a")["href"] == "https://mp.weixin.qq.com/s/text"


def test_process_image_only_article_creates_image_container():
    """测试纯图片文章会创建标题、描述和图片容器"""
    service = DownloadService()
    soup = BeautifulSoup(
        """
        <html>
          <head>
            <meta property="og:title" content="图文标题" />
            <meta property="og:description" content="描述\\x3cstrong\\x3e内容\\x3c/strong\\x3e" />
          </head>
          <body></body>
        </html>
        """,
        "lxml",
    )
    html_content = """
    create_time: JsDecode('2026-03-20')
    province_name: JsDecode('深圳')
    picture_page_info_list: [
      {cdn_url: JsDecode('https://img.test/1.jpg')},
      {cdn_url: JsDecode('https://img.test/2.jpg')}
    ]
    next_field: "done"
    """

    service._process_image_only_article(
        soup, "后备标题", html_content, "https://mp.weixin.qq.com/s/image"
    )

    content_div = soup.find("div", id="js_content")
    assert content_div is not None
    assert "图文标题" in content_div.get_text()
    assert "2026-03-20" in content_div.get_text()
    assert "深圳" in content_div.get_text()
    assert content_div.find("strong").get_text() == "内容"
    assert len(content_div.find_all("img")) == 2


def test_download_article_markdown_saves_markdown_and_meta(tmp_path: Path):
    """测试下载文章为 Markdown 时会写入正文和元数据"""
    service = DownloadService()
    html = """
    <html>
      <head><title>页面标题</title></head>
      <body>
        <div id="js_content">
          <p>第一段</p>
          <img src="https://img.test/1.png" />
        </div>
        <span id="meta_content_hide_info"></span>
        <em id="publish_time"></em>
      </body>
    </html>
    """

    with patch.object(service, "_fetch_article_response", return_value=(_make_response(html), False)), patch.object(
        service,
        "_download_and_replace_image",
        return_value="页面标题.assets/image_0.png",
    ):
        success, message = service.download_article(
            article_url="https://mp.weixin.qq.com/s/markdown",
            article_title="传入标题",
            account_name="测试号",
            save_dir=tmp_path,
            output_format="markdown",
        )

    account_dir = tmp_path / "测试号"
    article_path = account_dir / "页面标题.md"
    meta_path = account_dir / "页面标题.md.meta.json"

    assert success is True
    assert "下载成功" in message
    assert article_path.exists()
    assert meta_path.exists()
    markdown = article_path.read_text(encoding="utf-8")
    assert "# 页面标题" in markdown
    assert "> 原文链接: https://mp.weixin.qq.com/s/markdown" in markdown
    assert "![image](页面标题.assets/image_0.png)" in markdown


def test_download_articles_batch_collects_success_and_errors(tmp_path: Path):
    """测试批量下载会汇总成功数和错误信息"""
    service = DownloadService()

    with patch.object(
        service,
        "download_article",
        side_effect=[(True, "ok"), (False, "bad")],
    ) as mock_download:
        success_count, fail_count, errors = service.download_articles_batch(
            [
                {"url": "https://a", "title": "文章A", "account_name": "号A"},
                {"article_link": "https://b", "article_title": "文章B", "nickname": "号B"},
                {"article_title": "缺少链接"},
            ],
            save_dir=tmp_path,
        )

    assert mock_download.call_count == 2
    assert success_count == 1
    assert fail_count == 2
    assert "文章B: bad" in errors
    assert any("无效的文章数据" in error for error in errors)


def test_download_from_file_ignores_comments_and_blank_lines(tmp_path: Path):
    """测试从文件批量下载时会忽略注释和空行"""
    service = DownloadService()
    file_path = tmp_path / "urls.txt"
    file_path.write_text(
        "# 注释\nhttps://mp.weixin.qq.com/s/1\n\nhttps://mp.weixin.qq.com/s/2\n",
        encoding="utf-8",
    )

    with patch.object(
        service,
        "download_articles_batch",
        return_value=(2, 0, []),
    ) as mock_batch:
        result = service.download_from_file(str(file_path), save_dir=tmp_path, output_format="markdown")

    articles = mock_batch.call_args.args[0]
    assert result == (2, 0, [])
    assert [article["url"] for article in articles] == [
        "https://mp.weixin.qq.com/s/1",
        "https://mp.weixin.qq.com/s/2",
    ]
