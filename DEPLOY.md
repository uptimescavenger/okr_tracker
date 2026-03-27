# OKR & KPI Tracker — Deployment Guide

## 1. Google Cloud Setup

### Create a Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable **Google Sheets API** and **Google Drive API**:
   - APIs & Services → Library → search each, click Enable
4. Create a service account:
   - APIs & Services → Credentials → Create Credentials → Service Account
   - Name it (e.g. `okr-tracker`)
   - Click Create and Continue (skip optional steps)
5. Create a key:
   - Click the service account → Keys tab → Add Key → Create new key → JSON
   - Save the downloaded JSON file as `service_account.json`

### Prepare the Google Sheet

1. Create a new Google Sheet
2. Copy the spreadsheet ID from the URL:
   `https://docs.google.com/spreadsheets/d/<THIS_PART>/edit`
3. Share the sheet with the service account email
   (found in `client_email` of your JSON key) — give **Editor** access
4. The app auto-creates tabs on first run; no manual setup needed

## 2. Local Development

```bash
# Clone and enter the repo
cd "OKR Tracker"

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure secrets
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml: paste your spreadsheet ID and the full JSON key contents

# Run
streamlit run app.py
```

## 3. GitHub Repository Setup

```bash
git init
git add .
git commit -m "Initial commit: OKR & KPI Tracker"
git remote add origin https://github.com/YOUR_USERNAME/okr-tracker.git
git push -u origin main
```

## 4. Streamlit Cloud Deployment

1. Go to [share.streamlit.io](https://share.streamlit.io/)
2. Click **New app** → connect your GitHub repo
3. Set:
   - **Repository:** `YOUR_USERNAME/okr-tracker`
   - **Branch:** `main`
   - **Main file path:** `app.py`
4. Click **Advanced settings** → **Secrets**
5. Paste the contents of your `secrets.toml`:

```toml
SPREADSHEET_ID = "your-spreadsheet-id"

[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "...@...iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
```

6. Click **Deploy**

## 5. Google Sheet Structure (auto-created)

The app creates these tabs automatically on first access:

| Tab name | Columns |
|---|---|
| `OKRs 2026-Q1` | id, title, description, owner, target_date, progress, last_updated |
| `KPIs 2026-Q1` | id, name, owner, current_value, target_value, unit, last_updated |
| `KPI History 2026-Q1` | kpi_id, date, value |
| `Notes` | parent_type, parent_id, timestamp, author, text |

New quarter tabs are created automatically when selected.

## File Structure

```
OKR Tracker/
├── .gitignore
├── .streamlit/
│   ├── config.toml          # Theme and server settings
│   └── secrets.toml.example  # Template for credentials
├── app.py                    # Main entry point
├── config.py                 # Settings, quarter helpers, column schemas
├── sheets.py                 # Google Sheets read/write operations
├── data.py                   # Data processing and aggregation
├── ui.py                     # Streamlit UI components
├── requirements.txt          # Python dependencies
└── DEPLOY.md                 # This file
```
