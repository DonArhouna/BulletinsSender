# 🧪 Tests Rapides - SendBulletin

## 🚀 Démarrage rapide

### Terminal 1 - Backend
```bash
cd backend
uvicorn app.main:app --reload
```
✅ Backend accessible sur : http://localhost:8000

### Terminal 2 - Frontend
```bash
cd frontend
npm run dev
```
✅ Frontend accessible sur : http://localhost:5173

---

## ✅ Test 1 : Vérification de la base de données

### Avant l'envoi
```bash
cd backend
python test_send_bulletin_db.py
```

**Résultat attendu** :
```
============================================================
VÉRIFICATION DES EMAILS DANS LA BASE DE DONNÉES
============================================================

📊 Total d'emails AVANT: 21

📈 Statistiques par statut:
  - failed: 21

📬 5 derniers emails:
  ...
```

---

## ✅ Test 2 : Interface de sélection de fichiers

### Étapes
1. Ouvrir http://localhost:5173
2. Se connecter avec vos identifiants
3. Cliquer sur le champ "Choisir le dossier"
4. Sélectionner un dossier contenant des PDFs

### Résultat attendu
Un composant Alert stylé apparaît :
```
┌─────────────────────────────────────────────────────┐
│ 📁  📄 X fichier(s) PDF sélectionné(s)    [Annuler] │
│     Prêt à envoyer les bulletins aux destinataires  │
└─────────────────────────────────────────────────────┘
```

### Vérifications
- ✅ Icône de dossier visible
- ✅ Nombre de fichiers correct
- ✅ Bouton "Annuler" présent
- ✅ Message de confirmation affiché

### Test du bouton Annuler
1. Cliquer sur "Annuler"
2. Le composant Alert disparaît
3. Le champ de sélection est réinitialisé

---

## ✅ Test 3 : Loading pendant l'envoi

### Étapes
1. Sélectionner un dossier avec 2-3 PDFs
2. Remplir :
   - Email : votre.email@test.com
   - Sujet : Test bulletin
   - Message : Message de test
3. Cliquer sur "Envoyer les bulletins"

### Résultat attendu pendant l'envoi

#### Bouton
```
┌──────────────────────────────────┐
│  ⟳  Envoi en cours...            │
└──────────────────────────────────┘
```
- ✅ Icône de chargement animée (rotation)
- ✅ Texte "Envoi en cours..."
- ✅ Bouton désactivé (grisé)
- ✅ Impossible de cliquer à nouveau

#### Alert de progression
```
┌─────────────────────────────────────────────────────┐
│ ⟳  Envoi des bulletins en cours...                  │
│    Veuillez patienter pendant le traitement et      │
│    l'envoi des emails.                              │
└─────────────────────────────────────────────────────┘
```
- ✅ Fond bleu clair
- ✅ Icône de chargement animée
- ✅ Message informatif

---

## ✅ Test 4 : Message de confirmation

### Résultat attendu après l'envoi

#### Cas de succès complet
```
┌─────────────────────────────────────────────────────┐
│ ✅ Envoi réussi !                                    │
│                                                      │
│ ✅ 3 email(s) envoyé(s) avec succès                 │
│ Total : 3 fichier(s) traité(s)                      │
└─────────────────────────────────────────────────────┘
```

#### Cas avec échecs partiels
```
┌─────────────────────────────────────────────────────┐
│ ✅ Envoi réussi !                                    │
│                                                      │
│ ✅ 2 email(s) envoyé(s) avec succès                 │
│ ⚠️ 1 échec(s)                                       │
│ Total : 3 fichier(s) traité(s)                      │
└─────────────────────────────────────────────────────┘
```

### Vérifications
- ✅ Icône verte de validation
- ✅ Nombre d'emails envoyés correct
- ✅ Nombre d'échecs affiché si > 0
- ✅ Total de fichiers traités
- ✅ Toast disparaît après 5 secondes

---

## ✅ Test 5 : Réinitialisation du formulaire

### Après l'envoi réussi

Vérifier que :
- ✅ Le champ de sélection de fichiers est vide
- ✅ Le composant Alert des fichiers a disparu
- ✅ Le champ email est vide
- ✅ Le champ message est vide
- ✅ Le sujet est réinitialisé à "Votre bulletin de salaire"

---

## ✅ Test 6 : Historique automatique

### Après l'envoi

L'historique doit se rafraîchir automatiquement et afficher :

```
┌─────────────────────────────────────────────────────┐
│ Octobre 2025                              3         │
│ Dernière activité : 28/10/2025 14:30    bulletins  │
│ 3 envoyés                                           │
└─────────────────────────────────────────────────────┘
```

### Vérifications
- ✅ Nouvelle période ajoutée (ou mise à jour)
- ✅ Nombre de bulletins correct
- ✅ Date et heure de la dernière activité
- ✅ Statut affiché (envoyés/échecs)

### Test du bouton Rafraîchir
1. Cliquer sur "Rafraîchir"
2. Vérifier l'animation de chargement
3. Vérifier que les données sont à jour

---

## ✅ Test 7 : Vérification dans PostgreSQL

### Après l'envoi
```bash
cd backend
python test_send_bulletin_db.py
```

**Résultat attendu** :
```
============================================================
VÉRIFICATION DES EMAILS DANS LA BASE DE DONNÉES
============================================================

📊 Total d'emails AVANT: 24  (21 + 3 nouveaux)

📈 Statistiques par statut:
  - failed: 21
  - sent: 3  ← NOUVEAUX

📬 5 derniers emails:
  📧 ID: 24
     À: destinataire3@example.com
     Sujet: Test bulletin
     Statut: sent  ← NOUVEAU
     Date création: 2025-10-28 14:30:00
     Date envoi: 2025-10-28 14:30:05  ← NOUVEAU
     Tenant ID: 1

  📧 ID: 23
     À: destinataire2@example.com
     Sujet: Test bulletin
     Statut: sent  ← NOUVEAU
     ...
```

### Vérifications
- ✅ Le nombre total d'emails a augmenté
- ✅ Les nouveaux emails ont le statut "sent"
- ✅ Le champ `sent_at` est rempli
- ✅ Le `tenant_id` est correct
- ✅ Les champs `recipient_email`, `subject`, `body` sont corrects

---

## ✅ Test 8 : Gestion des erreurs

### Test sans fichiers
1. Ne pas sélectionner de fichiers
2. Cliquer sur "Envoyer les bulletins"

**Résultat attendu** :
```
❌ Fichiers requis
Veuillez sélectionner les fichiers PDF des bulletins.
```

### Test sans email
1. Sélectionner des fichiers
2. Laisser le champ email vide
3. Cliquer sur "Envoyer les bulletins"

**Résultat attendu** :
```
❌ Email requis
Veuillez saisir votre email.
```

### Test avec backend arrêté
1. Arrêter le backend (Ctrl+C dans le terminal 1)
2. Essayer d'envoyer des bulletins

**Résultat attendu** :
```
❌ Erreur réseau
Impossible de contacter le serveur.
```

---

## 🎯 Checklist complète

### Interface
- [ ] Composant Alert pour les fichiers sélectionnés
- [ ] Bouton "Annuler" fonctionne
- [ ] Bouton d'envoi avec animation de chargement
- [ ] Alert de progression pendant l'envoi
- [ ] Bouton désactivé pendant l'envoi
- [ ] Message de succès détaillé avec statistiques
- [ ] Réinitialisation du formulaire après envoi

### Fonctionnalités
- [ ] Emails enregistrés dans PostgreSQL
- [ ] Statut mis à jour après envoi (sent/failed)
- [ ] Historique rafraîchi automatiquement
- [ ] Bouton "Rafraîchir" fonctionne
- [ ] Gestion des erreurs (pas de fichiers, pas d'email, etc.)

### Base de données
- [ ] Nouveaux emails visibles dans PostgreSQL
- [ ] Statut "sent" pour les emails réussis
- [ ] Champ `sent_at` rempli
- [ ] `tenant_id` correct
- [ ] Tous les champs remplis correctement

---

## 🐛 Problèmes courants et solutions

### Le bouton reste bloqué sur "Envoi en cours..."
**Solution** :
1. Vérifier que le backend est démarré
2. Ouvrir la console du navigateur (F12)
3. Vérifier les erreurs réseau
4. Rafraîchir la page (F5)

### Les fichiers ne sont pas sélectionnés
**Solution** :
1. Assurez-vous de sélectionner un **dossier** (pas des fichiers individuels)
2. Le dossier doit contenir des fichiers PDF
3. Vérifier les permissions du dossier

### L'historique ne s'affiche pas
**Solution** :
1. Cliquer sur "Rafraîchir"
2. Vérifier que vous êtes connecté
3. Vérifier que des emails ont été envoyés
4. Vérifier les logs du backend

### Erreur "Tenant not found"
**Solution** :
1. Vérifier que l'utilisateur a un `tenant_id` assigné
2. Vérifier la base de données :
```bash
cd backend
python -c "from app.db.session import SessionLocal; from app.models.users import User; db = SessionLocal(); users = db.query(User).all(); print([(u.email, u.tenant_id) for u in users])"
```

---

## 📊 Résultats attendus - Résumé

| Test | Durée | Résultat attendu |
|------|-------|------------------|
| 1. Vérification DB avant | 5s | Affichage des emails existants |
| 2. Sélection de fichiers | 10s | Composant Alert stylé |
| 3. Loading pendant envoi | 5-10s | Animation + Alert de progression |
| 4. Message de confirmation | 2s | Toast avec statistiques |
| 5. Réinitialisation | 1s | Formulaire vide |
| 6. Historique automatique | 2s | Nouvelle période affichée |
| 7. Vérification DB après | 5s | Nouveaux emails avec statut "sent" |
| 8. Gestion des erreurs | 5s | Messages d'erreur appropriés |

**Temps total estimé** : 5-10 minutes

---

## 🎉 Validation finale

Si tous les tests passent :
- ✅ L'historique est dynamique et basé sur PostgreSQL
- ✅ Le loading est stylé et informatif
- ✅ Le message de confirmation est détaillé
- ✅ Le composant de sélection est professionnel
- ✅ L'expérience utilisateur est fluide et rassurante

**Félicitations ! Toutes les fonctionnalités sont opérationnelles ! 🚀**

