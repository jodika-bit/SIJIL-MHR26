# NADI MyHeartRisk Certificate App

This Streamlit app allows NADI participants to enter details, generate certificate PDF, store data, and optionally email the certificate.

## Run in VS Code

```powershell
cd NADI_MHR_VSCode_Certificate_App
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m streamlit run app.py
```

## Required assets

Put PNG files in the assets folder:

- uitm_care_logo.png
- myheartrisk_icon.png
- myheartrisk_gold_seal.png
- signature_sazzli_transparent.png
- signature_johanes_transparent.png

## Setup

```powershell
$env:TRAINING_ACCESS_CODE="NADI2026MHR"
$env:ADMIN_PASSWORD="your-secure-password"
python -m streamlit run app.py
```

## Enable Gmail email sending

Use Gmail App Password.

```powershell
$env:ENABLE_EMAIL="true"
$env:SMTP_USER="yourgmail@gmail.com"
$env:SMTP_PASSWORD="your-gmail-app-password"
$env:EMAIL_FROM="yourgmail@gmail.com"
python -m streamlit run app.py
```


Updated certificate layout: A4 landscape, two signatures, dynamic participant name and certificate ID (MHR0001 onwards).
