import pytest
import pandas as pd
import numpy as np
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_dataframe():
    data = {
        'user_id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'channel': ['微信', '百度', '抖音', '微信', '小红书', '百度', '抖音', '微信', '小红书', '百度'],
        'signup_date': ['2024-01-15', '2024-01-20', '2024-02-01', '2024-02-05', '2024-02-10',
                        '2024-02-15', '2024-02-20', '2024-02-25', '2024-03-01', '2024-03-05'],
        'purchase_amount': [1250.50, 300.00, 5600.75, 890.00, 150.25,
                           3200.00, 450.00, 7800.00, 2200.50, 1800.00],
        'purchase_count': [5, 2, 12, 3, 1, 8, 2, 15, 6, 4],
        'is_active': [1, 0, 1, 1, 0, 1, 0, 1, 1, 1],
        'age_group': ['25-34', '18-24', '25-34', '35-44', '18-24',
                     '25-34', '35-44', '25-34', '18-24', '35-44'],
        'region': ['华东', '华北', '华南', '华东', '西南',
                  '华北', '华南', '华东', '西南', '华北']
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_dataframe_with_outliers():
    np.random.seed(42)
    n = 100
    
    normal_data = np.random.normal(100, 10, n)
    outliers = [200, 250, 300, -50, -100]
    values = np.concatenate([normal_data, outliers])
    total_length = len(values)
    
    categories = (['A', 'B', 'C', 'D'] * ((total_length // 4) + 1))[:total_length]
    
    return pd.DataFrame({
        'id': list(range(total_length)),
        'value': values,
        'category': categories,
        'other_value': values * 2 + np.random.normal(0, 5, total_length)
    })


@pytest.fixture
def sample_csv_file(tmp_path):
    content = """user_id,channel,signup_date,purchase_amount,purchase_count
1,微信,2024-01-15,1250.50,5
2,百度,2024-01-20,300.00,2
3,抖音,2024-02-01,5600.75,12
4,微信,2024-02-05,890.00,3
5,小红书,2024-02-10,150.25,1
"""
    csv_file = tmp_path / "test_data.csv"
    csv_file.write_text(content, encoding='utf-8')
    return str(csv_file)
