"""公众号管理服务"""

from typing import Any

from ..models import WechatAccount, get_db
from ..utils.logger import get_module_logger
from ..utils.validators import validate_required

logger = get_module_logger(__name__)


class WechatService:
    """公众号管理服务"""

    def __init__(self):
        """初始化公众号服务"""
        pass

    def get_all_accounts(self) -> list[dict[str, Any]]:
        """
        获取所有公众号列表

        Returns:
            公众号列表
        """
        try:
            with get_db() as db:
                accounts = db.query(WechatAccount).order_by(WechatAccount.update_time.desc()).all()
                return [account.to_dict() for account in accounts]
        except Exception as e:
            logger.error(f"获取公众号列表失败: {e}")
            return []

    def get_account_by_id(self, account_id: int) -> dict[str, Any] | None:
        """
        根据ID获取公众号

        Args:
            account_id: 公众号ID

        Returns:
            公众号信息，不存在返回None
        """
        try:
            with get_db() as db:
                account = db.query(WechatAccount).filter(WechatAccount.id == account_id).first()
                return account.to_dict() if account else None
        except Exception as e:
            logger.error(f"获取公众号失败: {e}")
            return None

    def create_account(self, account_data: dict[str, Any]) -> tuple[bool, str, int | None]:
        """
        创建公众号

        Args:
            account_data: 公众号数据

        Returns:
            (是否成功, 消息, 公众号ID)
        """
        try:
            # 验证必填字段
            if not validate_required(account_data.get("nickname"), "nickname"):
                return False, "公众号名称不能为空", None

            with get_db() as db:
                # 检查是否已存在
                if account_data.get("fakeid"):
                    exists = (
                        db.query(WechatAccount)
                        .filter(WechatAccount.fakeid == account_data["fakeid"])
                        .first()
                    )
                    if exists:
                        return False, "该公众号已存在", None

                # 创建公众号
                account = WechatAccount(
                    fakeid=account_data.get("fakeid"),
                    nickname=account_data.get("nickname"),
                    alias=account_data.get("alias"),
                    round_head_img=account_data.get("round_head_img"),
                    service_type=account_data.get("service_type"),
                    signature=account_data.get("signature"),
                    verify_status=account_data.get("verify_status"),
                    memo=account_data.get("memo"),
                    begin=account_data.get("begin", 0),
                    count=account_data.get("count", 5),
                    collect_status="未采集",
                )

                db.add(account)
                db.commit()
                db.refresh(account)

                logger.info(f"创建公众号成功: {account.nickname}")
                return True, "创建成功", int(account.id)  # type: ignore

        except Exception as e:
            logger.error(f"创建公众号失败: {e}")
            return False, f"创建失败: {str(e)}", None

    def update_account(self, account_id: int, account_data: dict[str, Any]) -> tuple[bool, str]:
        """
        更新公众号

        Args:
            account_id: 公众号ID
            account_data: 公众号数据

        Returns:
            (是否成功, 消息)
        """
        try:
            with get_db() as db:
                account = db.query(WechatAccount).filter(WechatAccount.id == account_id).first()

                if not account:
                    return False, "公众号不存在"

                # 更新字段
                for key, value in account_data.items():
                    if hasattr(account, key) and key not in ["id", "create_time"]:
                        setattr(account, key, value)

                db.commit()
                logger.info(f"更新公众号成功: {account.nickname}")
                return True, "更新成功"

        except Exception as e:
            logger.error(f"更新公众号失败: {e}")
            return False, f"更新失败: {str(e)}"

    def delete_account(self, account_id: int) -> tuple[bool, str]:
        """
        删除公众号（不删除文章）

        Args:
            account_id: 公众号ID

        Returns:
            (是否成功, 消息)
        """
        try:
            with get_db() as db:
                account = db.query(WechatAccount).filter(WechatAccount.id == account_id).first()

                if not account:
                    return False, "公众号不存在"

                nickname = account.nickname
                db.delete(account)
                db.commit()

                logger.info(f"删除公众号成功: {nickname}")
                return True, "删除成功"

        except Exception as e:
            logger.error(f"删除公众号失败: {e}")
            return False, f"删除失败: {str(e)}"

    def update_collect_status(self, account_id: int, status: str) -> bool:
        """
        更新采集状态

        Args:
            account_id: 公众号ID
            status: 采集状态

        Returns:
            是否成功
        """
        try:
            with get_db() as db:
                account = db.query(WechatAccount).filter(WechatAccount.id == account_id).first()

                if account:
                    account.collect_status = status  # type: ignore[assignment]
                    db.commit()
                    return True
                return False

        except Exception as e:
            logger.error(f"更新采集状态失败: {e}")
            return False

    def update_begin_position(self, account_id: int, begin: int) -> bool:
        """
        更新采集起始位置

        Args:
            account_id: 公众号ID
            begin: 起始位置

        Returns:
            是否成功
        """
        try:
            with get_db() as db:
                account = db.query(WechatAccount).filter(WechatAccount.id == account_id).first()

                if account:
                    account.begin = begin  # type: ignore[assignment]
                    db.commit()
                    return True
                return False

        except Exception as e:
            logger.error(f"更新采集位置失败: {e}")
            return False
