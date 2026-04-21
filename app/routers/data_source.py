from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import uuid
from datetime import datetime

from app.models.schemas import (
    DataSourceType, DataSourceConfig, DatabaseConfig,
    CSVConfig, DataSourceResponse, ErrorResponse
)
from app.services.data_source_service import data_source_service

router = APIRouter()

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/connect", response_model=DataSourceResponse, responses={400: {"model": ErrorResponse}})
async def connect_data_source(config: DataSourceConfig):
    try:
        response = data_source_service.create_data_source(config)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"连接失败: {str(e)}")


@router.post("/upload-csv", response_model=DataSourceResponse, responses={400: {"model": ErrorResponse}})
async def upload_csv(
    file: UploadFile = File(...),
    name: str = Form(None),
    delimiter: str = Form(","),
    encoding: str = Form("utf-8"),
    has_header: bool = Form(True)
):
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="只支持CSV文件")
        
        file_id = str(uuid.uuid4())
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        data_source_name = name or file.filename
        
        csv_config = CSVConfig(
            file_path=file_path,
            delimiter=delimiter,
            encoding=encoding,
            has_header=has_header
        )
        
        config = DataSourceConfig(
            name=data_source_name,
            type=DataSourceType.CSV,
            csv_config=csv_config
        )
        
        response = data_source_service.create_data_source(config)
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.get("/list", response_model=List[DataSourceResponse])
async def list_data_sources():
    return data_source_service.list_data_sources()


@router.get("/{data_source_id}", response_model=DataSourceResponse, responses={404: {"model": ErrorResponse}})
async def get_data_source(data_source_id: str):
    data_source = data_source_service.get_data_source(data_source_id)
    if not data_source:
        raise HTTPException(status_code=404, detail="数据源不存在")
    return data_source


@router.get("/{data_source_id}/preview", responses={404: {"model": ErrorResponse}})
async def preview_data(data_source_id: str, limit: int = 10):
    try:
        df = data_source_service.get_dataframe(data_source_id)
        preview_data = df.head(limit).to_dict(orient='records')
        columns = list(df.columns)
        dtypes = {col: str(df[col].dtype) for col in columns}
        
        return {
            "columns": columns,
            "data_types": dtypes,
            "preview": preview_data,
            "total_rows": len(df),
            "preview_rows": len(preview_data)
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")


@router.delete("/{data_source_id}", responses={404: {"model": ErrorResponse}})
async def delete_data_source(data_source_id: str):
    success = data_source_service.delete_data_source(data_source_id)
    if not success:
        raise HTTPException(status_code=404, detail="数据源不存在")
    return {"message": "数据源已删除", "id": data_source_id}


@router.post("/{data_source_id}/query", responses={404: {"model": ErrorResponse}})
async def execute_query(data_source_id: str, query: str):
    try:
        result = data_source_service.execute_query(data_source_id, query)
        return {
            "columns": list(result.columns),
            "data": result.to_dict(orient='records'),
            "row_count": len(result)
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询执行失败: {str(e)}")
