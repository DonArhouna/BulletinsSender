# 📖 Guide Utilisateur - SendBulletin

## 🚀 Démarrage de l'application

### Backend
```bash
cd backend
uvicorn app.main:app --reload
```
Le backend sera accessible sur : `http://localhost:8000`

### Frontend
```bash
cd frontend
npm run dev
```
Le frontend sera accessible sur : `http://localhost:5173`

## 📧 Envoi de bulletins - Nouvelle interface

### 1️⃣ Sélection du dossier

1. Cliquez sur le champ **"Choisir le dossier"**
2. Sélectionnez le dossier contenant vos fichiers PDF

**Nouveau** : Un composant stylé apparaît avec :
- 📁 Icône de dossier
- 📄 Nombre de fichiers sélectionnés
- ❌ Bouton "Annuler" pour désélectionner
- ✅ Message "Prêt à envoyer les bulletins aux destinataires"

```
┌─────────────────────────────────────────────────────┐
│ 📁  📄 15 fichier(s) PDF sélectionné(s)    [Annuler]│
│     Prêt à envoyer les bulletins aux destinataires  │
└─────────────────────────────────────────────────────┘
```

### 2️⃣ Remplissage des informations

- **Email de l'envoyeur** : Votre adresse email professionnelle
- **Sujet de l'email** : Par défaut "Votre bulletin de salaire"
- **Message personnalisé** : Message optionnel pour vos employés

### 3️⃣ Envoi des bulletins

Cliquez sur le bouton **"Envoyer les bulletins"**

**Nouveau** : Pendant l'envoi, vous verrez :

#### Bouton avec animation
```
┌──────────────────────────────────┐
│  ⟳  Envoi en cours...            │
└──────────────────────────────────┘
```
- Le bouton est désactivé (impossible de cliquer plusieurs fois)
- Icône de chargement animée
- Texte "Envoi en cours..."

#### Alert de progression
```
┌─────────────────────────────────────────────────────┐
│ ⟳  Envoi des bulletins en cours...                  │
│    Veuillez patienter pendant le traitement et      │
│    l'envoi des emails.                              │
└─────────────────────────────────────────────────────┘
```

### 4️⃣ Confirmation de l'envoi

**Nouveau** : Message de succès détaillé avec statistiques :

```
┌─────────────────────────────────────────────────────┐
│ ✅ Envoi réussi !                                    │
│                                                      │
│ ✅ 15 email(s) envoyé(s) avec succès                │
│ Total : 15 fichier(s) traité(s)                     │
└─────────────────────────────────────────────────────┘
```

Si des échecs sont détectés :
```
┌─────────────────────────────────────────────────────┐
│ ✅ Envoi réussi !                                    │
│                                                      │
│ ✅ 13 email(s) envoyé(s) avec succès                │
│ ⚠️ 2 échec(s)                                       │
│ Total : 15 fichier(s) traité(s)                     │
└─────────────────────────────────────────────────────┘
```

### 5️⃣ Historique automatique

Après l'envoi, l'historique se rafraîchit automatiquement et affiche :
- La période d'envoi (Mois Année)
- La date et heure de la dernière activité
- Le nombre de bulletins envoyés
- Le statut (envoyés/échecs)

## 🎨 Codes couleurs

| Couleur | Signification |
|---------|---------------|
| 🔵 Bleu ciel (Sky) | Sélection de fichiers, interface principale |
| 🔵 Bleu (Blue) | Envoi en cours, progression |
| 🟢 Vert (Green) | Succès, validation |
| 🟠 Orange | Avertissement, échecs partiels |
| 🔴 Rouge | Erreur, échec complet |

## ✅ Avantages de la nouvelle interface

### Avant
- ❌ Pas de feedback pendant l'envoi
- ❌ Message de succès basique
- ❌ Affichage simple du nombre de fichiers
- ❌ Possibilité de cliquer plusieurs fois

### Après
- ✅ **Feedback visuel clair** à chaque étape
- ✅ **Statistiques détaillées** après l'envoi
- ✅ **Composant stylé** pour la sélection de fichiers
- ✅ **Protection** contre les clics multiples
- ✅ **Animation fluide** et professionnelle
- ✅ **Messages informatifs** tout au long du processus

## 🔍 Vérification dans la base de données

Pour vérifier que les emails sont bien enregistrés :

```bash
cd backend
python test_send_bulletin_db.py
```

Vous verrez :
```
============================================================
VÉRIFICATION DES EMAILS DANS LA BASE DE DONNÉES
============================================================

📊 Total d'emails AVANT: 45

📈 Statistiques par statut:
  - sent: 40
  - failed: 5

📬 5 derniers emails:
  📧 ID: 45
     À: employe@example.com
     Sujet: Votre bulletin de salaire
     Statut: sent
     Date création: 2025-10-28 10:30:00
     Date envoi: 2025-10-28 10:30:05
     Tenant ID: 1
```

## 🐛 Résolution de problèmes

### Le bouton reste bloqué sur "Envoi en cours..."
- Vérifiez que le backend est bien démarré
- Vérifiez la console du navigateur (F12) pour les erreurs
- Rafraîchissez la page (F5)

### Les fichiers ne sont pas sélectionnés
- Assurez-vous de sélectionner un **dossier** et non des fichiers individuels
- Le dossier doit contenir des fichiers PDF

### L'historique ne s'affiche pas
- Cliquez sur le bouton "Rafraîchir"
- Vérifiez que vous êtes bien connecté
- Vérifiez que des emails ont été envoyés

### Message d'erreur "Impossible de contacter le serveur"
- Vérifiez que le backend est démarré sur `http://localhost:8000`
- Vérifiez votre connexion réseau
- Vérifiez les logs du backend

## 📝 Format des fichiers PDF

Les fichiers PDF doivent contenir à la fin :
1. **Email du destinataire** : Format standard (exemple@domain.com)
2. **Mot de passe** (optionnel) : Pour protéger le PDF

Exemple de contenu à la fin du PDF :
```
...
[Contenu du bulletin]
...
employe@entreprise.com
MotDePasse123
```

## 🔐 Sécurité

- ✅ Authentification JWT requise
- ✅ Isolation des données par tenant (multi-tenancy)
- ✅ Validation des fichiers (uniquement PDF)
- ✅ Protection contre les injections
- ✅ Logs détaillés pour audit

## 📊 Statistiques et rapports

L'historique affiche :
- **Période** : Mois et année de l'envoi
- **Dernière activité** : Date et heure précises
- **Nombre de bulletins** : Total envoyé dans la période
- **Statut** : Résumé des succès et échecs

Exemple :
```
┌─────────────────────────────────────────────────────┐
│ Octobre 2025                              45        │
│ Dernière activité : 28/10/2025 10:30    bulletins  │
│ 40 envoyés, 5 échecs                                │
└─────────────────────────────────────────────────────┘
```

## 🎯 Bonnes pratiques

1. **Préparation des fichiers**
   - Vérifiez que tous les PDFs contiennent les informations nécessaires
   - Testez avec 1-2 fichiers avant un envoi massif

2. **Vérification avant envoi**
   - Vérifiez l'email de l'envoyeur
   - Personnalisez le sujet et le message si nécessaire
   - Vérifiez le nombre de fichiers sélectionnés

3. **Après l'envoi**
   - Consultez les statistiques dans le message de confirmation
   - Vérifiez l'historique
   - En cas d'échecs, vérifiez les logs du backend

4. **Maintenance**
   - Consultez régulièrement l'historique
   - Vérifiez la base de données périodiquement
   - Gardez une sauvegarde des PDFs envoyés

## 🆘 Support

En cas de problème :
1. Consultez les logs du backend
2. Vérifiez la console du navigateur (F12)
3. Exécutez le script de diagnostic : `python test_send_bulletin_db.py`
4. Vérifiez la configuration dans `backend/.env`

## 🎉 Conclusion

La nouvelle interface offre une expérience utilisateur **professionnelle, intuitive et rassurante** avec :
- ✅ Feedback visuel à chaque étape
- ✅ Messages clairs et détaillés
- ✅ Protection contre les erreurs
- ✅ Historique dynamique et en temps réel
- ✅ Enregistrement automatique dans PostgreSQL

