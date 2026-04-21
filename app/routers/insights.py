from fastapi import APIRouter, HTTPException
from typing import Optional

from app.models.schemas import InsightsResponse, ErrorResponse
from app.services.insight_service import insight_service

router = APIRouter()


@router.post("/generate/{data_source_id}", response_model=InsightsResponse, responses={404: {"model": ErrorResponse}})
async def generate_insights(data_source_id: str, use_cache: bool = True):
    try:
        if use_cache:
            cached = insight_service.get_cached_insights(data_source_id)
            if cached:
                return cached
        
        response = insight_service.generate_insights(data_source_id)
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成洞察失败: {str(e)}")


@router.get("/{data_source_id}", response_model=Optional[InsightsResponse], responses={404: {"model": ErrorResponse}})
async def get_insights(data_source_id: str):
    cached = insight_service.get_cached_insights(data_source_id)
    if not cached:
        raise HTTPException(status_code=404, detail="未找到该数据源的洞察数据，请先调用 generate 接口生成")
    return cached


@router.post("/refresh/{data_source_id}", response_model=InsightsResponse, responses={404: {"model": ErrorResponse}})
async def refresh_insights(data_source_id: str):
    try:
        response = insight_service.generate_insights(data_source_id)
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刷新洞察失败: {str(e)}")
