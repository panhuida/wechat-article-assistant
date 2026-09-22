"""命令行参数解析及人类可读、JSON 响应。"""

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import NoReturn

from .browser.wechat_authenticator import WechatAuthenticator
from .config import config
from .services.article_service import ArticleService
from .services.download_service import DownloadResult, DownloadService
from .utils.logger import cli_logger


@dataclass
class CommandResult:
    """CLI 的稳定输出结构，schema_version 用于后续兼容。"""

    command: str
    status: str = "success"
    exit_code: int = 0
    message: str = "完成"
    success_count: int = 0
    failure_count: int = 0
    items: list[DownloadResult] = field(default_factory=list)
    details: dict[str, object] = field(default_factory=dict)
    schema_version: int = 1


class CliParser(argparse.ArgumentParser):
    """让参数错误也能按 JSON 协议返回。"""

    def error(self, message: str) -> NoReturn:
        """由入口统一组织参数错误响应。"""
        raise ValueError(message)


def build_parser() -> argparse.ArgumentParser:
    """构造兼容原命令的参数定义。"""
    common = CliParser(add_help=False)
    common.add_argument(
        "--json", action="store_true", default=argparse.SUPPRESS, help="输出单个 JSON 对象"
    )
    parser = CliParser(description="微信公众号文章阅读助手", parents=[common])
    subparsers = parser.add_subparsers(dest="command")
    download = subparsers.add_parser("download", parents=[common], help="按链接下载文章")
    download.add_argument("url", nargs="?", help="文章 URL")
    download.add_argument("--file", "-f", help="UTF-8 链接文件")
    collected = subparsers.add_parser(
        "download-articles", parents=[common], help="下载已采集的文章"
    )
    collected.add_argument("--start-time", help="开始时间，默认最近一天")
    collected.add_argument("--end-time", help="结束时间，默认当前时间")
    collected.add_argument("--nickname", help="公众号名称，逗号分隔，精确匹配")
    for command in (download, collected):
        command.add_argument("--output", "-o", help="输出目录")
        command.add_argument(
            "--format", dest="save_format", choices=["html", "markdown"], default="markdown"
        )
        command.add_argument("--verbose", "-v", action="store_true", help="显示逐篇结果")
    collect = subparsers.add_parser(
        "collect-recent", parents=[common], help="采集所有已配置公众号最近 5 次群发"
    )
    collect.add_argument("--verbose", "-v", action="store_true")
    collect.add_argument(
        "--interactive", action="store_true", help="允许打开浏览器扫码；默认仅复用现有登录态"
    )
    subparsers.add_parser("login", parents=[common], help="验证登录态，必要时打开浏览器扫码")
    subparsers.add_parser("doctor", parents=[common], help="检查本地路径，不发起网络请求")
    return parser


def download_response(command: str, items: list[DownloadResult]) -> CommandResult:
    """根据逐篇结果确定退出码，部分失败不能冒充全部成功。"""
    success = sum(item.success for item in items)
    failed = len(items) - success
    code = 0
    status = "success"
    if failed:
        code, status = (3, "partial_failure") if success else (1, "failed")
        if not success and all(item.error_code == "verification_required" for item in items):
            code, status = 5, "verification_required"
    return CommandResult(
        command, status, code, f"成功 {success} 篇，失败 {failed} 篇", success, failed, items
    )


def _parse_cli_datetime(value: str, is_end: bool = False) -> datetime:
    """解析 CLI 传入的日期时间字符串"""
    value = value.strip()
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            parsed = datetime.strptime(value, fmt)
            if fmt == "%Y-%m-%d":
                if is_end:
                    return parsed.replace(hour=23, minute=59, second=59)
                return parsed.replace(hour=0, minute=0, second=0)
            return parsed
        except ValueError:
            continue

    # 兼容 ISO 格式（例如 2026-03-06T12:00:00）
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is not None:
            return parsed.replace(tzinfo=None)
        return parsed
    except ValueError as e:
        raise ValueError(f"无法解析时间: {value}") from e


def execute_command(args: argparse.Namespace) -> CommandResult:
    """将已解析参数交给服务并组织响应。"""
    if args.command == "doctor":
        return CommandResult(
            "doctor",
            details={
                "home": str(config.APP_HOME),
                "config_file": str(config.APP_HOME / ".env"),
                "config_exists": (config.APP_HOME / ".env").is_file(),
                "download_dir": str(config.DOWNLOAD_DIR),
                "session_file": str(config.SESSION_FILE),
                "session_exists": config.SESSION_FILE.is_file(),
                "session_verified": False,
            },
            message="本地路径检查完成；会话是否有效需在线验证",
        )
    if args.command == "login":
        success = WechatAuthenticator().ensure_authenticated()
        return CommandResult(
            "login",
            "success" if success else "login_required",
            0 if success else 4,
            "登录成功" if success else "登录未完成，请重试扫码登录",
        )
    if args.command == "collect-recent":
        success, message, stats = ArticleService().collect_recent_articles_all_accounts(
            interactive=args.interactive
        )
        failed = int(stats.get("failed_accounts", 0))
        code = 3 if success and failed else (0 if success else 1)
        status = "partial_failure" if code == 3 else ("success" if success else "failed")
        if stats.get("error_code") == "login_required":
            code, status = 4, "login_required"
        return CommandResult(
            args.command,
            status,
            code,
            message,
            success_count=int(stats.get("success_accounts", 0)),
            failure_count=failed,
            details=stats,
        )
    output = Path(args.output).expanduser().resolve() if args.output else None
    if args.command == "download":
        if bool(args.url) == bool(args.file):
            raise ValueError("请指定文章 URL 或 --file，且只能选择一种")
        service = DownloadService()
        if args.file:
            items = service.download_file_results(Path(args.file), output, args.save_format)
        else:
            items = [
                service.download_article_result(
                    args.url, "命令行下载", "命令行下载", output, args.save_format
                )
            ]
        return download_response(args.command, items)
    now = datetime.now()
    start = _parse_cli_datetime(args.start_time) if args.start_time else now - timedelta(days=1)
    end = _parse_cli_datetime(args.end_time, is_end=True) if args.end_time else now
    if start > end:
        raise ValueError("开始时间不能晚于结束时间")
    nicknames = [name.strip() for name in (args.nickname or "").split(",") if name.strip()]
    items = ArticleService().download_collected_articles(
        start, end, nicknames, output, args.save_format
    )
    result = download_response(args.command, items)
    if not items:
        result.message = "未找到符合条件的已采集文章"
    return result


def main() -> None:
    """执行命令；stdout 专用于 JSON，日志和人类可读结果写入 stderr。"""
    parser = build_parser()
    json_output = "--json" in sys.argv[1:]
    command = "unknown"
    try:
        args = parser.parse_args()
        command = args.command or "help"
        if not args.command:
            if json_output:
                raise ValueError("请指定子命令；使用 --help 查看帮助")
            parser.print_help()
            return
        result = execute_command(args)
    except ValueError as exc:
        result = CommandResult(command, "invalid_arguments", 2, str(exc))
    except Exception as exc:
        cli_logger.exception("命令执行失败")
        result = CommandResult(command, "failed", 1, f"执行失败: {exc}")
    if json_output:
        sys.stdout.write(json.dumps(asdict(result), ensure_ascii=False) + "\n")
    else:
        cli_logger.info(result.message)
        for item in result.items:
            cli_logger.info("%s: %s", item.title, item.path if item.success else item.message)
        if result.details:
            cli_logger.info("%s", json.dumps(result.details, ensure_ascii=False))
    if result.exit_code:
        raise SystemExit(result.exit_code)


if __name__ == "__main__":
    main()
