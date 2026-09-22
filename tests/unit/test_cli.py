"""CLI 结构化输出、失败状态与参数兼容测试。"""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from wechat_article_assistant.cli import main
from wechat_article_assistant.services.download_service import DownloadResult


def run_cli(arguments: list[str]) -> int:
    """运行入口并捕获正常退出和错误退出。"""
    with patch("sys.argv", ["wechat-cli", *arguments]):
        try:
            main()
        except SystemExit as exc:
            return int(exc.code)
    return 0


@pytest.mark.parametrize("prefix", [[], ["--json"]])
def test_json_single_download(
    prefix: list[str], capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    """全局及子命令位置均支持 JSON，返回真实标题和路径。"""
    output = tmp_path / "正文.md"
    service = Mock()
    service.download_article_result.return_value = DownloadResult(
        "https://example.com", "中文标题", True, "ok", str(output)
    )
    with patch("wechat_article_assistant.cli.DownloadService", return_value=service):
        assert (
            run_cli(
                [
                    *prefix,
                    "download",
                    "https://example.com",
                    "--format",
                    "html",
                    *([] if prefix else ["--json"]),
                ]
            )
            == 0
        )
    result = json.loads(capsys.readouterr().out)
    assert result["items"][0]["path"] == str(output)
    assert result["items"][0]["title"] == "中文标题"
    assert result["schema_version"] == 1
    assert service.download_article_result.call_args.args[-1] == "html"


@pytest.mark.parametrize(
    ("items", "expected"),
    [
        ([DownloadResult("u", "t", False, "失败")], 1),
        ([DownloadResult("u", "t", False, "验证", error_code="verification_required")], 5),
        (
            [
                DownloadResult("u", "t", True, "完成", "C:/a.md"),
                DownloadResult("v", "t", False, "失败"),
            ],
            3,
        ),
    ],
)
def test_download_exit_codes(
    items: list[DownloadResult], expected: int, capsys: pytest.CaptureFixture[str]
) -> None:
    """单篇失败与批量部分失败都提供准确退出码。"""
    service = Mock()
    service.download_file_results.return_value = items
    with patch("wechat_article_assistant.cli.DownloadService", return_value=service):
        assert run_cli(["download", "--file", "urls.txt", "--json"]) == expected
    result = json.loads(capsys.readouterr().out)
    assert result["exit_code"] == expected
    assert result["failure_count"] == sum(not item.success for item in items)
    assert service.download_file_results.call_args.args[-1] == "markdown"


@pytest.mark.parametrize(
    "arguments",
    [
        ["download"],
        ["download", "url", "--file", "a.txt"],
        ["download", "url", "--format", "pdf"],
        ["download-articles", "--start-time", "invalid"],
        ["download-articles", "--start-time", "2026-09-22", "--end-time", "2026-09-21"],
        ["missing-command"],
        [],
    ],
)
def test_invalid_arguments_json(arguments: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    """参数错误仍输出可解析 JSON。"""
    assert run_cli([*arguments, "--json"]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "invalid_arguments"


def test_download_exception_json(capsys: pytest.CaptureFixture[str]) -> None:
    """文件缺失不会把 traceback 混入 stdout。"""
    service = Mock()
    service.download_file_results.side_effect = FileNotFoundError("链接文件不存在")
    with patch("wechat_article_assistant.cli.DownloadService", return_value=service):
        assert run_cli(["download", "--file", "missing", "--json"]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "failed"


@pytest.mark.parametrize(
    ("success", "stats", "code"),
    [
        (True, {"success_accounts": 2, "failed_accounts": 0}, 0),
        (True, {"success_accounts": 1, "failed_accounts": 1}, 3),
        (False, {"success_accounts": 0, "failed_accounts": 1}, 1),
        (False, {"error_code": "login_required"}, 4),
    ],
)
def test_collect_status(
    success: bool, stats: dict[str, object], code: int, capsys: pytest.CaptureFixture[str]
) -> None:
    """采集默认不启动交互式登录，区分部分失败和缺少登录态。"""
    service = Mock()
    service.collect_recent_articles_all_accounts.return_value = success, "采集结果", stats
    with patch("wechat_article_assistant.cli.ArticleService", return_value=service):
        assert run_cli(["collect-recent", "--json"]) == code
    service.collect_recent_articles_all_accounts.assert_called_once_with(interactive=False)
    assert json.loads(capsys.readouterr().out)["exit_code"] == code


def test_collected_filters(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    """公众号、日期和格式参数正确传入服务，空匹配是成功的空结果。"""
    service = Mock()
    service.download_collected_articles.return_value = []
    with patch("wechat_article_assistant.cli.ArticleService", return_value=service):
        assert (
            run_cli(
                [
                    "download-articles",
                    "--nickname",
                    "公众号A,公众号B",
                    "--start-time",
                    "2026-09-21",
                    "--end-time",
                    "2026-09-21",
                    "--output",
                    str(tmp_path),
                    "--json",
                ]
            )
            == 0
        )
    args = service.download_collected_articles.call_args.args
    assert args[0].hour == 0
    assert args[1].hour == 23 and args[1].second == 59
    assert args[2:] == (["公众号A", "公众号B"], tmp_path, "markdown")
    assert json.loads(capsys.readouterr().out)["items"] == []


def test_doctor_offline(capsys: pytest.CaptureFixture[str]) -> None:
    """本地诊断不创建认证器，不泄漏数据库口令或会话内容。"""
    with patch("wechat_article_assistant.cli.WechatAuthenticator") as auth:
        assert run_cli(["doctor", "--json"]) == 0
    auth.assert_not_called()
    result = json.loads(capsys.readouterr().out)
    assert result["details"]["session_verified"] is False
    assert "DATABASE_URL" not in result["details"]


@pytest.mark.parametrize("success", [True, False])
def test_login(success: bool, capsys: pytest.CaptureFixture[str]) -> None:
    """登录命令向用户提供可识别的完成状态。"""
    with patch("wechat_article_assistant.cli.WechatAuthenticator") as auth:
        auth.return_value.ensure_authenticated.return_value = success
        assert run_cli(["login", "--json"]) == (0 if success else 4)
    assert json.loads(capsys.readouterr().out)["command"] == "login"
