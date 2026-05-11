# 微信公众号文章阅读助手 - 产品需求文档 (PRD)



## 1. 执行概要

这个项目是一个Web应用 ，旨在为用户提供一个集中管理、采集和下载微信公众号历史文章的工具。用户可以通过本应用添加公众号，自动或手动采集其历史文章列表，并能方便地筛选和批量下载这些文章。此外，还提供命令行工具用于快速下载指定链接的文章。





## 2 功能需求

### 2.1 公众号管理模块

#### 2.1.1 公众号列表展示

**功能描述**：以表格形式展示已添加的公众号列表，支持编辑和删除公众号

**显示字段**：

- 公众号名称
- 别名
- 头像
- 签名
- 采集进度（单页起始位置）
- 采集状态

**显示规则**：

- 按更新时间降序排列显示



#### 2.1.2 新增公众号

**功能描述**：通过弹出页面录入公众号信息

**触发方式**：点击"新增公众号"按钮

**方式一：手工录入**

- 提供表单输入以下字段：
  - 公众号名称 (必填)
  - 别名
  - 圆形头像URL
  - 签名
  - 备注
  - 公众号 fakeid
  - 起始位置 (默认: 0)
  - 采集数量 (默认: 5)
- 验证规则：必填项不能为空
- 表单操作：
  - 保存按钮：提交表单数据
  - 取消按钮：关闭弹出页面

**方式二：自动获取公众号信息**

- 输入公众号名称关键词
- 点击"搜索"按钮
- 登录态处理：
  - 检测本地是否有效登录会话
  - 检测到登录态失效时，弹出模态框显示微信公众平台 (https://mp.weixin.qq.com/)登录二维码
  - 用户扫码后，保存浏览器登录会话数据，并提取Token 和 Cookie等信息，构造微信公众平台账号搜索接口请求(https://mp.weixin.qq.com/cgi-bin/searchbiz)
  - 执行搜索请求
- 显示搜索结果列表，用户选择目标公众号
- 自动填充公众号信息到表单
- 用户确认后保存



#### 2.1.3 编辑公众号

**功能描述**：支持对已录入的公众号信息进行编辑

**操作流程**：

1. 点击列表中的"编辑"按钮
2. 弹出表单，预填充现有数据
3. 修改后点击"保存"按钮更新
4. 点击"取消"按钮关闭弹出页面



#### 2.1.4 删除公众号

**功能描述**：支持删除不需要的公众号记录

**操作流程**：

1. 点击列表中的"删除"按钮
2. 弹出确认对话框
3. 确认后删除公众号记录（不删除公众号文章记录）



### 2.2 文章采集模块

#### 2.2.1 触发采集

- 在公众号列表中，每行显示"单页采集"、"全部采集"按钮
  - 点击"单页采集"，根据公众号配置的 `begin` 和 `count` 参数采集一页文章
  - 点击"全部采集"，循环采集所有历史文章，直到没有更多文章



#### 2.2.2 采集过程

- 点击"单页采集"或"全部采集"
- 登录态处理:
  - 检测本地是否有效登录会话
  - 检测到登录态失效时，弹出模态框显示微信公众平台 (https://mp.weixin.qq.com/)登录二维码
  - 用户扫码后，保存浏览器登录会话数据，并提取 Token 等信息，构造微信公众平台文章列表接口请求(https://mp.weixin.qq.com/cgi-bin/appmsgpublish)
  - 执行采集请求
  
- 解析返回的文章数据，提取以下字段：
  - 文章 ID (aid)
  - 文章标题 (title)
  - 文章封面 (cover)
  - 文章链接 (link)
  - 文章作者 (author_name)
  - 文章是否删除 (is_deleted)
  - 文章创建时间(create_time)
  - 文章更新时间 (update_time)
- 将公众号名称和文章数据保存到 `wechat_article_list` 表
- 更新公众号的 `collect_status` 为"已采集"或"采集中"



#### 2.2.3 采集状态

- 采集状态字段值：
  - `未采集`: 初始状态
  - `采集中`: 正在执行采集任务
  - `已采集`: 采集完成
  - `失败`: 采集过程出错
- 在公众号列表中显示当前采集状态



#### 2.2.4 采集日志

- 记录采集操作的日志信息：
  - 时间戳
  - 公众号名称
  - 操作类型 (单页采集/全部采集)
  - 采集数量
  - 状态 (成功/失败)
  - 错误信息 (如有)
- 日志保存到文件: `logs/collect.log`



### 2.3 文章管理与下载模块

#### 2.3.1 文章列表展示

**功能描述**：以表格形式展示采集到的文章信息

**显示字段**：

- 复选框 (用于选择)
- 公众号名称
- 文章标题（点击打开文章链接的页面）
- 文章作者
- 发布时间 ( 文章创建时间 )
- 文章是否删除
- 是否下载



#### 2.3.2 搜索功能

**功能描述**：支持按关键词搜索文章

**搜索范围**：

- 公众号名称
- 文章作者

**搜索方式**：

- 实时搜索或按钮触发搜索
- 支持模糊匹配



#### 2.3.3 筛选功能

**功能描述**：支持按条件筛选文章列表，点击“查询”按钮触发

**筛选条件**：

- 公众号名称（下拉选择）
- 发布时间范围（日期选择器）
- 文章是否删除（下拉选择）
- 是否下载（下拉选择）



#### 2.3.4 分页功能

**功能描述**：当文章数量较多时，支持分页展示

**分页参数**：

- 每页显示数量：20条（可配置）
- 显示页码导航



#### 2.3.5 文章选择

- 提供"全选"复选框，可一键选中/取消所有文章
- 单击单个复选框选择/取消单篇文章
- 显示已选择的文章数量



#### 2.3.6 批量删除文章

- **触发方式**: 点击"删除选中文章"按钮



#### 2.3.7 批量下载文章

**触发方式**: 点击"下载选中文章"按钮

**下载流程**:

1. 检查是否选择了文章，未选择则提示用户
2. 对每篇选中的文章执行以下操作：
   - 检查下载路径是否存在以"公众号名称"命名的文件夹
   - 不存在则创建文件夹: `{公众号名称}`
   - 访问文章链接，获取 HTML 内容
   - 解析 HTML，提取所有图片 URL
   - 下载所有图片到文件夹: `{公众号名称}/images/`
   - 替换 HTML 中的图片链接为本地相对路径
   - 保存 HTML 文件: `公众号名称}/{文章标题}.html`
3. 所有文章下载完成后，显示成功提示
4. 记录下载日志到 `logs/download.log`

**文件命名规则**:

- HTML 文件: `{文章标题}.html`
- 图片文件: 保持原始文件名或使用 `img_{序号}.{扩展名}`
- 特殊字符处理: 替换文件名中的 `/\:*?"<>|` 为 `_`



### 2.4 命令行工具

命令行工具下载链接，不涉及认证。



#### 2.4.1 命令行下载单个链接

```bash
python -m wechat_article_assistant download <article_url>
```

- 参数: `article_url` - 微信文章链接
- 功能: 下载指定链接的文章及图片
- 保存位置: `data/downloads/`



#### 2.4.2 命令行批量下载

```bash
python -m wechat_article_assistant download --file <file_path>
```

- 参数: `file_path` - 包含文章链接的 txt 文件路径
- 文件格式: 每行一个文章链接
- 功能: 批量下载文件中所有链接的文章
- 保存位置: `data/downloads/`



#### 2.4.3 命令行选项

- `--output, -o`: 指定输出目录 (默认: `data/downloads/`)
- `--verbose, -v`: 显示详细日志
- `--help, -h`: 显示帮助信息





## 3. 技术架构

### 3.1 技术栈

| 类别                 | 技术          | 说明                               |
| :------------------- | :------------ | :--------------------------------- |
| 前端样式             | Tailwind CSS  | 通过 CDN 加载，无需本地构建        |
| 后端框架             | Flask         | Python 3.12+                       |
| 数据库               | SQLite        | 用于本地轻量级存储                 |
| ORM                  | SQLAlchemy    | 用于数据库交互                     |
| 配置管理             | python-dotenv | 管理 `.env` 文件中的敏感信息       |
| 依赖管理             | uv            | 用于快速的依赖安装和管理           |
| 代码质量             | Ruff          | 格式化和 Linting                   |
| 类型检查             | mypy          | 静态类型检查                       |
| 测试框架             | pytest        | 用于单元测试和集成测试             |
| 浏览器自动化使用的库 | Playwright    | 用于模拟登录微信公众平台、保持会话 |





## 4. 数据模型

### 4.1 公众号列表表 (wechat_list)

| 字段中文名称      | 字段英文名称   | 字段类型     | 字段是否为空说明 |
| ----------------- | -------------- | ------------ | ---------------- |
| 序号              | id             | int          | NOT NULL         |
| 公众号唯一标识    | fakeid         | varchar(100) | NULL             |
| 公众号名称        | nickname       | varchar(50)  | NULL             |
| 公众号别名        | alias          | varchar(50)  | NULL             |
| 公众号圆形头像URL | round_head_img | varchar(200) | NULL             |
| 公众号类型        | service_type   | varchar(10)  | NULL             |
| 公众号签名        | signature      | varchar(200) | NULL             |
| 公众号认证状态    | verify_status  | varchar(10)  | NULL             |
| 备注              | memo           | varchar(200) | NULL             |
| 单页起始位置      | begin          | int          | NULL             |
| 单页采集数量      | count          | int          | NULL             |
| 采集状态          | collect_status | varchar(50)  | NULL             |
| 创建时间          | create_time    | timestamp    | NULL             |
| 更新时间          | update_time    | timestamp    | NULL             |



### 4.2 公众号文章列表表 (wechat_article_list)

| 字段中文名称 | 字段英文名称        | 字段类型     | 字段是否可以为空 |
| ------------ | ------------------- | ------------ | ---------------- |
| 序号         | id                  | int          | NOT NULL         |
| 公众号列表ID | wechat_list_id      | int          | NULL             |
| 公众号名称   | nickname            | varchar(50)  | NULL             |
| 文章ID       | article_id          | varchar(50)  | NULL             |
| 文章标题     | article_title       | varchar(100) | NULL             |
| 文章封面     | article_cover       | varchar(200) | NULL             |
| 文章链接     | article_link        | varchar(200) | NULL             |
| 文章作者     | article_author_name | varchar(20)  | NULL             |
| 文章是否删除 | article_is_deleted  | varchar(10)  | NULL             |
| 文章创建时间 | article_create_time | timestamp    | NULL             |
| 文章更新时间 | article_update_time | timestamp    | NULL             |
| 是否下载     | is_downloaded       | varchar(10)  | NULL             |
| 创建时间     | create_time         | timestamp    | NULL             |
| 更新时间     | update_time         | timestamp    | NULL             |

**表关系说明**:

- `wechat_list.id` = `wechat_article_list.wechat_list_id`



## 5. 项目结构

```
wechat-article-assistant/
├── src/
│   └── wechat_article_assistant/
│       ├── __init__.py                 # 包初始化
│       ├── app.py                      # Flask 应用入口
│       ├── config.py                   # 配置管理
│       ├── models.py                   # 数据模型
│       ├── cli.py                      # 命令行工具
│       │
│       ├── routes/                     # 路由层
│       │   ├── __init__.py
│       │   ├── wechat_routes.py        # 公众号管理路由
│       │   └── article_routes.py       # 文章管理路由
│       │
│       ├── services/                   # 业务逻辑层
│       │   ├── __init__.py
│       │   ├── wechat_service.py       # 公众号服务
│       │   ├── article_service.py      # 文章服务
│       │   └── download_service.py     # 下载服务
│       │
│       ├── browser/                   # 新增:浏览器自动化模块
│       │   ├── __init__.py
│       │   ├── browser_manager.py       # 浏览器实例管理
│       │   ├── wechat_login.py          # 微信登录处理
│       │   └── session_manager.py       # 会话管理(保存/加载cookie)
│       │
│       ├── utils/                      # 工具类
│       │   ├── __init__.py
│       │   ├── logger.py               # 日志工具
│       │   ├── qr_code.py              # 二维码生成
│       │   ├── file_helper.py          # 文件操作
│       │   └── validators.py           # 数据验证
│       │
│       ├── static/                     # 静态资源
│       │
│       └── templates/                  # HTML 模板
│           ├── base.html               # 基础模板
│           ├── index.html              # 首页
│           ├── wechat_list.html        # 公众号列表页
│           └── article_list.html       # 文章列表页
│
├── tests/                              # 测试目录
│   ├── __init__.py
│   ├── test_models.py                  # 模型测试
│   ├── test_services.py                # 服务层测试
│   ├── test_routes.py                  # 路由测试
│   └── conftest.py                     # pytest 配置
│
├── docs/                               # 文档目录
│   ├── API.md                          # API 文档
│   ├── DEPLOYMENT.md                   # 部署文档
│   └── DEVELOPMENT.md                  # 开发文档
│
├── logs/                               # 日志目录 (运行时生成)
│   ├── app.log                         # 应用日志
│   ├── collect.log                     # 采集日志
│   └── download.log                    # 下载日志
│
├── data/                               # 数据目录
│   ├── downloads/                      # 下载目录 (运行时生成)
│   └── wechat_assistant.db             # SQLite 数据库
│
├── requirements.txt                    # 依赖列表
├── pyproject.toml                      # 项目配置
├── .env.example                        # 环境变量示例
├── .gitignore                          # Git 忽略文件
├── README.md                           # 项目说明
├── LICENSE                             # 许可证
└── run.py                              # 启动脚本
```





## 6. 页面设计

### 6.1 设计原则

- **简洁性**: 界面简洁，操作直观
- **一致性**: 统一的色彩、字体和组件样式
- **反馈性**: 操作成功/失败有明确提示



### 6.2 页面布局

#### 6.2.1 基础布局

- 导航栏放在左侧，支持折叠

- 导航栏菜单如下

  - 公众号管理

  - 文章列表




#### 6.2.2 公众号列表页

**页面结构**:

**表格列**:

- 公众号名称
- 别名
- 头像
- 签名
- 采集进度（单页起始位置）
- 采集状态 (带颜色标签)
- 操作按钮:
  - 编辑 (蓝色按钮)
  - 删除 (红色按钮)
  - 采集单页
  - 采集全部



#### 6.2.3 文章列表页

**搜索和筛选**:

- 搜索（回车触发）

  - 搜索框: 实时搜索文章标题、作者

- 筛选（点击查询触发）

  - 公众号名称（下拉选择）

  - 发布时间范围（日期选择器）

  - 文章是否删除（下拉选择）

  - 是否下载（下拉选择）

**表格列**:

- 复选框 (用于选择文章)
- 公众号名称
- 文章标题 (可点击跳转到原文)
- 文章作者
- 发布时间 ( 文章创建时间 )
- 文章是否删除
- 是否下载

**批量操作**:

- 全选/取消全选
- 显示已选择数量
- 下载选中文章按钮
- 删除选中文章按钮





## 7. 非功能性需求

### 7.1 可维护性

#### 7.1.1 代码质量

- 使用 Ruff 进行代码格式化和检查
- 使用 mypy 进行类型检查

#### 7.1.2 文档完整性

- README: 项目介绍、安装和使用说明
- API 文档: 详细的接口说明
- 代码注释: 关键逻辑有清晰注释

#### 7.1.3 日志

- 分级日志: DEBUG, INFO, WARNING, ERROR
- 文件日志和终端日志同时输出
- 日志文件轮转: 按日期分割
- 错误追踪: 完整的堆栈信息





## 8. 附录

### 8.1 技术实现参考

#### 8.1.1 微信公众平台账号搜索接口请求

**curl 请求示例**

```bash
curl 'https://mp.weixin.qq.com/cgi-bin/searchbiz?action=search_biz&begin=0&count=5&query=%E6%AE%B5%E6%B0%B8%E6%9C%9D%E8%AF%BB%E4%B9%A6&fingerprint=7f01d2b1ee654ac8c1075d37c58eada6&token=552083673&lang=zh_CN&f=json&ajax=1' \
  -H 'accept: */*' \
  -H 'accept-language: zh-CN,zh;q=0.9,en;q=0.8' \
  -b 'appmsglist_action_3012657982=card; pgv_pvid=1781284592602618; _qimei_q36=; o_cookie=522642363; RK=/NtpTjRGPG; ptcz=6e8c0640cc810b12357aef369c24c1b4c69142c9d53c4055c69a1e8099983774; ua_id=ZUPqovXGDS59pxdHAAAAALT6ptH6OMoSxGlPIXNRd_4=; wxuin=40749508009107; mm_lang=zh_CN; __root_domain_v=.weixin.qq.com; _qddaz=QD.196941489093448; ts_uid=153586510; omgid=0_QJT1hzr1mWsjw; _qimei_uuid42=196011624071000a32bf3fcfcfd11612fbb5483ebd; qq_domain_video_guid_verify=7f808b607f0876e7; _qimei_i_3=4df254d3905a508fc194aa63538370e3f4eca1a510580385e687795a22c5263a626337943989e2d49fae; _qimei_fingerprint=cd838bb3f668d5a678cc7c3f05c52027; _qimei_q32=; _qimei_i_2=5df24debed04; _qimei_h38=8f952376771f33d99d2d706e0200000ac18418; _qimei_i_1=74d2578ac35355d9c290f8375c8525e3f4baadf846595785b4897d582493206c616366c63981e6dddeaefaf4; poc_sid=HB9YB2mjJYnquJILSgrG45WGxQT2KEU7ZE-Y59Mn; _clck=3012657982|1|g11|0; rewardsn=; wxtokenkey=777; uuid=af23205a0fa531a475b529d67e3eadba; rand_info=CAESIH/+qMxAo1QNTIOxf5j68XzuPxAkcuapzRqzlCVfSLnV; slave_bizuin=3012657982; data_bizuin=3012657982; bizuin=3012657982; data_ticket=KCVNjelmIdp5LEdXkITF8qcE1mL/r0MRilnuE+2lp61iqfYPBR8PDK9WS9HzgQQ2; slave_sid=Y1M1cmVrRlc0enE0dW9wTElnZTJXUmFqV000Nlp5VFAwd1Z4NUV6NVR1OWhaekd4RkdSTDgwcEc0b3RhczBwT2x1SzF0VzFtT29LS09fY2hwYm9sNXdsUkJpaGl4d3J6YWQ1YTdtUXhBR29TNlZLcUZWZ2xkTGxqT2k3MVFLQ1hUQWF5ZGVFaGZsQnN5OWdj; slave_user=gh_21eb36a00c2e; xid=7861239a09ce8fae6725bc4085367854; _clsk=281hdh|1763187649113|5|1|mp.weixin.qq.com/weheat-agent/payload/record' \
  -H 'dnt: 1' \
  -H 'priority: u=1, i' \
  -H 'referer: https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit_v2&action=edit&isNew=1&type=77&createType=0&token=552083673&lang=zh_CN&timestamp=1763187648025' \
  -H 'sec-ch-ua: "Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "Windows"' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: same-origin' \
  -H 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36' \
  -H 'x-requested-with: XMLHttpRequest'
```

**Response 示例**

```shell
{
    "base_resp": {
        "ret": 0,
        "err_msg": "ok"
    },
    "list": [
        {
            "fakeid": "MjM5ODE2NzYxMg==",
            "nickname": "段永朝读书",
            "alias": "duan-yongchao",
            "round_head_img": "http:\/\/mmbiz.qpic.cn\/mmbiz_png\/ues8YmvWIDOtlptGKc5OvTFPJiciaBnCNxQTDPlzpaHgrHmOpDicFmroZSTib4bD1KtQqf0iaciauan1ZRuiaNJeWtWLw\/0?wx_fmt=png",
            "service_type": 0,
            "signature": "读书即生活，生活即读书",
            "verify_status": 1
        }
    ],
    "total": 1
}
```



#### 8.1.2 微信公众平台文章列表接口请求

**curl 请求示例**

```bash
curl 'https://mp.weixin.qq.com/cgi-bin/appmsgpublish?sub=list&search_field=null&begin=0&count=5&query=&fakeid=MjM5ODE2NzYxMg%3D%3D&type=101_1&free_publish_type=1&sub_action=list_ex&fingerprint=7f01d2b1ee654ac8c1075d37c58eada6&token=552083673&lang=zh_CN&f=json&ajax=1' \
  -H 'accept: */*' \
  -H 'accept-language: zh-CN,zh;q=0.9,en;q=0.8' \
  -b 'appmsglist_action_3012657982=card; pgv_pvid=1781284592602618; _qimei_q36=; o_cookie=522642363; RK=/NtpTjRGPG; ptcz=6e8c0640cc810b12357aef369c24c1b4c69142c9d53c4055c69a1e8099983774; ua_id=ZUPqovXGDS59pxdHAAAAALT6ptH6OMoSxGlPIXNRd_4=; wxuin=40749508009107; mm_lang=zh_CN; __root_domain_v=.weixin.qq.com; _qddaz=QD.196941489093448; ts_uid=153586510; omgid=0_QJT1hzr1mWsjw; _qimei_uuid42=196011624071000a32bf3fcfcfd11612fbb5483ebd; qq_domain_video_guid_verify=7f808b607f0876e7; _qimei_i_3=4df254d3905a508fc194aa63538370e3f4eca1a510580385e687795a22c5263a626337943989e2d49fae; _qimei_fingerprint=cd838bb3f668d5a678cc7c3f05c52027; _qimei_q32=; _qimei_i_2=5df24debed04; _qimei_h38=8f952376771f33d99d2d706e0200000ac18418; _qimei_i_1=74d2578ac35355d9c290f8375c8525e3f4baadf846595785b4897d582493206c616366c63981e6dddeaefaf4; poc_sid=HB9YB2mjJYnquJILSgrG45WGxQT2KEU7ZE-Y59Mn; _clck=3012657982|1|g11|0; rewardsn=; wxtokenkey=777; uuid=af23205a0fa531a475b529d67e3eadba; rand_info=CAESIH/+qMxAo1QNTIOxf5j68XzuPxAkcuapzRqzlCVfSLnV; slave_bizuin=3012657982; data_bizuin=3012657982; bizuin=3012657982; data_ticket=KCVNjelmIdp5LEdXkITF8qcE1mL/r0MRilnuE+2lp61iqfYPBR8PDK9WS9HzgQQ2; slave_sid=Y1M1cmVrRlc0enE0dW9wTElnZTJXUmFqV000Nlp5VFAwd1Z4NUV6NVR1OWhaekd4RkdSTDgwcEc0b3RhczBwT2x1SzF0VzFtT29LS09fY2hwYm9sNXdsUkJpaGl4d3J6YWQ1YTdtUXhBR29TNlZLcUZWZ2xkTGxqT2k3MVFLQ1hUQWF5ZGVFaGZsQnN5OWdj; slave_user=gh_21eb36a00c2e; xid=7861239a09ce8fae6725bc4085367854; _clsk=281hdh|1763187649113|5|1|mp.weixin.qq.com/weheat-agent/payload/record' \
  -H 'dnt: 1' \
  -H 'priority: u=1, i' \
  -H 'referer: https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit_v2&action=edit&isNew=1&type=77&createType=0&token=552083673&lang=zh_CN&timestamp=1763187648025' \
  -H 'sec-ch-ua: "Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "Windows"' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: same-origin' \
  -H 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36' \
  -H 'x-requested-with: XMLHttpRequest'
```

**Response 示例**

微信公众平台文章列表接口请求响应.json
