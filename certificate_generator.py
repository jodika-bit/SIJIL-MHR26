
from pathlib import Path
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent
ASSET_DIR = BASE_DIR / "assets"
PAGE_WIDTH, PAGE_HEIGHT = landscape(A4)


def asset_path(filename):
    p = ASSET_DIR / filename
    return str(p) if p.exists() else None


def draw_image_preserve_aspect(c, image_path, x, y, w, h):
    if not image_path or not Path(image_path).exists():
        return

    try:
        img = Image.open(image_path)
        iw, ih = img.size
        aspect = iw / ih
        box_aspect = w / h

        if aspect > box_aspect:
            new_w = w
            new_h = w / aspect
        else:
            new_h = h
            new_w = h * aspect

        new_x = x + (w - new_w) / 2
        new_y = y + (h - new_h) / 2

        c.drawImage(ImageReader(image_path), new_x, new_y, width=new_w, height=new_h, preserveAspectRatio=True, mask="auto")
    except Exception:
        return


def centered_text(c, text, y, font="Helvetica", size=10, color=colors.HexColor("#1d2636")):
    c.setFillColor(color)
    c.setFont(font, size)
    c.drawCentredString(PAGE_WIDTH / 2, y, text)


def generate_certificate_pdf(output_path, participant_name, certificate_id, trainer_name="JOHANES DEDI KANCHAU"):
    c = canvas.Canvas(output_path, pagesize=landscape(A4))

    c.setFillColor(colors.white)
    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)

    gold = colors.HexColor("#b88a00")
    c.setStrokeColor(gold)
    c.setLineWidth(2.0)
    c.rect(8, 8, PAGE_WIDTH - 16, PAGE_HEIGHT - 16, fill=0, stroke=1)
    c.setLineWidth(0.8)
    c.rect(13, 13, PAGE_WIDTH - 26, PAGE_HEIGHT - 26, fill=0, stroke=1)

    draw_image_preserve_aspect(c, asset_path("uitm_care_logo.png"), x=55, y=PAGE_HEIGHT - 105, w=300, h=65)
    draw_image_preserve_aspect(c, asset_path("myheartrisk_icon.png"), x=PAGE_WIDTH - 170, y=PAGE_HEIGHT - 105, w=90, h=65)

    c.setFillColor(colors.HexColor("#b58a00"))
    c.rect(55, PAGE_HEIGHT - 128, PAGE_WIDTH - 110, 14, fill=1, stroke=0)

    y = PAGE_HEIGHT - 165
    centered_text(c, "CERTIFICATE OF COMPLETION", y, font="Times-Bold", size=20, color=colors.HexColor("#10243a"))

    y -= 26
    centered_text(c, "NADI MADANI: Jantung Sihat [MyHeartRisk] - Train-the-Trainer (ToT)", y, font="Helvetica-Bold", size=11, color=colors.HexColor("#4f5969"))

    y -= 21
    centered_text(c, "This certificate is awarded to", y, font="Helvetica", size=9, color=colors.HexColor("#4f5969"))

    y -= 30
    centered_text(c, participant_name, y, font="Times-Bold", size=24, color=colors.HexColor("#8a2c8b"))

    c.setStrokeColor(colors.HexColor("#999999"))
    c.setLineWidth(0.8)
    c.line(PAGE_WIDTH / 2 - 150, y - 12, PAGE_WIDTH / 2 + 150, y - 12)

    y -= 38
    centered_text(c, "for attending the Online Training for the National Heart Screening NADI MADANI Programme", y, font="Helvetica", size=8.5)
    y -= 16
    centered_text(c, "held on 20 May 2026, and for successfully completing the required assessment and test.", y, font="Helvetica", size=8.5)
    y -= 16
    centered_text(c, "The participant is certified to conduct MyHeartRisk-assisted community heart screening in line with the programme SOP.", y, font="Helvetica", size=8.5)
    y -= 16
    centered_text(c, "This covers participant registration, data entry, risk-result interpretation, referral advice generation when indicated, follow-up monitoring", y, font="Helvetica", size=8.2)
    y -= 16
    centered_text(c, "and reporting to CARE Institute UiTM through the designated system.", y, font="Helvetica", size=8.2)

    table_x = 60
    table_y = 178
    table_w = PAGE_WIDTH - 120
    table_h = 34
    col_w = table_w / 3

    c.setFillColor(colors.HexColor("#fff6df"))
    c.rect(table_x, table_y, table_w, table_h, fill=1, stroke=0)

    c.setStrokeColor(colors.HexColor("#d0a329"))
    c.setLineWidth(0.6)
    c.rect(table_x, table_y, table_w, table_h, fill=0, stroke=1)
    c.line(table_x + col_w, table_y, table_x + col_w, table_y + table_h)
    c.line(table_x + col_w * 2, table_y, table_x + col_w * 2, table_y + table_h)

    def table_cell(cx, header, value):
        c.setFillColor(colors.HexColor("#5a4a20"))
        c.setFont("Helvetica-Bold", 7.3)
        c.drawCentredString(cx, table_y + 22, header)
        c.setFillColor(colors.HexColor("#1d2636"))
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(cx, table_y + 9, value)

    table_cell(table_x + col_w / 2, "Training Date", "20 May 2026")
    table_cell(table_x + col_w * 1.5, "Training Session", "National Heart Screening NADI MADANI")
    table_cell(table_x + col_w * 2.5, "Certificate ID", certificate_id)

    sig_y = 45

    draw_image_preserve_aspect(c, asset_path("signature_sazzli_transparent.png"), x=250, y=sig_y + 50, w=150, h=75)
    c.setStrokeColor(colors.HexColor("#a0a0a0"))
    c.line(255, sig_y + 45, 390, sig_y + 45)
    c.setFillColor(colors.HexColor("#1d2636"))
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(322, sig_y + 28, "Prof. Dr. Sazzli Shahlan Kasim")
    c.setFont("Helvetica", 7)
    c.drawCentredString(322, sig_y + 13, "Director of CARE Institute,")
    c.drawCentredString(322, sig_y + 2, "Universiti Teknologi MARA")

    draw_image_preserve_aspect(c, asset_path("myheartrisk_gold_seal.png"), x=PAGE_WIDTH / 2 - 42, y=sig_y + 12, w=84, h=84)

    draw_image_preserve_aspect(c, asset_path("signature_johanes_transparent.png"), x=PAGE_WIDTH - 345, y=sig_y + 52, w=145, h=62)
    c.setStrokeColor(colors.HexColor("#a0a0a0"))
    c.line(PAGE_WIDTH - 350, sig_y + 45, PAGE_WIDTH - 215, sig_y + 45)
    c.setFillColor(colors.HexColor("#1d2636"))
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(PAGE_WIDTH - 282, sig_y + 28, trainer_name)
    c.setFont("Helvetica", 7)
    c.drawCentredString(PAGE_WIDTH - 282, sig_y + 13, "Trainer & Doctorate of Medicine,")
    c.drawCentredString(PAGE_WIDTH - 282, sig_y + 2, "CARE Institute, Universiti Teknologi MARA")

    c.save()
    return output_path
