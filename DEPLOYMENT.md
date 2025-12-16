# 🚀 Databricks App Deployment Guide

This guide explains how to deploy your Telecom IoT Dashboard as a Databricks App using Databricks Asset Bundles (DABs).

---

## 📋 Prerequisites

### 1. Install Databricks CLI

```bash
# Using pip
pip install databricks-cli

# Or using Homebrew (macOS)
brew tap databricks/tap
brew install databricks
```

### 2. Verify Installation

```bash
databricks --version
```

---

## 🔐 Authentication Setup

### Option 1: OAuth (Recommended for Development)

```bash
databricks auth login --host https://e2-demo-field-eng.cloud.databricks.com
```

This will open a browser window for authentication.

### Option 2: Personal Access Token

1. Go to your Databricks workspace
2. Click **User Settings** → **Developer** → **Access Tokens**
3. Generate a new token
4. Run:

```bash
databricks configure --token
```

Enter your:
- **Host**: `https://e2-demo-field-eng.cloud.databricks.com`
- **Token**: (paste your token)

---

## 📦 Project Structure

```
Telecom IoT_lakebase_aap_dash/
├── databricks.yml          # Main bundle configuration
├── lakebase_apps/
│   ├── app.py             # Dash application
│   ├── app.yml            # App configuration
│   └── requirements.txt   # Python dependencies
├── Data/
│   ├── data_store_variables.ipynb
│   ├── Data_generation.ipynb
│   ├── Data_ingestion.ipynb
│   └── Lakebase_setup.ipynb
└── DEPLOYMENT.md          # This file
```

---

## 🎯 Deployment Steps

### Step 1: Validate Bundle Configuration

```bash
cd "/Users/kunal.gaurav/Documents/Cursor/Telecom IoT_lakebase_aap_dash"
databricks bundle validate
```

### Step 2: Deploy to Development Environment

```bash
# Deploy to dev (default target)
databricks bundle deploy

# Or explicitly specify dev
databricks bundle deploy -t dev
```

This will:
- ✅ Upload your application files to Databricks
- ✅ Create the Databricks App resource
- ✅ Configure environment variables
- ✅ Set up permissions

### Step 3: Start the Application

```bash
# Start the app
databricks apps start telecom-iot-dashboard-dev

# Check app status
databricks apps get telecom-iot-dashboard-dev

# View app logs
databricks apps logs telecom-iot-dashboard-dev
```

### Step 4: Access Your Dashboard

Once deployed, you can access your dashboard at:
```
https://e2-demo-field-eng.cloud.databricks.com/apps/telecom-iot-dashboard-dev
```

---

## 🔄 Update Deployment

When you make changes to your code:

```bash
# Redeploy the updated code
databricks bundle deploy

# Restart the app to pick up changes
databricks apps restart telecom-iot-dashboard-dev
```

---

## 🌐 Deploy to Production

```bash
# Deploy to production
databricks bundle deploy -t prod

# Start production app
databricks apps start telecom-iot-dashboard-prod
```

Access at:
```
https://e2-demo-field-eng.cloud.databricks.com/apps/telecom-iot-dashboard-prod
```

---

## 🛠️ Troubleshooting

### View App Logs

```bash
# Stream logs in real-time
databricks apps logs telecom-iot-dashboard-dev --follow

# View last 100 lines
databricks apps logs telecom-iot-dashboard-dev --tail 100
```

### Check App Status

```bash
databricks apps get telecom-iot-dashboard-dev
```

### Stop the App

```bash
databricks apps stop telecom-iot-dashboard-dev
```

### Delete the App

```bash
databricks apps delete telecom-iot-dashboard-dev
```

### Destroy Bundle Resources

```bash
# Remove all deployed resources
databricks bundle destroy -t dev
```

---

## 📝 Environment Variables

The following environment variables are configured in `databricks.yml`:

| Variable | Value | Description |
|----------|-------|-------------|
| `PGDATABASE` | `pg_lakebase_kunal-gaurav` | PostgreSQL database name |
| `PGUSER` | `kunal.gaurav@databricks.com` | Database user |
| `PGHOST` | `instance-f60d62f1...` | Lakebase instance host |
| `PGPORT` | `5432` | PostgreSQL port |
| `PGSSLMODE` | `require` | SSL mode (required) |
| `SCHEMA_NAME` | `kunal.Telcom` | Unity Catalog schema |
| `TABLE_NAME` | `iot_data_synced` | Synced table name |

To update these values, edit `databricks.yml` and redeploy.

---

## 🔍 Useful Commands

```bash
# List all bundles
databricks bundle list

# Validate configuration
databricks bundle validate

# View deployment summary
databricks bundle summary

# Run notebooks in the bundle
databricks bundle run -t dev

# List all deployed apps
databricks apps list

# Open app in browser
open https://e2-demo-field-eng.cloud.databricks.com/apps/telecom-iot-dashboard-dev
```

---

## 🎨 Custom Configuration

### Update Variables

Edit `databricks.yml` to change configuration:

```yaml
variables:
  catalog_name:
    default: kunal  # Change this
  
  schema_name:
    default: Telcom  # Change this
```

Then redeploy:
```bash
databricks bundle deploy
```

### Override Variables at Deploy Time

```bash
databricks bundle deploy --var="catalog_name=my_catalog"
```

---

## 📚 Additional Resources

- [Databricks Apps Documentation](https://docs.databricks.com/en/dev-tools/databricks-apps/index.html)
- [Databricks Asset Bundles](https://docs.databricks.com/dev-tools/bundles/index.html)
- [Databricks CLI Reference](https://docs.databricks.com/dev-tools/cli/index.html)

---

## ✅ Quick Deploy Checklist

- [ ] Install Databricks CLI
- [ ] Authenticate with `databricks auth login`
- [ ] Validate bundle with `databricks bundle validate`
- [ ] Deploy with `databricks bundle deploy`
- [ ] Start app with `databricks apps start telecom-iot-dashboard-dev`
- [ ] Access dashboard in browser
- [ ] Check logs with `databricks apps logs`

---

## 🎉 Success!

Your Telecom IoT Dashboard is now running as a Databricks App! 🚀

For questions or issues, check the logs or contact your Databricks administrator.




