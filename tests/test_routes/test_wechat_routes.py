from wechat_article_assistant.models import WechatAccount

def test_get_accounts_empty(client, db):
    """测试获取公众号列表（空）"""
    response = client.get("/api/wechat/list")
    assert response.status_code == 200
    data = response.json
    assert data["success"] is True
    assert len(data["data"]) == 0

def test_create_account(client, db):
    """测试创建公众号"""
    payload = {
        "nickname": "新公众号",
        "fakeid": "new_fakeid",
        "alias": "new_alias"
    }
    response = client.post("/api/wechat/create", json=payload)
    assert response.status_code == 200
    data = response.json
    assert data["success"] is True
    assert "id" in data

    # 验证数据库
    account = db.query(WechatAccount).filter_by(fakeid="new_fakeid").first()
    assert account is not None
    assert account.nickname == "新公众号"

def test_update_account(client, db):
    """测试更新公众号"""
    account = WechatAccount(nickname="旧名称", fakeid="update_fakeid")
    db.add(account)
    db.commit()
    db.refresh(account)
    
    payload = {"nickname": "新名称"}
    response = client.put(f"/api/wechat/{account.id}", json=payload)
    assert response.status_code == 200
    assert response.json["success"] is True
    
    db.refresh(account)
    assert account.nickname == "新名称"

def test_delete_account(client, db):
    """测试删除公众号"""
    account = WechatAccount(nickname="待删除", fakeid="delete_fakeid")
    db.add(account)
    db.commit()
    db.refresh(account)
    
    response = client.delete(f"/api/wechat/{account.id}")
    assert response.status_code == 200
    assert response.json["success"] is True
    
    deleted = db.query(WechatAccount).filter_by(id=account.id).first()
    assert deleted is None
