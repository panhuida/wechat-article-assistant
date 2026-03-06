from wechat_article_assistant.models import WechatAccount
from wechat_article_assistant.services.wechat_service import WechatService


def test_create_account_requires_nickname(db):
    """测试创建公众号时 nickname 不能为空"""
    service = WechatService()

    success, message, account_id = service.create_account({"fakeid": "missing_nickname"})

    assert success is False
    assert message == "公众号名称不能为空"
    assert account_id is None


def test_create_account_rejects_duplicate_fakeid(db):
    """测试创建公众号时拒绝重复 fakeid"""
    service = WechatService()
    db.add(WechatAccount(nickname="已有公众号", fakeid="dup_fakeid"))
    db.commit()

    success, message, account_id = service.create_account(
        {"nickname": "重复公众号", "fakeid": "dup_fakeid"}
    )

    assert success is False
    assert message == "该公众号已存在"
    assert account_id is None


def test_update_account_not_found(db):
    """测试更新不存在的公众号"""
    service = WechatService()

    success, message = service.update_account(99999, {"nickname": "新名称"})

    assert success is False
    assert message == "公众号不存在"


def test_delete_account_not_found(db):
    """测试删除不存在的公众号"""
    service = WechatService()

    success, message = service.delete_account(99999)

    assert success is False
    assert message == "公众号不存在"


def test_get_account_by_id_not_found(db):
    """测试获取不存在的公众号返回 None"""
    service = WechatService()

    account = service.get_account_by_id(99999)

    assert account is None
