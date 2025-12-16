import dash
from dash import html, dcc, Input, Output, State
import pandas as pd
import os
import time
import uuid
from databricks.sdk import WorkspaceClient
import psycopg
from psycopg_pool import ConnectionPool
import plotly.graph_objects as go
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
PGDATABASE = os.getenv('PGDATABASE', 'pg_lakebase_kunal-gaurav')
PGHOST = os.getenv('PGHOST', 'instance-f60d62f1-e44a-43c7-813f-58138e0552fd.database.cloud.databricks.com')
PGUSER = current_user.user_name  # Use current user from Databricks
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
# Data Fetching (cached)
# ============================================================
data_cache = {'df': pd.DataFrame(), 'timestamp': 0}

def get_iot_data():
    global data_cache
    try:
        with get_connection() as conn:
            query = """
                SELECT *
                FROM telcom.iot_data_synced
               
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

app.title = "📡 Telecom IoT Dashboard"

# ============================================================
# CSS - NO FLICKERING
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
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                min-height: 100vh;
            }
            
            /* HIDE ALL LOADING SPINNERS */
            ._dash-loading-callback { display: none !important; }
            ._dash-loading { display: none !important; }
            .dash-spinner { display: none !important; }
            
            .chart-wrapper {
                background: white;
                border-radius: 16px;
                padding: 24px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
                position: relative;
            }
            
            .chart-wrapper:hover {
                transform: translateY(-4px);
                box-shadow: 0 8px 24px rgba(102, 126, 234, 0.15);
            }
            
            .metric-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 16px;
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
                box-shadow: 0 12px 28px rgba(102, 126, 234, 0.3);
            }
            
            .metric-card h3 {
                font-size: 38px;
                font-weight: 700;
                margin: 12px 0 8px 0;
            }
            
            .metric-card p {
                font-size: 14px;
                opacity: 0.95;
                font-weight: 500;
            }
            
            .metric-card i {
                font-size: 42px;
                opacity: 0.9;
            }
            
            .update-dot {
                position: absolute;
                top: 12px;
                right: 12px;
                width: 8px;
                height: 8px;
                background: #667eea;
                border-radius: 50%;
                opacity: 0;
                transition: opacity 0.5s;
            }
            
            .update-dot.active {
                opacity: 0.5;
                animation: pulse 2s ease-in-out infinite;
            }
            
            @keyframes pulse {
                0%, 100% { transform: scale(1); opacity: 0.3; }
                50% { transform: scale(1.3); opacity: 0.6; }
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .fade-in { animation: fadeIn 0.4s ease-out; }
            
            ::-webkit-scrollbar { width: 12px; }
            ::-webkit-scrollbar-track { background: #f1f1f1; border-radius: 10px; }
            ::-webkit-scrollbar-thumb { 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                border-radius: 10px; 
            }
            
            .dash-graph { min-height: 380px; }
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
        html.Div([
            html.I(className="fas fa-broadcast-tower", 
                   style={'fontSize': '52px', 'marginRight': '24px', 'color': '#00d4ff'}),
            html.Div([
                html.H1("Telecom Tower Performance Dashboard", 
                        style={'margin': '0', 'fontSize': '40px', 'fontWeight': '700'}),
                html.P("Real-time Network Analytics • Powered by Databricks Lakehouse", 
                       style={'margin': '8px 0 0 0', 'fontSize': '15px', 'opacity': '0.92'})
            ])
        ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'})
    ], style={
        'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'color': 'white',
        'padding': '36px 20px',
        'textAlign': 'center',
        'boxShadow': '0 6px 20px rgba(0,0,0,0.15)',
        'marginBottom': '32px'
    }),

    # KPI Cards
    html.Div([
        html.Div([
            html.I(className="fas fa-users"),
            html.H3(id='kpi-users', children='0'),
            html.P('Total Active Users')
        ], className='metric-card fade-in', style={'width': '23%', 'display': 'inline-block', 'margin': '0 1%'}),
        
        html.Div([
            html.I(className="fas fa-database"),
            html.H3(id='kpi-data', children='0 GB'),
            html.P('Total Data Usage')
        ], className='metric-card fade-in', style={'width': '23%', 'display': 'inline-block', 'margin': '0 1%'}),
        
        html.Div([
            html.I(className="fas fa-signal"),
            html.H3(id='kpi-signal', children='0 dBm'),
            html.P('Avg Signal Strength')
        ], className='metric-card fade-in', style={'width': '23%', 'display': 'inline-block', 'margin': '0 1%'}),
        
        html.Div([
            html.I(className="fas fa-tower-cell"),
            html.H3(id='kpi-towers', children='0'),
            html.P('Active Towers')
        ], className='metric-card fade-in', style={'width': '23%', 'display': 'inline-block', 'margin': '0 1%'}),
    ], style={'padding': '0 48px', 'marginBottom': '32px'}),

    # Filters
    html.Div([
        html.Div([
            html.Label("🌍 Select Region:", 
                      style={'fontWeight': '600', 'marginRight': '12px', 'fontSize': '16px', 'color': '#2c3e50'}),
            dcc.Dropdown(
                id='region-filter', 
                multi=False, 
                placeholder="All Regions",
                style={'width': '320px', 'display': 'inline-block'}
            ),
        ], style={'display': 'inline-block', 'marginRight': '40px'}),
        
        html.Div([
            html.I(className="fas fa-clock", style={'marginRight': '8px'}),
            html.Span(id='last-update', children='Initializing...')
        ], style={
            'display': 'inline-block',
            'padding': '12px 24px',
            'background': 'linear-gradient(135deg, #f0f4ff 0%, #e8eeff 100%)',
            'borderRadius': '24px',
            'fontWeight': '600',
            'color': '#667eea',
            'fontSize': '14px'
        })
    ], style={
        'textAlign': 'center',
        'marginBottom': '32px',
        'padding': '24px',
        'background': 'white',
        'boxShadow': '0 2px 8px rgba(0,0,0,0.06)',
        'borderRadius': '16px',
        'margin': '0 48px 32px 48px'
    }),

    # Intervals
    dcc.Interval(id='interval-fast', interval=30000, n_intervals=0),
    dcc.Interval(id='interval-slow', interval=60000, n_intervals=0),

    # Charts
    html.Div([
        
        # Row 1
        html.Div([
            html.Div([
                html.Div(className='update-dot', id='dot-1'),
                dcc.Graph(id='chart-data-usage', config={'displayModeBar': False}, style={'height': '380px'})
            ], className='chart-wrapper fade-in', style={'width': '65%'}),
            
            html.Div([
                html.Div(className='update-dot', id='dot-2'),
                dcc.Graph(id='chart-gauge', config={'displayModeBar': False}, style={'height': '380px'})
            ], className='chart-wrapper fade-in', style={'width': '33%'}),
        ], style={'display': 'flex', 'gap': '24px', 'marginBottom': '24px'}),

        # Row 2
        html.Div([
            html.Div([
                html.Div(className='update-dot', id='dot-3'),
                dcc.Graph(id='chart-users', config={'displayModeBar': False}, style={'height': '380px'})
            ], className='chart-wrapper fade-in', style={'width': '65%'}),
            
            html.Div([
                html.Div(className='update-dot', id='dot-4'),
                dcc.Graph(id='chart-pie', config={'displayModeBar': False}, style={'height': '380px'})
            ], className='chart-wrapper fade-in', style={'width': '33%'}),
        ], style={'display': 'flex', 'gap': '24px', 'marginBottom': '24px'}),

        # Row 3
        html.Div([
            html.Div([
                html.Div(className='update-dot', id='dot-5'),
                dcc.Graph(id='chart-heatmap', config={'displayModeBar': False}, style={'height': '380px'})
            ], className='chart-wrapper fade-in', style={'width': '100%'}),
        ], style={'marginBottom': '24px'}),

        # Row 4
        html.Div([
            html.Div([
                html.Div(className='update-dot', id='dot-6'),
                dcc.Graph(id='chart-bar', config={'displayModeBar': False}, style={'height': '380px'})
            ], className='chart-wrapper fade-in', style={'width': '100%'}),
        ], style={'marginBottom': '48px'}),

    ], style={'margin': '0 48px'}),

    # Footer
    html.Div([
        html.I(className="fas fa-copyright", style={'marginRight': '6px'}),
        "2024 Telecom Analytics Dashboard | Powered by Databricks Lakehouse"
    ], style={'textAlign': 'center', 'color': '#7f8c8d', 'padding': '24px', 'fontSize': '14px'})

], style={'minHeight': '100vh', 'paddingBottom': '40px'})

# ============================================================
# CALLBACK 1: Initialize Charts (runs once)
# ============================================================
@app.callback(
    [Output('chart-data-usage', 'figure'),
     Output('chart-users', 'figure'),
     Output('chart-gauge', 'figure'),
     Output('region-filter', 'options')],
    [Input('region-filter', 'value')],
    prevent_initial_call=False
)
def initialize_charts(region):
    """Initialize all time series charts"""
    
    df = get_iot_data()
    
    # Region options
    regions = []
    if not df.empty:
        regions = [{'label': r, 'value': r} for r in sorted(df['region'].unique())]
        if not region and regions:
            region = regions[0]['value']
    
    if df.empty:
        empty = go.Figure()
        empty.add_annotation(text="No Data Available", font=dict(size=20, color="gray"), 
                           showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5)
        empty.update_layout(template="plotly_white", height=380, paper_bgcolor='white')
        return empty, empty, empty, regions
    
    df_filtered = df[df['region'] == region] if region else df
    colors = ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b']
    
    # Chart 1: Data Usage
    fig1 = go.Figure()
    for idx, tower in enumerate(df_filtered['tower_id'].unique()[:5]):
        tower_df = df_filtered[df_filtered['tower_id'] == tower].sort_values('timestamp').tail(100)
        fig1.add_trace(go.Scatter(
            x=tower_df['timestamp'],
            y=tower_df['data_usage_mb'],
            name=tower,
            mode='lines+markers',
            line=dict(width=3, shape='spline', color=colors[idx]),
            marker=dict(size=6, line=dict(width=2, color='white')),
            hovertemplate='<b>%{fullData.name}</b><br>%{x|%H:%M:%S}<br>%{y:.1f} MB<extra></extra>'
        ))
    
    fig1.update_layout(
        title=dict(text=f"📡 Data Usage Trend - {region or 'All Regions'}", 
                  font=dict(size=20, color='#2c3e50', family='Arial Black'), x=0.5, xanchor='center'),
        template="plotly_white",
        hovermode='x unified',
        height=380,
        paper_bgcolor='white',
        plot_bgcolor='rgba(250,250,250,0.5)',
        margin=dict(l=60, r=40, t=80, b=60),
        xaxis=dict(showgrid=True, gridcolor='#e8e8e8', title='Time', tickformat='%H:%M:%S'),
        yaxis=dict(showgrid=True, gridcolor='#e8e8e8', title='Data (MB)', rangemode='tozero'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        uirevision='data-usage'
    )
    
    # Chart 2: Active Users
    fig2 = go.Figure()
    for idx, tower in enumerate(df_filtered['tower_id'].unique()[:5]):
        tower_df = df_filtered[df_filtered['tower_id'] == tower].sort_values('timestamp').tail(100)
        fig2.add_trace(go.Scatter(
            x=tower_df['timestamp'],
            y=tower_df['active_users'],
            name=tower,
            mode='lines',
            line=dict(width=0),
            stackgroup='one',
            fillcolor=colors[idx],
            hovertemplate='<b>%{fullData.name}</b><br>%{x|%H:%M:%S}<br>%{y} users<extra></extra>'
        ))
    
    fig2.update_layout(
        title=dict(text=f"👥 Active Users - {region or 'All Regions'}", 
                  font=dict(size=20, color='#2c3e50', family='Arial Black'), x=0.5, xanchor='center'),
        template="plotly_white",
        height=380,
        hovermode='x unified',
        paper_bgcolor='white',
        plot_bgcolor='rgba(250,250,250,0.5)',
        margin=dict(l=60, r=40, t=80, b=60),
        xaxis=dict(showgrid=True, gridcolor='#e8e8e8', title='Time', tickformat='%H:%M:%S'),
        yaxis=dict(showgrid=True, gridcolor='#e8e8e8', title='Users', rangemode='tozero'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        uirevision='active-users'
    )
    
    # Chart 3: Gauge
    avg_drop = df_filtered['call_drop_rate'].mean()
    if avg_drop < 1:
      avg_drop = avg_drop * 100
    fig3 = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=avg_drop,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "<b>📉 Call Drop Rate (%)</b>", 'font': {'size': 20, 'color': '#2c3e50'}},
        delta={'reference': 2.0, 'increasing': {'color': "#e74c3c"}, 'decreasing': {'color': "#2ecc71"}},
        number={'suffix': '%', 'font': {'size': 44, 'color': '#2c3e50'}},
        gauge={
            'axis': {'range': [0, 10], 'tickwidth': 2, 'tickcolor': "#2c3e50"},
            'bar': {'color': "#667eea", 'thickness': 0.7},
            'bgcolor': "white",
            'borderwidth': 3,
            'bordercolor': "#ecf0f1",
            'steps': [
                {'range': [0, 2], 'color': '#d4edda'},
                {'range': [2, 5], 'color': '#fff3cd'},
                {'range': [5, 10], 'color': '#f8d7da'}
            ],
            'threshold': {'line': {'color': "#e74c3c", 'width': 5}, 'thickness': 0.8, 'value': 5}
        }
    ))
    
    fig3.update_layout(
        paper_bgcolor="white",
        height=380,
        margin=dict(l=30, r=30, t=80, b=30),
        uirevision='gauge'
    )
    
    return fig1, fig2, fig3, regions

# ============================================================
# CALLBACK 2: Extend Time Series (30s - NO REDRAW)
# ============================================================
@app.callback(
    [Output('chart-data-usage', 'extendData'),
     Output('chart-users', 'extendData'),
     Output('kpi-users', 'children'),
     Output('kpi-data', 'children'),
     Output('kpi-signal', 'children'),
     Output('kpi-towers', 'children'),
     Output('last-update', 'children')],
    [Input('interval-fast', 'n_intervals')],
    [State('region-filter', 'value')]
)
def extend_timeseries(n, region):
    """Extend charts smoothly without redrawing"""
    
    if n == 0:
        return [None, None, '0', '0 GB', '0 dBm', '0', 'Initializing...']
    
    df = get_iot_data()
    
    if df.empty:
        return [None, None, '0', '0 GB', '0 dBm', '0', 'No data']
    
    df_filtered = df[df['region'] == region] if region else df
    
    # Get only NEW data (last 30 seconds)
    latest_time = df_filtered['timestamp'].max()
    new_data = df_filtered[df_filtered['timestamp'] >= (latest_time - pd.Timedelta(seconds=30))]
    
    if new_data.empty:
        # No new data, just update KPIs
        total_users = int(df_filtered['active_users'].sum())
        total_data = df_filtered['data_usage_mb'].sum() / 1024
        avg_signal = df_filtered['call_drop_rate'].mean() 
        total_towers = df_filtered['tower_id'].nunique()
        
        return [
            None, None,
            f"{total_users:,}",
            f"{total_data:.2f} GB",
            f"{avg_signal:.1f} dBm" if avg_signal > 0 else "N/A",
            f"{total_towers}",
            f"Live • {datetime.now().strftime('%H:%M:%S')}"
        ]
    
    # KPIs
    total_users = int(df_filtered['active_users'].sum())
    total_data = df_filtered['data_usage_mb'].sum() / 1024
    avg_signal = df_filtered['call_drop_rate'].mean() 
    total_towers = df_filtered['tower_id'].nunique()
    
    # Prepare extend data for Chart 1 (Data Usage)
    extend_data_usage = {'x': [], 'y': []}
    for tower in df_filtered['tower_id'].unique()[:5]:
        tower_new = new_data[new_data['tower_id'] == tower].sort_values('timestamp')
        extend_data_usage['x'].append(tower_new['timestamp'].tolist())
        extend_data_usage['y'].append(tower_new['data_usage_mb'].tolist())
    
    # Prepare extend data for Chart 2 (Active Users)
    extend_users = {'x': [], 'y': []}
    for tower in df_filtered['tower_id'].unique()[:5]:
        tower_new = new_data[new_data['tower_id'] == tower].sort_values('timestamp')
        extend_users['x'].append(tower_new['timestamp'].tolist())
        extend_users['y'].append(tower_new['active_users'].tolist())
    
    return [
        (extend_data_usage, list(range(5)), 200),  # Keep last 200 points
        (extend_users, list(range(5)), 200),
        f"{total_users:,}",
        f"{total_data:.2f} GB",
        f"{avg_signal:.1f} dBm" if avg_signal > 0 else "N/A",
        f"{total_towers}",
        f"Live • {datetime.now().strftime('%H:%M:%S')}"
    ]

# ============================================================
# CALLBACK 3: Update Gauge (30s - smooth update)
# ============================================================
@app.callback(
    Output('chart-gauge', 'figure', allow_duplicate=True),
    [Input('interval-fast', 'n_intervals')],
    [State('region-filter', 'value'),
     State('chart-gauge', 'figure')],
    prevent_initial_call=True
)
def update_gauge(n, region, existing_fig):
    """Update gauge value smoothly"""
    
    if n == 0 or existing_fig is None:
        return existing_fig
    
    df = get_iot_data()
    if df.empty:
        return existing_fig
    
    df_filtered = df[df['region'] == region] if region else df
    avg_drop = df_filtered['call_drop_rate'].mean()
     # Convert to percentage if needed
    if avg_drop < 1:
        avg_drop = avg_drop * 100
    # Update only the value
    if existing_fig and 'data' in existing_fig and len(existing_fig['data']) > 0:
        existing_fig['data'][0]['value'] = avg_drop
        existing_fig['data'][0]['delta']['reference'] = 2.0
    
    return existing_fig

# ============================================================
# CALLBACK 4: Static Charts (60s)
# ============================================================
@app.callback(
    [Output('chart-pie', 'figure'),
     Output('chart-heatmap', 'figure'),
     Output('chart-bar', 'figure')],
    [Input('interval-slow', 'n_intervals')],
    [State('region-filter', 'value')]
)
def update_static_charts(n, region):
    """Update static charts every 60 seconds"""
    
    df = get_iot_data()
    
    if df.empty:
        empty = go.Figure()
        empty.add_annotation(text="No Data", font=dict(size=20, color="gray"), 
                           showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5)
        empty.update_layout(template="plotly_white", height=380, paper_bgcolor='white')
        return [empty, empty, empty]
    
    colors = ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b', '#fa709a']
    
    # Pie Chart
    user_dist = df.groupby("region")["active_users"].sum().reset_index()
    
    fig_pie = go.Figure(data=[go.Pie(
        labels=user_dist['region'],
        values=user_dist['active_users'],
        hole=0.55,
        marker=dict(colors=colors, line=dict(color='white', width=4)),
        textinfo='label+percent',
        textfont=dict(size=14, color='white', family='Arial Black'),
        hovertemplate='<b>%{label}</b><br>%{value:,} users<br>%{percent}<extra></extra>',
        pull=[0.08 if i == 0 else 0 for i in range(len(user_dist))]
    )])
    
    total = user_dist['active_users'].sum()
    fig_pie.add_annotation(
        text=f"<b>{total:,}</b><br><span style='font-size:14px'>Total</span>",
        x=0.5, y=0.5,
        font=dict(size=20, color='#2c3e50', family='Arial Black'),
        showarrow=False
    )
    
    fig_pie.update_layout(
        title=dict(text="🧭 User Distribution", 
                  font=dict(size=20, color='#2c3e50', family='Arial Black'), x=0.5, xanchor='center'),
        height=380,
        paper_bgcolor='white',
        margin=dict(l=30, r=30, t=80, b=30),
        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05),
        uirevision='pie'
    )
    
    # Heatmap
    df['minute'] = pd.to_datetime(df['timestamp']).dt.floor('5T')
    heatmap_data = df.groupby(['minute', 'region'])['active_users'].mean().reset_index()
    pivot = heatmap_data.pivot(index='region', columns='minute', values='active_users')
    
    fig_heat = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=[t.strftime('%H:%M') for t in pivot.columns],
        y=pivot.index,
        colorscale='Viridis',
        hovertemplate='<b>%{y}</b><br>%{x}<br>%{z:.0f} users<extra></extra>',
        colorbar=dict(title="Users", titleside='right')
    ))
    
    fig_heat.update_layout(
        title=dict(text="🌐 Network Activity Heatmap", 
                  font=dict(size=20, color='#2c3e50', family='Arial Black'), x=0.5, xanchor='center'),
        template="plotly_white",
        height=380,
        paper_bgcolor='white',
        margin=dict(l=100, r=100, t=80, b=100),
        xaxis=dict(title='Time', tickangle=-45),
        yaxis=dict(title='Region'),
        uirevision='heatmap'
    )
    
    # Bar Chart
    summary = df.groupby("region").agg({
        'data_usage_mb': 'mean',
        'active_users': 'mean',
        'call_drop_rate': 'mean'
    }).reset_index()
    
    fig_bar = go.Figure()
    
    fig_bar.add_trace(go.Bar(
        name='Data (MB)',
        x=summary['region'],
        y=summary['data_usage_mb'],
        marker_color='#667eea',
        text=summary['data_usage_mb'].round(0),
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>%{y:.1f} MB<extra></extra>'
    ))
    
    fig_bar.add_trace(go.Bar(
        name='Users',
        x=summary['region'],
        y=summary['active_users'],
        marker_color='#764ba2',
        text=summary['active_users'].round(0),
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>%{y:.0f} users<extra></extra>'
    ))
    
    fig_bar.add_trace(go.Bar(
        name='Drop %',
        x=summary['region'],
        y=summary['call_drop_rate'] * 10,
        marker_color='#f093fb',
        text=summary['call_drop_rate'].round(2),
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>%{text:.2f}%<extra></extra>'
    ))
    
    fig_bar.update_layout(
        title=dict(text="📊 Regional Performance", 
                  font=dict(size=20, color='#2c3e50', family='Arial Black'), x=0.5, xanchor='center'),
        barmode='group',
        template="plotly_white",
        height=380,
        paper_bgcolor='white',
        plot_bgcolor='rgba(250,250,250,0.5)',
        margin=dict(l=60, r=40, t=80, b=60),
        xaxis=dict(title='Region'),
        yaxis=dict(showgrid=True, gridcolor='#e8e8e8', title='Metrics'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        uirevision='bar'
    )
    
    return fig_pie, fig_heat, fig_bar

# ============================================================
# Run Server
# ============================================================
if __name__ == "__main__":
    print("🚀 Starting Dashboard...")
    print("✨ ZERO FLICKER - Charts extend smoothly")
    print("⚡ Time Series: 30s (extend mode)")
    print("📊 Static: 60s")
    print("🌐 http://localhost:8000")
    app.run_server(debug=True, port=8000, host='0.0.0.0')