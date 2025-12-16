#!/bin/bash

# ContentPulse Dashboard Deployment Script
# This script deploys the ContentPulse app to Databricks Apps

set -e  # Exit on error

echo "======================================"
echo "📰 ContentPulse Dashboard Deployment"
echo "======================================"

# Set Databricks profile
export DATABRICKS_CONFIG_PROFILE=DEFAULT

# Configuration
APP_NAME="contentpulse-dashboard"
WORKSPACE_PATH="/Workspace/Users/kunal.gaurav@databricks.com/conde/01_demo/${APP_NAME}"
# Get script directory and construct path to contentpulse_apps
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOCAL_PATH="${SCRIPT_DIR}/contentpulse_apps"

echo "📁 App Name: ${APP_NAME}"
echo "📂 Local Path: ${LOCAL_PATH}"
echo "☁️  Workspace Path: ${WORKSPACE_PATH}"
echo "======================================"
echo ""

# Step 1: Upload files to workspace
echo "📤 Uploading files..."
databricks sync "${LOCAL_PATH}" "${WORKSPACE_PATH}"
echo "✅ Files uploaded"

# Step 2: Check if app exists and handle accordingly
echo ""
echo "🔍 Checking app status..."
if databricks apps get "${APP_NAME}" &>/dev/null; then
    echo "⚠️  App exists. Updating..."
    databricks apps update "${APP_NAME}" --description "ContentPulse - Live Publishing Analytics Dashboard"
else
    echo "🔨 Creating new app..."
    databricks apps create "${APP_NAME}" --description "ContentPulse - Live Publishing Analytics Dashboard"
fi

# Step 3: Deploy the app
databricks apps deploy "${APP_NAME}" --source-code-path "${WORKSPACE_PATH}"

echo ""
echo "======================================"
echo "✅ Deployment completed!"
echo "======================================"
echo "📂 Files location: ${WORKSPACE_PATH}"
echo ""
echo "Next steps:"
echo "  1. Go to Databricks workspace: ${WORKSPACE_PATH}"
echo "  2. View app status: databricks apps get ${APP_NAME}"
echo "  3. View app logs: databricks apps logs ${APP_NAME}"
echo ""
echo "🌐 Access your dashboard at the app URL provided by Databricks"

