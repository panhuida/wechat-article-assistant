"""CLI 测试"""

from unittest.mock import Mock, patch

import pytest

from wechat_article_assistant.cli import main


def test_collect_recent_command_success(capsys):
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

    output = capsys.readouterr().out
    assert "开始采集所有公众号最近5次发的文章" in output
    assert "公众号总数: 2" in output
    assert "新增文章: 10" in output


def test_collect_recent_command_failure_exit_code(capsys):
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
    ):
        with pytest.raises(SystemExit) as excinfo:
            main()

    output = capsys.readouterr().out
    assert excinfo.value.code == 1
    assert "采集失败！所有公众号均采集失败" in output
