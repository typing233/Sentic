import pytest
import pandas as pd
import os
from app.services.data_source_service import DataSourceService
from app.models.schemas import DataSourceType, DataSourceConfig, CSVConfig


class TestDataSourceService:
    def setup_method(self):
        self.service = DataSourceService()
    
    def test_initialization(self):
        assert self.service.data_sources == {}
        assert self.service.engines == {}
        assert self.service.dataframes == {}
    
    def test_load_csv_success(self, sample_csv_file):
        config = CSVConfig(
            file_path=sample_csv_file,
            delimiter=',',
            encoding='utf-8',
            has_header=True
        )
        
        result = self.service.load_csv(config)
        
        assert result['status'] == 'connected'
        assert result['row_count'] == 5
        assert 'user_id' in result['columns']
        assert 'purchase_amount' in result['columns']
    
    def test_load_csv_file_not_found(self):
        config = CSVConfig(
            file_path='/nonexistent/path/file.csv',
            delimiter=',',
            encoding='utf-8',
            has_header=True
        )
        
        result = self.service.load_csv(config)
        
        assert result['status'] == 'error'
        assert '不存在' in result['error_message']
    
    def test_create_csv_data_source(self, sample_csv_file):
        config = DataSourceConfig(
            name='测试数据',
            type=DataSourceType.CSV,
            csv_config=CSVConfig(
                file_path=sample_csv_file,
                delimiter=',',
                encoding='utf-8',
                has_header=True
            )
        )
        
        response = self.service.create_data_source(config)
        
        assert response.name == '测试数据'
        assert response.type == DataSourceType.CSV
        assert response.status == 'connected'
        assert response.row_count == 5
        assert response.id is not None
        
        assert response.id in self.service.data_sources
        assert response.id in self.service.dataframes
    
    def test_get_data_source(self, sample_csv_file):
        config = DataSourceConfig(
            name='测试数据',
            type=DataSourceType.CSV,
            csv_config=CSVConfig(
                file_path=sample_csv_file,
                delimiter=',',
                encoding='utf-8',
                has_header=True
            )
        )
        
        created = self.service.create_data_source(config)
        retrieved = self.service.get_data_source(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == created.name
    
    def test_get_data_source_not_found(self):
        result = self.service.get_data_source('nonexistent_id')
        assert result is None
    
    def test_list_data_sources(self, sample_csv_file):
        assert len(self.service.list_data_sources()) == 0
        
        config = DataSourceConfig(
            name='测试数据',
            type=DataSourceType.CSV,
            csv_config=CSVConfig(
                file_path=sample_csv_file,
                delimiter=',',
                encoding='utf-8',
                has_header=True
            )
        )
        
        self.service.create_data_source(config)
        
        assert len(self.service.list_data_sources()) == 1
    
    def test_get_dataframe(self, sample_csv_file):
        config = DataSourceConfig(
            name='测试数据',
            type=DataSourceType.CSV,
            csv_config=CSVConfig(
                file_path=sample_csv_file,
                delimiter=',',
                encoding='utf-8',
                has_header=True
            )
        )
        
        created = self.service.create_data_source(config)
        df = self.service.get_dataframe(created.id)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 5
        assert 'user_id' in df.columns
    
    def test_delete_data_source(self, sample_csv_file):
        config = DataSourceConfig(
            name='测试数据',
            type=DataSourceType.CSV,
            csv_config=CSVConfig(
                file_path=sample_csv_file,
                delimiter=',',
                encoding='utf-8',
                has_header=True
            )
        )
        
        created = self.service.create_data_source(config)
        
        assert created.id in self.service.data_sources
        
        result = self.service.delete_data_source(created.id)
        
        assert result is True
        assert created.id not in self.service.data_sources
        assert created.id not in self.service.dataframes
    
    def test_delete_data_source_not_found(self):
        result = self.service.delete_data_source('nonexistent_id')
        assert result is False
    
    def test_execute_query_on_csv(self, sample_csv_file):
        config = DataSourceConfig(
            name='测试数据',
            type=DataSourceType.CSV,
            csv_config=CSVConfig(
                file_path=sample_csv_file,
                delimiter=',',
                encoding='utf-8',
                has_header=True
            )
        )
        
        created = self.service.create_data_source(config)
        
        result = self.service.execute_query(created.id, 'SELECT * FROM temp_table WHERE purchase_amount > 1000')
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
    
    def test_create_data_source_without_csv_config(self):
        config = DataSourceConfig(
            name='测试数据',
            type=DataSourceType.CSV
        )
        
        with pytest.raises(ValueError) as excinfo:
            self.service.create_data_source(config)
        
        assert 'CSV配置不能为空' in str(excinfo.value)
