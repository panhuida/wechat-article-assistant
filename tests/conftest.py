"""pytest配置文件"""

import sys
from pathlib import Path

import pytest

# 添加src目录到Python路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """设置测试环境"""
    from wechat_article_assistant.config import config
    from wechat_article_assistant import models
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # 使用内存数据库
    config.DATABASE_URL = "sqlite:///:memory:"
    
    # 重新创建引擎和会话工厂
    models.engine = create_engine(config.DATABASE_URL, echo=False)
    models.SessionLocal = sessionmaker(bind=models.engine, autoflush=False, autocommit=False)
    
    # 初始化数据库表
    models.init_db()

@pytest.fixture
def app(setup_test_env):
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
def db(setup_test_env):
    """创建测试数据库会话"""
    from wechat_article_assistant.models import get_db, Base, engine

    # 每个测试前清空数据
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with get_db() as session:
        yield session
