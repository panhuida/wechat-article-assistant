# 文章下载功能修复

## 问题描述

下载公众号文章时存在以下问题：

1. **HTML文件打不开** - 缺少正确的字符编码声明
2. **图片没有下载** - 图片下载逻辑不完善
3. **文章内容不显示** - 微信文章有CSS隐藏样式
4. **相对路径处理不当** - 图片和CSS链接替换错误

## 修复内容

### 1. 完善的图片下载逻辑

**参考**：`scripts/wechat_service.py` 中的 `_download_and_replace_image()` 函数

#### 关键改进

**a) 使用 `urljoin` 处理相对URL**
```python
from urllib.parse import urljoin

# 之前：手动拼接，容易出错
if img_url.startswith("//"):
    img_url = "https:" + img_url

# 现在：自动处理各种相对URL
full_img_url = urljoin(article_url, img_url)
```

**b) 根据 Content-Type 确定扩展名**
```python
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
```

**c) 清理扩展名中的URL参数**
```python
# 清理如 .jpg?wx_fmt=jpeg&tp=xxx 这样的参数
ext = ext.split('?')[0]
```

**d) 返回相对路径**
```python
# 使用 Path.relative_to() 和 as_posix()
relative_img_path = img_path.relative_to(download_dir)
return relative_img_path.as_posix()
```

### 2. HTML编码问题修复

**问题**：下载的HTML文件乱码或无法打开

**修复**：
```python
# 1. 使用 response.content 而不是 response.text
soup = BeautifulSoup(response.content, 'lxml')

# 2. 确保HTML头中有正确的编码声明
head = soup.find('head')
if head:
    # 移除旧的charset，避免冲突
    for meta_tag in head.find_all('meta', attrs={'charset': True}):
        meta_tag.decompose()
    # 插入新的UTF-8 meta标签
    meta_charset_tag = soup.new_tag('meta', charset='UTF-8')
    head.insert(0, meta_charset_tag)
```

### 3. 强制显示文章内容

**问题**：微信文章默认隐藏内容（visibility: hidden）

**修复**：
```python
# 找到文章内容区域并移除隐藏样式
content_div = soup.find('div', id='js_content')
if content_div and content_div.has_attr('style'):
    del content_div['style']
```

### 4. 资源目录结构优化

**之前**：
```
公众号名称/
  ├── images/
  │   ├── img_0.jpg
  │   └── img_1.png
  └── 文章标题.html
```

**现在**：
```
公众号名称/
  ├── 文章标题.html
  ├── 文章标题.html.meta.json
  └── 文章标题.assets/
      ├── image_0.jpg
      ├── image_1.png
      └── style_123.css
```

**优点**：
- 每篇文章的资源独立存放
- 避免文章间资源冲突
- 便于管理和迁移

### 5. 下载CSS样式表

**新增功能**：下载并本地化CSS文件

```python
for link in soup.find_all('link', rel='stylesheet'):
    css_url = link.get('href')
    if not css_url:
        continue
    
    css_url = urljoin(article_url, css_url)
    css_response = requests.get(css_url, timeout=15)
    if css_response.status_code == 200:
        # 保存CSS到assets目录
        css_path = assets_dir / css_filename
        with open(css_path, 'w', encoding='utf-8') as f:
            f.write(css_response.text)
        
        # 替换为本地路径
        link['href'] = relative_css_path.as_posix()
```

### 6. 处理 data-src 和 srcset

**微信文章的图片特点**：
- 使用 `data-src` 懒加载
- 使用 `srcset` 响应式图片

**修复**：
```python
# 优先处理 data-src
img_url = img.get('data-src') or img.get('src')

# 下载后同时更新 src 和 data-src
if local_img_path:
    img['src'] = local_img_path
    if img.has_attr('data-src'):
        img['data-src'] = local_img_path

# 处理 srcset
if srcset:
    new_srcset = []
    for part in srcset.split(','):
        url_part = part.split()[0]
        descriptor = part.split()[1] if len(part.split()) > 1 else ''
        
        local_path = self._download_and_replace_image(...)
        if local_path:
            new_srcset.append(f"{local_path} {descriptor}")
    
    if new_srcset:
        img['srcset'] = ', '.join(new_srcset)
```

### 7. 移除外部脚本

**问题**：外部脚本可能导致加载失败或隐私问题

**修复**：
```python
# 移除所有外部脚本，保留内联脚本
for script in soup.find_all('script'):
    if script.has_attr('src'):  # 只删除外部脚本
        script.decompose()
```

### 8. 保存元数据

**新增**：保存文章源URL等元数据

```python
meta_path = account_dir / f"{base_filename}.html.meta.json"
meta_data = {'source_url': article_url}
with open(meta_path, 'w', encoding='utf-8') as f:
    json.dump(meta_data, f, ensure_ascii=False, indent=4)
```

## 使用 lxml 解析器

**重要**：使用 `lxml` 而不是默认的 `html.parser`

```python
# 之前
soup = BeautifulSoup(html_content, "html.parser")

# 现在
soup = BeautifulSoup(response.content, 'lxml')
```

**优点**：
- 更好的容错性
- 更快的解析速度
- 更准确的编码检测

**安装**：
```bash
pip install lxml
```

## 测试结果

### 修复前
- ❌ HTML文件打开显示乱码
- ❌ 图片全部显示为404
- ❌ 文章内容不显示
- ❌ 样式丢失

### 修复后
- ✅ HTML文件正常打开
- ✅ 所有图片正确显示
- ✅ 文章内容完整显示
- ✅ 样式保持一致
- ✅ 离线可用

## 代码对比

### 修复前（简化版）
```python
def download_article(self, article_url, article_title):
    response = requests.get(article_url)
    soup = BeautifulSoup(response.text, "html.parser")
    
    for img in soup.find_all("img"):
        img_url = img.get("src")
        # 简单下载...
```

### 修复后（完整版）
```python
def download_article(self, article_url, article_title):
    response = requests.get(article_url, headers=headers)
    soup = BeautifulSoup(response.content, 'lxml')
    
    # 1. 修复编码
    # 2. 强制显示内容
    # 3. 下载CSS
    # 4. 处理图片（data-src + srcset）
    # 5. 移除外部脚本
    # 6. 保存元数据
```

## 相关文件

- **修复文件**：`src/wechat_article_assistant/services/download_service.py`
- **参考代码**：`scripts/wechat_service.py`
  - `_download_and_replace_image()` - 图片下载逻辑
  - `_download_article_content()` - 文章下载逻辑

## 依赖更新

确保 `requirements.txt` 中包含：
```txt
beautifulsoup4>=4.12.0
lxml>=5.0.0
requests>=2.31.0
```

## 注意事项

1. **网络超时**：设置合理的超时时间（15-20秒）
2. **错误处理**：图片下载失败不应中断整个流程
3. **文件名安全**：使用 `sanitize_filename()` 处理特殊字符
4. **编码一致性**：统一使用UTF-8
5. **资源隔离**：每篇文章的资源单独存放

## 未来优化

1. **并发下载**：使用线程池并发下载图片
2. **断点续传**：支持大文件的断点续传
3. **缓存机制**：避免重复下载相同资源
4. **进度回调**：提供下载进度反馈
5. **格式转换**：支持转换为PDF、Markdown等格式

---

**修复日期**：2025-11-15  
**修复人员**：AI Assistant  
**测试状态**：✅ 已验证
