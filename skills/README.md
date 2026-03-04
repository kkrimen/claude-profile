# Skills 离线依赖说明

本目录包含以下 5 个 Skills，用于在脱网机器上处理常见文档和图片。

## 包含的 Skills

| Skill | 用途 |
|-------|------|
| pdf | PDF 提取、合并、拆分、填写表单 |
| docx | Word 文档读取、编辑、追踪修改 |
| pptx | PPT 读取、编辑、内容替换 |
| xlsx | Excel 读取、编辑、公式计算 |
| image-enhancer | 图片增强处理 |

## 迁移步骤

### 1. 复制 Skills 目录

将本目录整体复制到目标机器的以下路径：

```
C:\Users\<用户名>\.claude\skills\
```

### 2. 安装 Python 依赖

#### 联网机器上（提前下载 wheel 包）

```bash
pip download pypdf pdf2image Pillow defusedxml python-pptx six openpyxl -d ./offline_packages
```

#### 脱网机器上（离线安装）

```bash
pip install --no-index --find-links=./offline_packages pypdf pdf2image Pillow defusedxml python-pptx six openpyxl
```

#### 各 Skill 依赖明细

| Skill | Python 依赖包 |
|-------|--------------|
| pdf | `pypdf` `pdf2image` `Pillow` |
| docx | `defusedxml` |
| pptx | `python-pptx` `Pillow` `six` |
| xlsx | `openpyxl` |
| image-enhancer | 无 |

### 3. 验证

启动 Claude Code，尝试处理对应格式的文件，确认 Skill 正常加载即可。
