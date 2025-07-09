from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

def create_therecruit_pdf(buffer, content, title="Fiche de poste"):
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph(f"<b>{title}</b>", styles['Title']))
    story.append(Spacer(1, 1*cm))
    for block in content:
        label = block.get('label', '')
        value = block.get('value', '')
        story.append(Paragraph(f"<b>{label} :</b> {value}", styles['Normal']))
        story.append(Spacer(1, 0.5*cm))
    doc.build(story)
