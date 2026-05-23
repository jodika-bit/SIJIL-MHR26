
import os
import sqlite3
import re
import io
import zipfile
from datetime import datetime
from pathlib import Path
from email.message import EmailMessage
import smtplib

import pandas as pd
import streamlit as st

from certificate_generator import generate_certificate_pdf

APP_TITLE = "NADI MADANI: Jantung Sihat [MyHeartRisk] Certificate Portal"
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
GENERATED_DIR = BASE_DIR / "generated"
DB_PATH = DATA_DIR / "participants.sqlite3"

DATA_DIR.mkdir(exist_ok=True)
GENERATED_DIR.mkdir(exist_ok=True)

TRAINING_ACCESS_CODE = os.getenv("TRAINING_ACCESS_CODE", "NADI2026MHR")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change-me")
PASS_MARK = int(os.getenv("PASS_MARK", "80"))

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USER)
ENABLE_EMAIL = os.getenv("ENABLE_EMAIL", "false").lower() == "true"


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            certificate_id TEXT UNIQUE,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            participant_id TEXT,
            nadi_centre TEXT,
            state TEXT,
            score INTEGER,
            pass_status TEXT,
            consent INTEGER,
            completed_training INTEGER,
            pdf_path TEXT,
            email_status TEXT,
            created_at TEXT
        )
        """)
        conn.commit()


def get_next_certificate_id():
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT certificate_id FROM participants ORDER BY id DESC LIMIT 1").fetchone()

    if not row or not row[0]:
        return "MHR0001"

    match = re.search(r"MHR(\d+)", row[0])
    if not match:
        return "MHR0001"

    next_num = int(match.group(1)) + 1
    return f"MHR{next_num:04d}"


def clean_filename(text: str):
    text = re.sub(r"[^A-Za-z0-9_\- ]+", "", text).strip()
    text = re.sub(r"\s+", "_", text)
    return text[:80] if text else "participant"


def save_participant(data):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
        INSERT INTO participants (
            certificate_id, full_name, email, phone, participant_id, nadi_centre,
            state, score, pass_status, consent, completed_training,
            pdf_path, email_status, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["certificate_id"],
            data["full_name"],
            data["email"],
            data["phone"],
            data["participant_id"],
            data["nadi_centre"],
            data["state"],
            data["score"],
            data["pass_status"],
            int(data["consent"]),
            int(data["completed_training"]),
            data["pdf_path"],
            data["email_status"],
            data["created_at"],
        ))
        conn.commit()


def load_participants():
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query("SELECT * FROM participants ORDER BY id DESC", conn)


def send_certificate_email(to_email, full_name, certificate_id, pdf_path):
    if not ENABLE_EMAIL:
        return "Email disabled"

    if not SMTP_USER or not SMTP_PASSWORD:
        return "Email not configured"

    subject = "Sijil Penyertaan NADI MADANI: Jantung Sihat [MyHeartRisk]"
    body = f"""Assalamualaikum dan salam sejahtera,

Tahniah, {full_name}.

Dilampirkan sijil penyertaan anda bagi program NADI MADANI: Jantung Sihat [MyHeartRisk] - Train-the-Trainer (ToT).

Sijil ini diberikan kerana anda telah menghadiri latihan atas talian pada 20 Mei 2026 dan telah melengkapkan assessment serta test yang diperlukan.

Certificate ID: {certificate_id}

Sila simpan sijil ini untuk rujukan dan verifikasi program.

Terima kasih.

Sekretariat
NADI MADANI: Jantung Sihat [MyHeartRisk]
CARE Institute, Universiti Teknologi MARA
"""

    msg = EmailMessage()
    msg["From"] = EMAIL_FROM
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    with open(pdf_path, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="pdf",
            filename=Path(pdf_path).name
        )

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USER, SMTP_PASSWORD)
            smtp.send_message(msg)
        return "Sent"
    except Exception as e:
        return f"Email failed: {e}"


def participant_page():
    st.subheader("Generate Certificate")
    st.info("Isi maklumat peserta. Sijil PDF akan dijana selepas peserta disahkan telah selesai latihan, assessment dan test.")

    with st.form("participant_form"):
        access_code = st.text_input("Training access code *", type="password")
        full_name = st.text_input("Full name as it should appear on certificate *")
        email = st.text_input("Email address *")
        phone = st.text_input("Phone number *")
        participant_id = st.text_input("NADI staff ID / participant ID, if available")
        nadi_centre = st.text_input("NADI centre name *")
        state = st.text_input("State *")
        score = st.number_input("Assessment / test score (%) *", min_value=0, max_value=100, value=80, step=1)

        completed_training = st.checkbox("I confirm that I have completed the required online training, assessment and test.")
        consent = st.checkbox("I consent for these details to be stored by the programme admin for certificate verification and reporting.")
        submit = st.form_submit_button("Generate my certificate")

    if not submit:
        return

    errors = []

    if TRAINING_ACCESS_CODE and access_code.strip() != TRAINING_ACCESS_CODE:
        errors.append("Invalid training access code.")
    if not full_name.strip():
        errors.append("Full name is required.")
    if not email.strip() or "@" not in email:
        errors.append("Valid email address is required.")
    if not phone.strip():
        errors.append("Phone number is required.")
    if not nadi_centre.strip():
        errors.append("NADI centre name is required.")
    if not state.strip():
        errors.append("State is required.")
    if not completed_training:
        errors.append("Please confirm completion of training, assessment and test.")
    if not consent:
        errors.append("Consent is required.")
    if score < PASS_MARK:
        errors.append(f"Score must be at least {PASS_MARK}% to generate certificate.")

    if errors:
        st.error("Please correct the following before generating the certificate:")
        for e in errors:
            st.write(f"- {e}")
        return

    certificate_id = get_next_certificate_id()
    safe_name = clean_filename(full_name)
    pdf_filename = f"{certificate_id}_{safe_name}.pdf"
    pdf_path = GENERATED_DIR / pdf_filename

    generate_certificate_pdf(
        output_path=str(pdf_path),
        participant_name=full_name.strip().upper(),
        certificate_id=certificate_id,
        trainer_name="JOHANES DEDI KANCHAU",
    )

    email_status = send_certificate_email(email.strip(), full_name.strip(), certificate_id, str(pdf_path))

    save_participant({
        "certificate_id": certificate_id,
        "full_name": full_name.strip(),
        "email": email.strip(),
        "phone": phone.strip(),
        "participant_id": participant_id.strip(),
        "nadi_centre": nadi_centre.strip(),
        "state": state.strip(),
        "score": int(score),
        "pass_status": "PASS",
        "consent": consent,
        "completed_training": completed_training,
        "pdf_path": str(pdf_path),
        "email_status": email_status,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    })

    st.success(f"Certificate generated successfully. Certificate ID: {certificate_id}")

    with open(pdf_path, "rb") as f:
        st.download_button(
            label="Download PDF Certificate",
            data=f,
            file_name=pdf_filename,
            mime="application/pdf"
        )

    if ENABLE_EMAIL:
        st.write(f"Email status: {email_status}")
    else:
        st.warning("Email sending is currently disabled. The participant can download the PDF from this page.")


def admin_page():
    st.subheader("Admin Panel")
    password = st.text_input("Admin password", type="password")

    if password != ADMIN_PASSWORD:
        st.warning("Enter admin password to view participant data.")
        return

    df = load_participants()
    st.write(f"Total records: {len(df)}")

    if df.empty:
        st.info("No participant records yet.")
        return

    state_filter = st.selectbox("Filter by state", ["All"] + sorted(df["state"].dropna().unique().tolist()))
    df_view = df if state_filter == "All" else df[df["state"] == state_filter]

    st.dataframe(df_view, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download participant data CSV",
        data=csv,
        file_name="nadi_mhr_certificate_participants.csv",
        mime="text/csv"
    )

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as z:
        for path in GENERATED_DIR.glob("*.pdf"):
            z.write(path, arcname=path.name)
    zip_buffer.seek(0)

    st.download_button(
        "Download all generated certificates ZIP",
        data=zip_buffer,
        file_name="nadi_mhr_generated_certificates.zip",
        mime="application/zip"
    )


def setup_page():
    st.subheader("Setup Guide")
    st.markdown("""
### Cara run dalam VS Code

```powershell
cd nadi_mhr_certificate_app
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m streamlit run app.py
```

### Tetapkan access code dan admin password

```powershell
$env:TRAINING_ACCESS_CODE="NADI2026MHR"
$env:ADMIN_PASSWORD="your-secure-admin-password"
python -m streamlit run app.py
```

### Aktifkan penghantaran email Gmail

Gunakan Gmail App Password, bukan password Gmail biasa.

```powershell
$env:ENABLE_EMAIL="true"
$env:SMTP_USER="yourgmail@gmail.com"
$env:SMTP_PASSWORD="your-gmail-app-password"
$env:EMAIL_FROM="yourgmail@gmail.com"
python -m streamlit run app.py
```

### Letakkan gambar/logo dalam folder assets

```text
assets/
├── uitm_care_logo.png
├── myheartrisk_icon.png
├── myheartrisk_gold_seal.png
├── signature_sazzli_transparent.png
└── signature_johanes_transparent.png   # optional
```
""")


def main():
    st.set_page_config(page_title=APP_TITLE, page_icon="❤️", layout="wide")
    init_db()
    st.title(APP_TITLE)

    page = st.sidebar.radio("Menu", ["Participant Certificate Form", "Admin Panel", "Setup Guide"])

    if page == "Participant Certificate Form":
        participant_page()
    elif page == "Admin Panel":
        admin_page()
    else:
        setup_page()


if __name__ == "__main__":
    main()
