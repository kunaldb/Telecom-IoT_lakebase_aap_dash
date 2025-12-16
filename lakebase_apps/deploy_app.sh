#!/bin/bash

# Simple working deployment script

set -e
export DATABRICKS_CONFIG_PROFILE=DEFAULT  
APP_NAME="lakebase-postgress-dash"
WORKSPACE_PATH="/Workspace/Users/kunal.gaurav@databricks.com/conde/01_demo/$APP_NAME"

echo "======================================"
echo "📦 Telecom IoT Dashboard Deployment"
echo "======================================"
echo "Workspace Path: $WORKSPACE_PATH"
echo "======================================"
echo ""

# Step 1: Upload files
echo "📤 Uploading files..."
databricks sync ./lakebase_apps "$WORKSPACE_PATH"
echo "✅ Files uploaded"

# Step 2: Check if app exists and handle accordingly
echo ""
echo "🔍 Checking app status..."
if databricks apps get "$APP_NAME" &>/dev/null; then
    echo "⚠️  App exists. Updating..."
    databricks apps update "$APP_NAME" --description "Telecom IoT Dashboard"
else
    echo "🔨 Creating new app..."
    databricks apps create "$APP_NAME" --description "Telecom IoT Dashboard"
fi
databricks apps deploy "$APP_NAME" --source-code-path "$WORKSPACE_PATH"
echo ""
echo "======================================"
echo "✅ Deployment completed!"
echo "======================================"
echo "📂 Files location: $WORKSPACE_PATH"
echo ""
echo "Next steps:"
echo "  1. Go to Databricks workspace: $WORKSPACE_PATH"
echo "  2. Manually create/configure the app from the UI"
echo "  3. Or run: databricks apps start $APP_NAME"