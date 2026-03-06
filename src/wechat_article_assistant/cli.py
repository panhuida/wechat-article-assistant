"""命令行工具"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

from .config import config
from .services.article_service import ArticleService
from .services.download_service import DownloadService
from .utils.logger import cli_logger

__all__ = ["main"]


def main():
    """命令行工具主函数"""
    parser = argparse.ArgumentParser(description="微信公众号文章阅读助手")

    subparsers = parser.add_subparsers(dest="command", help="命令")

    # 下载命令
    download_parser = subparsers.add_parser("download", help="下载文章")
    download_parser.add_argument("url", nargs="?", help="文章URL")
    download_parser.add_argument("--file", "-f", help="包含文章链接的文件路径")
    download_parser.add_argument("--output", "-o", help="输出目录", default=None)
    download_parser.add_argument("--verbose", "-v", action="store_true", help="显示详细日志")

    # 采集最近文章命令
    collect_recent_parser = subparsers.add_parser(
        "collect-recent", help="获取所有公众号最近5次发的文章"
    )
    collect_recent_parser.add_argument("--verbose", "-v", action="store_true", help="显示失败详情")

    # 按时间范围下载已采集文章命令
    download_articles_parser = subparsers.add_parser(
        "download-articles", help="按文章创建时间范围批量下载文章"
    )
    download_articles_parser.add_argument(
        "--start-time",
        help="开始时间，支持 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS，默认最近一天",
        default=None,
    )
    download_articles_parser.add_argument(
        "--end-time",
        help="结束时间，支持 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS，默认当前时间",
        default=None,
    )
    download_articles_parser.add_argument(
        "--format",
        dest="save_format",
        choices=["html", "markdown"],
        default="markdown",
        help="保存格式，默认 markdown",
    )
    download_articles_parser.add_argument(
        "--nickname",
        help="按公众号名称筛选，支持逗号分隔多个名称（精确匹配）",
        default=None,
    )
    download_articles_parser.add_argument(
        "--output",
        "-o",
        help="保存目录，默认使用 .env 中的 DOWNLOAD_PATH / DOWNLOAD_DIR",
        default=None,
    )
    download_articles_parser.add_argument("--verbose", "-v", action="store_true", help="显示失败详情")

    args = parser.parse_args()
    cli_logger.info(f"CLI 启动，命令: {args.command}")

    if args.command == "download":
        download_command(args)
    elif args.command == "collect-recent":
        collect_recent_command(args)
    elif args.command == "download-articles":
        download_articles_command(args)
    else:
        parser.print_help()


def download_command(args: argparse.Namespace) -> None:
    """下载命令处理"""
    download_service = DownloadService()
    cli_logger.info("执行 download 命令")

    # 设置输出目录
    output_dir = Path(args.output) if args.output else None

    if args.file:
        cli_logger.info(f"从文件批量下载，file={args.file}, output={args.output}")
        # 从文件批量下载
        cli_logger.info("=" * 60)
        cli_logger.info(f"从文件读取URL: {args.file}")
        cli_logger.info("=" * 60)

        success_count, fail_count, errors = download_service.download_from_file(
            args.file, output_dir
        )
        cli_logger.info(f"批量下载完成，success={success_count}, fail={fail_count}")

        cli_logger.info("=" * 60)
        cli_logger.info("下载完成!")
        cli_logger.info("=" * 60)
        cli_logger.info(f"成功: {success_count} 篇")
        cli_logger.info(f"失败: {fail_count} 篇")

        if errors and args.verbose:
            cli_logger.info("错误详情:")
            for error in errors:
                cli_logger.error(f"  ✗ {error}")

        cli_logger.info("=" * 60)

    elif args.url:
        cli_logger.info(f"下载单篇文章，url={args.url}, output={args.output}")
        # 下载单个URL
        cli_logger.info("=" * 60)
        cli_logger.info(f"下载文章: {args.url}")
        cli_logger.info("=" * 60)

        success, message = download_service.download_article(
            args.url, "命令行下载", "命令行下载", output_dir
        )
        if success:
            cli_logger.info(f"单篇下载成功: {message}")
        else:
            cli_logger.error(f"单篇下载失败: {message}")

        cli_logger.info("=" * 60)
        if success:
            cli_logger.info(f"✓ {message}")
        else:
            cli_logger.error(f"✗ {message}")
        cli_logger.info("=" * 60)

    else:
        cli_logger.error("download 命令缺少 url 或 file 参数")
        cli_logger.error("错误: 请指定文章URL或文件路径")
        cli_logger.info("示例:")
        cli_logger.info("  # 下载单篇文章")
        cli_logger.info("  wechat-cli download <article_url>")
        cli_logger.info("  python wechat-cli.py download <article_url>")
        cli_logger.info("  # 批量下载")
        cli_logger.info("  wechat-cli download --file urls.txt")
        cli_logger.info("  python wechat-cli.py download --file urls.txt")
        cli_logger.info("  # 指定输出目录")
        cli_logger.info("  wechat-cli download <article_url> --output E:\\我的文档\\公众号")
        cli_logger.info("  # 显示详细日志")
        cli_logger.info("  wechat-cli download <article_url> --verbose")
        sys.exit(1)


def collect_recent_command(args: argparse.Namespace) -> None:
    """获取所有公众号最近5次发的文章"""
    article_service = ArticleService()
    cli_logger.info("执行 collect-recent 命令")

    cli_logger.info("=" * 60)
    cli_logger.info("开始采集所有公众号最近5次发的文章...")
    cli_logger.info("=" * 60)

    success, message, stats = article_service.collect_recent_articles_all_accounts()
    cli_logger.info(
        "采集最近文章完成，success=%s, total_accounts=%s, success_accounts=%s, failed_accounts=%s, total_articles=%s",
        success,
        stats.get("total_accounts") if stats else None,
        stats.get("success_accounts") if stats else None,
        stats.get("failed_accounts") if stats else None,
        stats.get("total_articles") if stats else None,
    )

    cli_logger.info("=" * 60)
    if success:
        cli_logger.info(f"✓ {message}")
    else:
        cli_logger.error(f"✗ {message}")

    if stats:
        cli_logger.info("-" * 60)
        cli_logger.info(f"公众号总数: {stats.get('total_accounts', 0)}")
        cli_logger.info(f"成功采集: {stats.get('success_accounts', 0)}")
        cli_logger.info(f"失败采集: {stats.get('failed_accounts', 0)}")
        cli_logger.info(f"新增文章: {stats.get('total_articles', 0)}")

        failed_list = stats.get("failed_list", [])
        if failed_list and args.verbose:
            cli_logger.info("失败详情:")
            for failed_item in failed_list:
                cli_logger.error(f"  ✗ {failed_item}")
    cli_logger.info("=" * 60)

    if not success:
        sys.exit(1)


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


def download_articles_command(args: argparse.Namespace) -> None:
    """按时间范围批量下载已采集文章"""
    article_service = ArticleService()
    download_service = DownloadService()
    cli_logger.info("执行 download-articles 命令")

    now = datetime.now()
    default_start = now - timedelta(days=1)
    start_time = default_start
    end_time = now

    try:
        if args.start_time:
            start_time = _parse_cli_datetime(args.start_time, is_end=False)
        if args.end_time:
            end_time = _parse_cli_datetime(args.end_time, is_end=True)
    except ValueError as e:
        cli_logger.error(f"download-articles 时间参数解析失败: {e}")
        cli_logger.error(f"错误: {e}")
        cli_logger.info("示例:")
        cli_logger.info("  wechat-cli download-articles --start-time 2026-03-05 --end-time 2026-03-06")
        cli_logger.info(
            "  wechat-cli download-articles --start-time '2026-03-05 00:00:00' --format markdown"
        )
        sys.exit(1)

    if start_time > end_time:
        cli_logger.error("download-articles 参数错误：start_time > end_time")
        cli_logger.error("错误: 开始时间不能晚于结束时间")
        sys.exit(1)

    output_dir = Path(args.output) if args.output else None
    nicknames = (
        [item.strip() for item in args.nickname.split(",") if item.strip()] if args.nickname else []
    )
    nickname_display = ",".join(nicknames) if nicknames else "全部"

    cli_logger.info("=" * 60)
    cli_logger.info("按时间范围批量下载文章")
    cli_logger.info(
        f"时间范围: {start_time.strftime('%Y-%m-%d %H:%M:%S')} ~ {end_time.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    cli_logger.info(f"公众号名称: {nickname_display}")
    cli_logger.info(f"保存格式: {args.save_format}")
    cli_logger.info(f"保存路径: {output_dir if output_dir else config.DOWNLOAD_DIR}")
    cli_logger.info("=" * 60)
    cli_logger.info(
        "下载筛选条件：start=%s, end=%s, nicknames=%s, format=%s, output=%s",
        start_time.strftime("%Y-%m-%d %H:%M:%S"),
        end_time.strftime("%Y-%m-%d %H:%M:%S"),
        nicknames if nicknames else "全部",
        args.save_format,
        str(output_dir if output_dir else config.DOWNLOAD_DIR),
    )

    articles = article_service.get_articles_by_create_time_range(
        start_time, end_time, nicknames=nicknames
    )
    if not articles:
        cli_logger.info("无匹配文章")
        cli_logger.info("未找到符合条件的文章。")
        return

    success_count, fail_count, errors = download_service.download_articles_batch(
        articles, output_dir, output_format=args.save_format
    )
    cli_logger.info(
        "批量下载执行完成，matched=%s, success=%s, fail=%s",
        len(articles),
        success_count,
        fail_count,
    )

    if success_count > 0:
        article_ids = [article["id"] for article in articles if isinstance(article.get("id"), int)]
        if article_ids:
            article_service.mark_as_downloaded(article_ids)

    cli_logger.info("=" * 60)
    cli_logger.info(f"匹配文章: {len(articles)} 篇")
    cli_logger.info(f"下载成功: {success_count} 篇")
    cli_logger.info(f"下载失败: {fail_count} 篇")
    cli_logger.info("=" * 60)

    if errors and args.verbose:
        cli_logger.info("失败详情:")
        for error in errors:
            cli_logger.error(f"  ✗ {error}")

    if fail_count > 0 and success_count == 0:
        cli_logger.error("批量下载全部失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
