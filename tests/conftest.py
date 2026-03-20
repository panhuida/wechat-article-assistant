"""pytest 配置文件"""

import sys
from pathlib import Path

import pytest

# 添加 src 目录到 Python 路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

_MARKERS_BY_DIR = {
    "unit": pytest.mark.unit,
    "integration": pytest.mark.integration,
    "contract": pytest.mark.contract,
    "manual": pytest.mark.manual,
}


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """按目录自动为测试打 marker。"""
    for item in items:
        path_parts = set(Path(str(item.fspath)).parts)
        for directory, marker in _MARKERS_BY_DIR.items():
            if directory in path_parts:
                item.add_marker(marker)


@pytest.fixture(scope="function")
def test_config(tmp_path: Path) -> dict[str, object]:
    """生成每个测试独立的运行配置"""
    return {
        "TESTING": True,
        "DATABASE_URL": f"sqlite:///{tmp_path / 'test.db'}",
        "DOWNLOAD_DIR": tmp_path / "downloads",
        "LOG_DIR": tmp_path / "logs",
        "SESSION_FILE": tmp_path / "wechat_session.json",
        "LOGIN_MODE": "popup",
    }


@pytest.fixture(scope="function")
def app(test_config: dict[str, object]):
    """创建测试 Flask 应用"""
    from wechat_article_assistant import create_app, models

    app = create_app(test_config)

    models.Base.metadata.drop_all(bind=models.engine)
    models.Base.metadata.create_all(bind=models.engine)

    yield app

    models.Base.metadata.drop_all(bind=models.engine)


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def db(app):
    """创建测试数据库会话"""
    from wechat_article_assistant.models import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def db_session(db):
    """为新测试提供更语义化的数据库会话名称"""
    yield db
