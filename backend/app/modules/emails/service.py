import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Tuple
import logging
import asyncio
import threading
import time
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.core.config import settings
from app.modules.emails import models, schemas
from app.modules.emails.performance_config import PerformanceConfig
from app.modules.emails.performance_monitor import PerformanceMonitor

# Configuration du logger
logger = logging.getLogger(__name__)


class SMTPConnectionPool:
    """Pool de connexions SMTP optimisé pour envois massifs haute performance"""

    def __init__(self, max_connections=50):
        self.smtp_server = settings.SMTP_HOST or "smtp.gmail.com"
        self.smtp_port = settings.SMTP_PORT or 587
        self.smtp_username = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.max_connections = max_connections
        self.connection_queue = queue.Queue(maxsize=max_connections)
        self.active_connections = set()
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
        
        # Pré-créer quelques connexions
        self._initialize_pool(min(5, max_connections))

    def _initialize_pool(self, initial_count):
        """Pré-crée des connexions pour démarrage rapide"""
        for _ in range(initial_count):
            try:
                conn = self._create_connection()
                self.connection_queue.put(conn, block=False)
            except Exception as e:
                logger.warning(f"Échec pré-création connexion: {e}")
                break

    def _create_connection(self):
        """Crée une nouvelle connexion SMTP"""
        conn = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=15)
        conn.starttls()
        conn.login(self.smtp_username, self.smtp_password)
        return conn

    def get_connection(self, timeout=30):
        """Récupère une connexion du pool avec timeout"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Essayer de récupérer une connexion existante
                conn = self.connection_queue.get(block=False)
                try:
                    conn.noop()  # Test de validité
                    with self._lock:
                        self.active_connections.add(conn)
                    return conn
                except:
                    # Connexion invalide, la supprimer
                    try:
                        conn.quit()
                    except:
                        pass
                    continue
            except queue.Empty:
                # Pas de connexion disponible, en créer une nouvelle si possible
                with self._lock:
                    if len(self.active_connections) + self.connection_queue.qsize() < self.max_connections:
                        try:
                            conn = self._create_connection()
                            self.active_connections.add(conn)
                            return conn
                        except Exception as e:
                            logger.error(f"Erreur création connexion: {e}")
                            time.sleep(0.1)
                            continue
                
                # Attendre qu'une connexion se libère
                time.sleep(0.05)
        
        raise Exception("Timeout: Impossible d'obtenir une connexion SMTP")

    def return_connection(self, conn):
        """Remet une connexion dans le pool"""
        with self._lock:
            if conn in self.active_connections:
                self.active_connections.remove(conn)
                try:
                    self.connection_queue.put(conn, block=False)
                except queue.Full:
                    # Pool plein, fermer la connexion
                    try:
                        conn.quit()
                    except:
                        pass

    def close_all(self):
        """Ferme toutes les connexions"""
        with self._lock:
            # Fermer les connexions actives
            for conn in list(self.active_connections):
                try:
                    conn.quit()
                except:
                    pass
            self.active_connections.clear()
            
            # Fermer les connexions en attente
            while not self.connection_queue.empty():
                try:
                    conn = self.connection_queue.get(block=False)
                    conn.quit()
                except:
                    pass


class EmailService:
    def __init__(self):
        self.smtp_server = settings.SMTP_HOST or "smtp.gmail.com"
        self.smtp_port = settings.SMTP_PORT or 587
        self.smtp_username = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.sender_email = settings.EMAILS_FROM_EMAIL or "noreply@sendbulletin.com"

        # Pool de connexions SMTP optimisé pour haute performance
        self.smtp_pool = SMTPConnectionPool(max_connections=50)

        # Executor pour les opérations concurrentes avec plus de workers
        self.executor = ThreadPoolExecutor(max_workers=50, thread_name_prefix="email-sender")
        
        # Monitoring de performance
        self.performance_monitor = PerformanceMonitor()
        
        # Statistiques de performance (legacy)
        self.stats = {
            'total_sent': 0,
            'total_failed': 0,
            'start_time': None,
            'batch_times': []
        }

        logger.info(f"SMTP Configuration - Server: {self.smtp_server}, Port: {self.smtp_port}, User: {self.smtp_username}, From: {self.sender_email}")

    def send_email_old(self, email_obj: models.Email) -> bool:
        """
        Send a single email (legacy method)
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = email_obj.sender_email or self.sender_email
            msg['To'] = email_obj.recipient_email
            msg['Subject'] = email_obj.subject

            # Add body
            msg.attach(MIMEText(email_obj.body, 'html'))

            # Create SMTP connection
            if self.smtp_username and self.smtp_password:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
            else:
                # For testing purposes, skip authentication if credentials are not set
                print("Warning: SMTP credentials not configured, skipping authentication")
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()

            # Send email
            text = msg.as_string()
            server.sendmail(msg['From'], msg['To'], text)
            server.quit()

            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

    def send_bulk_emails_optimized(self, email_objects: List[models.Email], batch_size: int = None) -> List[bool]:
        """
        Envoi optimisé par batch avec traitement concurrent
        """
        if not email_objects:
            return []
            
        total_emails = len(email_objects)
        
        # Configuration adaptative selon le volume
        config = PerformanceConfig.get_optimized_settings(total_emails)
        if batch_size is None:
            batch_size = config['batch_size']
        
        # Démarrage du monitoring
        self.performance_monitor.start_session(total_emails)
        self.stats['start_time'] = time.time()
        results = [False] * total_emails
        
        logger.info(f"🚀 Début envoi bulk de {total_emails} emails (batch: {batch_size}, concurrent: {config['max_concurrent']})")
        
        # Traitement par batch pour éviter la surcharge
        batch_number = 0
        for i in range(0, total_emails, batch_size):
            batch = email_objects[i:i + batch_size]
            batch_number += 1
            
            # Démarrage monitoring du batch
            batch_id = self.performance_monitor.start_batch(len(batch))
            
            # Traitement concurrent du batch
            max_workers = min(len(batch), config['max_concurrent'])
            batch_success = 0
            batch_failure = 0
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_index = {
                    executor.submit(self._send_single_email_pooled, email): i + j 
                    for j, email in enumerate(batch)
                }
                
                for future in as_completed(future_to_index):
                    index = future_to_index[future]
                    try:
                        success = future.result()
                        results[index] = success
                        if success:
                            batch_success += 1
                            self.stats['total_sent'] += 1
                        else:
                            batch_failure += 1
                            self.stats['total_failed'] += 1
                    except Exception as e:
                        logger.error(f"Erreur envoi email index {index}: {e}")
                        results[index] = False
                        batch_failure += 1
                        self.stats['total_failed'] += 1
            
            # Fin monitoring du batch
            self.performance_monitor.end_batch(batch_id, batch_success, batch_failure)
            
            # Pause entre les batches
            if i + batch_size < total_emails:
                time.sleep(PerformanceConfig.BATCH_PAUSE)
        
        # Fin de session monitoring
        self.performance_monitor.end_session()
        
        # Affichage des recommandations
        recommendations = self.performance_monitor.get_recommendations()
        for rec in recommendations:
            logger.info(rec)
        
        return results

    def _send_single_email_pooled(self, email_obj: models.Email) -> bool:
        """Envoi d'un email unique avec pool de connexions"""
        server = None
        try:
            server = self.smtp_pool.get_connection(timeout=10)
            
            msg = MIMEMultipart()
            msg['From'] = email_obj.sender_email or self.sender_email
            msg['To'] = email_obj.recipient_email
            msg['Subject'] = email_obj.subject
            msg.attach(MIMEText(email_obj.body, 'html'))
            
            server.sendmail(msg['From'], msg['To'], msg.as_string())
            return True
            
        except Exception as e:
            logger.error(f"Erreur envoi à {email_obj.recipient_email}: {e}")
            return False
        finally:
            if server:
                self.smtp_pool.return_connection(server)

    def send_bulletin_email(self, email_obj: models.Email, pdf_content: bytes, filename: str) -> bool:
        """
        Send email with password-protected PDF attachment
        """
        return self.send_bulletin_email_with_retry(email_obj, pdf_content, filename, max_retries=3)

    def send_bulletin_email_with_retry(self, email_obj: models.Email, pdf_content: bytes, filename: str, max_retries: int = 3) -> bool:
        """
        Send email with PDF attachment and retry mechanism for reliability
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"Tentative {attempt + 1}/{max_retries} - Envoi email à {email_obj.recipient_email}")

                # Create message
                msg = MIMEMultipart()
                msg['From'] = email_obj.sender_email or self.sender_email
                msg['To'] = email_obj.recipient_email
                msg['Subject'] = email_obj.subject

                # Add body
                msg.attach(MIMEText(email_obj.body, 'plain'))

                # Add PDF attachment
                part = MIMEApplication(pdf_content, Name=filename)
                part['Content-Disposition'] = f'attachment; filename="{filename}"'
                msg.attach(part)

                # Create SMTP connection with timeout
                server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30)
                server.starttls()

                # Login with error handling
                try:
                    server.login(self.smtp_username, self.smtp_password)
                except smtplib.SMTPAuthenticationError as auth_error:
                    logger.error(f"Erreur d'authentification SMTP: {auth_error}")
                    return False

                # Send email
                text = msg.as_string()
                server.sendmail(msg['From'], msg['To'], text)
                server.quit()

                logger.info(f"✅ Email envoyé avec succès à {email_obj.recipient_email}")
                return True

            except smtplib.SMTPConnectError as e:
                logger.warning(f"Tentative {attempt + 1} échouée - Erreur de connexion: {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                return False

            except smtplib.SMTPServerDisconnected as e:
                logger.warning(f"Tentative {attempt + 1} échouée - Serveur déconnecté: {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)
                    continue
                return False

            except smtplib.SMTPException as e:
                logger.error(f"Tentative {attempt + 1} échouée - Erreur SMTP: {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)
                    continue
                return False

            except Exception as e:
                logger.error(f"Tentative {attempt + 1} échouée - Erreur inattendue: {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)
                    continue
                return False

        logger.error(f"Échec définitif après {max_retries} tentatives pour {email_obj.recipient_email}")
        return False

    def send_email(self, to_email: str, subject: str, message: str) -> bool:
        """
        Send an HTML email using Outlook SMTP configuration
        """
        try:
            logger.info(f"Attempting to send email to {to_email} with subject: {subject}")

            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = to_email
            msg['Subject'] = subject

            # Add HTML body
            msg.attach(MIMEText(message, 'html'))

            # Create SMTP connection with TLS
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # Enable TLS

            # Login
            server.login(self.smtp_username, self.smtp_password)

            # Send email
            text = msg.as_string()
            server.sendmail(self.sender_email, to_email, text)
            server.quit()

            logger.info(f"Email sent successfully to {to_email}")
            print(f"✅ Email sent successfully to {to_email}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            error_code = str(e)
            if "5.7.139" in error_code or "basic authentication is disabled" in error_code.lower():
                error_msg = f"""
❌ ERREUR D'AUTHENTIFICATION OUTLOOK/HOTMAIL ❌

Le problème: Microsoft a désactivé l'authentification de base pour Outlook/Hotmail.

SOLUTION REQUISE - Créer un mot de passe d'application:
1. Connectez-vous à votre compte Microsoft/Outlook
2. Allez dans Sécurité > Options de sécurité avancées
3. Activez l'authentification à deux facteurs (2FA) si ce n'est pas déjà fait
4. Générez un "mot de passe d'application" pour SMTP
5. Remplacez le SMTP_PASSWORD dans votre fichier .env par ce nouveau mot de passe

Détails de l'erreur: {error_code}
"""
            else:
                error_msg = f"SMTP Authentication failed: {error_code}"
            
            logger.error(error_msg)
            print(error_msg)
            return False
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error: {str(e)}"
            logger.error(error_msg)
            print(f"❌ {error_msg}")
            return False
        except Exception as e:
            error_msg = f"Unexpected error while sending email: {str(e)}"
            logger.error(error_msg)
            print(f"❌ {error_msg}")
            return False

    def send_custom_email(self, request: schemas.SendEmailRequest) -> Tuple[bool, Optional[str]]:
        """
        Send email with automatic detection of SMTP mode (global or custom).
        Returns (success: bool, error_message: Optional[str])
        """
        try:
            # Détection automatique du mode : si credentials personnalisés fournis, utiliser mode personnalisé
            use_custom_smtp = (
                request.sender_email and
                request.smtp_host and
                request.smtp_port and
                request.smtp_password
            )

            if use_custom_smtp:
                # Mode personnalisé : utiliser les credentials de la requête
                smtp_server = request.smtp_host
                smtp_port = request.smtp_port
                smtp_username = request.sender_email
                smtp_password = request.smtp_password
                sender_email = request.sender_email
            else:
                # Mode global : utiliser les credentials du .env
                smtp_server = self.smtp_server
                smtp_port = self.smtp_port or 587
                smtp_username = self.smtp_username
                smtp_password = self.smtp_password
                sender_email = request.sender_email or self.sender_email

            # Validation des credentials
            if not smtp_username or not smtp_password:
                return False, "SMTP credentials not configured. Provide custom credentials or set them in .env"

            # Créer le message
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = ', '.join(request.to)
            if request.cc:
                msg['Cc'] = ', '.join(request.cc)
            msg['Subject'] = request.subject

            # Corps du message (HTML ou texte)
            body_type = 'html' if request.is_html else 'plain'
            msg.attach(MIMEText(request.body, body_type))

            # Ajouter les pièces jointes si présentes
            if request.attachments:
                for attachment in request.attachments:
                    # Lire le contenu du fichier
                    content = attachment.file.read()
                    attachment.file.seek(0)  # Reset file pointer

                    # Déterminer le type MIME basé sur l'extension
                    filename = attachment.filename
                    if filename.lower().endswith('.pdf'):
                        part = MIMEApplication(content, _subtype="pdf")
                    else:
                        # Pour autres types de fichiers
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(content)
                        encoders.encode_base64(part)

                    part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                    msg.attach(part)

            # Connexion SMTP avec TLS
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()

            # Authentification
            server.login(smtp_username, smtp_password)

            # Préparer la liste des destinataires (to + cc + bcc)
            recipients = request.to.copy()
            if request.cc:
                recipients.extend(request.cc)
            if request.bcc:
                recipients.extend(request.bcc)

            # Envoyer l'email
            text = msg.as_string()
            server.sendmail(sender_email, recipients, text)
            server.quit()

            return True, None

        except smtplib.SMTPAuthenticationError as e:
            return False, f"SMTP Authentication failed: {str(e)}"
        except smtplib.SMTPException as e:
            return False, f"SMTP error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    async def send_bulletins_concurrent(self, request: schemas.SendBulletinsRequest, db=None, tenant_id=None, max_concurrent=25) -> schemas.SendBulletinsResponse:
        """
        Send bulletins concurrently using asyncio for better performance with large volumes
        """
        import re
        import pdfplumber
        import PyPDF2
        from io import BytesIO
        from app.modules.emails import crud
        from datetime import datetime

        bulletins_status = []
        successful_sends = 0
        failed_sends = 0

        # Filter only PDF files from uploaded files
        pdf_files = [file for file in request.files if file.filename.lower().endswith('.pdf')]
        total_files = len(pdf_files)

        semaphore = asyncio.Semaphore(max_concurrent)
        
        # Configuration adaptative
        config = PerformanceConfig.get_optimized_settings(total_files)
        if max_concurrent > config['max_concurrent']:
            max_concurrent = config['max_concurrent']
        
        # Monitoring de performance
        self.performance_monitor.start_session(total_files)
        start_time = time.time()
        logger.info(f"🚀 Début traitement concurrent de {total_files} bulletins (max_concurrent={max_concurrent})")

        async def process_single_file(file):
            nonlocal successful_sends, failed_sends
            async with semaphore:
                filename = file.filename
                recipient_email = None
                try:
                    # Read PDF content from uploaded file
                    pdf_content = await asyncio.get_event_loop().run_in_executor(
                        self.executor, file.file.read
                    )
                    await asyncio.get_event_loop().run_in_executor(
                        self.executor, file.file.seek, 0
                    )  # Reset file pointer

                    # Extract text from PDF (CPU intensive, run in executor)
                    text = await asyncio.get_event_loop().run_in_executor(
                        self.executor, self._extract_text_from_pdf, pdf_content, filename
                    )

                    # Extract email and password
                    recipient_email, password = await asyncio.get_event_loop().run_in_executor(
                        self.executor, self._extract_email_and_password, text, recipient_email
                    )

                    if recipient_email:
                        # Create email content with password in body
                        email_body = request.message or ""
                        if password:
                            if email_body:
                                email_body += "\n\n"
                            email_body += f"Mot de passe pour ouvrir le PDF : {password}"

                        # Create email record (Pydantic schema)
                        email_obj = schemas.EmailCreate(
                            subject=request.subject,
                            body=email_body,
                            recipient_email=recipient_email,
                            sender_email=request.sender_email
                        )

                        # Save to database if db session is provided.
                        # IMPORTANT: do NOT reuse the request-scoped `db` across threads.
                        # Use a fresh SessionLocal inside the worker thread so commits are reliable.
                        db_email = None
                        if db is not None:
                            def _create_in_thread(email_obj_local, tenant_id_local):
                                from app.db.session import SessionLocal
                                db_session = SessionLocal()
                                try:
                                    return crud.email.create(db_session, obj_in=email_obj_local, tenant_id=tenant_id_local)
                                finally:
                                    db_session.close()

                            try:
                                db_email = await asyncio.get_event_loop().run_in_executor(
                                    self.executor, _create_in_thread, email_obj, tenant_id
                                )
                                logger.info(f"Email record created in database with ID: {getattr(db_email, 'id', None)}")
                            except Exception as db_error:
                                logger.error(f"Failed to save email to database: {db_error}")

                        # Send email with PDF attachment (I/O intensive)
                        success = await asyncio.get_event_loop().run_in_executor(
                            self.executor, self.send_bulletin_email_with_content_and_retry,
                            email_obj, pdf_content, filename, 3
                        )

                        # Update database status if email was saved
                        if db is not None and db_email is not None:
                            def _update_status_in_thread(email_id_local, status_local, sent_at_local):
                                from app.db.session import SessionLocal
                                db_session = SessionLocal()
                                try:
                                    email_obj_local = crud.email.get(db_session, id=email_id_local)
                                    if email_obj_local:
                                        return crud.email.update(db_session, db_obj=email_obj_local, obj_in={"status": status_local, "sent_at": sent_at_local})
                                    return None
                                finally:
                                    db_session.close()

                            try:
                                status = "sent" if success else "failed"
                                sent_at = datetime.utcnow() if success else None
                                await asyncio.get_event_loop().run_in_executor(
                                    self.executor, _update_status_in_thread, db_email.id, status, sent_at
                                )
                                logger.info(f"Email status updated to: {status}")
                            except Exception as e:
                                logger.error(f"Failed to update email status: {e}")

                        if success:
                            successful_sends += 1
                            return schemas.BulletinStatus(
                                filename=filename,
                                recipient_email=recipient_email,
                                password=password,
                                status="success"
                            )
                        else:
                            # Send failed (email was found but sending failed)
                            failed_sends += 1
                            return schemas.BulletinStatus(
                                filename=filename,
                                recipient_email=recipient_email,
                                password=password,
                                status="error",
                                error_message="Échec de l'envoi du bulletin"
                            )

                    # If no recipient email was found in the PDF
                    failed_sends += 1
                    return schemas.BulletinStatus(
                        filename=filename,
                        status="error",
                        error_message="Aucun email trouvé dans le PDF"
                    )

                except Exception as e:
                    failed_sends += 1
                    return schemas.BulletinStatus(
                        filename=filename,
                        status="error",
                        error_message=f"Erreur lors du traitement: {str(e)}"
                    )

        # Traitement par batch adaptatif
        batch_size = PerformanceConfig.BULLETIN_BATCH_SIZE
        all_results = []
        
        for i in range(0, len(pdf_files), batch_size):
            batch_files = pdf_files[i:i + batch_size]
            batch_start = time.time()
            
            batch_id = self.performance_monitor.start_batch(len(batch_files))
            logger.info(f"📦 Traitement batch {i//batch_size + 1}/{(len(pdf_files) + batch_size - 1)//batch_size} ({len(batch_files)} fichiers)")
            
            tasks = [process_single_file(file) for file in batch_files]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            all_results.extend(batch_results)
            
            # Compter les succès/échecs du batch
            batch_success = sum(1 for r in batch_results if not isinstance(r, Exception) and hasattr(r, 'status') and r.status == 'success')
            batch_failure = len(batch_results) - batch_success
            
            self.performance_monitor.end_batch(batch_id, batch_success, batch_failure)
            
            # Pause courte entre batches
            if i + batch_size < len(pdf_files):
                await asyncio.sleep(0.1)
        
        results = all_results

        # Collect results
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Exception in concurrent processing: {result}")
                failed_sends += 1
                bulletins_status.append(schemas.BulletinStatus(
                    filename="unknown",
                    status="error",
                    error_message=f"Erreur de traitement concurrent: {str(result)}"
                ))
            else:
                bulletins_status.append(result)

        # Fin de session monitoring
        self.performance_monitor.end_session()
        
        # Affichage des recommandations
        recommendations = self.performance_monitor.get_recommendations()
        for rec in recommendations:
            logger.info(rec)
        
        return schemas.SendBulletinsResponse(
            total_files=total_files,
            processed_files=len(bulletins_status),
            successful_sends=successful_sends,
            failed_sends=failed_sends,
            bulletins=bulletins_status
        )

    def _extract_text_from_pdf(self, pdf_content: bytes, filename: str) -> str:
        """Helper method to extract text from PDF"""
        import pdfplumber
        import PyPDF2
        from io import BytesIO
        
        text = ""
        try:
            with pdfplumber.open(BytesIO(pdf_content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text
        except Exception as e:
            print(f"pdfplumber failed for {filename}, falling back to PyPDF2: {e}")
            # Fallback to PyPDF2
            try:
                pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_content))
                for page in pdf_reader.pages:
                    text += page.extract_text()
            except Exception as e2:
                logger.error(f"Both pdfplumber and PyPDF2 failed for {filename}: {e2}")
        return text

    def _extract_email_and_password(self, text: str, recipient_email=None) -> Tuple[Optional[str], Optional[str]]:
        """Helper method to extract email and password from text"""
        import re
        password = None

        # Look for email pattern (typically at the end)
        email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            recipient_email = emails[-1]  # Take the last email (usually at the end)

        # Look for password pattern after email
        if recipient_email:
            # Find the position of the email and extract text after it
            email_pos = text.rfind(recipient_email)
            text_after_email = text[email_pos + len(recipient_email):]

            # Look for password patterns
            password_patterns = [
                r'(?:mot de passe|password|pwd)[\s:]*([A-Za-z0-9!@#$%^&*()_+=\-{}[\]|\\:;"\'<>,.?/~`]+)',
                r'([A-Za-z0-9!@#$%^&*()_+=\-{}[\]|\\:;"\'<>,.?/~`]{6,})'  # Fallback: any alphanumeric string of 6+ chars
            ]

            for pattern in password_patterns:
                passwords = re.findall(pattern, text_after_email, re.IGNORECASE)
                if passwords:
                    password = passwords[0].strip()
                    break

        return recipient_email, password

    def send_bulletins(self, request: schemas.SendBulletinsRequest, db=None, tenant_id=None) -> schemas.SendBulletinsResponse:
        """
        Send bulletins to employees by extracting emails and passwords from uploaded PDF files
        """
        # For backward compatibility, use synchronous version
        # In production, consider migrating to the async version
        import asyncio

        async def run_sync():
            return await self.send_bulletins_concurrent(request, db, tenant_id, max_concurrent=5)

        # Utiliser l'event loop existant ou en créer un nouveau
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Si dans un contexte async, créer une tâche
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.send_bulletins_concurrent(request, db, tenant_id, max_concurrent=20))
                    return future.result()
            else:
                return loop.run_until_complete(run_sync())
        except RuntimeError:
            # Pas d'event loop, en créer un nouveau
            return asyncio.run(run_sync())

    def send_bulletin_email_with_content(self, email_obj: schemas.EmailCreate, pdf_content: bytes, filename: str) -> bool:
        """
        Send email with PDF attachment using raw content
        """
        return self.send_bulletin_email_with_content_and_retry(email_obj, pdf_content, filename, max_retries=3)

    def send_bulletin_email_with_content_and_retry(self, email_obj: schemas.EmailCreate, pdf_content: bytes, filename: str, max_retries: int = 3) -> bool:
        """
        Send email with PDF attachment and retry mechanism using connection pooling
        """
        for attempt in range(max_retries):
            server = None
            try:
                logger.info(f"Tentative {attempt + 1}/{max_retries} - Envoi bulletin à {email_obj.recipient_email}")

                # Create message with attachment
                msg = MIMEMultipart()
                # Utiliser l'email de l'expéditeur fourni dans le formulaire comme adresse d'expédition visible
                msg['From'] = email_obj.sender_email or self.sender_email
                msg['To'] = email_obj.recipient_email
                msg['Subject'] = email_obj.subject

                # Add body
                msg.attach(MIMEText(email_obj.body, 'plain'))

                # Add PDF attachment
                part = MIMEApplication(pdf_content, Name=filename)
                part['Content-Disposition'] = f'attachment; filename="{filename}"'
                msg.attach(part)

                # Get connection from pool avec timeout réduit
                server = self.smtp_pool.get_connection(timeout=15)

                # Send email - l'adresse From dans le message sera celle saisie par l'utilisateur
                text = msg.as_string()
                server.sendmail(msg['From'], email_obj.recipient_email, text)

                logger.info(f"✅ Bulletin envoyé avec succès à {email_obj.recipient_email} (de: {msg['From']})")
                print(f"✅ Bulletin envoyé avec succès à {email_obj.recipient_email}")
                return True

            except smtplib.SMTPConnectError as e:
                logger.warning(f"Tentative {attempt + 1} échouée - Erreur de connexion: {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)
                    continue
                return False

            except smtplib.SMTPServerDisconnected as e:
                logger.warning(f"Tentative {attempt + 1} échouée - Serveur déconnecté: {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)
                    continue
                return False

            except smtplib.SMTPAuthenticationError as e:
                error_code = str(e)
                if "5.7.139" in error_code or "basic authentication is disabled" in error_code.lower():
                    error_msg = f"""
❌ ERREUR D'AUTHENTIFICATION OUTLOOK/HOTMAIL ❌

Le problème: Microsoft a désactivé l'authentification de base pour Outlook/Hotmail.

SOLUTION REQUISE - Créer un mot de passe d'application:
1. Connectez-vous à votre compte Microsoft/Outlook
2. Allez dans Sécurité > Options de sécurité avancées
3. Activez l'authentification à deux facteurs (2FA) si ce n'est pas déjà fait
4. Générez un "mot de passe d'application" pour SMTP
5. Remplacez le SMTP_PASSWORD dans votre fichier .env par ce nouveau mot de passe

Détails de l'erreur: {error_code}
"""
                else:
                    error_msg = f"SMTP Authentication failed for bulletin: {error_code}"

                logger.error(error_msg)
                print(error_msg)
                return False

            except smtplib.SMTPException as e:
                logger.error(f"Tentative {attempt + 1} échouée - Erreur SMTP: {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)
                    continue
                return False

            except Exception as e:
                logger.error(f"Tentative {attempt + 1} échouée - Erreur inattendue: {e}")
                if attempt < max_retries - 1:
                    time.sleep(min(2 ** attempt, 5))  # Cap à 5 secondes
                    continue
                return False

            finally:
                # Always return connection to pool
                if server:
                    self.smtp_pool.return_connection(server)

        logger.error(f"Échec définitif après {max_retries} tentatives pour {email_obj.recipient_email}")
        return False


    # Méthodes utilitaires pour monitoring des performances
    def get_performance_stats(self) -> dict:
        """Retourne les statistiques de performance détaillées"""
        # Stats du nouveau système de monitoring
        current_stats = self.performance_monitor.get_current_stats()
        
        # Stats legacy pour compatibilité
        if self.stats['start_time']:
            total_time = time.time() - self.stats['start_time']
            emails_per_second = self.stats['total_sent'] / total_time if total_time > 0 else 0
        else:
            total_time = 0
            emails_per_second = 0
        
        # Fusion des deux systèmes
        return {
            **current_stats,
            'legacy_total_sent': self.stats['total_sent'],
            'legacy_total_failed': self.stats['total_failed'],
            'legacy_total_time': total_time,
            'legacy_emails_per_second': emails_per_second,
            'recommendations': self.performance_monitor.get_recommendations()
        }
    
    def reset_stats(self):
        """Remet à zéro les statistiques"""
        self.stats = {
            'total_sent': 0,
            'total_failed': 0,
            'start_time': None,
            'batch_times': []
        }
        self.performance_monitor = PerformanceMonitor()
    
    def get_optimized_config(self, email_count: int) -> dict:
        """Retourne la configuration optimisée pour un nombre d'emails donné"""
        return PerformanceConfig.get_optimized_settings(email_count)


email_service = EmailService()
