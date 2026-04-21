import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
import json
import re

from app.models.schemas import (
    ChatRequest, ChatResponse, SQLQuery, 
    VisualizationRequest, VisualizationResponse
)
from app.services.data_source_service import data_source_service
from config import settings


class ChartTypeRecommender:
    @staticmethod
    def recommend_chart_type(df: pd.DataFrame, query: str = "") -> str:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        query_lower = query.lower()
        
        if '趋势' in query_lower or '时间' in query_lower or 'daily' in query_lower or 'monthly' in query_lower:
            return 'line'
        
        if '占比' in query_lower or '比例' in query_lower or 'percentage' in query_lower:
            if len(df) <= 10:
                return 'pie'
        
        if len(numeric_cols) >= 2 and len(categorical_cols) == 0:
            return 'scatter'
        
        if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
            if len(df) > 10:
                return 'bar'
            else:
                return 'bar'
        
        if len(numeric_cols) >= 1:
            return 'histogram'
        
        return 'table'
    
    @staticmethod
    def prepare_chart_data(df: pd.DataFrame, chart_type: str) -> Dict[str, Any]:
        result = {
            'chart_type': chart_type,
            'data': {},
            'config': {}
        }
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        if chart_type == 'bar':
            if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
                cat_col = categorical_cols[0]
                num_col = numeric_cols[0]
                
                result['data'] = {
                    'labels': df[cat_col].astype(str).tolist(),
                    'datasets': [{
                        'label': num_col,
                        'data': df[num_col].tolist()
                    }]
                }
                result['config'] = {'x_axis': cat_col, 'y_axis': num_col}
        
        elif chart_type == 'line':
            if len(numeric_cols) >= 1:
                x_col = categorical_cols[0] if categorical_cols else df.columns[0]
                y_col = numeric_cols[0]
                
                result['data'] = {
                    'labels': df[x_col].astype(str).tolist(),
                    'datasets': [{
                        'label': y_col,
                        'data': df[y_col].tolist()
                    }]
                }
                result['config'] = {'x_axis': x_col, 'y_axis': y_col}
        
        elif chart_type == 'pie':
            if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
                cat_col = categorical_cols[0]
                num_col = numeric_cols[0]
                
                result['data'] = {
                    'labels': df[cat_col].astype(str).tolist(),
                    'values': df[num_col].tolist()
                }
                result['config'] = {'category_column': cat_col, 'value_column': num_col}
        
        elif chart_type == 'scatter':
            if len(numeric_cols) >= 2:
                x_col = numeric_cols[0]
                y_col = numeric_cols[1]
                
                result['data'] = {
                    'datasets': [{
                        'label': f'{x_col} vs {y_col}',
                        'data': list(zip(df[x_col].tolist(), df[y_col].tolist()))
                    }]
                }
                result['config'] = {'x_axis': x_col, 'y_axis': y_col}
        
        elif chart_type == 'histogram':
            if len(numeric_cols) >= 1:
                num_col = numeric_cols[0]
                hist, bins = np.histogram(df[num_col].dropna(), bins='auto')
                
                result['data'] = {
                    'labels': [f'{bins[i]:.2f}-{bins[i+1]:.2f}' for i in range(len(bins)-1)],
                    'datasets': [{
                        'label': num_col,
                        'data': hist.tolist()
                    }]
                }
                result['config'] = {'column': num_col}
        
        result['config']['title'] = f'{chart_type.capitalize()} Chart'
        
        return result


class SQLGenerator:
    def __init__(self):
        self.aggregation_keywords = {
            '总和': 'SUM', 'sum': 'SUM', '总计': 'SUM',
            '平均': 'AVG', 'average': 'AVG', '均值': 'AVG',
            '计数': 'COUNT', 'count': 'COUNT', '数量': 'COUNT',
            '最大': 'MAX', 'max': 'MAX', '最大值': 'MAX',
            '最小': 'MIN', 'min': 'MIN', '最小值': 'MIN',
        }
    
    def generate_sql(self, query: str, columns: List[str], table_name: str = 'temp_table') -> str:
        query_lower = query.lower()
        
        numeric_cols = []
        categorical_cols = []
        
        for col in columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in ['id', 'date', 'time', 'name', 'channel', 'source', 'type', 'category']):
                categorical_cols.append(col)
            else:
                numeric_cols.append(col)
        
        select_cols = []
        aggregations = []
        group_by_cols = []
        where_conditions = []
        
        for keyword, agg_func in self.aggregation_keywords.items():
            if keyword in query_lower:
                for col in numeric_cols:
                    if col.lower() in query_lower:
                        aggregations.append(f"{agg_func}({col}) AS {agg_func.lower()}_{col}")
                        break
                else:
                    if numeric_cols:
                        aggregations.append(f"{agg_func}({numeric_cols[0]}) AS {agg_func.lower()}_value")
        
        for col in categorical_cols:
            if col.lower() in query_lower:
                group_by_cols.append(col)
                select_cols.append(col)
        
        if '日活' in query or 'dau' in query_lower or 'daily active' in query_lower:
            date_cols = [c for c in columns if 'date' in c.lower() or 'time' in c.lower()]
            if date_cols:
                select_cols.append(f"DATE({date_cols[0]}) AS date")
                aggregations.append(f"COUNT(DISTINCT user_id) AS dau" if 'user_id' in [c.lower() for c in columns] else f"COUNT(*) AS dau")
                group_by_cols.append(f"DATE({date_cols[0]})")
        
        if '转化率' in query or 'conversion' in query_lower:
            if numeric_cols:
                select_cols.append("'转化率' AS metric")
                aggregations.append(f"AVG(CASE WHEN {numeric_cols[0]} > 0 THEN 1 ELSE 0 END) AS conversion_rate")
        
        if not aggregations and not select_cols:
            select_cols = ['*']
        
        final_select = select_cols + aggregations if aggregations else select_cols
        if not final_select:
            final_select = ['*']
        
        sql = f"SELECT {', '.join(final_select)} FROM {table_name}"
        
        if group_by_cols:
            sql += f" GROUP BY {', '.join(group_by_cols)}"
        
        if '前' in query and '条' in query:
            match = re.search(r'(\d+)\s*条', query)
            if match:
                sql += f" LIMIT {match.group(1)}"
        
        return sql
    
    def explain_sql(self, sql: str) -> str:
        explanation_parts = []
        
        if 'SELECT' in sql.upper():
            select_match = re.search(r'SELECT\s+(.+?)\s+FROM', sql, re.IGNORECASE | re.DOTALL)
            if select_match:
                explanation_parts.append(f"查询字段: {select_match.group(1)}")
        
        if 'GROUP BY' in sql.upper():
            group_match = re.search(r'GROUP BY\s+(.+)', sql, re.IGNORECASE)
            if group_match:
                explanation_parts.append(f"分组依据: {group_match.group(1)}")
        
        if 'LIMIT' in sql.upper():
            limit_match = re.search(r'LIMIT\s+(\d+)', sql, re.IGNORECASE)
            if limit_match:
                explanation_parts.append(f"限制条数: {limit_match.group(1)}")
        
        return "此SQL查询将" + ("；".join(explanation_parts) if explanation_parts else "获取表中的数据")


class ChatService:
    def __init__(self):
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}
        self.sql_generator = SQLGenerator()
        self.chart_recommender = ChartTypeRecommender()
    
    def process_query(self, request: ChatRequest) -> ChatResponse:
        data_source_id = request.data_source_id
        query = request.query
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        try:
            data_source = data_source_service.get_data_source(data_source_id)
            if not data_source:
                raise ValueError(f"数据源不存在: {data_source_id}")
            
            columns = data_source.columns or []
            
            sql = self.sql_generator.generate_sql(query, columns)
            
            chart_type = self.chart_recommender.recommend_chart_type(
                pd.DataFrame(), query
            )
            
            sql_query = SQLQuery(
                sql=sql,
                explanation=self.sql_generator.explain_sql(sql),
                suggested_chart_type=chart_type
            )
            
            result_df = data_source_service.execute_query(data_source_id, sql)
            
            execution_result = {
                'columns': list(result_df.columns),
                'data': result_df.to_dict(orient='records'),
                'row_count': len(result_df)
            }
            
            actual_chart_type = self.chart_recommender.recommend_chart_type(result_df, query)
            chart_data = self.chart_recommender.prepare_chart_data(result_df, actual_chart_type)
            
            chart_config = {
                'chart_type': actual_chart_type,
                **chart_data
            }
            
            response_text = self._generate_natural_response(result_df, query, actual_chart_type)
            
            response = ChatResponse(
                conversation_id=conversation_id,
                query=query,
                sql_query=sql_query,
                execution_result=execution_result,
                chart_config=chart_config,
                response_text=response_text
            )
            
            if conversation_id not in self.conversations:
                self.conversations[conversation_id] = []
            
            self.conversations[conversation_id].append({
                'query': query,
                'response': response.model_dump(),
                'timestamp': datetime.now().isoformat()
            })
            
            return response
            
        except Exception as e:
            raise ValueError(f"处理查询失败: {str(e)}")
    
    def _generate_natural_response(self, df: pd.DataFrame, query: str, chart_type: str) -> str:
        if len(df) == 0:
            return "未找到符合条件的数据。请检查查询条件是否正确。"
        
        response_parts = []
        query_lower = query.lower()
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        if '日活' in query or 'dau' in query_lower or '活跃用户' in query:
            if len(df) == 1 and 'dau' in df.columns:
                response_parts.append(f"📊 查询结果：")
                response_parts.append(f"日活跃用户数 (DAU): {df['dau'].iloc[0]}")
            elif len(df) > 1:
                dau_col = None
                for col in df.columns:
                    if 'dau' in col.lower() or 'count' in col.lower():
                        dau_col = col
                        break
                
                if dau_col and len(df) > 0:
                    response_parts.append(f"📊 查询结果：共 {len(df)} 条记录")
                    response_parts.append(f"{dau_col} 的统计：")
                    response_parts.append(f"- 最大值: {df[dau_col].max():.0f}")
                    response_parts.append(f"- 最小值: {df[dau_col].min():.0f}")
                    response_parts.append(f"- 平均值: {df[dau_col].mean():.1f}")
                    response_parts.append(f"- 总计: {df[dau_col].sum():.0f}")
        
        elif '转化' in query or 'conversion' in query_lower:
            response_parts.append(f"📊 转化率分析：")
            if len(df) > 0:
                response_parts.append(f"共分析 {len(df)} 条记录")
                if numeric_cols:
                    col = numeric_cols[0]
                    converted = (df[col] > 0).sum()
                    total = len(df)
                    rate = converted / total * 100 if total > 0 else 0
                    response_parts.append(f"- 转化数量: {converted}")
                    response_parts.append(f"- 总数量: {total}")
                    response_parts.append(f"- 转化率: {rate:.1f}%")
        
        elif '总和' in query or '总计' in query or 'sum' in query_lower:
            response_parts.append(f"📊 求和结果：")
            for col in numeric_cols[:5]:
                total = df[col].sum()
                response_parts.append(f"- {col}: {total:.2f}")
        
        elif '平均' in query or '均值' in query or 'average' in query_lower:
            response_parts.append(f"📊 平均值结果：")
            for col in numeric_cols[:5]:
                avg = df[col].mean()
                response_parts.append(f"- {col}: {avg:.2f}")
        
        elif '最大' in query or '最高' in query or 'max' in query_lower:
            response_parts.append(f"📊 最大值结果：")
            for col in numeric_cols[:5]:
                max_val = df[col].max()
                response_parts.append(f"- {col}: {max_val:.2f}")
        
        elif '最小' in query or '最低' in query or 'min' in query_lower:
            response_parts.append(f"📊 最小值结果：")
            for col in numeric_cols[:5]:
                min_val = df[col].min()
                response_parts.append(f"- {col}: {min_val:.2f}")
        
        elif '数量' in query or '多少' in query or 'count' in query_lower:
            response_parts.append(f"📊 查询结果：")
            response_parts.append(f"共找到 {len(df)} 条记录")
        
        else:
            response_parts.append(f"📊 查询结果：共 {len(df)} 条记录")
            
            if categorical_cols and len(df) <= 20:
                response_parts.append(f"\n数据预览：")
                for i, row in df.head(10).iterrows():
                    preview_parts = []
                    for col in categorical_cols[:2]:
                        preview_parts.append(f"{row[col]}")
                    for col in numeric_cols[:2]:
                        preview_parts.append(f"{col}: {row[col]:.2f}" if pd.notna(row[col]) else f"{col}: N/A")
                    if preview_parts:
                        response_parts.append(f"- {' | '.join(preview_parts)}")
                
                if len(df) > 10:
                    response_parts.append(f"... 还有 {len(df) - 10} 条记录")
            
            elif numeric_cols:
                response_parts.append(f"\n数值字段统计：")
                for col in numeric_cols[:5]:
                    data = df[col].dropna()
                    if len(data) > 0:
                        response_parts.append(f"「{col}」：")
                        response_parts.append(f"  总计: {len(data)} 条 | 平均: {data.mean():.2f} | 最大: {data.max():.2f} | 最小: {data.min():.2f}")
        
        if chart_type == 'line':
            response_parts.append("\n💡 建议使用折线图展示数据趋势变化。")
        elif chart_type == 'bar':
            response_parts.append("\n💡 建议使用柱状图对比不同类别的数据。")
        elif chart_type == 'pie':
            response_parts.append("\n💡 建议使用饼图展示各部分占比情况。")
        elif chart_type == 'scatter':
            response_parts.append("\n💡 建议使用散点图观察变量间的相关性。")
        elif chart_type == 'histogram':
            response_parts.append("\n💡 建议使用直方图观察数据分布。")
        
        return "\n".join(response_parts)
    
    def get_conversation(self, conversation_id: str) -> Optional[List[Dict[str, Any]]]:
        return self.conversations.get(conversation_id)
    
    def generate_visualization(self, request: VisualizationRequest) -> VisualizationResponse:
        try:
            data_source_id = request.data_source_id
            query = request.query
            chart_type = request.chart_type
            
            data_source = data_source_service.get_data_source(data_source_id)
            if not data_source:
                raise ValueError(f"数据源不存在: {data_source_id}")
            
            if query.strip().upper().startswith('SELECT'):
                result_df = data_source_service.execute_query(data_source_id, query)
            else:
                result_df = data_source_service.get_dataframe(data_source_id)
                if query:
                    pass
            
            if request.x_axis and request.y_axis:
                cols_to_keep = [request.x_axis] + request.y_axis
                result_df = result_df[cols_to_keep]
            
            chart_data = self.chart_recommender.prepare_chart_data(result_df, chart_type)
            
            config = chart_data.get('config', {})
            if request.title:
                config['title'] = request.title
            
            return VisualizationResponse(
                chart_type=chart_type,
                data=chart_data.get('data', {}),
                config=config,
                json=chart_data
            )
            
        except Exception as e:
            raise ValueError(f"生成可视化失败: {str(e)}")


chat_service = ChatService()
