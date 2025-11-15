# API 文档

## 基础信息

- 基础URL: `http://localhost:5000/api`
- 数据格式: JSON
- 字符编码: UTF-8

## 通用响应格式

### 成功响应

```json
{
    "success": true,
    "message": "操作成功",
    "data": {}
}
```

### 错误响应

```json
{
    "success": false,
    "message": "错误信息"
}
```

## 公众号管理 API

### 1. 获取公众号列表

**请求**

```
GET /api/wechat/list
```

**响应**

```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "fakeid": "MjM5ODE2NzYxMg==",
            "nickname": "段永朝读书",
            "alias": "duan-yongchao",
            "round_head_img": "http://example.com/avatar.jpg",
            "service_type": "0",
            "signature": "读书即生活，生活即读书",
            "verify_status": "1",
            "memo": "备注信息",
            "begin": 0,
            "count": 5,
            "collect_status": "已采集",
            "create_time": "2025-01-01 12:00:00",
            "update_time": "2025-01-01 12:00:00"
        }
    ]
}
```

### 2. 获取单个公众号

**请求**

```
GET /api/wechat/{account_id}
```

**参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| account_id | int | 公众号ID |

**响应**

```json
{
    "success": true,
    "data": {
        "id": 1,
        "nickname": "段永朝读书",
        ...
    }
}
```

### 3. 创建公众号

**请求**

```
POST /api/wechat/create
Content-Type: application/json
```

**请求体**

```json
{
    "nickname": "公众号名称",
    "alias": "别名",
    "fakeid": "MjM5ODE2NzYxMg==",
    "round_head_img": "http://example.com/avatar.jpg",
    "signature": "公众号签名",
    "memo": "备注",
    "begin": 0,
    "count": 5
}
```

**字段说明**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| nickname | string | 是 | 公众号名称 |
| alias | string | 否 | 别名 |
| fakeid | string | 否 | 公众号唯一标识 |
| round_head_img | string | 否 | 头像URL |
| signature | string | 否 | 签名 |
| memo | string | 否 | 备注 |
| begin | int | 否 | 起始位置，默认0 |
| count | int | 否 | 采集数量，默认5 |

**响应**

```json
{
    "success": true,
    "message": "创建成功",
    "id": 1
}
```

### 4. 更新公众号

**请求**

```
PUT /api/wechat/{account_id}
Content-Type: application/json
```

**请求体**

```json
{
    "nickname": "新名称",
    "begin": 10,
    "count": 10
}
```

**响应**

```json
{
    "success": true,
    "message": "更新成功"
}
```

### 5. 删除公众号

**请求**

```
DELETE /api/wechat/{account_id}
```

**响应**

```json
{
    "success": true,
    "message": "删除成功"
}
```

### 6. 搜索公众号

**请求**

```
POST /api/wechat/search
Content-Type: application/json
```

**请求体**

```json
{
    "query": "段永朝"
}
```

**响应**

```json
{
    "success": true,
    "data": [
        {
            "fakeid": "MjM5ODE2NzYxMg==",
            "nickname": "段永朝读书",
            "alias": "duan-yongchao",
            "round_head_img": "http://example.com/avatar.jpg",
            "service_type": 0,
            "signature": "读书即生活，生活即读书",
            "verify_status": 1
        }
    ]
}
```

**特殊响应**

如果需要登录：

```json
{
    "success": false,
    "message": "请先登录",
    "needLogin": true
}
```

### 7. 检查登录状态

**请求**

```
GET /api/wechat/login/status
```

**响应**

```json
{
    "success": true,
    "isLoggedIn": true
}
```

### 8. 获取登录二维码

**请求**

```
GET /api/wechat/login/qrcode
```

**响应**

```json
{
    "success": true,
    "qrUrl": "https://mp.weixin.qq.com/qrcode/..."
}
```

### 9. 等待扫码登录

**请求**

```
POST /api/wechat/login/wait
```

**响应**

```json
{
    "success": true,
    "message": "登录成功"
}
```

### 10. 登出

**请求**

```
POST /api/wechat/logout
```

**响应**

```json
{
    "success": true,
    "message": "已登出"
}
```

## 文章管理 API

### 1. 获取文章列表

**请求**

```
GET /api/article/list?page=1&pageSize=20&search=关键词&nickname=公众号名称
```

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码，默认1 |
| pageSize | int | 否 | 每页数量，默认20 |
| search | string | 否 | 搜索关键词（公众号名称或作者） |
| nickname | string | 否 | 公众号名称 |
| isDeleted | string | 否 | 是否删除（是/否） |
| isDownloaded | string | 否 | 是否下载（是/否） |
| startDate | string | 否 | 开始日期（YYYY-MM-DD） |
| endDate | string | 否 | 结束日期（YYYY-MM-DD） |

**响应**

```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "wechat_list_id": 1,
            "nickname": "段永朝读书",
            "article_id": "2257502804_1",
            "article_title": "文章标题",
            "article_cover": "http://example.com/cover.jpg",
            "article_link": "https://mp.weixin.qq.com/s/xxx",
            "article_author_name": "作者名",
            "article_is_deleted": "否",
            "article_create_time": "2025-01-01 12:00:00",
            "article_update_time": "2025-01-01 12:00:00",
            "is_downloaded": "否",
            "create_time": "2025-01-01 12:00:00",
            "update_time": "2025-01-01 12:00:00"
        }
    ],
    "total": 100,
    "page": 1,
    "pageSize": 20
}
```

### 2. 获取单篇文章

**请求**

```
GET /api/article/{article_id}
```

**响应**

```json
{
    "success": true,
    "data": {
        "id": 1,
        "article_title": "文章标题",
        ...
    }
}
```

### 3. 批量删除文章

**请求**

```
POST /api/article/delete
Content-Type: application/json
```

**请求体**

```json
{
    "ids": [1, 2, 3]
}
```

**响应**

```json
{
    "success": true,
    "message": "成功删除 3 篇文章"
}
```

### 4. 采集单页文章

**请求**

```
POST /api/article/collect/single/{account_id}
```

**参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| account_id | int | 公众号ID |

**响应**

```json
{
    "success": true,
    "message": "采集成功，共 5 篇文章",
    "count": 5
}
```

### 5. 采集全部文章

**请求**

```
POST /api/article/collect/all/{account_id}
```

**响应**

```json
{
    "success": true,
    "message": "采集完成，共 100 篇文章",
    "count": 100
}
```

### 6. 批量下载文章

**请求**

```
POST /api/article/download
Content-Type: application/json
```

**请求体**

```json
{
    "ids": [1, 2, 3]
}
```

**响应**

```json
{
    "success": true,
    "message": "下载完成: 成功 3 篇, 失败 0 篇",
    "successCount": 3,
    "failCount": 0,
    "errors": []
}
```

### 7. 获取公众号名称列表

**请求**

```
GET /api/article/names
```

**响应**

```json
{
    "success": true,
    "data": ["段永朝读书", "其他公众号"]
}
```

## 错误码说明

| HTTP状态码 | 说明 |
|-----------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

## 注意事项

1. **登录态**：搜索公众号和采集文章需要先登录微信公众平台
2. **超时**：采集和下载操作可能耗时较长，建议设置较长的超时时间
3. **频率限制**：避免过于频繁地调用采集接口，可能被微信限制
4. **并发**：SQLite 不支持高并发写操作，建议控制并发请求数量

## 示例代码

### Python 示例

```python
import requests

# 获取公众号列表
response = requests.get('http://localhost:5000/api/wechat/list')
data = response.json()
print(data)

# 创建公众号
response = requests.post('http://localhost:5000/api/wechat/create', json={
    'nickname': '测试公众号',
    'begin': 0,
    'count': 5
})
data = response.json()
print(data)

# 采集文章
response = requests.post('http://localhost:5000/api/article/collect/single/1')
data = response.json()
print(data)
```

### JavaScript 示例

```javascript
// 获取公众号列表
fetch('http://localhost:5000/api/wechat/list')
    .then(response => response.json())
    .then(data => console.log(data));

// 创建公众号
fetch('http://localhost:5000/api/wechat/create', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        nickname: '测试公众号',
        begin: 0,
        count: 5
    })
})
    .then(response => response.json())
    .then(data => console.log(data));

// 采集文章
fetch('http://localhost:5000/api/article/collect/single/1', {
    method: 'POST'
})
    .then(response => response.json())
    .then(data => console.log(data));
```

### cURL 示例

```bash
# 获取公众号列表
curl http://localhost:5000/api/wechat/list

# 创建公众号
curl -X POST http://localhost:5000/api/wechat/create \
  -H "Content-Type: application/json" \
  -d '{"nickname":"测试公众号","begin":0,"count":5}'

# 采集文章
curl -X POST http://localhost:5000/api/article/collect/single/1
```
