from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Union
from fastapi import UploadFile


class EmailBase(BaseModel):
    subject: str
    body: str
    recipient_email: EmailStr
    sender_email: Optional[EmailStr] = None


class EmailCreate(EmailBase):
    pass


class Email(EmailBase):
    id: int
    sent_at: Optional[str] = None
    status: str = "pending"  # pending, sent, failed

    class Config:
        from_attributes = True


class BulkEmailCreate(BaseModel):
    subject: str
    body: str
    recipient_emails: List[EmailStr]
    sender_email: Optional[EmailStr] = None


class EmailResponse(BaseModel):
    message: str
    email_id: Optional[int] = None


# Nouveau schéma pour l'envoi d'email avec modes global/personnalisé
class SendEmailRequest(BaseModel):
    # Destinataires
    to: List[EmailStr] = Field(..., description="Liste des destinataires principaux")
    cc: Optional[List[EmailStr]] = Field(None, description="Liste des destinataires en copie carbone")
    bcc: Optional[List[EmailStr]] = Field(None, description="Liste des destinataires en copie carbone invisible")

    # Contenu
    subject: str = Field(..., description="Sujet de l'email")
    body: str = Field(..., description="Corps de l'email (peut être HTML ou texte)")
    is_html: bool = Field(False, description="Indique si le corps est en HTML (True) ou texte brut (False)")

    # Credentials SMTP personnalisés (optionnels pour mode personnalisé)
    sender_email: Optional[EmailStr] = Field(None, description="Email de l'expéditeur (requis en mode personnalisé)")
    smtp_host: Optional[str] = Field(None, description="Hôte SMTP (requis en mode personnalisé)")
    smtp_port: Optional[int] = Field(None, description="Port SMTP (défaut 587 pour TLS)")
    smtp_password: Optional[str] = Field(None, description="Mot de passe SMTP (requis en mode personnalisé)")

    # Pièces jointes (optionnelles)
    attachments: Optional[List[UploadFile]] = Field(None, description="Liste des fichiers à joindre (PDF, etc.)")


class SendEmailResponse(BaseModel):
    status: str = Field(..., description="Statut de l'envoi : 'success' ou 'error'")
    message: str = Field(..., description="Message descriptif du résultat")
    error: Optional[str] = Field(None, description="Détails de l'erreur si status='error'")
    email_id: Optional[int] = Field(None, description="ID de l'email enregistré (si applicable)")


class SendBulletinsRequest(BaseModel):
    files: List[UploadFile] = Field(..., description="Liste des fichiers PDF des bulletins à envoyer")
    sender_email: str = Field(..., description="Email de l'expéditeur")
    subject: Optional[str] = Field("Votre bulletin de salaire", description="Sujet personnalisé de l'email")
    message: Optional[str] = Field("", description="Message personnalisé à inclure dans l'email")


class BulletinStatus(BaseModel):
    filename: str
    recipient_email: Optional[str] = None
    password: Optional[str] = None
    status: str  # "success" or "error"
    error_message: Optional[str] = None


class SendBulletinsResponse(BaseModel):
    total_files: int
    processed_files: int
    successful_sends: int
    failed_sends: int
    bulletins: List[BulletinStatus]


class SendBulletinsQueuedResponse(BaseModel):
    total_files: int
    enqueued: int
    email_ids: List[int]
    recipients: List[str]
    message: str


class EmailHistoryPeriod(BaseModel):
    period: str  # Format: "Octobre 2024"
    date_time: str  # Date et heure de la dernière activité de la période
    bulletins_count: int  # Nombre de bulletins envoyés dans cette période
    status_summary: str  # Résumé du statut (ex: "12 envoyés, 1 échoué")
