# Configuration SMTP pour Outlook/Hotmail

## Problème
Microsoft a désactivé l'authentification de base SMTP pour les comptes Outlook/Hotmail pour des raisons de sécurité. Vous devez maintenant utiliser un **mot de passe d'application**.

## Solution : Créer un mot de passe d'application

### Étape 1 : Activer l'authentification à deux facteurs (2FA)
1. Connectez-vous à votre compte Microsoft : https://account.microsoft.com/
2. Allez dans **Sécurité** > **Options de sécurité avancées**
3. Activez **Vérification en deux étapes** si ce n'est pas déjà fait

### Étape 2 : Générer un mot de passe d'application
1. Dans les **Options de sécurité avancées**, trouvez la section **Mots de passe d'application**
2. Cliquez sur **Créer un nouveau mot de passe d'application**
3. Donnez-lui un nom descriptif comme "SendBulletin SMTP"
4. Copiez le mot de passe généré (il ressemble à : `abcd-efgh-ijkl-mnop`)

### Étape 3 : Mettre à jour votre configuration
1. Ouvrez le fichier `.env` dans le dossier `backend`
2. Remplacez la valeur de `SMTP_PASSWORD` par le mot de passe d'application :
   ```
   SMTP_PASSWORD=abcd-efgh-ijkl-mnop
   ```
3. Sauvegardez le fichier

### Étape 4 : Redémarrer le serveur
```bash
# Arrêtez le serveur (Ctrl+C)
# Puis redémarrez-le
uvicorn app.main:app --reload
```

## Configuration alternative : Gmail

Si vous préférez utiliser Gmail, voici la configuration :

### Dans le fichier `.env` :
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=votre-email@gmail.com
SMTP_PASSWORD=votre-mot-de-passe-application-gmail
EMAILS_FROM_EMAIL=votre-email@gmail.com
```

### Pour Gmail, vous devez aussi :
1. Activer la vérification en 2 étapes
2. Générer un mot de passe d'application dans les paramètres de sécurité Google

## Vérification
Une fois configuré, testez l'envoi d'un bulletin. Vous devriez voir :
```
✅ Bulletin email sent successfully to destinataire@example.com
```

Au lieu de :
```
❌ SMTP Authentication failed for bulletin: (535, b'5.7.139 Authentication unsuccessful...')
```

## Dépannage

### Erreur persistante ?
- Vérifiez que le mot de passe d'application est correctement copié (sans espaces)
- Assurez-vous que la 2FA est bien activée
- Essayez de générer un nouveau mot de passe d'application

### Autres erreurs SMTP courantes :
- **Port 587** : Utilisé pour STARTTLS (recommandé)
- **Port 465** : Utilisé pour SSL/TLS direct
- **Port 25** : Généralement bloqué par les FAI

## Sécurité
- Ne partagez jamais votre mot de passe d'application
- Révoque les mots de passe d'application non utilisés
- Utilisez un mot de passe d'application différent pour chaque service