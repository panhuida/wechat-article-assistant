"""pytest配置文件"""

import pytest
import sys
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture
def app():
    """创建测试Flask应用"""
    from wechat_article_assistant.app import create_app

    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def db():
    """创建测试数据库"""
    from wechat_article_assistant.models import init_db, get_db

    init_db()
    return get_db()
