
import requests
import json
import time
import traceback
import logging
import os
import re
from pathlib import Path
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_not_exception_type
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from markdownify import markdownify as md
from collections import deque

from app.models import WechatList, WechatArticleList
from app.extensions import db
from threading import Thread
from app.config import Config
from app.services.ingestion_manager import run_local_ingestion
from app.services.converters import convert_to_markdown
from app.models import Document, ConversionType

logger = logging.getLogger(__name__)


class ApiAuthError(Exception):
    """表示与微信API认证相关的错误（例如 cookie/session 无效）。"""
    pass

# --- 全局任务状态 ---
# 使用一个字典来跟踪后台任务的状态
# 简单的内存存储，如果服务器重启会丢失状态
collection_tasks = {}
download_tasks = {}


# --- 公众号管理服务 ---

def get_all_wechat_accounts():
    """获取所有公众号列表"""
    accounts = db.session.query(WechatList).order_by(WechatList.update_time.desc()).all()
    # 为每个账户附加任务状态
    for acc in accounts:
        acc.task_status = get_collection_task_status(acc.id)
    return accounts

def get_wechat_account_by_id(account_id):
    """通过ID获取单个公众号"""
    return db.session.query(WechatList).filter(WechatList.id == account_id).first()

def add_wechat_account(data):
    """新增公众号"""
    # 验证必填字段
    if not data.get('wechat_account_name'):
        raise ValueError("公众号名称 (wechat_account_name) 是必填项")

    # 验证日期
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    else:
        start_date = None

    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    else:
        end_date = None

    if start_date and end_date and end_date < start_date:
        raise ValueError("结束日期不能早于开始日期")

    new_account = WechatList(
        wechat_account_name=data['wechat_account_name'],
        memo=data.get('memo'),
        start_date=start_date,
        end_date=end_date,
        fakeid=data.get('fakeid'),
        token=data.get('token'),
        cookie=data.get('cookie'),
        begin=data.get('begin', 0),
        count=data.get('count', 5)
    )
    db.session.add(new_account)
    db.session.commit()
    return new_account

def update_wechat_account(account_id, data):
    """更新公众号信息"""
    account = get_wechat_account_by_id(account_id)
    if not account:
        return None
    
    # 更新字段
    account.wechat_account_name = data.get('wechat_account_name', account.wechat_account_name)
    account.memo = data.get('memo', account.memo)
    account.fakeid = data.get('fakeid', account.fakeid)
    account.token = data.get('token', account.token)
    account.cookie = data.get('cookie', account.cookie)
    account.begin = data.get('begin', account.begin)
    account.count = data.get('count', account.count)

    # 日期处理
    start_date_str = data.get('start_date')
    if start_date_str:
        account.start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()

    end_date_str = data.get('end_date')
    if end_date_str:
        account.end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    if account.start_date and account.end_date and account.end_date < account.start_date:
        raise ValueError("结束日期不能早于开始日期")

    db.session.commit()
    return account

def delete_wechat_account(account_id):
    """删除公众号及其文章"""
    account = get_wechat_account_by_id(account_id)
    if not account:
        return False
    
    # 删除关联的文章
    db.session.query(WechatArticleList).filter(WechatArticleList.wechat_list_id == account_id).delete()
    
    # 删除公众号
    db.session.delete(account)
    db.session.commit()
    return True

# --- 文章采集服务 ---

def parse_cookie_string(cookie_string):
    """将Cookie字符串解析为字典"""
    if not cookie_string:
        return {}
    return {item.split('=')[0].strip(): item.split('=')[1].strip() for item in cookie_string.split(';') if '=' in item}

def timestamp_to_datetime(timestamp):
    """将时间戳转换为datetime对象"""
    if timestamp:
        return datetime.fromtimestamp(timestamp)
    return None

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry=retry_if_not_exception_type(ApiAuthError), reraise=True)
def get_wechat_articles_from_api(wechat_account):
    """ 从微信API获取公众号历史文章列表 """
    cookies = parse_cookie_string(wechat_account.cookie)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    }

    params = {
        'sub': 'list',
        'search_field': 'null',
        'begin': str(wechat_account.begin),
        'count': str(wechat_account.count),
        'query': '',
        'fakeid': wechat_account.fakeid,
        'type': '101_1',
        'free_publish_type': '1',
        'sub_action': 'list_ex',
        'token': wechat_account.token,
        'lang': 'zh_CN',
        'f': 'json',
        'ajax': '1',
    }

    url = 'https://mp.weixin.qq.com/cgi-bin/appmsgpublish'

    try:
        response = requests.get(url, params=params, cookies=cookies, headers=headers, timeout=15)
        response.raise_for_status()

        # 打印响应片段以便调试（仅前1000字符，避免打印敏感信息）
        resp_snippet = response.text[:1000]
        logger.debug("wechat api response snippet:\n%s", resp_snippet)

        api_response = response.json()
        # 统一处理 base_resp.ret 非 0 的情况，便于上层捕获并给出提示
        ret = api_response.get("base_resp", {}).get("ret")
        err_msg = api_response.get("base_resp", {}).get("err_msg")
        if ret is not None and ret != 0:
            msg = f"微信API返回错误 ret={ret}, err_msg={err_msg}。请检查Cookie/Token是否过期或被封。响应片段: {resp_snippet}"
            # 识别常见的认证相关错误，抛出专用异常以便上层处理
            if ret in (-3, 200003) or (isinstance(err_msg, str) and ('invalid session' in err_msg.lower() or 'cookie' in err_msg.lower() or 'session' in err_msg.lower())):
                raise ApiAuthError(msg)
            raise Exception(msg)

        return api_response

    except json.JSONDecodeError:
        # 响应无法解析为JSON，抛出并带出片段
        raise Exception(f"请求成功但无法解析返回内容，内容: {response.text[:500]}")
    except requests.exceptions.RequestException as e:
        logger.error("请求微信API时发生网络错误: %s", e)
        raise


def parse_and_save_articles(api_response, wechat_account):
    """ 解析API响应并保存文章

    返回值: (saved_count, total_articles_in_response)
    保证在任何分支下都返回一个二元组，便于调用方解包。
    """
    if 'publish_page' not in api_response:
        # 当接口返回 base_resp.ret == 0 时，有时表示没有更多数据，返回 (0,0)
        if api_response.get("base_resp", {}).get("ret") == 0:
            return 0, 0
        else:
            # 为便于排查，附带部分响应内容
            snippet = json.dumps(api_response, ensure_ascii=False)[:1000]
            raise ValueError(f"API响应格式不正确，缺少 'publish_page' 键。响应片段: {snippet}")

    try:
        publish_page_content = api_response['publish_page']
        # publish_page 有时已经是 dict，有时是 JSON 字符串
        if isinstance(publish_page_content, str):
            publish_page = json.loads(publish_page_content)
        elif isinstance(publish_page_content, dict):
            publish_page = publish_page_content
        else:
            raise TypeError('未知的 publish_page 数据类型')

        publish_list = publish_page.get('publish_list', [])
    except (json.JSONDecodeError, TypeError) as e:
        raise ValueError(f"解析 'publish_page' 内容失败: {e}")

    saved_count = 0
    total_articles_in_response = 0
    for item in publish_list:
        try:
            publish_info = json.loads(item['publish_info'])
            appmsgex_list = publish_info.get('appmsgex', [])
            total_articles_in_response += len(appmsgex_list)
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            logger.error(f"解析 publish_info 失败: {e}. problematic string: {item.get('publish_info')}")
            continue

        for article_data in appmsgex_list:
            existing_article = db.session.query(WechatArticleList).filter_by(
                wechat_list_id=wechat_account.id,
                article_id=article_data.get('aid')
            ).first()

            if existing_article:
                continue

            article = WechatArticleList(
                wechat_list_id=wechat_account.id,
                wechat_account_name=wechat_account.wechat_account_name,
                article_id=article_data.get('aid'),
                article_title=article_data.get('title'),
                article_cover=article_data.get('cover'),
                article_link=article_data.get('link'),
                article_author_name=article_data.get('author_name'),
                article_is_deleted='false',
                article_create_time=timestamp_to_datetime(article_data.get('update_time')),
                article_update_time=timestamp_to_datetime(article_data.get('update_time'))
            )
            db.session.add(article)
            saved_count += 1
    
    if saved_count > 0 or total_articles_in_response > 0:
        account = get_wechat_account_by_id(wechat_account.id)
        account.begin += account.count
        db.session.add(account)

    db.session.commit()
    return saved_count, total_articles_in_response


def collect_articles_for_account(account_id):
    """为指定公众号采集单页文章"""
    account = get_wechat_account_by_id(account_id)
    if not account:
        raise ValueError(f"ID为 {account_id} 的公众号不存在")

    api_response = get_wechat_articles_from_api(account)
    saved_count, _ = parse_and_save_articles(api_response, account)
    return saved_count

# --- 后台全量采集任务 ---

def _collect_all_articles_worker(account_id, app_context):
    """在后台线程中循环采集所有文章的执行函数"""
    with app_context:
        try:
            total_saved = 0
            while True:
                account = get_wechat_account_by_id(account_id)
                if not account:
                    logger.info("[任务 %s] 公众号不存在，任务终止。", account_id)
                    break
                
                logger.info("[任务 %s] 正在采集 '%s'，起始位置: %s...", account_id, account.wechat_account_name, account.begin)
                
                api_response = get_wechat_articles_from_api(account)
                saved_count, total_in_response = parse_and_save_articles(api_response, account)
                
                total_saved += saved_count
                logger.info("[任务 %s] 本次采集到 %s 篇新文章。", account_id, saved_count)

                # 如果API返回的文章数少于请求数，或返回列表为空，说明到达末尾
                if total_in_response < account.count:
                    logger.info("[任务 %s] 已到达文章列表末尾，采集完成。", account_id)
                    break
                
                # 礼貌性等待，避免请求过于频繁
                time.sleep(2)
            
            collection_tasks[account_id] = {'status': 'finished', 'message': f'采集完成，共新增 {total_saved} 篇文章。'}

        except ApiAuthError as e:
            # 认证失败时给出专门状态，便于前端提示更新cookie/token
            traceback.print_exc()
            collection_tasks[account_id] = {'status': 'auth_failed', 'message': f'认证失败: {str(e)}'}
        except Exception as e:
            traceback.print_exc()
            collection_tasks[account_id] = {'status': 'error', 'message': f'采集失败: {str(e)}'}
        finally:
            # 确保数据库会话被正确关闭
            db.session.remove()


def start_full_collection_task(account_id, app):
    """启动一个后台线程来执行全量采集"""
    if collection_tasks.get(account_id, {}).get('status') == 'running':
        raise ValueError("该公众号的全量采集任务正在进行中，请勿重复启动。")

    collection_tasks[account_id] = {'status': 'running', 'message': '后台采集中...'}
    
    # 创建并启动后台线程
    thread = Thread(target=_collect_all_articles_worker, args=(account_id, app.app_context()))
    thread.daemon = True
    thread.start()

def get_collection_task_status(account_id):
    """获取指定公众号的采集任务状态"""
    return collection_tasks.get(account_id)

# --- 文章展示服务 ---

def get_paginated_articles(page=1, per_page=20, search=None, account_id=None, start_date=None, end_date=None, is_downloaded=None):
    """获取分页和筛选后的文章列表"""
    query = db.session.query(WechatArticleList)

    # 搜索
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (WechatArticleList.article_title.like(search_term)) |
            (WechatArticleList.wechat_account_name.like(search_term))
        )

    # 筛选
    if account_id:
        query = query.filter(WechatArticleList.wechat_list_id == account_id)
    if start_date:
        query = query.filter(WechatArticleList.article_create_time >= start_date)
    if end_date:
        query = query.filter(WechatArticleList.article_create_time <= end_date)
    if is_downloaded in ['是', '否']:
        query = query.filter(WechatArticleList.is_downloaded == is_downloaded)

    # 排序
    query = query.order_by(WechatArticleList.article_create_time.desc())

    # 分页
    total = query.count()
    articles = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return articles, total

# --- 文章下载服务 ---

def _sanitize_filename(filename):
    """清理文件名，移除不合法字符"""
    return re.sub(r'[\\/*?:\"<>|]', "", filename).strip()

def _download_and_replace_image(img_url, img_index, article, download_dir, assets_dir):
    """下载单张图片并返回其相对路径"""
    if not img_url or img_url.startswith('data:'):
        return None
    try:
        full_img_url = urljoin(article.article_link, img_url)  # 处理相对路径

        img_response = requests.get(full_img_url, stream=True, timeout=15)
        img_response.raise_for_status()

        content_type = img_response.headers.get('Content-Type', '')
        if 'jpeg' in content_type or 'jpg' in content_type:
            ext = '.jpg'
        elif 'png' in content_type:
            ext = '.png'
        elif 'gif' in content_type:
            ext = '.gif'
        elif 'webp' in content_type:
            ext = '.webp'
        else:
            ext = Path(full_img_url).suffix or '.jpg'

        # 清理扩展名中的参数
        ext = ext.split('?')[0]

        img_filename = f"image_{img_index}{ext}"
        img_path = assets_dir / img_filename

        with open(img_path, 'wb') as f:
            for chunk in img_response.iter_content(1024):
                f.write(chunk)

        relative_img_path = img_path.relative_to(download_dir)
        return relative_img_path.as_posix()

    except requests.exceptions.RequestException as e:
        logger.warning(f"下载图片失败: {full_img_url}, 错误: {e}")
        return None

def _download_article_content(article, download_dir):
    """下载单个文章的HTML和图片"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
        }
        response = requests.get(article.article_link, headers=headers, timeout=20)
        response.raise_for_status()

        # 使用 response.content 让 BeautifulSoup 自行处理编码
        soup = BeautifulSoup(response.content, 'lxml')

        # --- 确保HTML头中有正确的编码声明 ---
        head = soup.find('head')
        if head:
            # 移除旧的charset，避免冲突
            for meta_tag in head.find_all('meta', attrs={'charset': True}):
                meta_tag.decompose()
            # 插入新的UTF-8 meta标签
            meta_charset_tag = soup.new_tag('meta', charset='UTF-8')
            head.insert(0, meta_charset_tag)
        else:
            logger.warning(f"文章 '{article.article_title}' 缺少 <head> 标签，无法插入charset声明。")

        # --- 强制显示文章内容 ---
        content_div = soup.find('div', id='js_content')
        if content_div and content_div.has_attr('style'):
            del content_div['style']
            logger.info(f"强制显示文章 '{article.article_title}' 的内容。")

        # 创建文章和图片文件夹
        base_filename = _sanitize_filename(article.article_title)
        article_path = download_dir / f"{base_filename}.html"
        assets_dir = download_dir / f"{base_filename}.assets"
        assets_dir.mkdir(exist_ok=True)

        # 下载并替换CSS
        for link in soup.find_all('link', rel='stylesheet'):
            css_url = link.get('href')
            if not css_url:
                continue
            
            css_url = urljoin(article.article_link, css_url)
            try:
                css_response = requests.get(css_url, timeout=15)
                if css_response.status_code == 200:
                    css_filename = Path(css_url).name or "style.css"
                    # 防止文件名过长或重复
                    css_filename = f"{Path(css_filename).stem}_{len(os.listdir(assets_dir))}{Path(css_filename).suffix}"
                    css_path = assets_dir / css_filename
                    
                    with open(css_path, 'w', encoding='utf-8') as f:
                        f.write(css_response.text)
                    
                    relative_css_path = css_path.relative_to(download_dir)
                    link['href'] = relative_css_path.as_posix()
                else:
                    logger.warning(f"下载CSS失败: {css_url} (状态码: {css_response.status_code})")
            except requests.exceptions.RequestException as e:
                logger.warning(f"下载CSS失败: {css_url}, 错误: {e}")

        # 下载并替换图片
        img_tags = soup.find_all('img')
        for i, img in enumerate(img_tags):
            # 优先处理 data-src，其次是 src
            img_url = img.get('data-src') or img.get('src')
            srcset = img.get('srcset')

            if not img_url and not srcset:
                continue

            # 处理主图片 (src/data-src)
            if img_url:
                local_img_path = _download_and_replace_image(img_url, i, article, download_dir, assets_dir)
                if local_img_path:
                    img['src'] = local_img_path
                    # 确保 data-src 也被更新或移除
                    if img.has_attr('data-src'):
                        img['data-src'] = local_img_path
            
            # 处理 srcset
            if srcset:
                new_srcset = []
                for part in srcset.split(','):
                    part = part.strip()
                    if not part:
                        continue
                    
                    url_part = part.split()[0]
                    descriptor = part.split()[1] if len(part.split()) > 1 else ''
                    
                    local_path = _download_and_replace_image(url_part, f"{i}_{descriptor.replace(' ','')}", article, download_dir, assets_dir)
                    if local_path:
                        new_srcset.append(f"{local_path} {descriptor}")
                
                if new_srcset:
                    img['srcset'] = ', '.join(new_srcset)

        # 移除所有外部脚本，保留内联脚本（通常包含页面数据）
        for script in soup.find_all('script'):
            if not script.has_attr('src'):
                continue
            script.decompose()

        # 保存修改后的HTML
        with open(article_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))

        # 保存元数据文件
        meta_path = download_dir / f"{base_filename}.html.meta.json"
        meta_data = {'source_url': article.article_link}
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta_data, f, ensure_ascii=False, indent=4)
        
        logger.info(f"成功下载文章: {article.article_title}")
        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"下载文章页面失败: {article.article_link}, 错误: {e}")
    except Exception as e:
        logger.error(f"处理文章 '{article.article_title}' 时发生未知错误: {e}")
        traceback.print_exc()
    
    return False


def _download_articles_worker(task_id, article_ids, app_context):
    """在后台线程中下载所有选定文章的执行函数"""
    with app_context:
        download_tasks[task_id].update({'status': 'running', 'progress': 0, 'total': len(article_ids), 'message': '下载任务已开始...'})
        
        base_download_dir = Path(Config.DOWNLOAD_PATH)
        base_download_dir.mkdir(exist_ok=True)
        
        completed_count = 0
        processed_dirs = set()

        def _convert_and_upsert_document(html_path: Path, account_name: str, source_url: str):
            """直接对刚下载的 HTML 文件执行转换并写入 / 更新 Document 表，避免二次扫描。

            - 如果文件已存在且修改时间未变：跳过（但若之前失败可重试）。
            - 若转换失败：写入/更新为 failed 状态，保留 error_message。
            - 成功：写入 markdown_content, conversion_type=HTML_TO_MD。
            """
            try:
                # 获取文件元数据
                from app.utils.file_utils import get_file_metadata
                meta = get_file_metadata(str(html_path))
                if not meta:
                    logger.warning(f"[WeChatDirectIngest] 无法获取文件元数据: {html_path}")
                    return

                existing = Document.query.filter(Document.file_path.ilike(meta['file_path'])).first()
                # 若存在且mtime一致且status=completed，直接跳过
                if existing and existing.file_modified_time == meta['file_modified_time'] and existing.status == 'completed':
                    logger.debug(f"[WeChatDirectIngest] 跳过未变文件: {html_path}")
                    return

                result = convert_to_markdown(meta['file_path'], meta['file_type'])
                if not result.success:
                    if existing:
                        existing.status = 'failed'
                        existing.error_message = result.error
                        existing.source = f"公众号_{account_name}"
                        existing.source_url = source_url
                    else:
                        db.session.add(Document(
                            file_name=meta['file_name'], file_type=meta['file_type'], file_size=meta['file_size'],
                            file_created_at=meta['file_created_at'], file_modified_time=meta['file_modified_time'],
                            file_path=meta['file_path'], status='failed', error_message=result.error,
                            source=f"公众号_{account_name}", source_url=source_url
                        ))
                    logger.error(f"[WeChatDirectIngest] 转换失败: {html_path} -> {result.error}")
                else:
                    if existing:
                        existing.file_size = meta['file_size']
                        existing.file_modified_time = meta['file_modified_time']
                        existing.markdown_content = result.content
                        existing.conversion_type = result.conversion_type
                        existing.status = 'completed'
                        existing.error_message = None
                        existing.source = f"公众号_{account_name}"
                        existing.source_url = source_url
                    else:
                        db.session.add(Document(
                            file_name=meta['file_name'], file_type=meta['file_type'], file_size=meta['file_size'],
                            file_created_at=meta['file_created_at'], file_modified_time=meta['file_modified_time'],
                            file_path=meta['file_path'], markdown_content=result.content,
                            conversion_type=result.conversion_type, status='completed',
                            source=f"公众号_{account_name}", source_url=source_url
                        ))
                    logger.info(f"[WeChatDirectIngest] 转换成功: {html_path}")
                db.session.commit()
            except Exception as e:
                logger.error(f"[WeChatDirectIngest] 处理 {html_path} 发生异常: {e}", exc_info=True)
                db.session.rollback()

        for i, article_id in enumerate(article_ids):
            try:
                article = db.session.query(WechatArticleList).get(article_id)
                if not article:
                    logger.warning(f"未找到ID为 {article_id} 的文章，跳过。")
                    continue

                # 1. 获取并清理公众号名称
                account_name = _sanitize_filename(article.wechat_account_name or '未分类')
                
                # 2. 创建公众号专属文件夹
                article_download_dir = base_download_dir / account_name
                article_download_dir.mkdir(exist_ok=True)
                processed_dirs.add(str(article_download_dir))

                if _download_article_content(article, article_download_dir):
                    completed_count += 1
                    # 更新下载状态
                    article.is_downloaded = '是'
                    db.session.commit()
                    # 直接转换刚下载的HTML
                    base_filename = _sanitize_filename(article.article_title)
                    html_path = article_download_dir / f"{base_filename}.html"
                    if html_path.exists():
                        _convert_and_upsert_document(html_path, account_name, article.article_link)
                    else:
                        logger.warning(f"[WeChatDirectIngest] 期望的HTML文件不存在: {html_path}")

            except Exception as e:
                logger.error(f"下载文章ID {article_id} 时发生严重错误: {e}")
                db.session.rollback()
            finally:
                # 更新进度
                download_tasks[task_id]['progress'] = i + 1
        
        download_tasks[task_id]['status'] = 'finished'
        download_tasks[task_id]['message'] = f"下载完成！成功 {completed_count} 篇，失败 {len(article_ids) - completed_count} 篇。开始后台入库处理..."
        logger.info(f"下载任务 {task_id} 完成。")

        # 不再触发目录级二次扫描导入，已在下载时直接转换
        
        db.session.remove()


def start_download_task(article_ids, app):
    """启动一个后台线程来执行下载任务"""
    task_id = str(time.time())
    download_tasks[task_id] = {'status': 'starting', 'message': '任务准备中...'}
    
    thread = Thread(target=_download_articles_worker, args=(task_id, article_ids, app.app_context()))
    thread.daemon = True
    thread.start()
    return task_id

def get_all_download_tasks_status():
    """获取所有下载任务的状态"""
    return download_tasks
