from datetime import datetime
from unittest.mock import patch

from wechat_article_assistant.models import WechatArticle


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
        article_update_time=datetime.now(),
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
        article_update_time=datetime.now(),
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


def test_delete_articles_empty_ids(client):
    """测试批量删除文章时未传 ids"""
    response = client.post("/api/article/delete", json={"ids": []})
    assert response.status_code == 200
    assert response.json["success"] is False
    assert response.json["message"] == "请选择要删除的文章"


def test_delete_articles_success(client):
    """测试批量删除文章成功"""
    with patch(
        "wechat_article_assistant.routes.article_routes.article_service.delete_articles",
        return_value=(True, "成功删除 2 篇文章"),
    ) as mock_delete:
        response = client.post("/api/article/delete", json={"ids": [1, 2]})

    assert response.status_code == 200
    assert response.json["success"] is True
    assert response.json["message"] == "成功删除 2 篇文章"
    mock_delete.assert_called_once_with([1, 2])


def test_collect_single_requires_login(client):
    """测试采集单页文章时需要登录"""
    with patch(
        "wechat_article_assistant.routes.article_routes.wechat_auth.session_manager.is_session_valid",
        return_value=False,
    ), patch("wechat_article_assistant.routes.article_routes.config.LOGIN_MODE", "popup"):
        response = client.post("/api/article/collect/single/1")

    assert response.status_code == 200
    assert response.json["success"] is False
    assert response.json["needLogin"] is True
    assert response.json["loginMode"] == "popup"


def test_download_articles_marks_downloaded(client, db):
    """测试批量下载成功后标记文章为已下载"""
    article = WechatArticle(
        nickname="测试公众号",
        article_id="test_id_download",
        article_title="下载测试文章",
        article_link="https://mp.weixin.qq.com/s/test-download",
        article_create_time=datetime.now(),
        article_update_time=datetime.now(),
    )
    db.add(article)
    db.commit()
    db.refresh(article)

    with patch(
        "wechat_article_assistant.routes.article_routes.download_service.download_articles_batch",
        return_value=(1, 0, []),
    ) as mock_download, patch(
        "wechat_article_assistant.routes.article_routes.article_service.mark_as_downloaded",
        return_value=True,
    ) as mock_mark:
        response = client.post("/api/article/download", json={"ids": [article.id]})

    assert response.status_code == 200
    assert response.json["success"] is True
    assert response.json["successCount"] == 1
    assert response.json["failCount"] == 0
    mock_download.assert_called_once()
    mock_mark.assert_called_once_with([article.id])


def test_get_all_article_ids_with_filters(client, db):
    """测试获取符合筛选条件的文章 ID 列表"""
    now = datetime.now()
    article_a = WechatArticle(
        nickname="公众号A",
        article_id="id_a",
        article_title="A文章",
        article_create_time=now,
        article_update_time=now,
    )
    article_b = WechatArticle(
        nickname="公众号B",
        article_id="id_b",
        article_title="B文章",
        article_create_time=now,
        article_update_time=now,
    )
    db.add_all([article_a, article_b])
    db.commit()
    db.refresh(article_a)
    db.refresh(article_b)

    response = client.get("/api/article/all-ids", query_string={"nickname": "公众号A"})

    assert response.status_code == 200
    assert response.json["success"] is True
    assert response.json["ids"] == [article_a.id]
