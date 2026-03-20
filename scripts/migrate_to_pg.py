import os
import sys
from pathlib import Path

# 添加 src 到路径
current_dir = Path(__file__).resolve().parent
src_dir = current_dir.parent / "src"
sys.path.append(str(src_dir))

from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.engine.url import make_url  # noqa: E402
from sqlalchemy.orm import make_transient, sessionmaker  # noqa: E402

from wechat_article_assistant.config import BASE_DIR  # noqa: E402
from wechat_article_assistant.models import Base, WechatAccount, WechatArticle  # noqa: E402

# 配置
SQLITE_DB_PATH = BASE_DIR / "data" / "wechat_assistant.db"
SOURCE_URL = f"sqlite:///{SQLITE_DB_PATH}"
# 默认目标数据库，如果需要测试可以通过环境变量覆盖
TARGET_URL = os.getenv(
    "TARGET_DATABASE_URL", "postgresql://demo:demo@192.168.31.72:5432/wechat_assistant"
)

def create_database_if_not_exists(url):
    """如果目标数据库不存在则创建"""
    try:
        db_url = make_url(url)
        database_name = db_url.database

        # 连接到默认的 'postgres' 数据库以检查/创建目标数据库
        # 我们将 URL 中的数据库名称替换为 'postgres'
        postgres_db_url = db_url.set(database="postgres")

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


def fix_sequences(engine):
    """
    修复 PostgreSQL 序列值

    从 SQLite 迁移数据后，PostgreSQL 的序列值不会自动更新，
    需要手动将序列值设置为表中最大 ID + 1，否则插入新记录时会出现主键冲突。
    """
    print("\n正在修复 PostgreSQL 序列值...")

    # 需要修复的表和序列
    tables = [
        ("wechat_list", "wechat_list_id_seq"),
        ("wechat_article_list", "wechat_article_list_id_seq"),
    ]

    with engine.connect() as conn:
        for table_name, sequence_name in tables:
            try:
                # 获取表中的最大 ID
                result = conn.execute(text(f"SELECT MAX(id) FROM {table_name}"))
                max_id = result.scalar()

                if max_id is None:
                    print(f"  表 {table_name}: 空表，跳过")
                    continue

                # 修复序列值为 max_id + 1
                new_seq = max_id + 1
                conn.execute(text(f"SELECT setval('{sequence_name}', {new_seq}, false)"))
                conn.commit()
                print(f"  表 {table_name}: 序列已设置为 {new_seq} (最大ID: {max_id})")

            except Exception as e:
                print(f"  表 {table_name}: 修复失败 - {e}")

    print("序列修复完成！")

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
    source_session_factory = sessionmaker(bind=source_engine)

    # 目标数据库设置
    try:
        target_engine = create_engine(TARGET_URL)
        # 测试连接
        with target_engine.connect():
            pass
    except Exception as e:
        print(f"连接目标数据库失败: {e}")
        return

    target_session_factory = sessionmaker(bind=target_engine)

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

    source_session = source_session_factory()
    target_session = target_session_factory()

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

        target_session.flush()  # 刷新以检查错误

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

        # 修复 PostgreSQL 序列值
        fix_sequences(target_engine)

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
