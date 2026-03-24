# Google Sheets + Drive — Service Account Setup

> Follow these steps once. After setup, all scripts (`update_sheets.py`, `upload_to_drive.py`) will authenticate automatically.

## Step 1: Create a Google Cloud Project

1. Go to [console.cloud.google.com](https://console.cloud.google.com/)
2. Click **Select a project** → **New Project**
3. Name: `TeenCare-Pipeline` → Click **Create**
4. Make sure this project is selected in the top bar

## Step 2: Enable APIs

1. Go to **APIs & Services → Library** (left sidebar)
2. Search and **Enable** each:
   - `Google Sheets API` → Click **Enable**
   - `Google Drive API` → Click **Enable**

## Step 3: Create a Service Account

1. Go to **APIs & Services → Credentials** (left sidebar)
2. Click **+ CREATE CREDENTIALS** → **Service account**
3. Service account name: `teencare-pipeline`
4. Click **Create and Continue**
5. Role: **Editor** → Click **Continue** → **Done**

## Step 4: Download the Key File

1. In the **Credentials** page, click on the service account you just created (`teencare-pipeline@...`)
2. Go to **Keys** tab
3. Click **Add Key** → **Create new key**
4. Choose **JSON** → Click **Create**
5. A `.json` file downloads — this is your credentials file

## Step 5: Place the Key in the Project

```bash
# Move the downloaded file to the project root and rename it
mv ~/Downloads/teencare-pipeline-*.json \
   /Users/kaushiksayeemohan/Desktop/Local_Workspace/02_BuLoop/Auto_Video_Pipeline_Filipino/service_account.json
```

> ⚠️ This file is already in `.gitignore` — it won't be committed.

## Step 6: Share the Google Sheet with the Service Account

1. Open the downloaded `service_account.json` — find the `"client_email"` field
   - It looks like: `teencare-pipeline@teencare-pipeline.iam.gserviceaccount.com`
2. Open the Google Sheet: [Sheet Link](https://docs.google.com/spreadsheets/d/13EWGhUcOxtF_jZ-KlO9vXsMbqIR8rKVMoe9CFgC6hnM)
3. Click **Share** → paste the service account email → **Editor** role → **Send**

## Step 7: Share the Google Drive Folder with the Service Account

1. Open the Drive folder: [Drive Link](https://drive.google.com/drive/folders/1QjGFlsJQKISipQqaQjsBNkc6Z1bph3HU)
2. Click **Share** → paste the same service account email → **Editor** role → **Send**

## Step 8: Test

```bash
# Test Google Sheets connection
python3 execution/update_sheets.py --test

# Test Google Drive connection
python3 execution/upload_to_drive.py --test
```

Expected output:
```
✓ Authenticated via service_account.json
✓ Opened sheet: [Sheet Name]
✓ TEST — Google Sheets connection verified.
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `FileNotFoundError: service_account.json` | Make sure the file is in the project root, not in a subfolder |
| `PermissionError` on sheet | You forgot Step 6 — share the sheet with the service account email |
| `PermissionError` on Drive | You forgot Step 7 — share the folder with the service account email |
| `HttpError 403` | The API isn't enabled — go back to Step 2 |
