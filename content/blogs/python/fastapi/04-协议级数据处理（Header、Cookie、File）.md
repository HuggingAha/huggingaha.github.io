---
title: "FastAPI：协议级数据处理（Header/Cookie/File）"
showAuthor: false
date: 2025-04-27
description: ""
slug: "fastapi-04"
tags: ["Python", "FastAPI"]
series: ["FastAPI"]
series_order: 4
draft: false
---

<!-- 渲染公式 -->
{{< katex >}}

<!-- --------------------------- -->


<!-- # FastAPI 工程化开发指南 - 第四篇：协议级数据处理（Header/Cookie/File） -->

{{< alert "bell" >}}
除了标准的 JSON 数据交互，Web 工程还涉及对 HTTP 协议元数据（Headers/Cookies）的控制以及二进制文件流的处理。本文将深入 FastAPI 如何提取协议头信息、处理表单数据，并重点分析 `UploadFile` 的内存管理机制及大文件上传的安全实践。
{{< /alert >}}


## 1. 协议元数据：Header 与 Cookie

在 FastAPI 中，`Header` 和 `Cookie` 是与 `Path` 和 `Query` 同级的依赖项类。提取这些数据的机制遵循 HTTP 协议规范，但在命名转换上有一个关键细节。

### 1.1 Header 的自动转换
HTTP 协议中的 Header 通常使用连字符（如 `User-Agent`），而 Python 变量名不能包含连字符。FastAPI 会自动将参数名中的下划线 `_` 转换为连字符 `-`。

```python
from typing import Annotated
from fastapi import FastAPI, Header, Cookie

@app.get("/items/")
async def read_items(
    # 自动映射请求头 "User-Agent" -> user_agent
    user_agent: Annotated[str | None, Header()] = None,
    
    # 如果需要禁止自动转换，需设置 convert_underscores=False
    # 或者直接使用 alias 指定原始 Header 名
    x_token: Annotated[str | None, Header(alias="X-Token")] = None
):
    return {"User-Agent": user_agent, "X-Token": x_token}
```

### 1.2 Cookie 的状态保持
Cookie 的处理方式与 Header 类似。需要注意的是，Cookie 是客户端可伪造的，不可用于存储敏感信息（如权限标识），仅建议用于存储 Session ID 或非敏感的用户偏好设置。

```python
@app.get("/me")
async def read_current_user(
    session_id: Annotated[str | None, Cookie()] = None
):
    if not session_id:
        return {"msg": "No session"}
    return {"session_id": session_id}
```


## 2. 表单数据解析

尽管现代 API 多使用 JSON，但在处理文件上传或对接传统 Web 系统时，`application/x-www-form-urlencoded` 格式依然存在。

### 2.1 Form 依赖项
使用 `Form` 必须预先安装 `python-multipart` 库，这是因为 Starlette 需要它来解析表单流。

```bash
pip install python-multipart
```

```python
from fastapi import Form

@app.post("/login/")
async def login(
    username: Annotated[str, Form()],
    password: Annotated[str, Form()]
):
    return {"username": username}
```

**工程约束**：由于 HTTP 协议限制，请求体编码只能是 `application/json` 或 `application/x-www-form-urlencoded` 等其中一种。因此，**不能**在同一个路由中同时定义 Pydantic Model（JSON Body）和 `Form` 参数。


## 3. 文件上传机制深度解析

FastAPI 提供了 `bytes`（全量读取）和 `UploadFile`（流式处理）两种方式处理文件。在工程实践中，**强烈建议使用 `UploadFile`**。

### 3.1 `bytes` vs `UploadFile`
*   **bytes (`File`)**：将整个文件内容一次性读取到**内存**中。
    *   *风险*：如果用户上传 1GB 的视频，服务器内存将瞬间飙升，极易导致 OOM (Out Of Memory) 崩溃。
*   **UploadFile**：基于 Python 的 `SpooledTemporaryFile` 实现。
    *   *机制*：设置一个内存阈值（通常为 1MB）。文件小于该值时存内存；超过该值时，自动写入磁盘临时目录。
    *   *优势*：内存占用恒定，适合处理任意大小的文件。

### 3.2 流式写入（最佳实践）
不要使用 `await file.read()` 一次性读入内存，应该使用分块读取（Chunked Read）并写入目标存储（如本地磁盘或 S3）。

```python
import shutil
from pathlib import Path
from fastapi import FastAPI, UploadFile

# 定义存储目录
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.post("/upload/")
async def upload_file(file: UploadFile):
    destination = UPLOAD_DIR / file.filename
    
    try:
        # 方式A：使用 shutil (同步操作，会阻塞)
        # 注意：file.file 是一个标准的 Python file-like object
        # with destination.open("wb") as buffer:
        #     shutil.copyfileobj(file.file, buffer)
        
        # 方式B：异步分块写入 (推荐，非阻塞)
        async with aiofiles.open(destination, 'wb') as out_file:
            while content := await file.read(1024 * 1024):  # 每次读取 1MB
                await out_file.write(content)
                
    finally:
        # 务必关闭文件句柄，释放临时资源
        await file.close()
        
    return {"filename": file.filename}
```
*注：方式B需要安装 `aiofiles` 库。*

### 3.3 安全性考量
在处理文件上传时，必须防范以下两类攻击：
1.  **路径遍历 (Directory Traversal)**：
    *   攻击者可能构造文件名 `../../etc/passwd`。
    *   *防御*：不直接使用 `file.filename`，而是自行生成 UUID 作为文件名，或使用 `os.path.basename` 进行清洗。
2.  **文件类型伪造**：
    *   攻击者可能将 `.exe` 重命名为 `.jpg`。
    *   *防御*：不要仅通过 `content_type` 判断。应读取文件头（Magic Number）校验真实类型（可使用 `python-magic` 库）。

```python
import uuid

# 安全的文件名生成示例
file_ext = file.filename.split(".")[-1]
safe_filename = f"{uuid.uuid4()}.{file_ext}"
```


## 总结

1.  **协议规范**：`Header` 会自动处理 HTTP 头的大小写规范，`Cookie` 仅用于非敏感状态保持。
2.  **内存安全**：处理文件上传时，严禁使用 `bytes` 类型接收大文件，必须使用 `UploadFile`。
3.  **异步 IO**：在保存文件时，优先采用异步分块读写策略，避免阻塞 Event Loop。
4.  **安全防御**：不仅要关注上传功能实现，更要处理文件名清洗和文件内容校验，防止恶意文件攻击。
