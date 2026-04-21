import pytest
import pandas as pd
import numpy as np
from app.services.chat_service import SQLGenerator, ChartTypeRecommender, ChatService
from app.models.schemas import ChatRequest


class TestSQLGenerator:
    def setup_method(self):
        self.generator = SQLGenerator()
    
    def test_generate_sql_basic(self):
        columns = ['user_id', 'channel', 'purchase_amount', 'purchase_count']
        query = '显示所有数据'
        
        sql = self.generator.generate_sql(query, columns)
        
        assert 'SELECT' in sql
        assert 'FROM' in sql
    
    def test_generate_sql_with_aggregation(self):
        columns = ['user_id', 'channel', 'purchase_amount', 'purchase_count']
        query = '计算purchase_amount的总和'
        
        sql = self.generator.generate_sql(query, columns)
        
        assert 'SUM' in sql.upper() or 'sum' in sql
    
    def test_generate_sql_with_count(self):
        columns = ['user_id', 'channel', 'purchase_amount']
        query = '统计用户数量'
        
        sql = self.generator.generate_sql(query, columns)
        
        assert 'COUNT' in sql.upper()
    
    def test_generate_sql_with_average(self):
        columns = ['user_id', 'purchase_amount']
        query = '计算平均purchase_amount'
        
        sql = self.generator.generate_sql(query, columns)
        
        assert 'AVG' in sql.upper()
    
    def test_explain_sql(self):
        sql = 'SELECT channel, SUM(purchase_amount) FROM temp_table GROUP BY channel'
        
        explanation = self.generator.explain_sql(sql)
        
        assert isinstance(explanation, str)
        assert len(explanation) > 0


class TestChartTypeRecommender:
    def setup_method(self):
        self.recommender = ChartTypeRecommender()
    
    def test_recommend_chart_type_bar(self):
        df = pd.DataFrame({
            'channel': ['微信', '百度', '抖音'],
            'count': [100, 80, 60]
        })
        
        chart_type = self.recommender.recommend_chart_type(df)
        
        assert chart_type == 'bar'
    
    def test_recommend_chart_type_with_trend_keyword(self):
        df = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'value': [10, 20, 30]
        })
        
        chart_type = self.recommender.recommend_chart_type(df, '显示趋势')
        
        assert chart_type == 'line'
    
    def test_recommend_chart_type_with_percentage_keyword(self):
        df = pd.DataFrame({
            'category': ['A', 'B', 'C'],
            'percentage': [30, 40, 30]
        })
        
        chart_type = self.recommender.recommend_chart_type(df, '显示占比')
        
        assert chart_type == 'pie'
    
    def test_prepare_chart_data_bar(self):
        df = pd.DataFrame({
            'channel': ['微信', '百度', '抖音'],
            'count': [100, 80, 60]
        })
        
        result = self.recommender.prepare_chart_data(df, 'bar')
        
        assert 'chart_type' in result
        assert 'data' in result
        assert 'config' in result
        assert result['chart_type'] == 'bar'
    
    def test_prepare_chart_data_line(self):
        df = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'value': [10, 20, 30]
        })
        
        result = self.recommender.prepare_chart_data(df, 'line')
        
        assert result['chart_type'] == 'line'
    
    def test_prepare_chart_data_pie(self):
        df = pd.DataFrame({
            'category': ['A', 'B', 'C'],
            'value': [30, 40, 30]
        })
        
        result = self.recommender.prepare_chart_data(df, 'pie')
        
        assert result['chart_type'] == 'pie'


class TestChatService:
    def setup_method(self):
        self.service = ChatService()
    
    def test_initialization(self):
        assert self.service.conversations == {}
        assert self.service.sql_generator is not None
        assert self.service.chart_recommender is not None
    
    def test_get_conversation_not_found(self):
        conversation = self.service.get_conversation('nonexistent_id')
        assert conversation is None
    
    def test_generate_visualization_invalid_data_source(self):
        from app.models.schemas import VisualizationRequest
        
        request = VisualizationRequest(
            data_source_id='nonexistent',
            query='SELECT * FROM test',
            chart_type='bar'
        )
        
        with pytest.raises(ValueError):
            self.service.generate_visualization(request)
    
    def test_sql_generator_aggregation_keywords(self):
        generator = SQLGenerator()
        
        assert '总和' in generator.aggregation_keywords
        assert 'SUM' in generator.aggregation_keywords.values()
        assert '平均' in generator.aggregation_keywords
        assert 'AVG' in generator.aggregation_keywords.values()
    
    def test_chart_recommender_scatter(self):
        df = pd.DataFrame({
            'x': [1, 2, 3, 4, 5],
            'y': [10, 20, 30, 40, 50]
        })
        
        chart_type = ChartTypeRecommender.recommend_chart_type(df)
        
        assert chart_type in ['scatter', 'histogram', 'bar']
    
    def test_chart_recommender_histogram(self):
        df = pd.DataFrame({
            'value': np.random.normal(100, 10, 100)
        })
        
        chart_type = ChartTypeRecommender.recommend_chart_type(df)
        
        assert chart_type == 'histogram'
    
    def test_prepare_chart_data_scatter(self):
        df = pd.DataFrame({
            'x': [1, 2, 3, 4, 5],
            'y': [10, 20, 30, 40, 50]
        })
        
        result = ChartTypeRecommender.prepare_chart_data(df, 'scatter')
        
        assert result['chart_type'] == 'scatter'
    
    def test_prepare_chart_data_histogram(self):
        df = pd.DataFrame({
            'value': np.random.normal(100, 10, 100)
        })
        
        result = ChartTypeRecommender.prepare_chart_data(df, 'histogram')
        
        assert result['chart_type'] == 'histogram'
        assert 'labels' in result['data']
        assert 'datasets' in result['data']
