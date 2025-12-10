---
title: "FastAPI：构建 MCP 服务"
showAuthor: false
date: 2025-04-27
description: ""
slug: "fastapi-06"
tags: ["Python", "FastAPI"]
series: ["FastAPI"]
series_order: 6
draft: false
---

<!-- 渲染公式 -->
{{< katex >}}

<!-- --------------------------- -->

<!-- # FastAPI 工程化开发指南 - 第六篇：工程实战——构建 MCP 服务 -->


{{< alert "bell" >}}
本文将通过一个完整的实战项目——构建符合模型上下文协议（MCP）的天气查询服务，串联前五篇的核心知识点，涵盖项目结构规划、配置管理、MCP 协议适配、认证集成以及 Docker 容器化部署，展示从开发到交付的完整工程链路。
{{< /alert >}}


## 1. 项目规划与结构

遵循第一篇提到的工程化原则，将代码拆分为模块化结构，而非单文件应用。

```text
weather-mcp/
├── app/
│   ├── __init__.py
│   ├── main.py              # 应用入口与 MCP 挂载
│   ├── config.py            # 环境变量配置
│   ├── dependencies.py      # 依赖注入（认证、HTTP客户端）
│   ├── models.py            # Pydantic 模型定义
│   └── tools.py             # 核心业务逻辑（MCP工具函数）
├── .env                     # 敏感配置（不提交到 git）
├── Dockerfile               # 容器构建文件
├── requirements.txt
└── .gitignore
```


## 2. 配置管理 (pydantic-settings)

硬编码密钥是安全大忌。使用 `pydantic-settings` 从环境变量或 `.env` 文件读取配置。

```python
# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    WEATHER_API_KEY: str
    MCP_AUTH_TOKEN: str = "secret-token-123" # 默认值仅用于开发
    ENV: str = "production"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
```

---

## 3. 核心业务与 HTTP 客户端

需要一个异步 HTTP 客户端来调用上游天气 API。

```python
# app/dependencies.py
import httpx
from typing import AsyncGenerator

# 使用 httpx.AsyncClient 替代 requests 以支持异步
# 并将其作为 Yield 依赖项，确保资源释放
async def get_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        yield client
```

```python
# app/models.py
from pydantic import BaseModel, Field

class WeatherQuery(BaseModel):
    city: str = Field(..., description="City name to query weather for")

class WeatherData(BaseModel):
    temperature: float
    description: str
    humidity: int
```


## 4. MCP 服务实现与认证集成

将使用 `fastapi-mcp` 将 FastAPI 路由转换为 MCP 工具，并集成 Bearer Token 认证。

```python
# app/main.py
from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi_mcp import FastApiMCP, AuthConfig
import httpx

from app.config import settings
from app.models import WeatherQuery, WeatherData
from app.dependencies import get_http_client

# 1. 定义认证逻辑
security = HTTPBearer()

async def verify_token(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]):
    if credentials.credentials != settings.MCP_AUTH_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

# 2. 初始化 FastAPI 应用
app = FastAPI(title="Weather MCP Service")

# 3. 定义核心工具函数（路由）
# 注意：operation_id 将成为 MCP 工具的名称
@app.post(
    "/weather",
    response_model=WeatherData,
    operation_id="get_current_weather",
    description="Get current weather for a specific city."
)
async def get_weather(
    query: WeatherQuery,
    client: Annotated[httpx.AsyncClient, Depends(get_http_client)]
):
    # 模拟外部 API 调用
    # 真实场景应调用 https://api.weatherprovider.com...
    # response = await client.get(f"...", params={"q": query.city, "appid": settings.WEATHER_API_KEY})
    # data = response.json()
    
    return {
        "temperature": 25.5,
        "description": "Sunny",
        "humidity": 60
    }

# 4. 挂载 MCP 服务
# auth_config 将保护 /mcp 端点
mcp = FastApiMCP(
    app,
    name="WeatherService",
    version="1.0.0",
    include_operations=["get_current_weather"], # 显式指定暴露的工具
    auth_config=AuthConfig(dependencies=[Depends(verify_token)])
)
mcp.mount() # 默认挂载在 /mcp
```


## 5. Docker 容器化部署

为了交付标准化的服务，需要编写 `Dockerfile`。推荐使用 Multi-stage 构建以减小镜像体积，并使用非 root 用户运行以提高安全性。

```dockerfile
# Dockerfile
# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
# 安装依赖到用户目录，避免污染系统环境
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runner
FROM python:3.11-slim

WORKDIR /app
# 从 builder 阶段复制安装好的包
COPY --from=builder /root/.local /root/.local
COPY ./app ./app

# 更新 PATH 环境变量
ENV PATH=/root/.local/bin:$PATH

# 创建非 root 用户
RUN useradd -m appuser
USER appuser

# 生产级启动命令：使用 gunicorn 管理 uvicorn workers
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
```

**运行命令**：
```bash
# 构建镜像
docker build -t weather-mcp:v1 .

# 运行容器 (注入环境变量)
docker run -d \
  -p 8000:8000 \
  -e WEATHER_API_KEY="your_api_key" \
  -e MCP_AUTH_TOKEN="your_secure_token" \
  weather-mcp:v1
```


## 6. 集成验证

当服务启动后，AI Agent（如 Cherry Studio 或 Cursor）可以通过以下配置接入该服务：

*   **Server URL**: `http://<your-ip>:8000/mcp`
*   **Headers**: `Authorization: Bearer your_secure_token`

AI 将自动识别 `get_current_weather` 工具，解析其输入 Schema (`WeatherQuery`)，并在用户提问“查询北京天气”时自动构造请求调用你的 API。


## 总结

1.  **工程闭环**：通过分层结构、配置管理、依赖注入和 Pydantic 建模，构建了一个可维护、可测试的微服务。
2.  **MCP 适配**：借助 `fastapi-mcp`，以极低的成本将传统 Web API 转化为 AI 生态的一部分，无需重写业务逻辑。
3.  **交付标准**：Docker 化和环境变量配置是现代云原生应用交付的底线要求。
