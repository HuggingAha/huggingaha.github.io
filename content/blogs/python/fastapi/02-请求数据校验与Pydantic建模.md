---
title: "FastAPI：请求数据校验与 Pydantic 建模"
showAuthor: false
date: 2025-04-27
description: ""
slug: "fastapi-02"
tags: ["Python", "FastAPI"]
series: ["FastAPI"]
series_order: 2
draft: false
---

<!-- 渲染公式 -->
{{< katex >}}

<!-- --------------------------- -->

<!-- # FastAPI 工程化开发指南 - 第二篇：请求数据校验与 Pydantic 建模 -->

{{< alert "bell" >}}
数据校验是 Web 服务健壮性的第一道防线。本文将深入探讨 FastAPI 如何结合 Pydantic 进行从原子参数到复杂结构体的数据验证，重点分析 Python 3.9+ 的 `Annotated` 语法实践、Pydantic V2 的核心特性，以及在工程中如何设计可维护的模型继承链。
{{< /alert >}}


## 1. 原子参数校验：路径与查询

在处理简单的非 JSON 数据（如 URL 中的 ID 或分页参数）时，FastAPI 提供了 `Path` 和 `Query` 类。为了保持代码的整洁和类型系统的兼容性，推荐使用 Python 标准库 `typing.Annotated` 进行声明。

### 1.1 为什么使用 `Annotated`？
在旧版本 FastAPI 中，参数默认值的写法（如 `q: str = Query(None)`）混淆了“类型定义”与“验证逻辑”。`Annotated` 实现了**关注点分离**：第一个参数是类型，第二个参数是验证元数据。这使得静态类型检查工具（如 mypy, pyright）能正确识别变量类型，而不需要为了运行时行为牺牲静态检查的准确性。

### 1.2 校验实战
```python
from typing import Annotated
from fastapi import FastAPI, Path, Query

app = FastAPI()

@app.get("/items/{item_id}")
async def read_items(
    # 路径参数：必须大于等于1，小于等于1000
    item_id: Annotated[int, Path(title="Item ID", ge=1, le=1000)],
    
    # 查询参数：可选，最大长度50，正则匹配（仅允许字母数字）
    # 如果不传，默认为 None
    q: Annotated[str | None, Query(max_length=50, pattern="^[a-zA-Z0-9]+$")] = None,
    
    # 查询参数：包含别名（前端传 page-size，后端接收 size）
    size: Annotated[int, Query(alias="page-size", gt=0)] = 10
):
    results = {"item_id": item_id, "size": size}
    if q:
        results.update({"q": q})
    return results
```

**常用的校验算子**：
*   `gt`: greater than (>)
*   `ge`: greater than or equal (>=)
*   `lt`: less than (<)
*   `le`: less than or equal (<=)
*   `min_length` / `max_length`: 字符串长度限制
*   `pattern`: 正则表达式约束


## 2. 结构化建模：Pydantic 核心机制

对于 `POST` / `PUT` 请求中的 JSON Body，FastAPI 依赖 **Pydantic** 进行解析。Pydantic 的核心理念是：**解析即验证（Parse, don't validate）**。如果数据符合模型结构，它不仅被验证，还会被转换（Coercion）为指定的 Python 类型。

### 2.1 Pydantic V2 的核心变更
当前 FastAPI 版本底层已支持 Pydantic V2。V2 的核心校验逻辑重写为 Rust (`pydantic-core`)，带来了显著的性能提升。

*   **API 变更注意**：
    *   **序列化**：`model.dict()` 已被废弃，应使用 `model.model_dump()`。
    *   **JSON 序列化**：`model.json()` 已被废弃，应使用 `model.model_dump_json()`。

### 2.2 嵌套模型与复杂类型
处理复杂业务逻辑时，数据往往具有层级结构。

```python
from typing import List
from pydantic import BaseModel, HttpUrl, Field

class Image(BaseModel):
    url: HttpUrl  # 自动验证 URL 格式
    name: str

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float = Field(gt=0, description="价格必须为正数")
    tax: float | None = None
    
    # 嵌套模型列表
    # Set 集合类型可用于自动去重
    tags: set[str] = set() 
    
    # 引用其他模型
    images: List[Image] | None = None

@app.post("/items/")
async def create_item(item: Item):
    # 此处 item 已经是验证通过并转换好的 Item 对象
    # price 自动转为 float，url 自动转为 HttpUrl 对象
    
    # 将模型转换为字典，准备存入数据库
    item_dict = item.model_dump() 
    return item_dict
```


## 3. 高级校验模式

### 3.1 Strict 模式（严格模式）
默认情况下，Pydantic 会尝试转换类型。例如，如果模型定义 `id: int`，前端传 JSON `{"id": "123"}`，Pydantic 会自动将其转换为整数 `123`。

在某些对类型要求极高（如金融交易）的场景下，这种隐式转换可能带来风险。可以使用 Pydantic 的 `Strict` 类型来禁止转换。

```python
from pydantic import BaseModel, StrictInt, StrictBool

class Transaction(BaseModel):
    # 必须传 JSON number 类型，传 string "100" 会报错
    amount: StrictInt 
    # 必须传 JSON boolean 类型，传 "true" 或 1 会报错
    is_verified: StrictBool
```

### 3.2 Field 元数据
`Field` 不仅用于数据校验，还承担着文档生成的重任。
*   `title` / `description`: 渲染到 OpenAPI 文档。
*   `examples`: 提供给 Swagger UI 的示例值，方便调试。
*   `default_factory`: 处理可变类型的默认值（如 `list`, `dict`），避免 Python 中可变默认参数的陷阱。

```python
class LogEntry(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    details: dict = Field(default_factory=dict)
```


## 4. 工程设计模式：模型继承策略 (DRY)

在实际 CRUD 开发中，创建（Create）、更新（Update）、读取（Read）的数据结构往往高度相似但略有不同。例如，用户注册时有密码，但在返回用户信息时必须剔除密码。

为了避免代码重复（DRY 原则），推荐使用**继承链**模式。

### 4.1 基础模型 (Base)
定义所有操作共有的字段。

```python
class UserBase(BaseModel):
    username: str
    email: str
    full_name: str | None = None
```

### 4.2 输入模型 (Create/Input)
继承 Base，并添加创建时特有的字段（如密码）。

```python
class UserCreate(UserBase):
    password: str  # 必填，但在 API 响应中不存在
```

### 4.3 响应模型 (Response/Output)
继承 Base，添加数据库生成的字段（如 ID、创建时间）。

```python
class UserResponse(UserBase):
    id: int
    is_active: bool
    
    # Pydantic V2 配置：允许从 ORM 对象读取数据
    model_config = {"from_attributes": True}
```

### 4.4 在路由中的应用
```python
@app.post("/users/", response_model=UserResponse)
async def create_user(user_in: UserCreate):
    # 1. user_in 包含 password
    # 2. 执行数据库操作，保存 hash 后的密码
    user_db = fake_save_user(user_in) 
    
    # 3. 返回 user_db (包含 password 字段)
    # 4. FastAPI 根据 response_model=UserResponse 自动过滤掉 password
    return user_db
```

通过这种分层设计，我们确保了输入数据的完整性，同时严格控制了输出数据的安全性，且最大程度地复用了代码定义。


## 总结

1.  **原子校验**：使用 `Annotated[Type, Constraints]` 语法，保持类型系统的纯净。
2.  **Pydantic V2**：利用 Rust 内核的高性能，注意 API 从 `.dict()` 到 `.model_dump()` 的迁移。
3.  **严格模式**：在关键业务字段使用 `Strict` 类型防止隐式转换带来的副作用。
4.  **继承复用**：通过 Base -> Create -> Response 的模型继承链，解决字段冗余与敏感数据泄露问题。
