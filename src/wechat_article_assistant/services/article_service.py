"""文章管理服务"""

import json
import random
import time
from datetime import datetime
from typing import Any, cast

import requests
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..browser.wechat_authenticator import WechatAuthenticator
from ..config import config
from ..models import WechatAccount, WechatArticle, get_db
from ..utils.logger import get_module_logger

logger = get_module_logger(__name__)


class ArticleService:
    """文章管理服务"""

    def __init__(self):
        """初始化文章服务"""
        self.wechat_auth = WechatAuthenticator()

    def get_articles(
        self,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        nickname: str | None = None,
        is_deleted: str | None = None,
        is_downloaded: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """
        获取文章列表（支持筛选和分页）

        Args:
            page: 页码
            page_size: 每页数量
            search: 搜索关键词
            nickname: 公众号名称
            is_deleted: 是否删除
            is_downloaded: 是否下载
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            (文章列表, 总数)
        """
        try:
            with get_db() as db:
                query = db.query(WechatArticle)

                # 搜索条件
                if search:
                    query = query.filter(
                        or_(
                            WechatArticle.article_title.like(f"%{search}%"),
                            WechatArticle.article_author_name.like(f"%{search}%"),
                        )
                    )

                # 筛选条件
                if nickname:
                    query = query.filter(WechatArticle.nickname == nickname)

                if is_deleted:
                    query = query.filter(WechatArticle.article_is_deleted == is_deleted)

                if is_downloaded:
                    query = query.filter(WechatArticle.is_downloaded == is_downloaded)

                if start_date:
                    query = query.filter(WechatArticle.article_create_time >= start_date)

                if end_date:
                    query = query.filter(WechatArticle.article_create_time <= end_date)

                # 总数
                total = query.count()

                # 分页
                offset = (page - 1) * page_size
                articles = (
                    query.order_by(WechatArticle.article_create_time.desc())
                    .offset(offset)
                    .limit(page_size)
                    .all()
                )

                return [article.to_dict() for article in articles], total

        except Exception as e:
            logger.error(f"获取文章列表失败: {e}")
            return [], 0

    def get_article_by_id(self, article_id: int) -> dict[str, Any] | None:
        """
        根据ID获取文章

        Args:
            article_id: 文章ID

        Returns:
            文章信息，不存在返回None
        """
        try:
            with get_db() as db:
                article = db.query(WechatArticle).filter(WechatArticle.id == article_id).first()
                return article.to_dict() if article else None
        except Exception as e:
            logger.error(f"获取文章失败: {e}")
            return None

    def delete_articles(self, article_ids: list[int]) -> tuple[bool, str]:
        """
        批量删除文章

        Args:
            article_ids: 文章ID列表

        Returns:
            (是否成功, 消息)
        """
        try:
            with get_db() as db:
                deleted = (
                    db.query(WechatArticle)
                    .filter(WechatArticle.id.in_(article_ids))
                    .delete(synchronize_session=False)
                )
                db.commit()

                logger.info(f"删除文章成功，数量: {deleted}")
                return True, f"成功删除 {deleted} 篇文章"

        except Exception as e:
            logger.error(f"删除文章失败: {e}")
            return False, f"删除失败: {str(e)}"

    def mark_as_downloaded(self, article_ids: list[int]) -> bool:
        """
        标记文章为已下载

        Args:
            article_ids: 文章ID列表

        Returns:
            是否成功
        """
        try:
            with get_db() as db:
                db.query(WechatArticle).filter(WechatArticle.id.in_(article_ids)).update(
                    {"is_downloaded": "是"}, synchronize_session=False
                )
                db.commit()
                return True

        except Exception as e:
            logger.error(f"标记文章失败: {e}")
            return False

    def collect_articles_single_page(self, account_id: int) -> tuple[bool, str, int]:
        """
        采集单页文章

        Args:
            account_id: 公众号ID

        Returns:
            (是否成功, 消息, 采集数量)
        """
        try:
            # 确保已认证（自动处理会话复用和登录）
            if not self.wechat_auth.ensure_authenticated():
                return False, "认证失败，请重试", 0

            # 加载会话
            session_data = self.wechat_auth.get_session_data()
            if not session_data:
                return False, "获取会话数据失败", 0

            # 调用内部方法执行采集
            return self._collect_single_page_with_session(cast(int, account_id), session_data)

        except Exception as e:
            logger.error(f"采集文章失败: {e}")
            return False, f"采集失败: {str(e)}", 0

    def _collect_single_page_with_session(
        self, account_id: int, session_data: dict[str, Any]
    ) -> tuple[bool, str, int]:
        """
        使用已有会话采集单页文章（内部方法）

        Args:
            account_id: 公众号ID
            session_data: 会话数据

        Returns:
            (是否成功, 消息, 采集数量)
        """
        try:
            with get_db() as db:
                account = db.query(WechatAccount).filter(WechatAccount.id == account_id).first()

                if not account:
                    return False, "公众号不存在", 0

                # 更新采集状态
                account.collect_status = "采集中"  # type: ignore[assignment]
                db.commit()

                # 构造请求参数
                url = f"{config.WECHAT_MP_URL}/cgi-bin/appmsgpublish"
                params = {
                    "sub": "list",
                    "search_field": "null",
                    "begin": account.begin,
                    "count": account.count,
                    "query": "",
                    "fakeid": account.fakeid,
                    "type": "101_1",
                    "free_publish_type": "1",
                    "sub_action": "list_ex",
                    "token": session_data.get("token", ""),
                    "lang": "zh_CN",
                    "f": "json",
                    "ajax": "1",
                }

                # 构造请求头和cookies
                cookies = {
                    cookie["name"]: cookie["value"] for cookie in session_data.get("cookies", [])
                }

                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": config.WECHAT_MP_URL,
                }

                # 发送请求
                response = requests.get(
                    url, params=params, cookies=cookies, headers=headers, timeout=30
                )
                result = response.json()

                if result.get("base_resp", {}).get("ret") != 0:
                    account.collect_status = "失败"  # type: ignore[assignment]
                    db.commit()
                    error_msg = result.get("base_resp", {}).get("err_msg", "未知错误")
                    return False, f"采集失败: {error_msg}", 0

                # 解析文章数据
                count = self._parse_and_save_articles(db, account, result)

                # 更新采集状态和起始位置
                account.collect_status = "已采集"  # type: ignore[assignment]
                account.begin += account.count  # type: ignore[assignment]
                db.commit()

                logger.info(f"采集成功: {account.nickname}, 数量: {count}")
                return True, f"采集成功，共 {count} 篇文章", count

        except Exception as e:
            logger.error(f"采集文章失败: {e}")
            # 尝试更新失败状态
            try:
                with get_db() as db:
                    account = db.query(WechatAccount).filter(WechatAccount.id == account_id).first()
                    if account:
                        account.collect_status = "失败"  # type: ignore[assignment]
                        db.commit()
            except Exception:
                pass
            return False, f"采集失败: {str(e)}", 0

    def collect_articles_all(self, account_id: int) -> tuple[bool, str, int]:
        """
        采集全部文章（循环采集直到没有更多文章）

        Args:
            account_id: 公众号ID

        Returns:
            (是否成功, 消息, 采集总数)
        """
        try:
            # 只加载一次会话，在整个采集过程中复用
            logger.info(f"开始全部采集，公众号ID: {account_id}")

            # 确保已认证（自动处理会话复用和登录）
            if not self.wechat_auth.ensure_authenticated():
                return False, "认证失败，请重试", 0

            # 加载会话
            session_data = self.wechat_auth.get_session_data()
            if not session_data:
                return False, "获取会话数据失败", 0

            logger.info("会话加载成功，开始循环采集")

            total_count = 0
            page = 1

            while True:
                logger.info(f"采集第 {page} 页...")
                success, msg, count = self._collect_single_page_with_session(
                    account_id, session_data
                )

                if not success:
                    logger.error(f"采集失败: {msg}")
                    return False, msg, total_count

                total_count += count
                logger.info(f"第 {page} 页采集成功，本页: {count} 篇，累计: {total_count} 篇")

                # 如果本次采集数量为0，说明已经采集完毕
                if count == 0:
                    logger.info("没有更多文章，采集完成")
                    break

                # 增加随机延时，避免频率控制
                delay = random.uniform(1, 3)
                logger.info(f"延时 {delay:.2f} 秒后继续...")
                time.sleep(delay)

                page += 1

            logger.info(f"全部采集完成，总数: {total_count}")
            return True, f"采集完成，共 {total_count} 篇文章", total_count

        except Exception as e:
            logger.error(f"全部采集失败: {e}")
            return False, f"采集失败: {str(e)}", 0

    def _parse_and_save_articles(
        self, db: Session, account: WechatAccount, result: dict[str, Any]
    ) -> int:
        """
        解析并保存文章数据

        Args:
            db: 数据库会话
            account: 公众号对象
            result: API响应结果

        Returns:
            保存的文章数量
        """
        count = 0

        try:
            # 解析publish_page JSON字符串
            publish_page = json.loads(result.get("publish_page", "{}"))
            publish_list = publish_page.get("publish_list", [])

            for item in publish_list:
                publish_info = json.loads(item.get("publish_info", "{}"))
                appmsgex_list = publish_info.get("appmsgex", [])

                for appmsg in appmsgex_list:
                    # 检查文章是否已存在
                    aid = appmsg.get("aid", "")
                    exists = db.query(WechatArticle).filter(WechatArticle.article_id == aid).first()

                    if exists:
                        continue

                    # 创建文章记录
                    article = WechatArticle(
                        wechat_list_id=account.id,
                        nickname=account.nickname,
                        article_id=aid,
                        article_title=appmsg.get("title", ""),
                        article_cover=appmsg.get("cover", ""),
                        article_link=appmsg.get("link", ""),
                        article_author_name=appmsg.get("author_name", ""),
                        article_is_deleted="是" if appmsg.get("is_deleted", False) else "否",
                        article_create_time=datetime.fromtimestamp(appmsg.get("create_time", 0)),
                        article_update_time=datetime.fromtimestamp(appmsg.get("update_time", 0)),
                        is_downloaded="否",
                    )

                    db.add(article)
                    count += 1

            db.commit()

        except Exception as e:
            logger.error(f"解析文章数据失败: {e}")
            db.rollback()

        return count

    def collect_recent_articles_all_accounts(self) -> tuple[bool, str, dict[str, Any]]:
        """
        获取所有公众号最近5次发的文章

        Returns:
            (是否成功, 消息, 统计信息)
        """
        try:
            logger.info("开始获取所有公众号最近5次发的文章")

            # 确保已认证（自动处理会话复用和登录）
            if not self.wechat_auth.ensure_authenticated():
                return False, "认证失败，请重试", {}

            # 加载会话
            session_data = self.wechat_auth.get_session_data()
            if not session_data:
                return False, "获取会话数据失败", {}

            # 获取所有公众号
            with get_db() as db:
                accounts = db.query(WechatAccount).all()

                if not accounts:
                    return False, "没有找到公众号，请先添加公众号", {}

                total_accounts = len(accounts)
                success_accounts = 0
                failed_accounts = 0
                total_articles = 0
                failed_list = []

                logger.info(f"共找到 {total_accounts} 个公众号")

                # 循环采集每个公众号
                for index, account in enumerate(accounts, 1):
                    logger.info(f"[{index}/{total_accounts}] 开始采集: {account.nickname}")

                    # 保存原始的begin和count
                    original_begin = account.begin
                    original_count = account.count

                    try:
                        # 临时设置begin=0, count=5
                        account.begin = 0  # type: ignore[assignment]
                        account.count = 5  # type: ignore[assignment]
                        db.commit()

                        # 调用单页采集
                        success, msg, count = self._collect_single_page_with_session(
                            account.id, session_data
                        )

                        if success:
                            success_accounts += 1
                            total_articles += count
                            logger.info(
                                f"[{index}/{total_accounts}] 采集成功: {account.nickname}, 文章数: {count}"
                            )
                        else:
                            failed_accounts += 1
                            failed_list.append(f"{account.nickname}: {msg}")
                            logger.error(
                                f"[{index}/{total_accounts}] 采集失败: {account.nickname}, 原因: {msg}"
                            )

                    except Exception as e:
                        failed_accounts += 1
                        failed_list.append(f"{account.nickname}: {str(e)}")
                        logger.error(
                            f"[{index}/{total_accounts}] 采集异常: {account.nickname}, 错误: {e}"
                        )

                    finally:
                        # 恢复原始的begin和count
                        account.begin = original_begin  # type: ignore[assignment]
                        account.count = original_count  # type: ignore[assignment]
                        db.commit()

                    # 添加延时避免频率限制
                    if index < total_accounts:
                        delay = random.uniform(1, 2)
                        logger.info(f"延时 {delay:.2f} 秒后继续...")
                        time.sleep(delay)

                # 生成统计信息
                stats = {
                    "total_accounts": total_accounts,
                    "success_accounts": success_accounts,
                    "failed_accounts": failed_accounts,
                    "total_articles": total_articles,
                    "failed_list": failed_list,
                }

                if failed_accounts == 0:
                    message = f"全部采集完成！成功 {success_accounts} 个公众号，共 {total_articles} 篇文章"
                    logger.info(message)
                    return True, message, stats
                elif success_accounts == 0:
                    message = "采集失败！所有公众号均采集失败"
                    logger.error(message)
                    return False, message, stats
                else:
                    message = f"采集完成！成功 {success_accounts} 个，失败 {failed_accounts} 个，共 {total_articles} 篇文章"
                    logger.info(message)
                    return True, message, stats

        except Exception as e:
            logger.error(f"获取最近文章失败: {e}")
            return False, f"采集失败: {str(e)}", {}

    def get_account_names(self) -> list[str]:
        """
        获取所有公众号名称（用于筛选下拉列表）

        Returns:
            公众号名称列表
        """
        try:
            with get_db() as db:
                names = db.query(WechatArticle.nickname).distinct().all()
                return [name[0] for name in names if name[0]]
        except Exception as e:
            logger.error(f"获取公众号名称失败: {e}")
            return []

    def get_all_article_ids(
        self,
        search: str | None = None,
        nickname: str | None = None,
        is_deleted: str | None = None,
        is_downloaded: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[int]:
        """
        获取所有符合筛选条件的文章ID

        Args:
            search: 搜索关键词
            nickname: 公众号名称
            is_deleted: 是否删除
            is_downloaded: 是否下载
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            文章ID列表
        """
        try:
            with get_db() as db:
                query = db.query(WechatArticle.id)

                # 搜索条件
                if search:
                    query = query.filter(
                        or_(
                            WechatArticle.article_title.like(f"%{search}%"),
                            WechatArticle.article_author_name.like(f"%{search}%"),
                        )
                    )

                # 筛选条件
                if nickname:
                    query = query.filter(WechatArticle.nickname == nickname)

                if is_deleted:
                    query = query.filter(WechatArticle.article_is_deleted == is_deleted)

                if is_downloaded:
                    query = query.filter(WechatArticle.is_downloaded == is_downloaded)

                if start_date:
                    query = query.filter(WechatArticle.article_create_time >= start_date)

                if end_date:
                    query = query.filter(WechatArticle.article_create_time <= end_date)

                ids = [item[0] for item in query.all()]
                return ids

        except Exception as e:
            logger.error(f"获取所有文章ID失败: {e}")
            return []
