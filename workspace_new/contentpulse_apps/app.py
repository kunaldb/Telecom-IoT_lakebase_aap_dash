import dash
from dash import html, dcc, Input, Output
import pandas as pd
import os
import time
import uuid
from databricks.sdk import WorkspaceClient
import psycopg
from psycopg_pool import ConnectionPool
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import atexit

# ============================================================
# Database Configuration with Auto-Refreshing OAuth Tokens
# ============================================================
w = WorkspaceClient()

# Get current user information
current_user = w.current_user.me()
print(f"🔐 Current User: {current_user.user_name}")
print(f"   User ID: {current_user.id}")

class RotatingTokenConnection(psycopg.Connection):
    """psycopg3 Connection that injects a fresh OAuth token as the password."""
    
    @classmethod
    def connect(cls, conninfo: str = "", **kwargs):
        # Generate fresh token for each connection
        kwargs["password"] = w.database.generate_database_credential(
            request_id=str(uuid.uuid4()),
            instance_names=[kwargs.pop("_instance_name")]
        ).token
        kwargs.setdefault("sslmode", "require")
        return super().connect(conninfo, **kwargs)

def build_pool(instance_name: str, host: str, user: str, database: str) -> ConnectionPool:
    """Build connection pool with auto-rotating OAuth tokens"""
    print(f"🔌 Building connection pool:")
    print(f"   Instance: {instance_name}")
    print(f"   Host: {host}")
    print(f"   Database: {database}")
    print(f"   User: {user}")
    
    return ConnectionPool(
        conninfo=f"host={host} dbname={database} user={user}",
        connection_class=RotatingTokenConnection,
        kwargs={"_instance_name": instance_name},
        min_size=2,
        max_size=10,
        open=True,
    )

# Get configuration from environment
INSTANCE_NAME = os.getenv('INSTANCE_NAME', 'kunal-gaurav-lakebase-instance')
PGDATABASE = os.getenv('PGDATABASE', 'pg_contentpulse_kunal-gaurav')
PGHOST = os.getenv('PGHOST', 'instance-f60d62f1-e44a-43c7-813f-58138e0552fd.database.cloud.databricks.com')
SCHEMA_NAME = os.getenv('SCHEMA_NAME', 'publishing')
TABLE_NAME = os.getenv('TABLE_NAME', 'content_engagement_synced')
PGUSER = current_user.user_name
print(f"🔐 PGUSER: {PGUSER}")

# Create connection pool with auto-rotating tokens
connection_pool = build_pool(INSTANCE_NAME, PGHOST, PGUSER, PGDATABASE)
print("✅ Connection pool created with auto-rotating OAuth tokens")

@atexit.register
def shutdown_pool():
    """Clean shutdown of connection pool"""
    print("🔌 Shutting down connection pool...")
    connection_pool.close()

def get_connection():
    """Get a connection from the pool (token will be refreshed automatically)"""
    return connection_pool.connection()

# ============================================================
# Data Fetching
# ============================================================
data_cache = {'df': pd.DataFrame(), 'timestamp': 0}

def get_content_data():
    global data_cache
    try:
        with get_connection() as conn:
            query = f"""
                SELECT *
                FROM {SCHEMA_NAME}.{TABLE_NAME}
                ORDER BY timestamp DESC
            """
            df = pd.read_sql(query, conn)
            data_cache['df'] = df
            data_cache['timestamp'] = time.time()
            return df
    except Exception as e:
        print(f"❌ Error: {e}")
        if not data_cache['df'].empty:
            return data_cache['df']
        return pd.DataFrame()

# ============================================================
# Dash App
# ============================================================
app = dash.Dash(__name__, 
                external_stylesheets=['https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'])

app.title = "📰 ContentPulse - Live Publishing Analytics"

# Expose server for Databricks Apps
server = app.server

# ============================================================
# CSS Styling - Publishing Theme
# ============================================================
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body {
                font-family: 'Playfair Display', 'Georgia', serif;
                background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
                min-height: 100vh;
            }
            
            /* Hide loading spinners */
            ._dash-loading-callback { display: none !important; }
            ._dash-loading { display: none !important; }
            
            .main-header {
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                color: white;
                padding: 32px 48px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            }
            
            .main-header h1 {
                font-family: 'Playfair Display', serif;
                font-size: 42px;
                font-weight: 700;
                letter-spacing: -0.5px;
            }
            
            .main-header p {
                font-family: 'Segoe UI', sans-serif;
                font-size: 16px;
                opacity: 0.9;
                margin-top: 8px;
            }
            
            .metric-card {
                background: linear-gradient(135deg, #e94560 0%, #0f3460 100%);
                border-radius: 12px;
                padding: 28px;
                color: white;
                text-align: center;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                transition: all 0.3s ease;
                min-height: 140px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            }
            
            .metric-card:hover {
                transform: translateY(-6px);
                box-shadow: 0 12px 28px rgba(233, 69, 96, 0.3);
            }
            
            .metric-card h3 {
                font-size: 38px;
                font-weight: 700;
                margin: 12px 0 8px 0;
                font-family: 'Segoe UI', sans-serif;
            }
            
            .metric-card p {
                font-size: 14px;
                opacity: 0.95;
                font-weight: 500;
                font-family: 'Segoe UI', sans-serif;
            }
            
            .metric-card i {
                font-size: 40px;
                opacity: 0.9;
            }
            
            .chart-wrapper {
                background: white;
                border-radius: 12px;
                padding: 24px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.06);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }
            
            .chart-wrapper:hover {
                transform: translateY(-4px);
                box-shadow: 0 8px 24px rgba(0,0,0,0.12);
            }
            
            .chart-title {
                font-family: 'Playfair Display', serif;
                font-size: 22px;
                font-weight: 600;
                color: #1a1a2e;
                margin-bottom: 16px;
                padding-bottom: 12px;
                border-bottom: 2px solid #e94560;
            }
            
            .update-indicator {
                position: absolute;
                top: 16px;
                right: 16px;
                color: #e94560;
                font-size: 12px;
                font-weight: 600;
                animation: fadeIn 0.5s ease;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            
            .container-fluid {
                padding: 32px 48px;
                max-width: 1800px;
                margin: 0 auto;
            }
            
            .row {
                display: grid;
                gap: 24px;
                margin-bottom: 24px;
            }
            
            .row.metrics {
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            }
            
            .row.charts-2col {
                grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            }
            
            .row.charts-1col {
                grid-template-columns: 1fr;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# ============================================================
# Layout
# ============================================================
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("📰 ContentPulse", style={'margin': 0}),
        html.P("Live Publishing Analytics Dashboard", style={'margin': 0}),
    ], className='main-header'),
    
    # Main Container
    html.Div([
        # Key Metrics Row
        html.Div([
            html.P('📊 Live Metrics - Refreshes every 10 seconds', style={
                'fontSize': '12px', 
                'color': '#666', 
                'textAlign': 'center',
                'marginBottom': '16px',
                'fontStyle': 'italic'
            }),
        ]),
        html.Div([
            # Active Readers
            html.Div([
                html.Div([
                    html.I(className='fas fa-users'),
                    html.H3(id='active-readers', children='0'),
                    html.P('Active Readers'),
                ], className='metric-card')
            ]),
            
            # Page Views
            html.Div([
                html.Div([
                    html.I(className='fas fa-eye'),
                    html.H3(id='page-views', children='0'),
                    html.P('Page Views'),
                ], className='metric-card')
            ]),
            
            # Engagement Rate
            html.Div([
                html.Div([
                    html.I(className='fas fa-chart-line'),
                    html.H3(id='engagement-rate', children='0%'),
                    html.P('Engagement Rate'),
                ], className='metric-card')
            ]),
            
            # Revenue
            html.Div([
                html.Div([
                    html.I(className='fas fa-dollar-sign'),
                    html.H3(id='total-revenue', children='$0'),
                    html.P('Total Revenue'),
                ], className='metric-card')
            ]),
        ], className='row metrics'),
        
        # Charts Row 1: Geographic Distribution & Device Breakdown
        html.Div([
            html.Div([
                html.Div([
                    html.H2('🌍 Geographic Distribution', className='chart-title'),
                    html.P('Refreshes every 30 seconds', style={'fontSize': '11px', 'color': '#888', 'marginTop': '-8px', 'marginBottom': '8px'}),
                    dcc.Graph(id='geo-map', config={'displayModeBar': False}),
                ], className='chart-wrapper')
            ]),
            
            html.Div([
                html.Div([
                    html.H2('📱 Device Breakdown', className='chart-title'),
                    html.P('Refreshes every 30 seconds', style={'fontSize': '11px', 'color': '#888', 'marginTop': '-8px', 'marginBottom': '8px'}),
                    dcc.Graph(id='device-chart', config={'displayModeBar': False}),
                ], className='chart-wrapper')
            ]),
        ], className='row charts-2col'),
        
        # Charts Row 2: Top Articles & Publications
        html.Div([
            html.Div([
                html.Div([
                    html.H2('📚 Top Articles', className='chart-title'),
                    html.P('Refreshes every 60 seconds', style={'fontSize': '11px', 'color': '#888', 'marginTop': '-8px', 'marginBottom': '8px'}),
                    dcc.Graph(id='top-articles', config={'displayModeBar': False}),
                ], className='chart-wrapper')
            ]),
            
            html.Div([
                html.Div([
                    html.H2('📰 Publications Performance', className='chart-title'),
                    html.P('Refreshes every 60 seconds', style={'fontSize': '11px', 'color': '#888', 'marginTop': '-8px', 'marginBottom': '8px'}),
                    dcc.Graph(id='publications-chart', config={'displayModeBar': False}),
                ], className='chart-wrapper')
            ]),
        ], className='row charts-2col'),
        
        # Chart Row 3: Time Series Engagement
        html.Div([
            html.Div([
                html.Div([
                    html.H2('📈 Real-Time Engagement (Last 5 Minutes)', className='chart-title'),
                    html.P('Refreshes every 10 seconds', style={'fontSize': '11px', 'color': '#888', 'marginTop': '-8px', 'marginBottom': '8px'}),
                    dcc.Graph(id='time-series', config={'displayModeBar': False}),
                ], className='chart-wrapper')
            ]),
        ], className='row charts-1col'),
        
        # Intervals for auto-refresh
        dcc.Interval(id='interval-fast', interval=10*1000, n_intervals=0),  # 10 seconds
        dcc.Interval(id='interval-medium', interval=30*1000, n_intervals=0),  # 30 seconds
        dcc.Interval(id='interval-slow', interval=60*1000, n_intervals=0),  # 1 minute
        
    ], className='container-fluid'),
])

# ============================================================
# Callbacks - Metrics (Fast Refresh - 10s)
# ============================================================
@app.callback(
    [Output('active-readers', 'children'),
     Output('page-views', 'children'),
     Output('engagement-rate', 'children'),
     Output('total-revenue', 'children')],
    [Input('interval-fast', 'n_intervals')]
)
def update_metrics(n):
    df = get_content_data()
    
    if df.empty:
        return '0', '0', '0%', '$0'
    
    # Active Readers (unique readers)
    active_readers = df['reader_id'].nunique()
    
    # Page Views
    page_views = len(df[df['event_type'] == 'page_view'])
    
    # Engagement Rate (interactions / page views)
    interactions = len(df[df['event_type'].isin(['comment', 'share', 'subscribe'])])
    engagement_rate = (interactions / len(df) * 100) if len(df) > 0 else 0
    
    # Total Revenue
    total_revenue = df['estimated_ad_revenue'].sum()
    
    return (
        f"{active_readers:,}",
        f"{page_views:,}",
        f"{engagement_rate:.1f}%",
        f"${total_revenue:,.2f}"
    )

# ============================================================
# Callbacks - Geographic Map (Medium Refresh - 30s)
# ============================================================
@app.callback(
    Output('geo-map', 'figure'),
    [Input('interval-medium', 'n_intervals')]
)
def update_geo_map(n):
    df = get_content_data()
    
    if df.empty:
        return go.Figure()
    
    # Aggregate by city
    city_data = df.groupby(['city', 'country', 'latitude', 'longitude']).agg({
        'reader_id': 'count'
    }).reset_index()
    city_data.columns = ['city', 'country', 'latitude', 'longitude', 'readers']
    
    # Calculate marker sizes - fixed at 2px for minimal visibility
    marker_sizes = city_data['readers'] * 0.05  # Very small multiplier
    marker_sizes = marker_sizes.clip(lower=2, upper=10)  # Fixed range: 2-10px
    
    fig = go.Figure(data=go.Scattergeo(
        lon=city_data['longitude'],
        lat=city_data['latitude'],
        text=city_data['city'] + '<br>' + city_data['readers'].astype(str) + ' readers',
        mode='markers',
        marker=dict(
            size=marker_sizes,
            color=city_data['readers'],
            colorscale='Viridis',  # More vibrant colorscale: purple -> yellow
            showscale=True,
            sizemode='diameter',
            line=dict(width=2, color='white'),  # Thicker white border for better visibility
            opacity=0.85,
            colorbar=dict(
                title="Readers",
                thickness=15,
                len=0.7
            )
        )
    ))
    
    fig.update_layout(
        geo=dict(
            projection_type='natural earth',
            showland=True,
            landcolor='rgb(243, 243, 243)',
            coastlinecolor='rgb(204, 204, 204)',
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=350,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )
    
    return fig

# ============================================================
# Callbacks - Device Chart (Medium Refresh - 30s)
# ============================================================
@app.callback(
    Output('device-chart', 'figure'),
    [Input('interval-medium', 'n_intervals')]
)
def update_device_chart(n):
    df = get_content_data()
    
    if df.empty:
        return go.Figure()
    
    device_counts = df['device_type'].value_counts()
    
    fig = go.Figure(data=[go.Pie(
        labels=device_counts.index,
        values=device_counts.values,
        hole=0.4,
        marker=dict(colors=['#e94560', '#0f3460', '#533483']),
        textinfo='label+percent',
        textfont=dict(size=14, color='white')
    )])
    
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        height=350,
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
    )
    
    return fig

# ============================================================
# Callbacks - Top Articles (Slow Refresh - 1min)
# ============================================================
@app.callback(
    Output('top-articles', 'figure'),
    [Input('interval-slow', 'n_intervals')]
)
def update_top_articles(n):
    df = get_content_data()
    
    if df.empty:
        return go.Figure()
    
    # Top 10 articles by page views
    article_views = df[df['event_type'] == 'page_view'].groupby('article_title').size().sort_values(ascending=True).tail(10)
    
    fig = go.Figure(data=[go.Bar(
        y=article_views.index,
        x=article_views.values,
        orientation='h',
        marker=dict(color='#e94560'),
        text=article_views.values,
        textposition='auto',
    )])
    
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=40),
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(title='Page Views', gridcolor='#f0f0f0'),
        yaxis=dict(title='', tickfont=dict(size=11)),
    )
    
    return fig

# ============================================================
# Callbacks - Publications Performance (Slow Refresh - 1min)
# ============================================================
@app.callback(
    Output('publications-chart', 'figure'),
    [Input('interval-slow', 'n_intervals')]
)
def update_publications_chart(n):
    df = get_content_data()
    
    if df.empty:
        return go.Figure()
    
    pub_stats = df.groupby('publication').agg({
        'event_id': 'count',
        'estimated_ad_revenue': 'sum'
    }).reset_index()
    pub_stats.columns = ['publication', 'events', 'revenue']
    pub_stats = pub_stats.sort_values('events', ascending=False).head(8)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=pub_stats['publication'],
        y=pub_stats['events'],
        name='Events',
        marker_color='#0f3460',
        yaxis='y',
    ))
    
    fig.add_trace(go.Scatter(
        x=pub_stats['publication'],
        y=pub_stats['revenue'],
        name='Revenue ($)',
        marker_color='#e94560',
        yaxis='y2',
        mode='lines+markers',
        line=dict(width=3)
    ))
    
    fig.update_layout(
        yaxis=dict(title='Events', side='left'),
        yaxis2=dict(title='Revenue ($)', overlaying='y', side='right'),
        margin=dict(l=40, r=40, t=20, b=40),
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(tickangle=-45)
    )
    
    return fig

# ============================================================
# Callbacks - Time Series (Fast Refresh - 10s)
# ============================================================
@app.callback(
    Output('time-series', 'figure'),
    [Input('interval-fast', 'n_intervals')]
)
def update_time_series(n):
    df = get_content_data()
    
    if df.empty:
        return go.Figure()
    
    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Group by minute
    df['minute'] = df['timestamp'].dt.floor('min')
    time_series = df.groupby(['minute', 'event_type']).size().reset_index(name='count')
    
    # Color mapping for different event types
    event_colors = {
        'page_view': '#0f3460',    # Dark blue
        'scroll_depth': '#16537e',  # Medium blue
        'comment': '#e94560',       # Red
        'share': '#f39c12',         # Orange
        'subscribe': '#27ae60'      # Green
    }
    
    fig = go.Figure()
    
    for event_type in time_series['event_type'].unique():
        data = time_series[time_series['event_type'] == event_type]
        fig.add_trace(go.Scatter(
            x=data['minute'],
            y=data['count'],
            name=event_type.title(),
            mode='lines+markers',
            line=dict(width=3, color=event_colors.get(event_type, '#999')),
            marker=dict(size=8)
        ))
    
    fig.update_layout(
        margin=dict(l=40, r=40, t=20, b=40),
        height=300,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(title='Time', gridcolor='#f0f0f0'),
        yaxis=dict(title='Events Count', gridcolor='#f0f0f0'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode='x unified'
    )
    
    return fig

# ============================================================
# Run Server
# ============================================================
if __name__ == '__main__':
    app.run_server(host="0.0.0.0", port=8000, debug=False)

