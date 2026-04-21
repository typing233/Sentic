import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from app.models.schemas import (
    InsightType, InsightCard, InsightsResponse
)
from app.services.data_source_service import data_source_service


class InsightService:
    def __init__(self):
        self.insight_cache: Dict[str, InsightsResponse] = {}
    
    def analyze_anomalies(self, df: pd.DataFrame) -> List[InsightCard]:
        insights = []
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        for col in numeric_cols:
            data = df[col].dropna()
            if len(data) < 10:
                continue
            
            z_scores = np.abs(stats.zscore(data))
            outliers = data[z_scores > 3]
            
            if len(outliers) > 0:
                outlier_percent = (len(outliers) / len(data)) * 100
                
                if outlier_percent > 5:
                    insight = InsightCard(
                        id=str(uuid.uuid4()),
                        title=f"{col} 字段存在异常值",
                        type=InsightType.ANOMALY,
                        description=f"在 {col} 字段中发现 {len(outliers)} 个异常值（占比 {outlier_percent:.2f}%）。"
                                    f"这些值的 Z-score 大于 3，可能是数据录入错误或特殊业务情况。",
                        severity="高" if outlier_percent > 10 else "中",
                        metrics={
                            "column": col,
                            "outlier_count": len(outliers),
                            "outlier_percent": round(outlier_percent, 2),
                            "min_outlier": float(outliers.min()),
                            "max_outlier": float(outliers.max()),
                            "mean_normal": float(data[z_scores <= 3].mean()),
                            "std_normal": float(data[z_scores <= 3].std())
                        },
                        suggestion="建议：1) 检查这些异常值是否为数据录入错误；2) 如果是真实业务数据，分析其背后的业务原因；"
                                   "3) 考虑在分析时对这些值进行特殊处理或排除。",
                        evidence=[
                            {"type": "statistics", "data": {"z_score_threshold": 3, "sample_outliers": outliers.head(5).tolist()}}
                        ]
                    )
                    insights.append(insight)
        
        if len(numeric_cols) >= 2:
            try:
                scaler = StandardScaler()
                numeric_data = df[numeric_cols].dropna()
                
                if len(numeric_data) >= 50:
                    scaled_data = scaler.fit_transform(numeric_data)
                    
                    iso_forest = IsolationForest(contamination=0.05, random_state=42)
                    outliers = iso_forest.fit_predict(scaled_data)
                    
                    outlier_indices = np.where(outliers == -1)[0]
                    
                    if len(outlier_indices) > 0:
                        outlier_percent = (len(outlier_indices) / len(numeric_data)) * 100
                        
                        insight = InsightCard(
                            id=str(uuid.uuid4()),
                            title="发现多维度异常记录",
                            type=InsightType.ANOMALY,
                            description=f"通过孤立森林算法在多维度分析中发现 {len(outlier_indices)} 条异常记录"
                                        f"（占比 {outlier_percent:.2f}%）。这些记录在多个维度上与正常数据模式存在显著差异。",
                            severity="中",
                            metrics={
                                "outlier_count": len(outlier_indices),
                                "outlier_percent": round(outlier_percent, 2),
                                "dimensions_analyzed": len(numeric_cols),
                                "algorithm": "Isolation Forest"
                            },
                            suggestion="建议：1) 抽样查看这些异常记录的具体内容；2) 分析这些记录是否代表特殊的用户群体或业务场景；"
                                       "3) 考虑将这些记录单独分析，可能蕴含重要的业务洞察。",
                            evidence=[
                                {"type": "sample_indices", "data": {"sample_outlier_indices": outlier_indices[:5].tolist()}}
                            ]
                        )
                        insights.append(insight)
            except Exception as e:
                pass
        
        return insights
    
    def analyze_trends(self, df: pd.DataFrame) -> List[InsightCard]:
        insights = []
        
        date_cols = df.select_dtypes(include=['datetime', 'object']).columns.tolist()
        
        for col in date_cols:
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                valid_dates = df[col].dropna()
                
                if len(valid_dates) > 10:
                    date_range = valid_dates.max() - valid_dates.min()
                    
                    if date_range.days > 7:
                        insight = InsightCard(
                            id=str(uuid.uuid4()),
                            title=f"{col} 字段包含时间序列数据",
                            type=InsightType.TREND,
                            description=f"发现 {col} 字段包含时间序列数据，时间跨度为 {date_range.days} 天。"
                                        f"最早记录: {valid_dates.min().strftime('%Y-%m-%d')}，"
                                        f"最晚记录: {valid_dates.max().strftime('%Y-%m-%d')}",
                            severity="低",
                            metrics={
                                "column": col,
                                "date_range_days": date_range.days,
                                "min_date": valid_dates.min().strftime('%Y-%m-%d'),
                                "max_date": valid_dates.max().strftime('%Y-%m-%d'),
                                "total_records": len(valid_dates)
                            },
                            suggestion="建议：1) 可以基于时间维度进行趋势分析；2) 分析关键指标随时间的变化趋势；"
                                       "3) 识别周期性模式或季节性变化。",
                            evidence=[
                                {"type": "date_range", "data": {"days": date_range.days}}
                            ]
                        )
                        insights.append(insight)
                        
                        df_sorted = df.sort_values(col)
                        df_sorted['date_group'] = df_sorted[col].dt.to_period('D')
                        daily_counts = df_sorted.groupby('date_group').size()
                        
                        if len(daily_counts) >= 7:
                            mean_count = daily_counts.mean()
                            std_count = daily_counts.std()
                            
                            if std_count > 0:
                                cv = std_count / mean_count
                                
                                if cv > 0.5:
                                    sample_days_dict = {}
                                    for k, v in daily_counts.head(7).items():
                                        if hasattr(k, 'strftime'):
                                            sample_days_dict[k.strftime('%Y-%m-%d')] = int(v)
                                        elif hasattr(k, '__str__'):
                                            sample_days_dict[str(k)] = int(v)
                                        else:
                                            sample_days_dict[k] = int(v)
                                    
                                    insight = InsightCard(
                                        id=str(uuid.uuid4()),
                                        title="日活跃度存在显著波动",
                                        type=InsightType.TREND,
                                        description=f"数据按日期分组后，日记录数波动较大（变异系数: {cv:.2f}）。"
                                                    f"平均每日 {mean_count:.1f} 条记录，标准差 {std_count:.1f}。",
                                        severity="中",
                                        metrics={
                                            "mean_daily": round(mean_count, 1),
                                            "std_daily": round(std_count, 1),
                                            "cv": round(cv, 2),
                                            "max_daily": int(daily_counts.max()),
                                            "min_daily": int(daily_counts.min())
                                        },
                                        suggestion="建议：1) 分析波动是否与特定业务事件相关；2) 识别高活跃度和低活跃度的日期模式；"
                                                   "3) 考虑是否存在周期性规律（如工作日vs周末）。",
                                        evidence=[
                                            {"type": "daily_stats", "data": {"sample_days": sample_days_dict}}
                                        ]
                                    )
                                    insights.append(insight)
            except Exception:
                continue
        
        return insights
    
    def analyze_correlations(self, df: pd.DataFrame) -> List[InsightCard]:
        insights = []
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) >= 2:
            corr_matrix = df[numeric_cols].corr()
            
            for i, col1 in enumerate(numeric_cols):
                for j, col2 in enumerate(numeric_cols[i+1:], i+1):
                    corr = corr_matrix.loc[col1, col2]
                    
                    if abs(corr) > 0.7 and not np.isnan(corr):
                        corr_type = "正相关" if corr > 0 else "负相关"
                        
                        insight = InsightCard(
                            id=str(uuid.uuid4()),
                            title=f"{col1} 与 {col2} 存在强{corr_type}",
                            type=InsightType.CORRELATION,
                            description=f"发现 {col1} 与 {col2} 之间存在强{corr_type}关系，相关系数为 {corr:.3f}。"
                                        f"这种强相关性可能揭示重要的业务关系。",
                            severity="中",
                            metrics={
                                "column1": col1,
                                "column2": col2,
                                "correlation": round(corr, 3),
                                "correlation_type": corr_type
                            },
                            suggestion=f"建议：1) 深入分析 {col1} 和 {col2} 之间的因果关系；2) 考虑是否可以利用这种相关性进行预测；"
                                       f"3) 检查是否存在 confounding 变量影响这种相关性。",
                            evidence=[
                                {"type": "correlation", "data": {"value": round(corr, 3)}}
                            ]
                        )
                        insights.append(insight)
        
        return insights
    
    def analyze_opportunities(self, df: pd.DataFrame) -> List[InsightCard]:
        insights = []
        
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        for cat_col in categorical_cols[:5]:
            value_counts = df[cat_col].value_counts()
            
            if len(value_counts) >= 2 and len(value_counts) <= 20:
                total = value_counts.sum()
                largest_category = value_counts.index[0]
                largest_count = value_counts.iloc[0]
                largest_percent = (largest_count / total) * 100
                
                if largest_percent > 60:
                    insight = InsightCard(
                        id=str(uuid.uuid4()),
                        title=f"{cat_col} 字段分布高度集中",
                        type=InsightType.OPPORTUNITY,
                        description=f"{cat_col} 字段中，'{largest_category}' 类别占比高达 {largest_percent:.1f}%，"
                                    f"而其他 {len(value_counts)-1} 个类别合计仅占 {100-largest_percent:.1f}%。",
                        severity="低",
                        metrics={
                            "column": cat_col,
                            "dominant_category": largest_category,
                            "dominant_percent": round(largest_percent, 1),
                            "other_categories_count": len(value_counts)-1,
                            "total_categories": len(value_counts)
                        },
                        suggestion="建议：1) 分析占比较小的类别是否有增长潜力；2) 考虑是否可以针对小众类别推出差异化策略；"
                                   "3) 检查是否存在数据收集偏差导致的分布不均。",
                        evidence=[
                            {"type": "distribution", "data": value_counts.head(5).to_dict()}
                        ]
                    )
                    insights.append(insight)
                
                smallest_category = value_counts.index[-1]
                smallest_count = value_counts.iloc[-1]
                smallest_percent = (smallest_count / total) * 100
                
                if smallest_percent < 5 and smallest_count >= 10:
                    insight = InsightCard(
                        id=str(uuid.uuid4()),
                        title=f"发现潜在机会：{cat_col} 中的 '{smallest_category}' 类别",
                        type=InsightType.OPPORTUNITY,
                        description=f"{cat_col} 字段中，'{smallest_category}' 类别占比仅为 {smallest_percent:.1f}%（{smallest_count} 条记录）。"
                                    f"这个小众类别可能代表未被充分挖掘的市场机会。",
                        severity="中",
                        metrics={
                            "column": cat_col,
                            "opportunity_category": smallest_category,
                            "count": smallest_count,
                            "percent": round(smallest_percent, 1)
                        },
                        suggestion="建议：1) 深入分析这个小众类别的特征；2) 对比其与主流类别的关键指标差异；"
                                   "3) 评估是否可以通过针对性策略提升这类别的贡献。",
                        evidence=[
                            {"type": "opportunity", "data": {"category": smallest_category, "count": smallest_count}}
                        ]
                    )
                    insights.append(insight)
        
        if len(numeric_cols) >= 1 and len(categorical_cols) >= 1:
            for num_col in numeric_cols[:3]:
                for cat_col in categorical_cols[:3]:
                    try:
                        group_stats = df.groupby(cat_col)[num_col].agg(['mean', 'std', 'count'])
                        group_stats = group_stats[group_stats['count'] >= 10]
                        
                        if len(group_stats) >= 2:
                            max_mean = group_stats['mean'].max()
                            min_mean = group_stats['mean'].min()
                            
                            if min_mean > 0:
                                ratio = max_mean / min_mean
                                
                                if ratio > 2:
                                    insight = InsightCard(
                                        id=str(uuid.uuid4()),
                                        title=f"{num_col} 在 {cat_col} 不同类别间差异显著",
                                        type=InsightType.OPPORTUNITY,
                                        description=f"{num_col} 的平均值在 {cat_col} 的不同类别间存在 {ratio:.1f} 倍的差异。"
                                                    f"最高: {group_stats['mean'].idxmax()} ({max_mean:.2f})，"
                                                    f"最低: {group_stats['mean'].idxmin()} ({min_mean:.2f})。",
                                        severity="中",
                                        metrics={
                                            "numeric_column": num_col,
                                            "categorical_column": cat_col,
                                            "max_category": group_stats['mean'].idxmax(),
                                            "max_mean": round(max_mean, 2),
                                            "min_category": group_stats['mean'].idxmin(),
                                            "min_mean": round(min_mean, 2),
                                            "ratio": round(ratio, 1)
                                        },
                                        suggestion="建议：1) 分析高表现类别的成功因素；2) 研究低表现类别是否有改进空间；"
                                                   "3) 考虑资源分配是否应该向高潜力类别倾斜。",
                                        evidence=[
                                            {"type": "group_comparison", "data": group_stats.to_dict()}
                                        ]
                                    )
                                    insights.append(insight)
                    except Exception:
                        continue
        
        return insights
    
    def analyze_missing_data(self, df: pd.DataFrame) -> List[InsightCard]:
        insights = []
        
        missing_stats = df.isnull().sum()
        total_rows = len(df)
        
        for col, missing_count in missing_stats.items():
            if missing_count > 0:
                missing_percent = (missing_count / total_rows) * 100
                
                if missing_percent > 10:
                    insight = InsightCard(
                        id=str(uuid.uuid4()),
                        title=f"{col} 字段缺失值较多",
                        type=InsightType.ANOMALY,
                        description=f"{col} 字段存在 {missing_count} 个缺失值，占比 {missing_percent:.1f}%。"
                                    f"大量缺失值可能影响数据分析的准确性。",
                        severity="高" if missing_percent > 30 else "中",
                        metrics={
                            "column": col,
                            "missing_count": missing_count,
                            "missing_percent": round(missing_percent, 1),
                            "total_rows": total_rows
                        },
                        suggestion="建议：1) 分析缺失值的模式（随机缺失 vs 系统性缺失）；2) 评估是否需要补充数据；"
                                   "3) 考虑使用合适的填充方法或删除策略；4) 检查数据收集流程是否存在问题。",
                        evidence=[
                            {"type": "missing_stats", "data": {"count": missing_count, "percent": round(missing_percent, 1)}}
                        ]
                    )
                    insights.append(insight)
        
        return insights
    
    def generate_insights(self, data_source_id: str) -> InsightsResponse:
        try:
            df = data_source_service.get_dataframe(data_source_id)
            
            all_insights: List[InsightCard] = []
            
            all_insights.extend(self.analyze_missing_data(df))
            all_insights.extend(self.analyze_anomalies(df))
            all_insights.extend(self.analyze_trends(df))
            all_insights.extend(self.analyze_correlations(df))
            all_insights.extend(self.analyze_opportunities(df))
            
            all_insights.sort(key=lambda x: {
                "高": 3,
                "中": 2,
                "低": 1
            }.get(x.severity, 0), reverse=True)
            
            selected_insights = all_insights[:5]
            
            response = InsightsResponse(
                data_source_id=data_source_id,
                insights=selected_insights,
                generated_at=datetime.now()
            )
            
            self.insight_cache[data_source_id] = response
            
            return response
            
        except ValueError as e:
            raise e
        except Exception as e:
            raise ValueError(f"生成洞察失败: {str(e)}")
    
    def get_cached_insights(self, data_source_id: str) -> Optional[InsightsResponse]:
        return self.insight_cache.get(data_source_id)


insight_service = InsightService()
