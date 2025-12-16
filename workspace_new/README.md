# 📰 ContentPulse - Live Publishing Analytics Dashboard

A real-time publishing analytics platform built on Databricks, perfect for demonstrating to companies like Condé Nast, The New York Times, or any digital publishing organization.

## 🎯 Project Overview

ContentPulse tracks and visualizes real-time reader engagement across digital publications, including:
- **Geographic distribution** of readers
- **Device breakdown** (mobile, desktop, tablet)
- **Top performing articles** by engagement
- **Publication performance** metrics
- **Real-time event streams** (page views, comments, shares, subscriptions)
- **Revenue tracking** (ad impressions and estimated revenue)

---

## 📂 Project Structure

```
workspace_new/
├── ContentPulse_Data/
│   ├── contentpulse_config.ipynb              # Configuration & setup
│   ├── ContentPulse_DataGeneration.ipynb      # Streaming data generator
│   ├── ContentPulse_DataIngestion.ipynb       # Delta Lake ingestion
│   └── ContentPulse_LakebaseSetup.ipynb       # PostgreSQL sync setup
│
└── contentpulse_apps/
    ├── app.py                                  # Dash dashboard application
    ├── app.yaml                                # Databricks Apps config
    ├── requirements.txt                        # Python dependencies
    └── deploy_contentpulse.sh                  # Deployment script
```

---

## 🚀 Quick Start Guide

### Step 1: Setup Resources (One-time)

Run these notebooks in **Databricks** in order:

```bash
1. ContentPulse_Data/contentpulse_config.ipynb
   └── Creates catalog, schema, volume, and Delta table

2. ContentPulse_Data/ContentPulse_LakebaseSetup.ipynb
   └── Sets up PostgreSQL sync (reuses existing Lakebase instance)
```

### Step 2: Start Data Pipeline

```bash
3. ContentPulse_Data/ContentPulse_DataGeneration.ipynb
   └── Generates publishing events every 5 seconds (let it run)

4. ContentPulse_Data/ContentPulse_DataIngestion.ipynb
   └── Streams data from volume to Delta table (let it run)
```

### Step 3: Deploy Dashboard

```bash
cd workspace_new/contentpulse_apps
./deploy_contentpulse.sh
```

---

## 📊 Dashboard Features

### Key Metrics (Refreshes every 10 seconds)
- **Active Readers** - Unique readers currently engaging
- **Page Views** - Total page view events
- **Engagement Rate** - Percentage of interactive events
- **Total Revenue** - Sum of estimated ad revenue

### Visual Analytics

1. **Geographic Heat Map** (30s refresh)
   - Shows reader distribution across global cities
   - Bubble size indicates reader volume

2. **Device Breakdown** (30s refresh)
   - Pie chart of mobile vs desktop vs tablet usage

3. **Top Articles** (1 min refresh)
   - Horizontal bar chart of most-viewed articles
   - Updates to show trending content

4. **Publications Performance** (1 min refresh)
   - Dual-axis chart showing events and revenue by publication
   - Compare performance across different magazines/sites

5. **Real-Time Engagement** (10s refresh)
   - Time series showing event types over last 5 minutes
   - Tracks page views, comments, shares, subscriptions

---

## 🎨 Design Theme

**Publishing-Focused Aesthetic**
- Elegant serif fonts (Playfair Display) for headers
- Color palette inspired by premium publishing brands
- Professional gradient cards
- Smooth animations and transitions
- Clean, editorial-style layout

**Color Scheme**
- Primary: `#e94560` (Editorial Red)
- Secondary: `#0f3460` (Deep Navy)
- Accent: `#533483` (Royal Purple)
- Background: Soft gradients for premium feel

---

## 📈 Sample Data Generated

### Event Types (Weighted Distribution)
- **Page Views** (60%) - Article reading events
- **Scroll** (20%) - Scroll depth tracking
- **Comments** (10%) - User comments
- **Shares** (5%) - Social media shares
- **Subscriptions** (5%) - New subscribers

### Data Schema
```json
{
  "event_id": "evt_abc123",
  "timestamp": "2024-12-16T10:23:45Z",
  "event_type": "page_view",
  "reader_id": "reader_45123",
  "article_id": "art_7894",
  "article_title": "10 Best Winter Fashion Trends 2024",
  "category": "Fashion",
  "publication": "Vogue",
  "device_type": "mobile",
  "country": "USA",
  "city": "New York",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "time_on_page_seconds": 145,
  "scroll_depth_percent": 75,
  "num_comments": 0,
  "num_shares": 0,
  "ad_impressions": 4,
  "estimated_ad_revenue": 0.24,
  "is_subscriber": true,
  "subscription_tier": "premium"
}
```

### Content Categories
Fashion • Beauty • Entertainment • Technology • Travel • Food • Lifestyle • News • Sports • Business

### Publications (Condé Nast-style)
Vogue • GQ • Vanity Fair • Wired • Bon Appétit • The New Yorker • Architectural Digest • Glamour • Allure • Self

### Global Cities
New York • Los Angeles • London • Paris • Tokyo • Sydney • Toronto • Berlin • Mumbai • São Paulo

---

## 🔧 Technical Architecture

### Data Flow
```
1. Data Generation (Every 5s)
   └── JSON files → /Volumes/kunal/publishing/publishing_data/CONTENT_EVENTS/

2. Spark Streaming (Every 10s)
   └── Auto Loader → Delta Table (kunal.publishing.content_engagement_events)

3. Lakebase Sync (Continuous)
   └── Change Data Feed → PostgreSQL (kunal.publishing.content_engagement_synced)

4. Dashboard (Multiple refresh rates)
   └── PostgreSQL → Dash App → Real-time charts
```

### Key Technologies
- **Databricks**: Unified data platform
- **Delta Lake**: ACID transactions, time travel
- **Lakebase**: Managed PostgreSQL for low-latency queries
- **Spark Structured Streaming**: Real-time data processing
- **Dash (Plotly)**: Interactive Python dashboards
- **Auto Loader**: Incremental file ingestion

### Security
- **OAuth Token Rotation**: Automatic credential refresh
- **SSL/TLS**: Encrypted connections
- **Connection Pooling**: Efficient resource usage
- **Service Principal**: Databricks Apps authentication

---

## 🎯 Demo Scenarios

### Scenario 1: "Breaking News Spike"
Run the data generator with increased frequency to simulate viral content:
- Watch geographic map light up with new readers
- See engagement rate climb in real-time
- Track revenue increase from ad impressions

### Scenario 2: "Global Audience"
The data generator includes 10 global cities, showing:
- International reach of content
- Time-zone based reading patterns
- Geographic diversity of readership

### Scenario 3: "Multi-Platform Engagement"
Device breakdown shows:
- Mobile-first reading behavior (60%)
- Desktop for long-form content (30%)
- Tablet for premium experiences (10%)

---

## 📊 KPIs Demonstrated

**Audience Metrics**
- Unique readers (deduplicated)
- Geographic reach
- Device preferences

**Content Performance**
- Article engagement
- Time on page
- Scroll depth

**Business Metrics**
- Ad impressions
- Estimated revenue
- Subscription conversions

**Publication Analytics**
- Performance by magazine/site
- Category trends
- Event distribution

---

## 🚀 Deployment Commands

### Check App Status
```bash
databricks apps get contentpulse-dashboard
```

### View Logs
```bash
databricks apps logs contentpulse-dashboard
```

### Restart App
```bash
databricks apps restart contentpulse-dashboard
```

### Stop Data Generation
In the Databricks notebook, click "Stop" button or:
```python
# Stop streaming query
query.stop()
```

---

## 🌟 Why This Demo Works

✅ **Universal Appeal** - Every publisher cares about reader engagement
✅ **Visual Impact** - Geographic maps and live counters are impressive
✅ **Real-time Wow Factor** - Numbers updating every 10 seconds
✅ **Business Relevance** - Shows clear ROI (revenue, subscriptions)
✅ **Scalable Story** - Works for small blogs to enterprise publishers
✅ **Modern Tech Stack** - Demonstrates cloud-native architecture
✅ **Production Ready** - Uses best practices (OAuth, pooling, CDC)

---

## 📝 Notes

- **Reuses Lakebase Instance**: Uses the same `kunal-gaurav-lakebase-instance` as the telecom project
- **Separate Catalog**: Creates `pg_contentpulse_kunal-gaurav` for isolation
- **No Data Conflicts**: Completely independent from telecom IoT data
- **Easy Cleanup**: All resources are in `kunal.publishing` schema

---

## 🎨 Customization

### Change Publishing Brands
Edit `ContentPulse_DataGeneration.ipynb`:
```python
PUBLICATIONS = [
    "Your Brand 1", "Your Brand 2", ...
]
```

### Adjust Refresh Rates
Edit `contentpulse_apps/app.py`:
```python
dcc.Interval(id='interval-fast', interval=10*1000)  # Change 10 to desired seconds
```

### Modify Color Theme
Edit CSS in `contentpulse_apps/app.py`:
```css
background: linear-gradient(135deg, #e94560 0%, #0f3460 100%);
```

---

## 🏆 Perfect For

- **Job Interviews** at publishing companies
- **Client Demos** for media/publishing sector
- **Portfolio Projects** showcasing end-to-end data pipelines
- **Learning Databricks** with a realistic, engaging use case
- **Conference Talks** on real-time analytics

---

Built with ❤️ for publishers everywhere

