import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from wechat_article_assistant.models import WechatAccount, WechatArticle
from wechat_article_assistant.services.article_service import ArticleService


def test_article_service_get_articles(db):
    """测试文章服务：获取文章列表"""
    service = ArticleService()

    # 准备数据
    article1 = WechatArticle(
        nickname="公众号A", article_title="标题A", article_create_time=datetime.now()
    )
    article2 = WechatArticle(
        nickname="公众号B", article_title="标题B", article_create_time=datetime.now()
    )
    db.add_all([article1, article2])
    db.commit()

    # 测试获取所有
    articles, total = service.get_articles()
    assert total == 2
    assert len(articles) == 2

    # 测试搜索
    articles, total = service.get_articles(search="标题A")
    assert total == 1
    assert articles[0]["article_title"] == "标题A"

    # 测试筛选
    articles, total = service.get_articles(nickname="公众号B")
    assert total == 1
    assert articles[0]["nickname"] == "公众号B"


def test_article_service_delete(db):
    """测试文章服务：删除文章"""
    service = ArticleService()

    article = WechatArticle(article_title="待删除")
    db.add(article)
    db.commit()
    db.refresh(article)

    success, msg = service.delete_articles([article.id])
    assert success is True

    deleted = db.query(WechatArticle).filter_by(id=article.id).first()
    assert deleted is None


def test_get_articles_by_create_time_range(db):
    """测试按创建时间范围获取文章"""
    service = ArticleService()
    now = datetime.now()

    in_range = WechatArticle(
        nickname="公众号A",
        article_title="范围内文章",
        article_create_time=now - timedelta(hours=6),
    )
    out_of_range = WechatArticle(
        nickname="公众号B",
        article_title="范围外文章",
        article_create_time=now - timedelta(days=3),
    )
    db.add_all([in_range, out_of_range])
    db.commit()

    articles = service.get_articles_by_create_time_range(
        start_time=now - timedelta(days=1),
        end_time=now,
    )

    assert len(articles) == 1
    assert articles[0]["article_title"] == "范围内文章"


def test_get_articles_by_create_time_range_with_nickname(db):
    """测试按创建时间范围和公众号名称获取文章"""
    service = ArticleService()
    now = datetime.now()

    article_a = WechatArticle(
        nickname="公众号A",
        article_title="A文章",
        article_create_time=now - timedelta(hours=2),
    )
    article_b = WechatArticle(
        nickname="公众号B",
        article_title="B文章",
        article_create_time=now - timedelta(hours=2),
    )
    db.add_all([article_a, article_b])
    db.commit()

    articles = service.get_articles_by_create_time_range(
        start_time=now - timedelta(days=1),
        end_time=now,
        nickname="公众号A",
    )

    assert len(articles) == 1
    assert articles[0]["nickname"] == "公众号A"


def test_get_articles_by_create_time_range_with_nicknames(db):
    """测试按创建时间范围和多个公众号名称获取文章"""
    service = ArticleService()
    now = datetime.now()

    article_a = WechatArticle(
        nickname="公众号A",
        article_title="A文章",
        article_create_time=now - timedelta(hours=2),
    )
    article_b = WechatArticle(
        nickname="公众号B",
        article_title="B文章",
        article_create_time=now - timedelta(hours=2),
    )
    article_c = WechatArticle(
        nickname="公众号C",
        article_title="C文章",
        article_create_time=now - timedelta(hours=2),
    )
    db.add_all([article_a, article_b, article_c])
    db.commit()

    articles = service.get_articles_by_create_time_range(
        start_time=now - timedelta(days=1),
        end_time=now,
        nicknames=["公众号A", "公众号B"],
    )

    assert len(articles) == 2
    assert {item["nickname"] for item in articles} == {"公众号A", "公众号B"}


def test_collect_articles_single_page_requires_authentication():
    """测试单页采集在认证失败时直接返回"""
    service = ArticleService()

    with patch.object(service.wechat_auth, "ensure_authenticated", return_value=False):
        success, message, count = service.collect_articles_single_page(1)

    assert success is False
    assert message == "认证失败，请重试"
    assert count == 0


def test_collect_articles_single_page_requires_session_data():
    """测试单页采集在缺少会话数据时返回失败"""
    service = ArticleService()

    with patch.object(service.wechat_auth, "ensure_authenticated", return_value=True), patch.object(
        service.wechat_auth, "get_session_data", return_value=None
    ):
        success, message, count = service.collect_articles_single_page(1)

    assert success is False
    assert message == "获取会话数据失败"
    assert count == 0


def test_collect_single_page_with_session_returns_not_found_for_missing_account(db):
    """测试单页采集时公众号不存在"""
    service = ArticleService()

    success, message, count = service._collect_single_page_with_session(
        99999,
        {"token": "token", "cookies": []},
    )

    assert success is False
    assert message == "公众号不存在"
    assert count == 0


def test_collect_single_page_with_session_marks_account_failed_on_api_error(db):
    """测试微信接口返回错误时会更新采集状态为失败"""
    service = ArticleService()
    account = WechatAccount(nickname="测试号", fakeid="fakeid-1", begin=0, count=5)
    db.add(account)
    db.commit()
    db.refresh(account)

    mock_response = Mock()
    mock_response.json.return_value = {"base_resp": {"ret": -1, "err_msg": "token expired"}}

    with patch(
        "wechat_article_assistant.services.article_service.requests.get",
        return_value=mock_response,
    ):
        success, message, count = service._collect_single_page_with_session(
            account.id,
            {"token": "token", "cookies": [{"name": "pass_ticket", "value": "cookie"}]},
        )

    db.refresh(account)
    assert success is False
    assert message == "采集失败: token expired"
    assert count == 0
    assert account.collect_status == "失败"


def test_collect_single_page_with_session_saves_articles_and_updates_begin(db):
    """测试单页采集成功时保存文章并推进 begin"""
    service = ArticleService()
    account = WechatAccount(nickname="测试号", fakeid="fakeid-2", begin=0, count=2)
    db.add(account)
    db.commit()
    db.refresh(account)

    result = {
        "base_resp": {"ret": 0},
        "publish_page": json.dumps(
            {
                "publish_list": [
                    {
                        "publish_info": json.dumps(
                            {
                                "appmsgex": [
                                    {
                                        "aid": "article-1",
                                        "title": "普通标题",
                                        "cover": "https://img.test/1.png",
                                        "link": "https://mp.weixin.qq.com/s/1",
                                        "author_name": "作者A",
                                        "is_deleted": False,
                                        "create_time": 1700000000,
                                        "update_time": 1700000100,
                                    },
                                    {
                                        "aid": "article-2",
                                        "title": "X" * 60,
                                        "item_show_type": 10,
                                        "cover": "https://img.test/2.png",
                                        "link": "https://mp.weixin.qq.com/s/2",
                                        "author_name": "作者B",
                                        "is_deleted": True,
                                        "create_time": 1700000200,
                                        "update_time": 1700000300,
                                    },
                                ]
                            }
                        )
                    }
                ]
            }
        ),
    }
    mock_response = Mock()
    mock_response.json.return_value = result

    with patch(
        "wechat_article_assistant.services.article_service.requests.get",
        return_value=mock_response,
    ):
        success, message, count = service._collect_single_page_with_session(
            account.id,
            {"token": "token", "cookies": [{"name": "pass_ticket", "value": "cookie"}]},
        )

    db.refresh(account)
    saved_articles = db.query(WechatArticle).filter_by(wechat_list_id=account.id).all()

    assert success is True
    assert message == "采集成功，共 2 篇文章"
    assert count == 2
    assert account.collect_status == "已采集"
    assert account.begin == 2
    assert len(saved_articles) == 2
    assert saved_articles[0].nickname == "测试号"
    assert any(article.article_is_deleted == "是" for article in saved_articles)
    assert any(article.article_title.endswith("...") for article in saved_articles)


def test_collect_articles_all_stops_when_page_returns_zero():
    """测试全部采集在无更多文章时结束"""
    service = ArticleService()

    with patch.object(service.wechat_auth, "ensure_authenticated", return_value=True), patch.object(
        service.wechat_auth,
        "get_session_data",
        return_value={"token": "token", "cookies": []},
    ), patch.object(
        service,
        "_collect_single_page_with_session",
        side_effect=[(True, "ok", 2), (True, "ok", 0)],
    ) as mock_collect, patch(
        "wechat_article_assistant.services.article_service.time.sleep"
    ) as mock_sleep:
        success, message, count = service.collect_articles_all(1)

    assert success is True
    assert message == "采集完成，共 2 篇文章"
    assert count == 2
    assert mock_collect.call_count == 2
    mock_sleep.assert_called_once()


def test_collect_recent_articles_all_accounts_restores_account_settings(db):
    """测试采集最近文章后恢复公众号原始 begin 和 count"""
    service = ArticleService()
    account = WechatAccount(nickname="公众号A", fakeid="fakeid-a", begin=10, count=20)
    db.add(account)
    db.commit()
    db.refresh(account)

    with patch.object(service.wechat_auth, "ensure_authenticated", return_value=True), patch.object(
        service.wechat_auth,
        "get_session_data",
        return_value={"token": "token", "cookies": []},
    ), patch.object(
        service,
        "_collect_single_page_with_session",
        return_value=(True, "ok", 3),
    ) as mock_collect:
        success, message, stats = service.collect_recent_articles_all_accounts()

    db.refresh(account)
    assert success is True
    assert message == "全部采集完成！成功 1 个公众号，共 3 篇文章"
    assert stats["success_accounts"] == 1
    assert stats["failed_accounts"] == 0
    assert stats["total_articles"] == 3
    assert account.begin == 10
    assert account.count == 20
    mock_collect.assert_called_once()
