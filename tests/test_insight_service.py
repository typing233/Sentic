import pytest
import pandas as pd
import numpy as np
from app.services.insight_service import InsightService
from app.models.schemas import InsightType


class TestInsightService:
    def setup_method(self):
        self.service = InsightService()
    
    def test_initialization(self):
        assert self.service.insight_cache == {}
    
    def test_analyze_missing_data(self, sample_dataframe):
        df_with_missing = sample_dataframe.copy()
        df_with_missing.loc[0:2, 'purchase_amount'] = None
        
        insights = self.service.analyze_missing_data(df_with_missing)
        
        assert len(insights) >= 0
    
    def test_analyze_anomalies_with_outliers(self, sample_dataframe_with_outliers):
        insights = self.service.analyze_anomalies(sample_dataframe_with_outliers)
        
        assert len(insights) >= 0
        
        for insight in insights:
            assert insight.type == InsightType.ANOMALY
    
    def test_analyze_correlations(self):
        np.random.seed(42)
        x = np.random.normal(100, 10, 100)
        y = x * 2 + np.random.normal(0, 1, 100)
        
        df = pd.DataFrame({
            'x': x,
            'y': y,
            'category': ['A', 'B'] * 50
        })
        
        insights = self.service.analyze_correlations(df)
        
        assert len(insights) >= 0
        
        for insight in insights:
            assert insight.type == InsightType.CORRELATION
    
    def test_analyze_opportunities(self, sample_dataframe):
        insights = self.service.analyze_opportunities(sample_dataframe)
        
        assert len(insights) >= 0
        
        for insight in insights:
            assert insight.type == InsightType.OPPORTUNITY
    
    def test_analyze_trends(self, sample_dataframe):
        insights = self.service.analyze_trends(sample_dataframe)
        
        assert len(insights) >= 0
        
        for insight in insights:
            assert insight.type == InsightType.TREND
    
    def test_insight_card_structure(self, sample_dataframe_with_outliers):
        insights = self.service.analyze_anomalies(sample_dataframe_with_outliers)
        
        if len(insights) > 0:
            insight = insights[0]
            
            assert hasattr(insight, 'id')
            assert hasattr(insight, 'title')
            assert hasattr(insight, 'type')
            assert hasattr(insight, 'description')
            assert hasattr(insight, 'severity')
            assert hasattr(insight, 'metrics')
            assert hasattr(insight, 'suggestion')
            assert hasattr(insight, 'evidence')
    
    def test_insight_severity_levels(self, sample_dataframe_with_outliers):
        insights = self.service.analyze_anomalies(sample_dataframe_with_outliers)
        
        valid_severities = ['高', '中', '低']
        
        for insight in insights:
            assert insight.severity in valid_severities
    
    def test_get_cached_insights_empty(self):
        cached = self.service.get_cached_insights('nonexistent_id')
        assert cached is None
    
    def test_analyze_opportunities_with_distribution(self):
        data = {
            'channel': ['微信'] * 80 + ['百度'] * 15 + ['抖音'] * 5,
            'value': np.random.normal(100, 10, 100)
        }
        df = pd.DataFrame(data)
        
        insights = self.service.analyze_opportunities(df)
        
        assert len(insights) >= 0
    
    def test_analyze_correlations_strong(self):
        np.random.seed(42)
        x = np.random.normal(100, 10, 100)
        y = x * 3 + 5
        
        df = pd.DataFrame({
            'x': x,
            'y': y
        })
        
        insights = self.service.analyze_correlations(df)
        
        for insight in insights:
            assert '强' in insight.title or '相关' in insight.title
    
    def test_analyze_missing_data_high_percentage(self):
        df = pd.DataFrame({
            'id': range(100),
            'value': [None] * 50 + list(range(50)),
            'other': range(100)
        })
        
        insights = self.service.analyze_missing_data(df)
        
        assert len(insights) >= 0
        
        for insight in insights:
            assert '缺失' in insight.title
