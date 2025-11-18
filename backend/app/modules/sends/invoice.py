import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from sqlalchemy.orm import Session
from app.modules.sends import models
from datetime import datetime


def _make_invoice_number(send: models.Send) -> str:
    # Simple invoice numbering: SB-{send_id}-{YYYYMMDDHHMMSS}
    ts = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    return f"SB-{send.id}-{ts}"


def generate_invoice_pdf(db: Session, send_id: int) -> str:
    """Generate a professional invoice PDF for the given Send, update send with invoice path/number/date and return the file path.

    The function writes the file under backend/invoices/ and returns absolute path.
    """
    send = db.query(models.Send).filter(models.Send.id == send_id).first()
    if not send:
        raise ValueError("Send not found")

    user = send.user

    invoices_dir = os.path.join(os.getcwd(), "invoices")
    os.makedirs(invoices_dir, exist_ok=True)

    # Ensure invoice_number exists
    if not getattr(send, 'invoice_number', None):
        send.invoice_number = _make_invoice_number(send)

    filename = f"invoice_{send.invoice_number}.pdf"
    path = os.path.join(invoices_dir, filename)

    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4

    # Colors
    primary_color = (0.259, 0.596, 0.698)  # #2596be
    text_color = (0.2, 0.2, 0.2)

    # Header with company info
    c.setFillColorRGB(*primary_color)
    c.rect(0, height - 50 * mm, width, 50 * mm, fill=1)

    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(20 * mm, height - 25 * mm, "SENDBULLETIN")

    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, height - 35 * mm, "Solution SaaS d'envoi de bulletins de salaire")
    c.drawString(20 * mm, height - 42 * mm, "Email: contact@sendbulletin.com | Tél: +221 XX XXX XX XX")

    # Invoice title
    c.setFillColorRGB(*text_color)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(20 * mm, height - 70 * mm, "FACTURE")

    # Invoice details
    c.setFont("Helvetica", 11)
    c.drawString(140 * mm, height - 70 * mm, f"Numéro : {send.invoice_number}")

    invoice_date = datetime.utcnow()
    c.drawString(140 * mm, height - 78 * mm, f"Date: {invoice_date.strftime('%d-%m-%Y')}")

    # Client section
    client_y = height - 100 * mm
    c.setFillColorRGB(*primary_color)
    c.rect(20 * mm, client_y - 25 * mm, 80 * mm, 25 * mm, fill=1)

    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(25 * mm, client_y - 8 * mm, "FACTURER À")

    c.setFillColorRGB(*text_color)
    c.setFont("Helvetica-Bold", 11)
    client_name = getattr(user, 'full_name', None) or getattr(user, 'email', 'Client inconnu')
    c.drawString(25 * mm, client_y - 35 * mm, client_name)

    c.setFont("Helvetica", 10)
    c.drawString(25 * mm, client_y - 45 * mm, f"Email: {getattr(user, 'email', 'N/A')}")

    if getattr(user, 'company', None):
        c.drawString(25 * mm, client_y - 55 * mm, f"Entreprise: {user.company}")

    # Table header
    table_y = client_y - 80 * mm
    c.setFillColorRGB(*primary_color)
    c.rect(20 * mm, table_y - 10 * mm, 170 * mm, 10 * mm, fill=1)

    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(25 * mm, table_y - 6 * mm, "DESCRIPTION")
    c.drawString(120 * mm, table_y - 6 * mm, "QUANTITÉ")
    c.drawString(150 * mm, table_y - 6 * mm, "PRIX UNITAIRE")
    c.drawString(180 * mm, table_y - 6 * mm, "MONTANT")

    # Table content
    c.setFillColorRGB(*text_color)
    c.setFont("Helvetica", 10)
    content_y = table_y - 20 * mm

    # Draw table row background
    c.setFillColorRGB(0.95, 0.95, 0.95)
    c.rect(20 * mm, content_y - 8 * mm, 170 * mm, 12 * mm, fill=1)
    c.setFillColorRGB(*text_color)

    # Get month name from send creation date
    send_date = send.created_at.date() if send.created_at else datetime.utcnow().date()
    month_names = {
        1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril", 5: "Mai", 6: "Juin",
        7: "Juillet", 8: "Août", 9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"
    }
    month_name = month_names.get(send_date.month, "Inconnu")
    desc = f"Envoi de bulletins de {month_name}"
    c.drawString(25 * mm, content_y - 5 * mm, desc)
    c.drawRightString(145 * mm, content_y - 5 * mm, str(send.nb_bulletins))
    c.drawRightString(175 * mm, content_y - 5 * mm, f"{send.price_per_bulletin:.2f} {getattr(send.pricing_plan, 'currency', 'EUR')}")
    c.drawRightString(185 * mm, content_y - 5 * mm, f"{send.total_amount:.2f} {getattr(send.pricing_plan, 'currency', 'EUR')}")

    # Totals section
    totals_y = content_y - 40 * mm
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(185 * mm, totals_y, f"TOTAL HT : {send.total_amount:.2f} {getattr(send.pricing_plan, 'currency', 'EUR')}")
    c.drawRightString(185 * mm, totals_y - 8 * mm, f"TVA (0%) : 0.00 {getattr(send.pricing_plan, 'currency', 'EUR')}")
    c.drawRightString(185 * mm, totals_y - 16 * mm, f"TOTAL TTC : {send.total_amount:.2f} {getattr(send.pricing_plan, 'currency', 'EUR')}")

    # Payment terms
    terms_y = totals_y - 40 * mm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(20 * mm, terms_y, "Conditions de paiement :")
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, terms_y - 10 * mm, "• Paiement à réception de facture")
    c.drawString(20 * mm, terms_y - 18 * mm, "• Délai de paiement : 30 jours")
    c.drawString(20 * mm, terms_y - 26 * mm, "• Mode de paiement : Virement bancaire")

    # Footer
    footer_y = 30 * mm
    c.setFillColorRGB(*primary_color)
    c.rect(0, 0, width, footer_y, fill=1)

    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica", 8)
    c.drawString(20 * mm, 15 * mm, "SendBulletin - Solution professionnelle d'envoi de bulletins de salaire")
    c.drawString(20 * mm, 8 * mm, "Tous droits réservés © 2024 SendBulletin")

    c.drawRightString(width - 20 * mm, 15 * mm, f"Facture générée le {invoice_date.strftime('%d/%m/%Y à %H:%M')}")
    c.drawRightString(width - 20 * mm, 8 * mm, f"Numéro : {send.invoice_number}")

    c.showPage()
    c.save()

    # Update send invoice_path, invoice_date and persist
    send.invoice_path = path
    send.invoice_date = invoice_date
    send.status = getattr(send, 'status', 'invoiced')
    db.add(send)
    db.commit()
    return path
