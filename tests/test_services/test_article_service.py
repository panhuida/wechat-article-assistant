from wechat_article_assistant.services.article_service import ArticleService
from wechat_article_assistant.models import WechatArticle
from datetime import datetime

def test_article_service_get_articles(db):
    """测试文章服务：获取文章列表"""
    service = ArticleService()
    
    # 准备数据
    article1 = WechatArticle(
        nickname="公众号A",
        article_title="标题A",
        article_create_time=datetime.now()
    )
    article2 = WechatArticle(
        nickname="公众号B",
        article_title="标题B",
        article_create_time=datetime.now()
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
