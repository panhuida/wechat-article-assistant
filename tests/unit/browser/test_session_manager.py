import json
from pathlib import Path

from wechat_article_assistant.browser.session_manager import SessionManager


def test_save_and_load_session(tmp_path: Path):
    """测试保存并重新加载会话数据"""
    session_file = tmp_path / "session.json"
    manager = SessionManager(session_file=session_file)

    saved = manager.save_session(
        cookies=[{"name": "token", "value": "abc"}],
        token="abc",
        other_data={"x": 1},
    )

    loaded = manager.load_session(force_reload=True)

    assert saved is True
    assert loaded == {
        "cookies": [{"name": "token", "value": "abc"}],
        "token": "abc",
        "other_data": {"x": 1},
    }


def test_load_session_uses_cache_before_ttl_expires(tmp_path: Path):
    """测试缓存未过期时优先返回缓存内容"""
    session_file = tmp_path / "session.json"
    manager = SessionManager(session_file=session_file)
    manager.save_session(cookies=[{"name": "a", "value": "1"}], token="t1")

    session_file.write_text(
        json.dumps({"cookies": [{"name": "a", "value": "2"}], "token": "t2", "other_data": {}}),
        encoding="utf-8",
    )

    loaded = manager.load_session()

    assert loaded is not None
    assert loaded["token"] == "t1"


def test_load_session_force_reload_bypasses_cache(tmp_path: Path):
    """测试强制重载时忽略缓存"""
    session_file = tmp_path / "session.json"
    manager = SessionManager(session_file=session_file)
    manager.save_session(cookies=[{"name": "a", "value": "1"}], token="t1")

    session_file.write_text(
        json.dumps({"cookies": [{"name": "a", "value": "2"}], "token": "t2", "other_data": {}}),
        encoding="utf-8",
    )

    loaded = manager.load_session(force_reload=True)

    assert loaded is not None
    assert loaded["token"] == "t2"


def test_clear_session_removes_file_and_cache(tmp_path: Path):
    """测试清理会话时删除文件并清空缓存"""
    session_file = tmp_path / "session.json"
    manager = SessionManager(session_file=session_file)
    manager.save_session(cookies=[{"name": "a", "value": "1"}], token="t1")

    cleared = manager.clear_session()

    assert cleared is True
    assert session_file.exists() is False
    assert manager._cached_session is None
    assert manager._cache_time == 0


def test_is_session_valid_requires_non_empty_cookies(tmp_path: Path):
    """测试会话有效性依赖 cookies 非空"""
    session_file = tmp_path / "session.json"
    manager = SessionManager(session_file=session_file)

    assert manager.is_session_valid() is False

    session_file.write_text(json.dumps({"cookies": [], "token": None}), encoding="utf-8")
    assert manager.is_session_valid() is False

    session_file.write_text(
        json.dumps({"cookies": [{"name": "token", "value": "x"}], "token": "x"}),
        encoding="utf-8",
    )
    manager.invalidate_cache()
    assert manager.is_session_valid() is True
