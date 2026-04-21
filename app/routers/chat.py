from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any

from app.models.schemas import ChatRequest, ChatResponse, ErrorResponse
from app.services.chat_service import chat_service

router = APIRouter()


@router.post("/query", response_model=ChatResponse, responses={404: {"model": ErrorResponse}})
async def chat_query(request: ChatRequest):
    try:
        response = chat_service.process_query(request)
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询处理失败: {str(e)}")


@router.get("/conversation/{conversation_id}", responses={404: {"model": ErrorResponse}})
async def get_conversation(conversation_id: str):
    conversation = chat_service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {
        "conversation_id": conversation_id,
        "messages": conversation
    }


@router.post("/clear-conversation/{conversation_id}")
async def clear_conversation(conversation_id: str):
    if conversation_id in chat_service.conversations:
        chat_service.conversations[conversation_id] = []
        return {"message": "会话已清空", "conversation_id": conversation_id}
    raise HTTPException(status_code=404, detail="会话不存在")
