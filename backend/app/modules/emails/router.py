from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Form
from sqlalchemy.orm import Session
import os
import io
import PyPDF2
import pdfplumber
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pydantic import BaseModel

from app import deps
from app.modules.emails import crud, models, schemas, service
from app.modules.users import models as user_models

router = APIRouter()


class SendMailRequest(BaseModel):
    to_email: str
    subject: str
    message: str


@router.post("/send-email", response_model=schemas.SendEmailResponse)
async def send_email(
    *,
    request: schemas.SendEmailRequest,
    current_user: user_models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Envoyer un email avec détection automatique du mode SMTP (global ou personnalisé).

    - Mode global : utilise les credentials du fichier .env
    - Mode personnalisé : utilise les credentials fournis dans la requête

    Supporte :
    - Plusieurs destinataires (to, cc, bcc)
    - Corps HTML ou texte brut
    - Pièces jointes (PDF, etc.)
    - TLS sur port 587 par défaut
    """
    try:
        # Envoyer l'email via le service
        success, error_message = service.email_service.send_custom_email(request)

        if success:
            return schemas.SendEmailResponse(
                status="success",
                message="Email envoyé avec succès",
                email_id=None  # Pas d'enregistrement DB pour cet endpoint simple
            )
        else:
            return schemas.SendEmailResponse(
                status="error",
                message="Échec de l'envoi de l'email",
                error=error_message,
                email_id=None
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur interne lors de l'envoi de l'email: {str(e)}"
        )


@router.post("/emails/", response_model=schemas.Email)
def send_email(
    *,
    db: Session = Depends(deps.get_db),
    email_in: schemas.EmailCreate,
    background_tasks: BackgroundTasks,
    current_user: user_models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Send a single email
    """
    # Create email record
    email_obj = crud.email.create(db, obj_in=email_in, tenant_id=current_user.tenant_id)

    # Send email in background
    background_tasks.add_task(send_email_background, email_obj.id, db)

    return email_obj


@router.post("/emails/bulk", response_model=List[schemas.Email])
def send_bulk_emails(
    *,
    db: Session = Depends(deps.get_db),
    bulk_email_in: schemas.BulkEmailCreate,
    background_tasks: BackgroundTasks,
    current_user: user_models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Send bulk emails
    """
    # Create email records
    email_objects = crud.email.create_bulk(db, bulk_email=bulk_email_in, tenant_id=current_user.tenant_id)

    # Send emails in background
    for email_obj in email_objects:
        background_tasks.add_task(send_email_background, email_obj.id, db)

    return email_objects


@router.get("/emails/", response_model=List[schemas.Email])
def read_emails(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: user_models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve emails for current tenant
    """
    emails = crud.email.get_multi(db, skip=skip, limit=limit, tenant_id=current_user.tenant_id)
    return emails


@router.get("/emails/{email_id}", response_model=schemas.Email)
def read_email(
    *,
    db: Session = Depends(deps.get_db),
    email_id: int,
    current_user: user_models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get email by ID
    """
    email_obj = crud.email.get(db, id=email_id)
    if not email_obj:
        raise HTTPException(status_code=404, detail="Email not found")
    if email_obj.tenant_id != current_user.tenant_id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return email_obj


@router.post("/send-mail")
async def send_mail(
    *,
    request: SendMailRequest,
    background_tasks: BackgroundTasks,
    current_user: user_models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Envoyer un email HTML simple en utilisant les variables d'environnement Outlook.
    Utilise BackgroundTasks pour l'envoi asynchrone.
    """
    try:
        # Ajouter la tâche d'envoi d'email en arrière-plan
        background_tasks.add_task(service.email_service.send_email, request.to_email, request.subject, request.message)

        return {"message": "Email en cours d'envoi en arrière-plan"}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la mise en file d'attente de l'email: {str(e)}"
        )


@router.post("/send-bulletins", response_model=schemas.SendBulletinsResponse)
async def send_bulletins(
    *,
    files: List[UploadFile] = File(..., description="Liste des fichiers PDF des bulletins"),
    sender_email: str = Form(..., description="Email de l'expéditeur"),
    subject: Optional[str] = Form("Votre bulletin de salaire", description="Sujet personnalisé de l'email"),
    message: Optional[str] = Form("", description="Message personnalisé à inclure dans l'email"),
    db: Session = Depends(deps.get_db),
    current_user: user_models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Send bulletins to employees by extracting emails and passwords from uploaded PDF files.
    Each PDF contains hidden fields with recipient email and password at the end.
    """
    try:
        # Create request object from form data
        request = schemas.SendBulletinsRequest(
            files=files,
            sender_email=sender_email,
            subject=subject,
            message=message
        )

        # Send bulletins using the service with database session and tenant_id
        result = service.email_service.send_bulletins(request, db=db, tenant_id=current_user.tenant_id)

        # Create a Send record to store the operation and trigger invoice generation
        try:
            from app.modules.sends import crud as sends_crud, schemas as sends_schemas, invoice as sends_invoice
            nb = getattr(result, 'processed_files', None) or getattr(result, 'total_files', 0)
            send_in = sends_schemas.SendCreate(nb_bulletins=nb)
            send_obj = sends_crud.send.create(db, obj_in=send_in, user_id=current_user.id, tenant_id=current_user.tenant_id)
            # Generate invoice synchronously since we can't use background_tasks here
            try:
                sends_invoice.generate_invoice_pdf(db, send_obj.id)
            except Exception as e:
                print(f"Warning: invoice generation failed for send {send_obj.id}: {e}")
        except Exception as e:
            print(f"Warning: failed to record Send for bulletins: {e}")

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'envoi des bulletins: {str(e)}"
        )


@router.post("/send-bulletins/queue", response_model=schemas.SendBulletinsQueuedResponse)
async def send_bulletins_queue(
    *,
    files: List[UploadFile] = File(..., description="Liste des fichiers PDF des bulletins"),
    sender_email: str = Form(..., description="Email de l'expéditeur"),
    subject: Optional[str] = Form("Votre bulletin de salaire", description="Sujet personnalisé de l'email"),
    message: Optional[str] = Form("", description="Message personnalisé à inclure dans l'email"),
    batch_size: Optional[int] = Form(50, description="Taille des lots pour traitement (défaut: 50)"),
    delay_between_batches: Optional[int] = Form(30, description="Délai en secondes entre lots (défaut: 30)"),
    smtp_rate_limit: Optional[int] = Form(10, description="Nombre max d'emails par minute (défaut: 10)"),
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user: user_models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Met en file l'envoi des bulletins en tâches d'arrière-plan avec traitement par lots.
    Optimisé pour des volumes importants (ex: 700 bulletins).
    """
    import re
    import pdfplumber
    import PyPDF2
    from io import BytesIO

    pdf_files = [file for file in files if file.filename.lower().endswith('.pdf')]
    total_files = len(pdf_files)

    # Validation des paramètres pour gros volumes
    if batch_size < 1:
        batch_size = 50
    if batch_size > 200:
        batch_size = 200  # Limite supérieure pour éviter surcharge

    if delay_between_batches < 0:
        delay_between_batches = 30
    if delay_between_batches > 300:
        delay_between_batches = 300  # Max 5 minutes

    if smtp_rate_limit < 1:
        smtp_rate_limit = 10
    if smtp_rate_limit > 100:
        smtp_rate_limit = 100  # Max 100 emails/minute

    # Calculer le délai entre emails basé sur la limite de débit
    delay_between_emails = 60 // smtp_rate_limit  # secondes entre chaque email

    email_ids: List[int] = []
    recipients: List[str] = []
    processed_files = 0

    # Traitement par lots pour éviter surcharge mémoire
    for i in range(0, total_files, batch_size):
        batch_files = pdf_files[i:i + batch_size]
        batch_number = (i // batch_size) + 1

        print(f"Traitement du lot {batch_number} ({len(batch_files)} fichiers)")

        for file in batch_files:
            filename = file.filename
            try:
                pdf_content = file.file.read()
                file.file.seek(0)

                # Extraction texte optimisée
                text = ""
                try:
                    with pdfplumber.open(BytesIO(pdf_content)) as pdf:
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            if page_text:
                                text += page_text
                except Exception:
                    pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_content))
                    for page in pdf_reader.pages:
                        text += page.extract_text()

                # Email et mot de passe
                email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
                emails = re.findall(email_pattern, text)
                recipient_email = emails[-1] if emails else None

                password = None
                if recipient_email:
                    email_pos = text.rfind(recipient_email)
                    text_after_email = text[email_pos + len(recipient_email):]
                    password_patterns = [
                        r'(?:mot de passe|password|pwd)[\s:]*([A-Za-z0-9!@#$%^&*()_+=\-{}[\]|\\:;"\'<>.,?/~`]+)',
                        r'([A-Za-z0-9!@#$%^&*()_+=\-{}[\]|\\:;"\'<>.,?/~`]{6,})'
                    ]
                    for pattern in password_patterns:
                        passwords = re.findall(pattern, text_after_email, re.IGNORECASE)
                        if passwords:
                            password = passwords[0].strip()
                            break

                if recipient_email:
                    # Composer le corps
                    email_body = message or ""
                    if password:
                        if email_body:
                            email_body += "\n\n"
                        email_body += f"Mot de passe pour ouvrir le PDF : {password}"

                    # Enregistrer l'email (status pending)
                    email_in = schemas.EmailCreate(
                        subject=subject,
                        body=email_body,
                        recipient_email=recipient_email,
                        sender_email=sender_email,
                    )
                    email_obj = crud.email.create(db, obj_in=email_in, tenant_id=current_user.tenant_id)
                    email_ids.append(email_obj.id)
                    recipients.append(recipient_email)

                    # Mettre en file l'envoi du bulletin avec délai pour respecter limites SMTP
                    email_index_in_batch = processed_files % batch_size
                    total_delay = (batch_number * delay_between_batches) + (email_index_in_batch * delay_between_emails)

                    background_tasks.add_task(
                        send_bulletin_background_with_delay,
                        email_obj.id,
                        pdf_content,
                        filename,
                        db,
                        total_delay  # Délai calculé pour respecter le débit SMTP
                    )

                processed_files += 1

            except Exception as e:
                print(f"Erreur traitement fichier {filename}: {e}")
                continue

        # Petit délai entre lots pour éviter surcharge
        if i + batch_size < total_files:
            print(f"Pause de {delay_between_batches}s avant le prochain lot...")

    estimated_time = (len(email_ids) * delay_between_emails + batch_number * delay_between_batches) // 60
    success_message = f"Bulletins mis en file: {len(email_ids)}/{total_files} traités en {batch_number} lot(s) de {batch_size}. Temps estimé: ~{estimated_time}min"

    response = schemas.SendBulletinsQueuedResponse(
        total_files=total_files,
        enqueued=len(email_ids),
        email_ids=email_ids,
        recipients=recipients,
        message=success_message
    )

    # Record a Send for this queued batch and schedule invoice generation
    try:
        from app.modules.sends import crud as sends_crud, schemas as sends_schemas, invoice as sends_invoice
        nb = len(email_ids)
        send_in = sends_schemas.SendCreate(nb_bulletins=nb)
        send_obj = sends_crud.send.create(db, obj_in=send_in, user_id=current_user.id, tenant_id=current_user.tenant_id)
        # schedule invoice generation in background avec délai
        background_tasks.add_task(sends_invoice.generate_invoice_pdf, db, send_obj.id)
    except Exception as e:
        print(f"Warning: failed to create Send record for queued batch: {e}")

    return response


def send_email_background(email_id: int, db: Session):
    """
    Background task to send email
    """
    email_obj = crud.email.get(db, id=email_id)
    if email_obj:
        # Utilise la méthode compatible avec models.Email
        success = service.email_service.send_email_old(email_obj)
        status = "sent" if success else "failed"
        crud.email.update(db, db_obj=email_obj, obj_in={"status": status})


def send_bulletin_background(email_id: int, pdf_content: bytes, filename: str, db: Session):
    """
    Background task to send bulletin email with PDF attachment
    """
    email_obj = crud.email.get(db, id=email_id)
    if email_obj:
        success = service.email_service.send_bulletin_email(email_obj, pdf_content, filename)
        status = "sent" if success else "failed"
        crud.email.update(db, db_obj=email_obj, obj_in={"status": status})


def send_bulletin_background_with_delay(email_id: int, pdf_content: bytes, filename: str, db: Session, delay_seconds: int = 0):
    """
    Background task to send bulletin email with delay for rate limiting and retry mechanism
    """
    import time
    import asyncio
    import logging

    logger = logging.getLogger(__name__)

    async def send_with_delay():
        try:
            # Attendre le délai spécifié
            if delay_seconds > 0:
                logger.info(f"Attente de {delay_seconds}s avant envoi de l'email {email_id}...")
                await asyncio.sleep(delay_seconds)

            # Créer une nouvelle session DB pour la tâche en arrière-plan
            from app.db.session import SessionLocal
            db_session = SessionLocal()
            try:
                email_obj = crud.email.get(db_session, id=email_id)
                if email_obj:
                    logger.info(f"Envoi de l'email {email_id} à {email_obj.recipient_email}")

                    # Utiliser la nouvelle méthode avec retry
                    success = service.email_service.send_bulletin_email_with_content_and_retry(email_obj, pdf_content, filename, max_retries=3)

                    status = "sent" if success else "failed"
                    crud.email.update(db_session, db_obj=email_obj, obj_in={"status": status})

                    if success:
                        logger.info(f"Email {email_id}: ✅ envoyé avec succès")
                    else:
                        logger.error(f"Email {email_id}: ❌ échec définitif après retries")

                else:
                    logger.error(f"Email {email_id} non trouvé en base de données")

            except Exception as e:
                logger.error(f"Erreur lors de l'envoi de l'email {email_id}: {e}")
                # Marquer comme failed en cas d'exception
                try:
                    email_obj = crud.email.get(db_session, id=email_id)
                    if email_obj:
                        crud.email.update(db_session, db_obj=email_obj, obj_in={"status": "failed"})
                except Exception as update_error:
                    logger.error(f"Erreur lors de la mise à jour du statut: {update_error}")
            finally:
                db_session.close()

        except Exception as e:
            logger.error(f"Erreur critique dans send_bulletin_background_with_delay: {e}")

    # Lancer la tâche asynchrone dans un thread séparé
    import threading
    def run_async():
        try:
            asyncio.run(send_with_delay())
        except Exception as e:
            logger.error(f"Erreur dans le thread asynchrone: {e}")

    thread = threading.Thread(target=run_async)
    thread.daemon = True
    thread.start()


@router.get("/email-stats")
def emails_stats(
    db: Session = Depends(deps.get_db),
    current_user: user_models.User = Depends(deps.get_current_active_user),
):
    """
    Retourne des métriques de base pour le tableau de bord: total, envoyés, échecs, en attente, et envois des 7 derniers jours.
    """
    from sqlalchemy import func
    # Si superuser, voir tous les tenants, sinon filtrer par tenant
    if current_user.is_superuser:
        q = db.query(models.Email)
    else:
        q = db.query(models.Email).filter(models.Email.tenant_id == current_user.tenant_id)
    total = q.count()
    # Compter à la fois les statuts 'sent' et 'success' comme envoyés (certaines parties du code utilisent l'un ou l'autre)
    sent = q.filter(models.Email.status.in_(["sent", "success"])) .count()
    # Compter les échecs en incluant 'failed' et 'error'
    failed = q.filter(models.Email.status.in_(["failed", "error"])) .count()
    pending = q.filter(models.Email.status == "pending").count()

    # Groupement par jour pour les 7 derniers jours
    if current_user.is_superuser:
        last7_query = db.query(func.date(models.Email.created_at).label("day"), func.count().label("count"))
    else:
        last7_query = (
            db.query(func.date(models.Email.created_at).label("day"), func.count().label("count"))
            .filter(models.Email.tenant_id == current_user.tenant_id)
        )
    last7 = (
        last7_query
        .group_by(func.date(models.Email.created_at))
        .order_by(func.date(models.Email.created_at).desc())
        .limit(7)
        .all()
    )
    by_day = [{"day": d, "count": c} for d, c in last7]

    return {
        "total": total,
        "sent": sent,
        "failed": failed,
        "pending": pending,
        "last7Days": list(reversed(by_day)),
    }


@router.get("/email-recent-activity", response_model=List[schemas.Email])
def emails_recent_activity(
    db: Session = Depends(deps.get_db),
    limit: int = 20,
    current_user: user_models.User = Depends(deps.get_current_active_user),
):
    """
    Retourne les derniers emails pour l'activité récente.
    """
    emails = (
        db.query(models.Email)
        .filter(models.Email.tenant_id == current_user.tenant_id)
        .order_by(models.Email.created_at.desc())
        .limit(limit)
        .all()
    )
    return emails


@router.get("/email-recent-activity-detailed")
def emails_recent_activity_detailed(
    db: Session = Depends(deps.get_db),
    limit: int = 5,
    current_user: user_models.User = Depends(deps.get_current_active_user),
):
    """
    Retourne les derniers emails avec des informations détaillées pour l'activité récente.
    Inclut le nom du destinataire, l'email, le statut, la date et le mois du bulletin.
    """
    from datetime import datetime, timedelta, timezone

    emails = (
        db.query(models.Email)
        .filter(models.Email.tenant_id == current_user.tenant_id)
        .order_by(models.Email.created_at.desc())
        .limit(limit)
        .all()
    )

    result = []
    for email in emails:
        try:
            # Calculer le temps écoulé
            if email.created_at:
                # Utiliser datetime avec timezone UTC
                now = datetime.now(timezone.utc)
                created_at = email.created_at

                # Si created_at n'a pas de timezone, on assume UTC
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)

                time_diff = now - created_at

                if time_diff < timedelta(minutes=1):
                    time_ago = "Il y a quelques secondes"
                elif time_diff < timedelta(hours=1):
                    minutes = int(time_diff.total_seconds() / 60)
                    time_ago = f"Il y a {minutes} min"
                elif time_diff < timedelta(days=1):
                    hours = int(time_diff.total_seconds() / 3600)
                    time_ago = f"Il y a {hours}h"
                else:
                    days = time_diff.days
                    time_ago = f"Il y a {days}j"
            else:
                time_ago = "Date inconnue"

            # Extraire le nom du destinataire de l'email (partie avant @)
            recipient_name = email.recipient_email.split('@')[0].replace('.', ' ').title() if email.recipient_email else "Inconnu"

            # Extraire le mois du bulletin du sujet si possible
            bulletin_month = "Bulletin de salaire"
            if email.subject and "bulletin" in email.subject.lower():
                bulletin_month = email.subject

            result.append({
                "id": str(email.id),
                "employee": recipient_name,
                "email": email.recipient_email or "",
                "status": "success" if email.status == "sent" else ("failed" if email.status == "failed" else "pending"),
                "date": time_ago,
                "bulletinMonth": bulletin_month,
                "created_at": email.created_at.isoformat() if email.created_at else None
            })
        except Exception as e:
            # Log l'erreur mais continue avec les autres emails
            print(f"Error processing email {email.id}: {e}")
            continue

    return result


@router.get("/email-recent-activity-users")
def emails_recent_activity_by_user(
    db: Session = Depends(deps.get_db),
    limit: int = 5,
    current_user: user_models.User = Depends(deps.get_current_active_user),
):
    """
    Retourne l'activité récente agrégée par utilisateur (expéditeur).
    Pour chaque utilisateur expéditeur, renvoie: nom complet, email, nombre de bulletins envoyés,
    statut du dernier envoi et le temps écoulé depuis le dernier envoi.
    """
    from sqlalchemy import func, case
    from datetime import datetime, timedelta, timezone

    # Agréger par expéditeur avec date et compteur
    aggregated = (
        db.query(
            models.Email.sender_email.label("sender_email"),
            func.max(models.Email.created_at).label("latest_date"),
            func.sum(
                case((models.Email.status.in_(["sent", "success"]), 1), else_=0)
            ).label("sent_count"),
        )
        .filter(models.Email.tenant_id == current_user.tenant_id)
        .group_by(models.Email.sender_email)
        .order_by(func.max(models.Email.created_at).desc())
        .limit(limit)
        .all()
    )

    results = []
    for row in aggregated:
        sender_email = row.sender_email or ""
        latest_date = row.latest_date
        sent_count = int(row.sent_count or 0)

        # Dernier email pour récupérer le statut exact
        last_email = (
            db.query(models.Email)
            .filter(
                models.Email.tenant_id == current_user.tenant_id,
                models.Email.sender_email == sender_email,
            )
            .order_by(models.Email.created_at.desc())
            .first()
        )
        last_status = (
            "success"
            if last_email and last_email.status in ["sent", "success"]
            else ("failed" if last_email and last_email.status in ["failed", "error"] else "pending")
        )

        # Récupérer le nom complet de l'utilisateur (si présent)
        user = (
            db.query(user_models.User)
            .filter(
                user_models.User.email == sender_email,
                user_models.User.tenant_id == current_user.tenant_id,
            )
            .first()
        )
        full_name = user.full_name if user and user.full_name else (sender_email.split("@")[0].replace(".", " ").title() if sender_email else "Inconnu")

        # Calculer le temps écoulé depuis le dernier envoi
        if latest_date:
            now = datetime.now(timezone.utc)
            created_at = latest_date
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            time_diff = now - created_at

            if time_diff < timedelta(minutes=1):
                time_ago = "Il y a quelques secondes"
            elif time_diff < timedelta(hours=1):
                minutes = int(time_diff.total_seconds() / 60)
                time_ago = f"Il y a {minutes} min"
            elif time_diff < timedelta(days=1):
                hours = int(time_diff.total_seconds() / 3600)
                time_ago = f"Il y a {hours}h"
            else:
                days = time_diff.days
                time_ago = f"Il y a {days}j"
        else:
            time_ago = "Date inconnue"

        results.append(
            {
                "id": sender_email or full_name,
                "fullName": full_name,
                "email": sender_email,
                "sentCount": sent_count,
                "status": last_status,
                "date": time_ago,
            }
        )

    return results


@router.get("/email-history-periods", response_model=List[schemas.EmailHistoryPeriod])
def emails_history_periods(
    db: Session = Depends(deps.get_db),
    current_user: user_models.User = Depends(deps.get_current_active_user),
    limit: int = 3,
):
    """
    Retourne l'historique des emails groupé par période (mois/année).
    """
    from sqlalchemy import func, extract, case
    from datetime import datetime
    import calendar

    # Adapter l'extraction year/month selon le dialecte (SQLite vs PostgreSQL)
    try:
        bind = db.get_bind()
        dialect_name = bind.dialect.name if bind is not None else ""
    except Exception:
        dialect_name = ""

    # Filtrage par tenant pour les utilisateurs normaux, voir tous pour superuser
    tenant_filter = models.Email.tenant_id == current_user.tenant_id if not current_user.is_superuser else True

    if dialect_name == "sqlite":
        # SQLite: utiliser strftime pour extraire année/mois
        year_expr = func.strftime('%Y', models.Email.created_at)
        month_expr = func.strftime('%m', models.Email.created_at)
        results = (
            db.query(
                year_expr.label('year'),
                month_expr.label('month'),
                func.count(models.Email.id).label('total_count'),
                func.sum(
                    case(
                        (models.Email.status.in_(['sent', 'success']), 1),
                        else_=0
                    )
                ).label('sent_count'),
                func.sum(
                    case(
                        (models.Email.status.in_(['failed', 'error']), 1),
                        else_=0
                    )
                ).label('failed_count'),
                func.max(models.Email.created_at).label('latest_date')
            )
            .filter(tenant_filter)
            .group_by(year_expr, month_expr)
            .order_by(year_expr.desc(), month_expr.desc())
            .limit(limit)
            .all()
        )
    else:
        # PostgreSQL: regrouper par mois avec date_trunc('month') pour plus de robustesse
        period_expr = func.date_trunc('month', models.Email.created_at)
        results = (
            db.query(
                period_expr.label('period'),
                func.count(models.Email.id).label('total_count'),
                func.sum(
                    case(
                        (models.Email.status.in_(['sent', 'success']), 1),
                        else_=0
                    )
                ).label('sent_count'),
                func.sum(
                    case(
                        (models.Email.status.in_(['failed', 'error']), 1),
                        else_=0
                    )
                ).label('failed_count'),
                func.max(models.Email.created_at).label('latest_date')
            )
            .filter(tenant_filter)
            .group_by(period_expr)
            .order_by(period_expr.desc())
            .limit(limit)
            .all()
        )

    periods = []
    for result in results:
        # Déterminer année/mois en fonction du dialecte et des champs disponibles
        if dialect_name == "sqlite":
            try:
                year = int(result.year)
            except Exception:
                year = int(str(result.year))
            try:
                month = int(result.month)
            except Exception:
                month = int(str(result.month))
        else:
            latest_date = result.latest_date
            if latest_date:
                year = latest_date.year
                month = latest_date.month
            else:
                # fallback si latest_date est nul
                period_ts = getattr(result, 'period', None)
                year = int(period_ts.strftime('%Y')) if period_ts else datetime.utcnow().year
                month = int(period_ts.strftime('%m')) if period_ts else datetime.utcnow().month
        total_count = result.total_count or 0
        sent_count = result.sent_count or 0
        failed_count = result.failed_count or 0
        latest_date = result.latest_date

        # Formatage du nom du mois en français
        month_names = {
            1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
            5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
            9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"
        }

        period_name = f"{month_names[month]} {year}"
        date_time = latest_date.strftime("%d/%m/%Y à %H:%M") if latest_date else ""

        # Résumé du statut
        if failed_count > 0:
            status_summary = f"{sent_count} envoyés, {failed_count} échoués"
        else:
            status_summary = f"{sent_count} envoyés"

        periods.append(schemas.EmailHistoryPeriod(
            period=period_name,
            date_time=date_time,
            bulletins_count=total_count,
            status_summary=status_summary
        ))

    return periods
