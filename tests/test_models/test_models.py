from datetime import datetime
from wechat_article_assistant.models import WechatAccount, WechatArticle

def test_wechat_account_model():
    """测试公众号模型"""
    account = WechatAccount(
        fakeid="test_fakeid",
        nickname="测试公众号",
        alias="test_alias",
        round_head_img="http://example.com/head.jpg",
        service_type="1",
        signature="测试签名",
        verify_status="0",
        memo="测试备注",
        begin=0,
        count=5,
        collect_status="未采集"
    )
    
    assert account.nickname == "测试公众号"
    assert account.fakeid == "test_fakeid"
    
    # 测试 to_dict
    data = account.to_dict()
    assert data["nickname"] == "测试公众号"
    assert data["fakeid"] == "test_fakeid"
    assert data["collect_status"] == "未采集"

def test_wechat_article_model():
    """测试文章模型"""
    now = datetime.now()
    article = WechatArticle(
        nickname="测试公众号",
        article_id="test_article_id",
        article_title="测试文章",
        article_cover="http://example.com/cover.jpg",
        article_link="http://example.com/article",
        article_author_name="测试作者",
        article_is_deleted="否",
        article_create_time=now,
        article_update_time=now,
        is_downloaded="否"
    )
    
    assert article.article_title == "测试文章"
    assert article.article_id == "test_article_id"
    
    # 测试 to_dict
    data = article.to_dict()
    assert data["article_title"] == "测试文章"
    assert data["article_id"] == "test_article_id"
    assert data["is_downloaded"] == "否"
