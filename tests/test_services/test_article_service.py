from datetime import datetime, timedelta

from wechat_article_assistant.models import WechatArticle
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
