import os
import logging
from typing import List

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from app.config import settings
from app.user import user_router
from app.search import search_router
from app.file import file_router

app = FastAPI(title="群晖NAS管理API", description="提供对群晖NAS的管理接口", version="1.0.0")

# 注册路由
app.include_router(user_router)
app.include_router(search_router)
app.include_router(file_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}

# 健康检查接口
@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    import os
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))