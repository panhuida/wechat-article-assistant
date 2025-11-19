from wechat_article_assistant.models import WechatArticle
from datetime import datetime

def test_get_articles_empty(client, db):
    """测试获取文章列表（空）"""
    response = client.get("/api/article/list")
    assert response.status_code == 200
    data = response.json
    assert data["success"] is True
    assert data["total"] == 0
    assert len(data["data"]) == 0

def test_get_articles_with_data(client, db):
    """测试获取文章列表（有数据）"""
    # 插入测试数据
    article = WechatArticle(
        nickname="测试公众号",
        article_id="test_id_1",
        article_title="测试文章标题",
        article_create_time=datetime.now(),
        article_update_time=datetime.now()
    )
    db.add(article)
    db.commit()

    response = client.get("/api/article/list")
    assert response.status_code == 200
    data = response.json
    assert data["success"] is True
    assert data["total"] == 1
    assert data["data"][0]["article_title"] == "测试文章标题"

def test_get_article_detail(client, db):
    """测试获取文章详情"""
    article = WechatArticle(
        nickname="测试公众号",
        article_id="test_id_2",
        article_title="详情测试文章",
        article_create_time=datetime.now(),
        article_update_time=datetime.now()
    )
    db.add(article)
    db.commit()
    
    # 获取刚插入的文章ID
    db.refresh(article)
    article_id = article.id

    response = client.get(f"/api/article/{article_id}")
    assert response.status_code == 200
    data = response.json
    assert data["success"] is True
    assert data["data"]["article_title"] == "详情测试文章"

def test_get_article_not_found(client):
    """测试获取不存在的文章"""
    response = client.get("/api/article/99999")
    assert response.status_code == 404
