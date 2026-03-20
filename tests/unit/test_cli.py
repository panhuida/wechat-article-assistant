"""CLI 测试"""

from unittest.mock import Mock, patch

import pytest

from wechat_article_assistant.cli import main


def test_collect_recent_command_success():
    """测试 collect-recent 命令成功路径"""
    mock_service = Mock()
    mock_service.collect_recent_articles_all_accounts.return_value = (
        True,
        "采集完成！成功 2 个，失败 0 个，共 10 篇文章",
        {
            "total_accounts": 2,
            "success_accounts": 2,
            "failed_accounts": 0,
            "total_articles": 10,
            "failed_list": [],
        },
    )

    with patch("sys.argv", ["wechat-cli", "collect-recent"]), patch(
        "wechat_article_assistant.cli.ArticleService", return_value=mock_service
    ):
        main()

def test_collect_recent_command_failure_exit_code():
    """测试 collect-recent 命令失败时退出码为 1"""
    mock_service = Mock()
    mock_service.collect_recent_articles_all_accounts.return_value = (
        False,
        "采集失败！所有公众号均采集失败",
        {
            "total_accounts": 1,
            "success_accounts": 0,
            "failed_accounts": 1,
            "total_articles": 0,
            "failed_list": ["测试号: 认证失败"],
        },
    )

    with patch("sys.argv", ["wechat-cli", "collect-recent"]), patch(
        "wechat_article_assistant.cli.ArticleService", return_value=mock_service
    ), pytest.raises(SystemExit) as excinfo:
        main()

    assert excinfo.value.code == 1


def test_download_articles_default_markdown():
    """测试 download-articles 默认参数"""
    mock_article_service = Mock()
    mock_download_service = Mock()

    mock_article_service.get_articles_by_create_time_range.return_value = [
        {"id": 1, "article_title": "测试文章", "article_link": "https://mp.weixin.qq.com/s/test"}
    ]
    mock_download_service.download_articles_batch.return_value = (1, 0, [])

    with patch("sys.argv", ["wechat-cli", "download-articles"]), patch(
        "wechat_article_assistant.cli.ArticleService", return_value=mock_article_service
    ), patch("wechat_article_assistant.cli.DownloadService", return_value=mock_download_service):
        main()

    mock_download_service.download_articles_batch.assert_called_once()
    call_args = mock_download_service.download_articles_batch.call_args
    assert call_args.kwargs["output_format"] == "markdown"


def test_download_articles_html_format():
    """测试 download-articles 指定 html 格式"""
    mock_article_service = Mock()
    mock_download_service = Mock()

    mock_article_service.get_articles_by_create_time_range.return_value = []
    mock_download_service.download_articles_batch.return_value = (0, 0, [])

    with patch(
        "sys.argv",
        [
            "wechat-cli",
            "download-articles",
            "--start-time",
            "2026-03-05",
            "--end-time",
            "2026-03-06",
            "--format",
            "html",
        ],
    ), patch("wechat_article_assistant.cli.ArticleService", return_value=mock_article_service), patch(
        "wechat_article_assistant.cli.DownloadService", return_value=mock_download_service
    ):
        main()

def test_download_articles_with_nickname():
    """测试 download-articles 指定公众号名称筛选"""
    mock_article_service = Mock()
    mock_download_service = Mock()

    mock_article_service.get_articles_by_create_time_range.return_value = []
    mock_download_service.download_articles_batch.return_value = (0, 0, [])

    with patch(
        "sys.argv",
        [
            "wechat-cli",
            "download-articles",
            "--nickname",
            "测试公众号A,测试公众号B",
        ],
    ), patch("wechat_article_assistant.cli.ArticleService", return_value=mock_article_service), patch(
        "wechat_article_assistant.cli.DownloadService", return_value=mock_download_service
    ):
        main()

    call_args = mock_article_service.get_articles_by_create_time_range.call_args
    assert call_args.kwargs["nicknames"] == ["测试公众号A", "测试公众号B"]


def test_download_articles_invalid_time_exit():
    """测试 download-articles 非法时间参数"""
    with patch(
        "sys.argv", ["wechat-cli", "download-articles", "--start-time", "invalid-date"]
    ), pytest.raises(SystemExit) as excinfo:
        main()

    assert excinfo.value.code == 1
