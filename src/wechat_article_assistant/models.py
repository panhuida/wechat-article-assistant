"""数据模型定义"""

from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session

from .config import config

# 创建基类
Base = declarative_base()

# 创建引擎
engine = create_engine(config.DATABASE_URL, echo=False)

# 创建会话工厂
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Session:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass


class WechatAccount(Base):
    """公众号列表表"""

    __tablename__ = "wechat_list"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="序号")
    fakeid = Column(String(100), nullable=True, comment="公众号唯一标识")
    nickname = Column(String(50), nullable=True, comment="公众号名称")
    alias = Column(String(50), nullable=True, comment="公众号别名")
    round_head_img = Column(String(200), nullable=True, comment="公众号圆形头像URL")
    service_type = Column(String(10), nullable=True, comment="公众号类型")
    signature = Column(String(200), nullable=True, comment="公众号签名")
    verify_status = Column(String(10), nullable=True, comment="公众号认证状态")
    memo = Column(String(200), nullable=True, comment="备注")
    begin = Column(Integer, default=0, nullable=True, comment="单页起始位置")
    count = Column(Integer, default=5, nullable=True, comment="单页采集数量")
    collect_status = Column(String(50), default="未采集", nullable=True, comment="采集状态")
    create_time = Column(DateTime, default=datetime.now, nullable=True, comment="创建时间")
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=True, comment="更新时间")

    # 关联文章
    articles = relationship("WechatArticle", back_populates="account")

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "fakeid": self.fakeid,
            "nickname": self.nickname,
            "alias": self.alias,
            "round_head_img": self.round_head_img,
            "service_type": self.service_type,
            "signature": self.signature,
            "verify_status": self.verify_status,
            "memo": self.memo,
            "begin": self.begin,
            "count": self.count,
            "collect_status": self.collect_status,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S") if self.create_time else None,
            "update_time": self.update_time.strftime("%Y-%m-%d %H:%M:%S") if self.update_time else None,
        }


class WechatArticle(Base):
    """公众号文章列表表"""

    __tablename__ = "wechat_article_list"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="序号")
    wechat_list_id = Column(Integer, ForeignKey("wechat_list.id"), nullable=True, comment="公众号列表ID")
    nickname = Column(String(50), nullable=True, comment="公众号名称")
    article_id = Column(String(50), nullable=True, comment="文章ID")
    article_title = Column(String(100), nullable=True, comment="文章标题")
    article_cover = Column(String(200), nullable=True, comment="文章封面")
    article_link = Column(String(200), nullable=True, comment="文章链接")
    article_author_name = Column(String(20), nullable=True, comment="文章作者")
    article_is_deleted = Column(String(10), default="否", nullable=True, comment="文章是否删除")
    article_create_time = Column(DateTime, nullable=True, comment="文章创建时间")
    article_update_time = Column(DateTime, nullable=True, comment="文章更新时间")
    is_downloaded = Column(String(10), default="否", nullable=True, comment="是否下载")
    create_time = Column(DateTime, default=datetime.now, nullable=True, comment="创建时间")
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=True, comment="更新时间")

    # 关联公众号
    account = relationship("WechatAccount", back_populates="articles")

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "wechat_list_id": self.wechat_list_id,
            "nickname": self.nickname,
            "article_id": self.article_id,
            "article_title": self.article_title,
            "article_cover": self.article_cover,
            "article_link": self.article_link,
            "article_author_name": self.article_author_name,
            "article_is_deleted": self.article_is_deleted,
            "article_create_time": self.article_create_time.strftime("%Y-%m-%d %H:%M:%S") if self.article_create_time else None,
            "article_update_time": self.article_update_time.strftime("%Y-%m-%d %H:%M:%S") if self.article_update_time else None,
            "is_downloaded": self.is_downloaded,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S") if self.create_time else None,
            "update_time": self.update_time.strftime("%Y-%m-%d %H:%M:%S") if self.update_time else None,
        }


def init_db():
    """初始化数据库"""
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("数据库初始化完成")
