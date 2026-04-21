from fastapi import APIRouter, HTTPException
from typing import Optional

from app.models.schemas import VisualizationRequest, VisualizationResponse, ErrorResponse
from app.services.chat_service import chat_service

router = APIRouter()


@router.post("/generate", response_model=VisualizationResponse, responses={404: {"model": ErrorResponse}})
async def generate_visualization(request: VisualizationRequest):
    try:
        response = chat_service.generate_visualization(request)
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成可视化失败: {str(e)}")


@router.get("/chart-types")
async def get_available_chart_types():
    return {
        "chart_types": [
            {"type": "bar", "name": "柱状图", "description": "用于对比不同类别数据"},
            {"type": "line", "name": "折线图", "description": "用于展示数据趋势变化"},
            {"type": "pie", "name": "饼图", "description": "用于展示各部分占比"},
            {"type": "scatter", "name": "散点图", "description": "用于观察变量间相关性"},
            {"type": "histogram", "name": "直方图", "description": "用于展示数据分布"},
            {"type": "table", "name": "表格", "description": "直接展示原始数据"}
        ]
    }
