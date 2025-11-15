# 性能优化记录

## 会话加载优化

### 问题描述

在采集文章时，日志显示频繁加载会话：

```
2025-11-15 17:28:49 - app - INFO - 会话数据加载成功
2025-11-15 17:28:50 - collect - INFO - 采集成功: 段永朝读书, 数量: 5
2025-11-15 17:28:50 - app - INFO - 会话数据加载成功
2025-11-15 17:28:52 - collect - INFO - 采集成功: 段永朝读书, 数量: 8
...
```

每次采集都会加载会话文件，造成不必要的IO操作。

### 优化方案

#### 方案一：会话缓存机制 ✅

在 `SessionManager` 中添加缓存：

**优点**：
- 自动缓存，透明使用
- 支持过期时间（默认5分钟）
- 支持手动清除缓存

**实现**：
```python
class SessionManager:
    def __init__(self):
        self._cached_session = None
        self._cache_time = 0
        self._cache_ttl = 300  # 5分钟
    
    def load_session(self, force_reload=False):
        # 检查缓存
        if not force_reload and self._cached_session:
            if time.time() - self._cache_time < self._cache_ttl:
                return self._cached_session
        
        # 加载并缓存
        session = self._load_from_file()
        self._cached_session = session
        self._cache_time = time.time()
        return session
```

#### 方案二：采集时复用会话 ✅（推荐）

在采集开始时加载一次，循环采集时复用：

**优点**：
- 更清晰的逻辑
- 减少不必要的IO
- 更容易调试

**实现**：
```python
def collect_articles_all(self, account_id: int):
    # 只加载一次
    session_data = self.session_manager.load_session()
    
    while True:
        # 传递会话给内部方法，不再重复加载
        success, msg, count = self._collect_single_page_with_session(
            account_id, 
            session_data
        )
        ...
```

### 最终实现

采用**方案二**作为主要优化，同时保留**方案一**作为额外优化：

1. **采集逻辑优化**：
   - `collect_articles_single_page()` - 对外接口，加载会话后调用内部方法
   - `_collect_single_page_with_session()` - 内部方法，接收会话参数
   - `collect_articles_all()` - 加载一次会话，循环调用内部方法

2. **会话管理优化**：
   - 添加缓存机制（5分钟TTL）
   - 保存/清除时自动更新缓存
   - 支持 `force_reload` 参数强制重新加载

### 优化效果

**优化前**：
- 采集10页 = 加载会话10次
- 日志充满 "会话数据加载成功"

**优化后**：
- 采集10页 = 加载会话1次
- 日志清晰，只在真正加载时输出

### 相关文件

- `src/wechat_article_assistant/browser/session_manager.py`
  - 添加缓存机制
  - `load_session()` 支持缓存
  - `save_session()` 更新缓存
  - `clear_session()` 清除缓存
  - `invalidate_cache()` 使缓存失效

- `src/wechat_article_assistant/services/article_service.py`
  - `collect_articles_single_page()` - 重构为加载会话后调用内部方法
  - `_collect_single_page_with_session()` - 新增内部方法
  - `collect_articles_all()` - 优化为只加载一次会话

### 使用建议

1. **正常使用**：无需改变，自动享受优化
2. **强制刷新**：`session_manager.load_session(force_reload=True)`
3. **清除缓存**：`session_manager.invalidate_cache()`

### 其他优化建议

#### 1. 数据库连接池

当前每次操作都创建新连接，可以使用连接池：

```python
engine = create_engine(
    database_url,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10
)
```

#### 2. 批量插入优化

当前使用 `db.add()` 逐条插入，可以改为批量：

```python
db.bulk_insert_mappings(WechatArticle, articles_data)
```

#### 3. 异步采集

使用异步任务队列（如Celery）处理采集：

```python
@celery_app.task
def collect_articles_async(account_id):
    ...
```

#### 4. 前端轮询优化

使用WebSocket代替轮询获取采集进度：

```javascript
const ws = new WebSocket('ws://localhost:5000/ws');
ws.onmessage = (event) => {
    updateProgress(JSON.parse(event.data));
};
```

## 更新日志

**2025-11-15**
- 实现会话缓存机制
- 优化采集时的会话加载
- 添加详细日志

---

性能优化是持续的过程，欢迎提出更多优化建议！
