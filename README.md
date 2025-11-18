# Bulletin Sender

Bulletin Sender est une application web complète de gestion et d'envoi de bulletins d'information par email. Elle permet aux utilisateurs de créer, gérer et envoyer des bulletins personnalisés à leurs abonnés.

## Fonctionnalités principales

### Pour les Clients
- **Interface client intuitive** : Tableau de bord personnel pour suivre les envois
- **Gestion des abonnements** : Consultation des forfaits souscrits et historique des paiements
- **Historique des envois** : Suivi détaillé des bulletins envoyés
- **Statistiques** : Graphiques et métriques sur les performances des envois

### Pour les Superadministrateurs
- **Gestion des utilisateurs** : Création, modification et suppression des comptes clients
- **Gestion des forfaits** : Configuration des plans d'abonnement et tarifs
- **Surveillance des envois** : Monitoring en temps réel des campagnes email
- **Tableaux de bord avancés** : Statistiques globales et rapports détaillés
- **Gestion des factures** : Génération automatique des factures PDF

## Architecture technique

### Backend
- **Framework** : FastAPI (Python)
- **Base de données** : PostgreSQL avec SQLAlchemy
- **Authentification** : JWT tokens
- **Envoi d'emails** : SMTP avec optimisation des performances
- **Migrations** : Alembic
- **Architecture modulaire** : Séparation claire des responsabilités (users, emails, subscriptions, sends)

### Frontend
- **Framework** : React avec TypeScript
- **UI/UX** : Tailwind CSS + shadcn/ui
- **Build tool** : Vite
- **Routing** : React Router
- **State management** : React hooks

## Installation et déploiement

### Prérequis
- Python 3.11+
- Node.js 18+
- PostgreSQL
- Git

### Installation du backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Installation du frontend
```bash
cd frontend
npm install
```

### Configuration
1. Copier `.env.example` vers `.env` et configurer les variables d'environnement
2. Configurer la base de données PostgreSQL
3. Exécuter les migrations Alembic

### Lancement
```bash
# Backend
cd backend
uvicorn app.main:app --reload

# Frontend
cd frontend
npm run dev
```

## Structure du projet

```
bulletin-sender/
├── backend/                 # API FastAPI
│   ├── app/
│   │   ├── core/           # Configuration et sécurité
│   │   ├── db/             # Connexion base de données
│   │   ├── models/         # Modèles SQLAlchemy
│   │   ├── modules/        # Modules métier
│   │   └── main.py         # Point d'entrée
│   ├── alembic/            # Migrations base de données
│   └── requirements.txt    # Dépendances Python
├── frontend/                # Application React
│   ├── src/
│   │   ├── components/     # Composants réutilisables
│   │   ├── pages/          # Pages de l'application
│   │   ├── lib/            # Utilitaires
│   │   └── App.tsx         # Application principale
│   └── package.json        # Dépendances Node.js
└── README.md
```

## API Documentation

L'API FastAPI fournit une documentation interactive accessible via `/docs` une fois le serveur lancé.

### Endpoints principaux
- `POST /auth/login` : Authentification
- `GET /users/me` : Profil utilisateur
- `POST /emails/send` : Envoi de bulletin
- `GET /subscriptions/` : Gestion des abonnements
- `GET /dashboard/stats` : Statistiques du tableau de bord

## Sécurité

- Authentification JWT
- Hachage des mots de passe avec bcrypt
- Validation des données d'entrée
- Protection CSRF
- Logs d'audit

## Performance

- Optimisation des requêtes email avec files d'attente
- Cache des données fréquemment consultées
- Pagination des listes volumineuses
- Monitoring des performances en temps réel

## Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commit les changements (`git commit -am 'Ajout nouvelle fonctionnalité'`)
4. Push la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Ouvrir une Pull Request

## Licence

Ce projet est sous licence MIT.

## Support

Pour toute question ou problème, veuillez ouvrir une issue sur GitHub ou contacter l'équipe de développement.
