from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from config import settings
from app.models.database import Base, engine
from app.routers import data_source, insights, chat, visualization
from app.routers import auth, team_project, dashboard, export_share


def init_db():
    Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="数字分析科学家 - 自动从原始行为数据中嗅探异常、发现机会并提供增长建议",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(data_source.router, prefix="/api/data-source", tags=["数据源"])
app.include_router(insights.router, prefix="/api/insights", tags=["业务洞察"])
app.include_router(chat.router, prefix="/api/chat", tags=["对话查询"])
app.include_router(visualization.router, prefix="/api/visualization", tags=["可视化"])
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(team_project.router, prefix="/api", tags=["团队与项目"])
app.include_router(dashboard.router, prefix="/api/dashboards", tags=["看板"])
app.include_router(export_share.router, prefix="/api", tags=["导出与分享"])


@app.get("/", response_class=HTMLResponse)
async def root():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


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
