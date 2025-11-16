"""文章管理路由"""

from flask import Blueprint, jsonify, request

from ..services.article_service import ArticleService
from ..services.download_service import DownloadService

article_bp = Blueprint("article", __name__, url_prefix="/api/article")
article_service = ArticleService()
download_service = DownloadService()


@article_bp.route("/list", methods=["GET"])
def get_articles():
    """获取文章列表"""
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("pageSize", 20, type=int)
    search = request.args.get("search", "")
    nickname = request.args.get("nickname", "")
    is_deleted = request.args.get("isDeleted", "")
    is_downloaded = request.args.get("isDownloaded", "")
    start_date = request.args.get("startDate", "")
    end_date = request.args.get("endDate", "")

    articles, total = article_service.get_articles(
        page=page,
        page_size=page_size,
        search=search if search else None,
        nickname=nickname if nickname else None,
        is_deleted=is_deleted if is_deleted else None,
        is_downloaded=is_downloaded if is_downloaded else None,
        start_date=start_date if start_date else None,
        end_date=end_date if end_date else None,
    )

    return jsonify(
        {"success": True, "data": articles, "total": total, "page": page, "pageSize": page_size}
    )


@article_bp.route("/<int:article_id>", methods=["GET"])
def get_article(article_id):
    """获取单篇文章"""
    article = article_service.get_article_by_id(article_id)
    if article:
        return jsonify({"success": True, "data": article})
    return jsonify({"success": False, "message": "文章不存在"}), 404


@article_bp.route("/delete", methods=["POST"])
def delete_articles():
    """批量删除文章"""
    data = request.json
    article_ids = data.get("ids", [])

    if not article_ids:
        return jsonify({"success": False, "message": "请选择要删除的文章"})

    success, message = article_service.delete_articles(article_ids)
    return jsonify({"success": success, "message": message})


@article_bp.route("/collect/single/<int:account_id>", methods=["POST"])
def collect_single_page(account_id):
    """采集单页文章"""
    success, message, count = article_service.collect_articles_single_page(account_id)
    return jsonify({"success": success, "message": message, "count": count})


@article_bp.route("/collect/all/<int:account_id>", methods=["POST"])
def collect_all(account_id):
    """采集全部文章"""
    success, message, count = article_service.collect_articles_all(account_id)
    return jsonify({"success": success, "message": message, "count": count})


@article_bp.route("/download", methods=["POST"])
def download_articles():
    """批量下载文章"""
    data = request.json
    article_ids = data.get("ids", [])

    if not article_ids:
        return jsonify({"success": False, "message": "请选择要下载的文章"})

    # 获取文章信息
    db_articles = []
    for article_id in article_ids:
        article = article_service.get_article_by_id(article_id)
        if article:
            db_articles.append(article)

    if not db_articles:
        return jsonify({"success": False, "message": "未找到要下载的文章"})

    # 批量下载
    success_count, fail_count, errors = download_service.download_articles_batch(db_articles)

    # 标记已下载
    if success_count > 0:
        article_service.mark_as_downloaded(article_ids)

    return jsonify(
        {
            "success": True,
            "message": f"下载完成: 成功 {success_count} 篇, 失败 {fail_count} 篇",
            "successCount": success_count,
            "failCount": fail_count,
            "errors": errors,
        }
    )


@article_bp.route("/names", methods=["GET"])
def get_account_names():
    """获取所有公众号名称（用于筛选）"""
    names = article_service.get_account_names()
    return jsonify({"success": True, "data": names})
