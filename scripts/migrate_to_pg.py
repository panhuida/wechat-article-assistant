import sys
import os
from pathlib import Path

# 添加 src 到路径
current_dir = Path(__file__).resolve().parent
src_dir = current_dir.parent / "src"
sys.path.append(str(src_dir))

from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import sessionmaker, make_transient
from wechat_article_assistant.models import Base, WechatAccount, WechatArticle
from wechat_article_assistant.config import BASE_DIR

# 配置
SQLITE_DB_PATH = BASE_DIR / "data" / "wechat_assistant.db"
SOURCE_URL = f"sqlite:///{SQLITE_DB_PATH}"
# 默认目标数据库，如果需要测试可以通过环境变量覆盖
TARGET_URL = os.getenv("TARGET_DATABASE_URL", "postgresql://demo:demo@192.168.31.72:5432/wechat_assistant")

def create_database_if_not_exists(url):
    """如果目标数据库不存在则创建"""
    try:
        db_url = make_url(url)
        database_name = db_url.database
        
        # 连接到默认的 'postgres' 数据库以检查/创建目标数据库
        # 我们将 URL 中的数据库名称替换为 'postgres'
        postgres_db_url = db_url.set(database='postgres')
        
        # CREATE DATABASE 需要 isolation_level="AUTOCOMMIT"
        engine = create_engine(postgres_db_url, isolation_level="AUTOCOMMIT")
        
        with engine.connect() as conn:
            # 检查数据库是否存在
            # 使用 text() 执行原始 SQL
            result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{database_name}'"))
            if not result.scalar():
                print(f"数据库 '{database_name}' 不存在。正在创建...")
                conn.execute(text(f"CREATE DATABASE {database_name}"))
                print(f"数据库 '{database_name}' 创建成功。")
            else:
                print(f"数据库 '{database_name}' 已存在。")
        
        engine.dispose()
    except Exception as e:
        print(f"警告: 无法检查/创建数据库: {e}")
        print("将尝试直接连接到目标数据库...")

def migrate():
    print("开始迁移...")
    print(f"源数据库: {SOURCE_URL}")
    print(f"目标数据库: {TARGET_URL}")
    
    # 确保目标数据库存在
    create_database_if_not_exists(TARGET_URL)
    
    # 源数据库设置
    if not SQLITE_DB_PATH.exists():
        print(f"错误: 源数据库未在 {SQLITE_DB_PATH} 找到")
        return

    source_engine = create_engine(SOURCE_URL)
    SourceSession = sessionmaker(bind=source_engine)
    
    # 目标数据库设置
    try:
        target_engine = create_engine(TARGET_URL)
        # 测试连接
        with target_engine.connect() as conn:
            pass
    except Exception as e:
        print(f"连接目标数据库失败: {e}")
        return

    TargetSession = sessionmaker(bind=target_engine)
    
    # 在目标数据库中创建表
    print("正在目标数据库中创建表...")
    try:
        # 先删除所有表以确保架构更新
        print("正在删除目标数据库中的现有表以确保架构更新...")
        Base.metadata.drop_all(target_engine)
        Base.metadata.create_all(target_engine)
    except Exception as e:
        print(f"创建表失败: {e}")
        return
    
    source_session = SourceSession()
    target_session = TargetSession()
    
    try:
        # 迁移 WechatAccount
        print("正在迁移 WechatAccount...")
        accounts = source_session.query(WechatAccount).all()
        print(f"找到 {len(accounts)} 个公众号账号。")
        
        for account in accounts:
            # 从源会话中分离
            source_session.expunge(account)
            # 使其变为瞬态（像一个新对象）
            make_transient(account)
            # 添加到目标会话
            target_session.add(account)
            
        target_session.flush() # 刷新以检查错误
        
        # 迁移 WechatArticle
        print("正在迁移 WechatArticle...")
        articles = source_session.query(WechatArticle).all()
        print(f"找到 {len(articles)} 篇文章。")
        
        for article in articles:
            source_session.expunge(article)
            make_transient(article)
            target_session.add(article)
            
        target_session.commit()
        print("迁移成功完成！")
        
    except Exception as e:
        target_session.rollback()
        print(f"迁移失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        source_session.close()
        target_session.close()

if __name__ == "__main__":
    migrate()
