"""文章管理服务"""

import json
import requests
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import or_
from sqlalchemy.orm import Session
from ..models import WechatArticle, WechatAccount, get_db
from ..utils.logger import app_logger, collect_logger
from ..browser.session_manager import SessionManager
from ..config import config


class ArticleService:
    """文章管理服务"""

    def __init__(self):
        """初始化文章服务"""
        self.session_manager = SessionManager()

    def get_articles(
        self,
        page: int = 1,
        page_size: int = 20,
        search: str = None,
        nickname: str = None,
        is_deleted: str = None,
        is_downloaded: str = None,
        start_date: str = None,
        end_date: str = None
    ) -> Tuple[List[Dict[str, Any]], int]:
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
            db = get_db()
            query = db.query(WechatArticle)

            # 搜索条件
            if search:
                query = query.filter(
                    or_(
                        WechatArticle.nickname.like(f"%{search}%"),
                        WechatArticle.article_author_name.like(f"%{search}%")
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
            articles = query.order_by(WechatArticle.article_create_time.desc()).offset(offset).limit(page_size).all()

            return [article.to_dict() for article in articles], total

        except Exception as e:
            app_logger.error(f"获取文章列表失败: {e}")
            return [], 0
        finally:
            db.close()

    def get_article_by_id(self, article_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取文章

        Args:
            article_id: 文章ID

        Returns:
            文章信息，不存在返回None
        """
        try:
            db = get_db()
            article = db.query(WechatArticle).filter(WechatArticle.id == article_id).first()
            return article.to_dict() if article else None
        except Exception as e:
            app_logger.error(f"获取文章失败: {e}")
            return None
        finally:
            db.close()

    def delete_articles(self, article_ids: List[int]) -> Tuple[bool, str]:
        """
        批量删除文章

        Args:
            article_ids: 文章ID列表

        Returns:
            (是否成功, 消息)
        """
        try:
            db = get_db()
            deleted = db.query(WechatArticle).filter(WechatArticle.id.in_(article_ids)).delete(synchronize_session=False)
            db.commit()

            app_logger.info(f"删除文章成功，数量: {deleted}")
            return True, f"成功删除 {deleted} 篇文章"

        except Exception as e:
            app_logger.error(f"删除文章失败: {e}")
            db.rollback()
            return False, f"删除失败: {str(e)}"
        finally:
            db.close()

    def mark_as_downloaded(self, article_ids: List[int]) -> bool:
        """
        标记文章为已下载

        Args:
            article_ids: 文章ID列表

        Returns:
            是否成功
        """
        try:
            db = get_db()
            db.query(WechatArticle).filter(WechatArticle.id.in_(article_ids)).update(
                {"is_downloaded": "是"},
                synchronize_session=False
            )
            db.commit()
            return True

        except Exception as e:
            app_logger.error(f"标记文章失败: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def collect_articles_single_page(self, account_id: int) -> Tuple[bool, str, int]:
        """
        采集单页文章

        Args:
            account_id: 公众号ID

        Returns:
            (是否成功, 消息, 采集数量)
        """
        try:
            # 获取会话数据（只加载一次）
            session_data = self.session_manager.load_session()
            if not session_data:
                return False, "请先登录微信公众平台", 0
            
            # 调用内部方法执行采集
            return self._collect_single_page_with_session(account_id, session_data)
            
        except Exception as e:
            collect_logger.error(f"采集文章失败: {e}")
            return False, f"采集失败: {str(e)}", 0

    def _collect_single_page_with_session(self, account_id: int, session_data: dict) -> Tuple[bool, str, int]:
        """
        使用已有会话采集单页文章（内部方法）

        Args:
            account_id: 公众号ID
            session_data: 会话数据

        Returns:
            (是否成功, 消息, 采集数量)
        """
        db = None
        account = None
        
        try:
            db = get_db()
            account = db.query(WechatAccount).filter(WechatAccount.id == account_id).first()

            if not account:
                return False, "公众号不存在", 0

            # 更新采集状态
            account.collect_status = "采集中"
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
                "ajax": "1"
            }

            # 构造请求头和cookies
            cookies = {cookie["name"]: cookie["value"] for cookie in session_data.get("cookies", [])}

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": config.WECHAT_MP_URL,
            }

            # 发送请求
            response = requests.get(url, params=params, cookies=cookies, headers=headers, timeout=30)
            result = response.json()

            if result.get("base_resp", {}).get("ret") != 0:
                account.collect_status = "失败"
                db.commit()
                error_msg = result.get("base_resp", {}).get("err_msg", "未知错误")
                return False, f"采集失败: {error_msg}", 0

            # 解析文章数据
            count = self._parse_and_save_articles(db, account, result)

            # 更新采集状态和起始位置
            account.collect_status = "已采集"
            account.begin += account.count
            db.commit()

            collect_logger.info(f"采集成功: {account.nickname}, 数量: {count}")
            return True, f"采集成功，共 {count} 篇文章", count

        except Exception as e:
            collect_logger.error(f"采集文章失败: {e}")
            if account and db:
                account.collect_status = "失败"
                db.commit()
            return False, f"采集失败: {str(e)}", 0
        finally:
            if db:
                db.close()

    def collect_articles_all(self, account_id: int) -> Tuple[bool, str, int]:
        """
        采集全部文章（循环采集直到没有更多文章）

        Args:
            account_id: 公众号ID

        Returns:
            (是否成功, 消息, 采集总数)
        """
        try:
            # 只加载一次会话，在整个采集过程中复用
            collect_logger.info(f"开始全部采集，公众号ID: {account_id}")
            session_data = self.session_manager.load_session()
            if not session_data:
                return False, "请先登录微信公众平台", 0
            
            collect_logger.info("会话加载成功，开始循环采集")
            
            total_count = 0
            page = 1
            
            while True:
                collect_logger.info(f"采集第 {page} 页...")
                success, msg, count = self._collect_single_page_with_session(account_id, session_data)
                
                if not success:
                    collect_logger.error(f"采集失败: {msg}")
                    return False, msg, total_count

                total_count += count
                collect_logger.info(f"第 {page} 页采集成功，本页: {count} 篇，累计: {total_count} 篇")

                # 如果本次采集数量为0，说明已经采集完毕
                if count == 0:
                    collect_logger.info("没有更多文章，采集完成")
                    break
                
                page += 1

            collect_logger.info(f"全部采集完成，总数: {total_count}")
            return True, f"采集完成，共 {total_count} 篇文章", total_count
            
        except Exception as e:
            collect_logger.error(f"全部采集失败: {e}")
            return False, f"采集失败: {str(e)}", 0

    def _parse_and_save_articles(self, db: Session, account: WechatAccount, result: dict) -> int:
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
                    exists = db.query(WechatArticle).filter(
                        WechatArticle.article_id == aid
                    ).first()

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
                        is_downloaded="否"
                    )

                    db.add(article)
                    count += 1

            db.commit()

        except Exception as e:
            collect_logger.error(f"解析文章数据失败: {e}")
            db.rollback()

        return count

    def get_account_names(self) -> List[str]:
        """
        获取所有公众号名称（用于筛选下拉列表）

        Returns:
            公众号名称列表
        """
        try:
            db = get_db()
            names = db.query(WechatArticle.nickname).distinct().all()
            return [name[0] for name in names if name[0]]
        except Exception as e:
            app_logger.error(f"获取公众号名称失败: {e}")
            return []
        finally:
            db.close()
