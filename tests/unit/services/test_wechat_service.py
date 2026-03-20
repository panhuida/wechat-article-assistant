from wechat_article_assistant.models import WechatAccount
from wechat_article_assistant.services.wechat_service import WechatService


def test_create_account_success(db):
    """测试创建公众号成功"""
    service = WechatService()

    success, message, account_id = service.create_account(
        {
            "nickname": "新公众号",
            "fakeid": "new_fakeid",
            "alias": "new_alias",
            "begin": 3,
            "count": 10,
        }
    )

    created = db.query(WechatAccount).filter_by(id=account_id).first()

    assert success is True
    assert message == "创建成功"
    assert account_id is not None
    assert created is not None
    assert created.nickname == "新公众号"
    assert created.fakeid == "new_fakeid"
    assert created.alias == "new_alias"
    assert created.begin == 3
    assert created.count == 10
    assert created.collect_status == "未采集"


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


def test_update_account_success(db):
    """测试更新公众号成功"""
    service = WechatService()
    account = WechatAccount(nickname="旧名称", fakeid="old_fakeid", begin=0, count=5)
    db.add(account)
    db.commit()
    db.refresh(account)

    success, message = service.update_account(
        account.id,
        {"nickname": "新名称", "memo": "备注", "begin": 7, "id": 99999},
    )

    db.refresh(account)
    assert success is True
    assert message == "更新成功"
    assert account.nickname == "新名称"
    assert account.memo == "备注"
    assert account.begin == 7
    assert account.id != 99999


def test_delete_account_not_found(db):
    """测试删除不存在的公众号"""
    service = WechatService()

    success, message = service.delete_account(99999)

    assert success is False
    assert message == "公众号不存在"


def test_delete_account_success(db):
    """测试删除公众号成功"""
    service = WechatService()
    account = WechatAccount(nickname="待删除公众号", fakeid="delete_fakeid")
    db.add(account)
    db.commit()
    db.refresh(account)

    success, message = service.delete_account(account.id)

    deleted = db.query(WechatAccount).filter_by(id=account.id).first()
    assert success is True
    assert message == "删除成功"
    assert deleted is None


def test_get_account_by_id_not_found(db):
    """测试获取不存在的公众号返回 None"""
    service = WechatService()

    account = service.get_account_by_id(99999)

    assert account is None


def test_get_account_by_id_success(db):
    """测试按 ID 获取公众号成功"""
    service = WechatService()
    account = WechatAccount(nickname="查询公众号", fakeid="get_fakeid")
    db.add(account)
    db.commit()
    db.refresh(account)

    result = service.get_account_by_id(account.id)

    assert result is not None
    assert result["id"] == account.id
    assert result["nickname"] == "查询公众号"


def test_get_all_accounts_returns_latest_first(db):
    """测试获取公众号列表按更新时间倒序返回"""
    service = WechatService()
    older = WechatAccount(nickname="较早公众号", fakeid="older_fakeid")
    newer = WechatAccount(nickname="较新公众号", fakeid="newer_fakeid")
    db.add_all([older, newer])
    db.commit()

    service.update_account(older.id, {"memo": "先更新"})
    service.update_account(newer.id, {"memo": "后更新"})

    accounts = service.get_all_accounts()

    assert len(accounts) == 2
    assert accounts[0]["nickname"] == "较新公众号"
    assert accounts[1]["nickname"] == "较早公众号"


def test_update_collect_status_success(db):
    """测试更新采集状态成功"""
    service = WechatService()
    account = WechatAccount(nickname="状态公众号", fakeid="status_fakeid")
    db.add(account)
    db.commit()
    db.refresh(account)

    success = service.update_collect_status(account.id, "已采集")

    db.refresh(account)
    assert success is True
    assert account.collect_status == "已采集"


def test_update_begin_position_success(db):
    """测试更新采集起始位置成功"""
    service = WechatService()
    account = WechatAccount(nickname="位置公众号", fakeid="begin_fakeid", begin=0)
    db.add(account)
    db.commit()
    db.refresh(account)

    success = service.update_begin_position(account.id, 12)

    db.refresh(account)
    assert success is True
    assert account.begin == 12
