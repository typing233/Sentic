import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text, inspect
from typing import Optional, Dict, Any, List
import uuid
from datetime import datetime
import os

from app.models.schemas import (
    DataSourceType, DataSourceConfig, DatabaseConfig, 
    CSVConfig, DataSourceResponse
)


class DataSourceService:
    def __init__(self):
        self.data_sources: Dict[str, Dict[str, Any]] = {}
        self.engines: Dict[str, Any] = {}
        self.dataframes: Dict[str, pd.DataFrame] = {}
        
    def connect_database(self, config: DatabaseConfig) -> Dict[str, Any]:
        try:
            if config.db_type == "sqlite":
                connection_url = f"sqlite:///{config.database}"
            elif config.db_type == "mysql":
                connection_url = f"mysql+pymysql://{config.username}:{config.password}@{config.host}:{config.port}/{config.database}"
            elif config.db_type == "postgresql":
                connection_url = f"postgresql://{config.username}:{config.password}@{config.host}:{config.port}/{config.database}"
            else:
                raise ValueError(f"不支持的数据库类型: {config.db_type}")
            
            engine = create_engine(connection_url)
            
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            if config.table_name and config.table_name not in tables:
                raise ValueError(f"表不存在: {config.table_name}")
            
            target_table = config.table_name or tables[0]
            
            with engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {target_table}"))
                row_count = result.scalar()
            
            columns = inspector.get_columns(target_table)
            column_names = [col['name'] for col in columns]
            
            return {
                "engine": engine,
                "tables": tables,
                "current_table": target_table,
                "columns": column_names,
                "row_count": row_count,
                "status": "connected"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_message": str(e)
            }
    
    def load_csv(self, config: CSVConfig) -> Dict[str, Any]:
        try:
            if not os.path.exists(config.file_path):
                raise FileNotFoundError(f"文件不存在: {config.file_path}")
            
            df = pd.read_csv(
                config.file_path,
                delimiter=config.delimiter,
                encoding=config.encoding,
                header=0 if config.has_header else None
            )
            
            column_names = list(df.columns)
            row_count = len(df)
            
            return {
                "dataframe": df,
                "columns": column_names,
                "row_count": row_count,
                "status": "connected"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_message": str(e)
            }
    
    def create_data_source(self, config: DataSourceConfig) -> DataSourceResponse:
        data_source_id = str(uuid.uuid4())
        created_at = datetime.now()
        
        if config.type == DataSourceType.DATABASE:
            if not config.database_config:
                raise ValueError("数据库配置不能为空")
            
            connection_result = self.connect_database(config.database_config)
            
            if connection_result["status"] == "error":
                raise ValueError(connection_result["error_message"])
            
            self.engines[data_source_id] = connection_result["engine"]
            
            self.data_sources[data_source_id] = {
                "id": data_source_id,
                "name": config.name,
                "type": config.type,
                "config": config,
                "connection_info": connection_result,
                "created_at": created_at
            }
            
            return DataSourceResponse(
                id=data_source_id,
                name=config.name,
                type=config.type,
                status="connected",
                created_at=created_at,
                columns=connection_result.get("columns"),
                row_count=connection_result.get("row_count")
            )
            
        elif config.type == DataSourceType.CSV:
            if not config.csv_config:
                raise ValueError("CSV配置不能为空")
            
            load_result = self.load_csv(config.csv_config)
            
            if load_result["status"] == "error":
                raise ValueError(load_result["error_message"])
            
            self.dataframes[data_source_id] = load_result["dataframe"]
            
            self.data_sources[data_source_id] = {
                "id": data_source_id,
                "name": config.name,
                "type": config.type,
                "config": config,
                "connection_info": load_result,
                "created_at": created_at
            }
            
            return DataSourceResponse(
                id=data_source_id,
                name=config.name,
                type=config.type,
                status="connected",
                created_at=created_at,
                columns=load_result.get("columns"),
                row_count=load_result.get("row_count")
            )
        
        else:
            raise ValueError(f"不支持的数据源类型: {config.type}")
    
    def get_data_source(self, data_source_id: str) -> Optional[DataSourceResponse]:
        if data_source_id not in self.data_sources:
            return None
        
        ds = self.data_sources[data_source_id]
        return DataSourceResponse(
            id=ds["id"],
            name=ds["name"],
            type=ds["type"],
            status=ds["connection_info"]["status"],
            created_at=ds["created_at"],
            columns=ds["connection_info"].get("columns"),
            row_count=ds["connection_info"].get("row_count")
        )
    
    def list_data_sources(self) -> List[DataSourceResponse]:
        return [
            self.get_data_source(ds_id) 
            for ds_id in self.data_sources.keys()
            if self.get_data_source(ds_id) is not None
        ]
    
    def get_dataframe(self, data_source_id: str) -> pd.DataFrame:
        if data_source_id in self.dataframes:
            return self.dataframes[data_source_id]
        
        if data_source_id in self.engines:
            ds = self.data_sources[data_source_id]
            table_name = ds["connection_info"]["current_table"]
            query = f"SELECT * FROM {table_name}"
            return pd.read_sql_query(query, self.engines[data_source_id])
        
        raise ValueError(f"数据源不存在: {data_source_id}")
    
    def execute_query(self, data_source_id: str, query: str) -> pd.DataFrame:
        if data_source_id in self.engines:
            with self.engines[data_source_id].connect() as conn:
                return pd.read_sql_query(text(query), conn)
        elif data_source_id in self.dataframes:
            import sqlite3
            from sqlalchemy import create_engine
            
            df = self.dataframes[data_source_id]
            temp_db = create_engine('sqlite:///:memory:')
            df.to_sql('temp_table', temp_db, index=False, if_exists='replace')
            
            with temp_db.connect() as conn:
                result = pd.read_sql_query(text(query), conn)
            
            return result
        else:
            raise ValueError(f"数据源不存在: {data_source_id}")
    
    def delete_data_source(self, data_source_id: str) -> bool:
        if data_source_id not in self.data_sources:
            return False
        
        if data_source_id in self.engines:
            self.engines[data_source_id].dispose()
            del self.engines[data_source_id]
        
        if data_source_id in self.dataframes:
            del self.dataframes[data_source_id]
        
        del self.data_sources[data_source_id]
        return True


data_source_service = DataSourceService()
