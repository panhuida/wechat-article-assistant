# item_show_type 文件名优化功能说明

## 功能概述

根据微信公众号文章的 `item_show_type` 类型，自动调整保存的HTML文件名长度，确保特殊类型文章的文件名更简洁。

## 实现位置

文件：`src/wechat_article_assistant/services/download_service.py`

## item_show_type 说明

`item_show_type` 是微信公众号文章的类型标识，不同的值代表不同类型的文章：

| item_show_type | 文章类型 | 文件名长度限制  |
| -------------- | -------- | --------------- |
| 0              | 普通图文 | 100字符（默认） |
| 8              | 轮播图片 | 100字符（默认） |
| 10             | 纯文字   | 40字符（较短）  |
| 11             | 转发     | 100字符（默认） |

### item_show_type = 10

这类文章的特点：
- **标题超长**：通常包含大量换行符和完整段落
- **类型**：图片文章、语音文章、视频文章等
- **示例**：如巴菲特告别信全文作为标题的文章

## 实现方法

### 1. 提取 item_show_type

从HTML源码中使用正则表达式提取：

```python
item_show_type_match = re.search(r'item_show_type["\']?\s*[:=]\s*["\']?(\d+)', response.text)
if item_show_type_match:
    item_show_type = int(item_show_type_match.group(1))
```

### 2. 根据类型调整文件名长度

```python
max_filename_length = 100  # 默认长度

if item_show_type == 10:
    max_filename_length = 40  # 特殊类型使用较短文件名
    logger.info(f"item_show_type=10，使用较短文件名长度: {max_filename_length}")
```

### 3. 应用到文件名清理

```python
base_filename = sanitize_filename(article_title, max_length=max_filename_length)
```

## 效果对比

### item_show_type = 10 的文章

**标题（完整）**：
```
今天才认真读了巴菲特的告别信：

六十多年来，查理对我影响巨大，他是一位极好的老师，也是我保护有加的"大哥"。我们之间虽有分歧，但从无争执。他从不说"我早就跟你说过"。
For more than 60 years, Charlie had a huge impact on me...
（更多内容）
```

**文件名（优化后）**：
```
今天才认真读了巴菲特的告别信： 六十多年来，查理对我影响巨大，他是一位极好....html
```

长度：43字符（40 + "..."）

### 普通文章（item_show_type = 0 或 8）

**标题**：
```
物理学革命
```

**文件名**：
```
物理学革命.html
```

长度：5字符

## 日志输出

### 检测到 item_show_type = 10

```
INFO 从 og:title 提取标题: 今天才认真读了巴菲特的告别信：\n\n六十多年来，查理对我影响巨大，他是一位极好的老师，也是我保护有...
INFO 检测到 item_show_type: 10
INFO item_show_type=10，使用较短文件名长度: 40
INFO 文章下载成功: E:\documents\...\今天才认真读了巴菲特的告别信： 六十多年来，查理对我影响巨大，他是一位极好....html
```

### 普通文章

```
INFO 从 og:title 提取标题: 物理学革命...
INFO 检测到 item_show_type: 0
INFO 文章下载成功: E:\documents\...\物理学革命.html
```

## 优势

### 1. 自动识别 ✅
- 无需手动判断文章类型
- 自动从HTML源码提取类型标识

### 2. 灵活配置 ✅
- 不同类型使用不同的长度限制
- 易于扩展支持更多类型

### 3. 避免文件名过长 ✅
- Windows文件名限制：260字符（路径全长）
- 截断后添加"..."标识
- 确保文件系统兼容

### 4. 保留可读性 ✅
- 保留标题前40个字符
- 仍然能识别文章内容
- 避免完全无意义的文件名

## 兼容性

- ✅ 向后兼容：未检测到 item_show_type 时使用默认长度
- ✅ 类型扩展：易于添加新的类型处理规则
- ✅ 错误容错：提取失败时使用默认长度

## 测试用例

### 测试文章

1. **item_show_type=8**
   - URL: https://mp.weixin.qq.com/s/HCvfj4h2GgLrkAHFm_L1Tg
   - 标题: "Such is Singapore"
   - 文件名: 17字符
   - 限制: 100字符（默认）

2. **item_show_type=10**
   - URL: https://mp.weixin.qq.com/s/Ld4TvMMg6T9moE0S1EwdFg
   - 标题: 超长段落（约500字符）
   - 文件名: 43字符
   - 限制: 40字符

3. **item_show_type=10**
   - URL: https://mp.weixin.qq.com/s/BnEZx6Fc25yfxKAgjjHDfQ
   - 标题: 超长段落（约300字符）
   - 文件名: 43字符
   - 限制: 40字符

### 测试命令

```bash
python wechat-cli.py download <url> --output <dir> --verbose
```

验证输出中包含：
- `检测到 item_show_type: X`
- `使用较短文件名长度: 40`（仅当 item_show_type=10）

## 更新日期

2025-11-26：初始版本
- 实现 item_show_type 检测
- 支持 item_show_type=10 的特殊处理
- 文件名长度从100字符优化到40字符
