import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np


def basic_groupby(df: pd.DataFrame, column: str) -> pd.DataFrame:
    if column not in df.columns:
        return pd.DataFrame()

    numeric_cols = df.select_dtypes(include="number").columns
    if len(numeric_cols) == 0:
        return df.groupby(column).size().reset_index(name="건수")

    grouped = df.groupby(column)[list(numeric_cols)].agg(["count", "mean", "min", "max"])
    grouped.columns = ["_".join([c, stat]) for c, stat in grouped.columns]
    grouped = grouped.reset_index()
    return grouped


def create_region_chart(df: pd.DataFrame) -> str:
    """지역별 물건 수 막대 그래프"""
    if "지역" not in df.columns:
        return None
    
    region_counts = df['지역'].value_counts().sort_values(ascending=False)
    
    fig = go.Figure(data=[
        go.Bar(
            x=region_counts.index,
            y=region_counts.values,
            marker_color='steelblue',
            text=region_counts.values,
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>물건 수: %{y}건<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title='지역별 물건 수',
        xaxis_title='지역',
        yaxis_title='물건 수',
        height=400,
        hovermode='x unified',
        margin=dict(b=100)
    )
    
    return fig.to_html(div_id="region_chart", include_plotlyjs='cdn')


def create_price_by_region_chart(df: pd.DataFrame) -> str:
    """지역별 평균 예상낙찰가 막대 그래프"""
    price_columns = [col for col in df.columns if '낙찰' in col or '가격' in col or '값' in col]
    
    if "지역" not in df.columns or not price_columns:
        return None
    
    price_col = price_columns[0]
    
    # 지역별 평균 가격
    region_price = df.groupby('지역')[price_col].mean().sort_values(ascending=False)
    
    fig = go.Figure(data=[
        go.Bar(
            x=region_price.index,
            y=region_price.values,
            marker_color='seagreen',
            text=[f'{int(v/100000000):.1f}억' for v in region_price.values],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>평균가격: %{y:,.0f}원<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title='지역별 평균 예상낙찰가',
        xaxis_title='지역',
        yaxis_title='평균 예상낙찰가 (원)',
        height=400,
        hovermode='x unified',
        margin=dict(b=100)
    )
    
    return fig.to_html(div_id="price_chart", include_plotlyjs=False)


def create_type_pie_chart(df: pd.DataFrame) -> str:
    """물건유형별 분포 파이 차트"""
    if '물건유형' not in df.columns:
        return None
    
    type_counts = df['물건유형'].value_counts()
    
    fig = go.Figure(data=[
        go.Pie(
            labels=type_counts.index,
            values=type_counts.values,
            hovertemplate='<b>%{label}</b><br>%{value}건 (%{percent})<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title='물건유형별 분포',
        height=400
    )
    
    return fig.to_html(div_id="type_chart", include_plotlyjs=False)


def create_histogram_chart(df: pd.DataFrame) -> str:
    """수치 데이터 분포 히스토그램"""
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    
    if not numeric_cols:
        return None
    
    # 평수, 가격 관련 컬럼 우선
    priority = [col for col in numeric_cols if '평' in col or '낙찰' in col or '가격' in col]
    selected_col = priority[0] if priority else numeric_cols[0]
    
    fig = go.Figure(data=[
        go.Histogram(
            x=df[selected_col],
            nbinsx=15,
            marker_color='coral',
            hovertemplate='<b>%{x}</b><br>개수: %{y}개<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title=f'{selected_col} 분포 분석',
        xaxis_title=selected_col,
        yaxis_title='빈도',
        height=400
    )
    
    return fig.to_html(div_id="histogram_chart", include_plotlyjs=False)


def create_boxplot_chart(df: pd.DataFrame) -> str:
    """박스플롯 - 이상치 탐지"""
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    
    if not numeric_cols:
        return None
    
    # 가격 관련 컬럼 우선
    price_cols = [col for col in numeric_cols if '낙찰' in col or '가격' in col]
    selected_col = price_cols[0] if price_cols else numeric_cols[0]
    
    fig = go.Figure()
    
    # 전체 데이터 박스플롯
    fig.add_trace(go.Box(
        y=df[selected_col],
        name='전체',
        marker_color='lightblue',
        hovertemplate='<b>값</b>: %{y:,.0f}원<extra></extra>'
    ))
    
    # 물건유형별 박스플롯
    if '물건유형' in df.columns:
        for type_val in df['물건유형'].unique():
            type_data = df[df['물건유형'] == type_val][selected_col]
            fig.add_trace(go.Box(
                y=type_data,
                name=type_val,
                hovertemplate=f'<b>{type_val}</b><br>값: %{{y:,.0f}}원<extra></extra>'
            ))
    
    fig.update_layout(
        title=f'{selected_col} 박스플롯 (이상치 탐지)',
        yaxis_title=selected_col,
        height=400
    )
    
    return fig.to_html(div_id="boxplot_chart", include_plotlyjs=False)


def create_type_price_comparison(df: pd.DataFrame) -> str:
    """물건유형별 평균가격 비교"""
    if '물건유형' not in df.columns:
        return None
    
    price_columns = [col for col in df.columns if '낙찰' in col or '가격' in col or '값' in col]
    
    if not price_columns:
        return None
    
    price_col = price_columns[0]
    
    type_price = df.groupby('물건유형')[price_col].agg(['mean', 'count']).reset_index()
    type_price.columns = ['물건유형', '평균가격', '건수']
    
    fig = go.Figure(data=[
        go.Bar(
            x=type_price['물건유형'],
            y=type_price['평균가격'],
            marker_color=['gold', 'lightblue', 'lightgreen'],
            text=[f'{int(v/100000000):.1f}억<br>({int(c)}건)' for v, c in zip(type_price['평균가격'], type_price['건수'])],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>평균가격: %{y:,.0f}원<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title='물건유형별 평균 예상낙찰가',
        xaxis_title='물건유형',
        yaxis_title='평균 예상낙찰가 (원)',
        height=400
    )
    
    return fig.to_html(div_id="type_price_chart", include_plotlyjs=False)


def create_region_pyeong_comparison(df: pd.DataFrame) -> str:
    """지역별 평수 비교"""
    if '지역' not in df.columns:
        return None
    
    pyeong_cols = [col for col in df.columns if '평' in col]
    
    if not pyeong_cols:
        return None
    
    pyeong_col = pyeong_cols[0]
    
    region_pyeong = df.groupby('지역')[pyeong_col].agg(['mean', 'min', 'max']).reset_index()
    region_pyeong = region_pyeong.sort_values('mean', ascending=False)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=region_pyeong['지역'],
        y=region_pyeong['mean'],
        name='평균',
        marker_color='steelblue',
        error_y=dict(
            type='data',
            symmetric=False,
            array=region_pyeong['max'] - region_pyeong['mean'],
            arrayminus=region_pyeong['mean'] - region_pyeong['min']
        ),
        hovertemplate='<b>%{x}</b><br>평균: %{y:.1f}평<extra></extra>'
    ))
    
    fig.update_layout(
        title='지역별 평수 비교 (최대/최소)',
        xaxis_title='지역',
        yaxis_title='평수',
        height=400,
        margin=dict(b=100)
    )
    
    return fig.to_html(div_id="region_pyeong_chart", include_plotlyjs=False)


def create_heatmap_chart(df: pd.DataFrame) -> str:
    """상관계수 히트맵"""
    numeric_df = df.select_dtypes(include=['number'])
    
    if numeric_df.shape[1] < 2:
        return None
    
    # 상관계수 계산
    corr = numeric_df.corr()
    
    fig = go.Figure(data=go.Heatmap(
        z=corr.values,
        x=corr.columns,
        y=corr.columns,
        colorscale='RdBu',
        zmid=0,
        zmin=-1,
        zmax=1,
        text=np.round(corr.values, 2),
        texttemplate='%{text:.2f}',
        textfont={"size": 10},
        hovertemplate='%{y} vs %{x}<br>상관계수: %{z:.3f}<extra></extra>'
    ))
    
    fig.update_layout(
        title='수치 변수 간 상관계수 분석',
        height=400 + len(corr) * 30
    )
    
    return fig.to_html(div_id="heatmap_chart", include_plotlyjs=False)


def get_statistics_summary(df: pd.DataFrame) -> dict:
    """통계 요약"""
    numeric_df = df.select_dtypes(include=['number'])
    
    if numeric_df.empty:
        return None
    
    stats = {}
    for col in numeric_df.columns:
        stats[col] = {
            '개수': int(numeric_df[col].count()),
            '평균': float(numeric_df[col].mean()),
            '중앙값': float(numeric_df[col].median()),
            '표준편차': float(numeric_df[col].std()),
            '최소값': float(numeric_df[col].min()),
            '최대값': float(numeric_df[col].max()),
            '범위': float(numeric_df[col].max() - numeric_df[col].min())
        }
    
    return stats


def create_missing_data_chart(df: pd.DataFrame) -> str:
    """누락값 분석"""
    missing_data = df.isnull().sum()
    missing_percent = (missing_data / len(df) * 100)
    
    missing_df = pd.DataFrame({
        '컬럼': missing_data.index,
        '누락값': missing_data.values,
        '비율(%)': missing_percent.values
    })
    
    missing_df = missing_df[missing_df['누락값'] > 0].sort_values('누락값', ascending=False)
    
    if missing_df.empty:
        return None
    
    fig = go.Figure(data=[
        go.Bar(
            x=missing_df['컬럼'],
            y=missing_df['비율(%)'],
            marker_color='salmon',
            text=[f'{v:.1f}%<br>({int(n)}건)' for v, n in zip(missing_df['비율(%)'], missing_df['누락값'])],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>누락비율: %{y:.2f}%<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title='누락값 분석',
        xaxis_title='컬럼',
        yaxis_title='누락값 비율 (%)',
        height=400,
        margin=dict(b=100)
    )
    
    return fig.to_html(div_id="missing_chart", include_plotlyjs=False)


def detect_outliers(df: pd.DataFrame) -> dict:
    """이상치 탐지"""
    numeric_df = df.select_dtypes(include=['number'])
    outliers = {}
    
    for col in numeric_df.columns:
        Q1 = numeric_df[col].quantile(0.25)
        Q3 = numeric_df[col].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outlier_mask = (numeric_df[col] < lower_bound) | (numeric_df[col] > upper_bound)
        outlier_count = outlier_mask.sum()
        
        if outlier_count > 0:
            outliers[col] = {
                '이상치개수': int(outlier_count),
                '비율(%)': float(outlier_count / len(df) * 100),
                '하한': float(lower_bound),
                '상한': float(upper_bound)
            }
    
    return outliers if outliers else None

