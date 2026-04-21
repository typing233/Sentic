from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from config import settings
from app.routers import data_source, insights, chat, visualization

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="数字分析科学家 - 自动从原始行为数据中嗅探异常、发现机会并提供增长建议",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 注册路由
app.include_router(data_source.router, prefix="/api/data-source", tags=["数据源"])
app.include_router(insights.router, prefix="/api/insights", tags=["业务洞察"])
app.include_router(chat.router, prefix="/api/chat", tags=["对话查询"])
app.include_router(visualization.router, prefix="/api/visualization", tags=["可视化"])

# 主页路由
@app.get("/", response_class=HTMLResponse)
async def root():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.app_version}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
