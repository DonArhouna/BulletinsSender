# TODO: Implémentation du module d'envoi d'emails FastAPI

## Étapes à suivre :
- [x] Mettre à jour schemas.py : Ajouter SendEmailRequest et SendEmailResponse
- [x] Mettre à jour service.py : Ajouter méthode send_custom_email avec détection automatique des credentials, support multi-destinataires et pièces jointes
- [x] Mettre à jour router.py : Ajouter endpoint POST /send-email
- [x] Tester l'importation des modules (schemas, service, router)
- [x] Corriger le problème de dépendance dans l'endpoint (Depends() retiré)
- [ ] Tester l'endpoint avec mode global et personnalisé
- [ ] Vérifier gestion des exceptions SMTP

## Implémentation de l'envoi de bulletins
- [x] Créer une nouvelle route POST /send-bulletins qui prend le chemin du dossier et l'email de l'expéditeur
- [x] Implémenter la lecture des PDFs et extraction des champs masqués (email et mot de passe)
- [x] Ajouter la fonctionnalité d'envoi individuel des bulletins avec confidentialité
- [x] Retourner un JSON avec le statut de chaque envoi (succès/erreur)
- [x] Inclure le mot de passe PDF dans le corps du mail (bonus)
- [x] Permettre un sujet et message personnalisé (bonus)
- [ ] Tester avec MailHog en local

## Modification du champ "Chemin du dossier"
- [x] Changer le titre en "Choisir le dossier"
- [x] Rendre le champ cliquable pour sélectionner un dossier via HTML5 directory picker
- [x] Mettre à jour le backend pour accepter les fichiers PDF téléchargés au lieu d'un chemin de dossier
- [x] Modifier schemas.py : Remplacer folder_path par files: List[UploadFile]
- [x] Modifier router.py : Changer l'endpoint pour accepter les fichiers via Form
- [x] Modifier service.py : Adapter send_bulletins pour traiter les fichiers téléchargés
- [x] Modifier Client.tsx : Changer l'input en file input avec webkitdirectory
