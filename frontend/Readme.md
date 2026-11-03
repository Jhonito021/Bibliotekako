# BiblioTech — Application de gestion de bibliothèque

BiblioTech est un projet académique de Licence 3 visant à faciliter la gestion d'une bibliothèque : livres, exemplaires, lecteurs, emprunts, retours et réservations.

> **Important :** ce README décrit le périmètre et l'architecture prévus. Adaptez les commandes, les variables et les endpoints à votre code réel.

## Objectifs

- Centraliser les informations sur les livres et leurs exemplaires.
- Gérer les utilisateurs et leurs rôles.
- Suivre les emprunts, les retours, les retards et les réservations.
- Proposer une API REST utilisable par une interface web.

## Fonctionnalités prévues

### Administrateur
- Gérer les utilisateurs et les rôles.
- Consulter les statistiques et les journaux d'activité.
- Configurer les paramètres de l'application.

### Bibliothécaire
- Gérer les livres, auteurs, catégories et éditeurs.
- Gérer les lecteurs.
- Enregistrer les emprunts et les retours.
- Suivre les retards et gérer les réservations.

### Lecteur
- Rechercher et consulter les livres.
- Voir la disponibilité des exemplaires.
- Consulter son historique d'emprunts.
- Effectuer et suivre des réservations, selon les règles définies.

Ces fonctionnalités sont prévues et ne sont disponibles que si elles sont implémentées dans le code.

## Technologies proposées

| Élément | Technologie |
|---|---|
| Backend | Python 3, Flask |
| Base de données | MySQL |
| ORM | Flask-SQLAlchemy |
| Migrations | Flask-Migrate |
| Authentification API | Flask-JWT-Extended |
| Hachage des mots de passe | Flask-Bcrypt |
| Validation / sérialisation | Marshmallow ou Flask-Smorest |
| Tests | pytest |
| Frontend | À préciser selon le choix retenu |

## Architecture proposée

```text
bibliotech/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── extensions.py
│   ├── models/
│   ├── schemas/
│   ├── repositories/
│   ├── services/
│   ├── routes/
│   ├── utils/
│   └── errors/
├── migrations/
├── tests/
├── .env.example
├── .gitignore
├── requirements.txt
├── run.py
└── README.md
```

Cette arborescence est indicative : ajustez-la à la structure réelle du projet.

## Prérequis

- Python 3.10 ou version compatible avec les dépendances.
- MySQL Server.
- Git.
- Un environnement virtuel Python.

Vérifiez vos installations :

```bash
python --version
pip --version
git --version
```

## Installation

### 1. Cloner le dépôt

Remplacez les valeurs entre chevrons par les informations de votre dépôt :

```bash
git clone <URL_DU_DEPOT>
cd <NOM_DU_DOSSIER>
```

### 2. Créer et activer un environnement virtuel

**Windows PowerShell**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Installer les dépendances

Si `requirements.txt` existe :

```bash
pip install -r requirements.txt
```

Sinon, installez les dépendances réellement utilisées. Exemple de base :

```bash
pip install Flask Flask-SQLAlchemy Flask-Migrate Flask-JWT-Extended Flask-Bcrypt marshmallow pymysql python-dotenv
```

Vous pouvez ensuite enregistrer les versions installées :

```bash
pip freeze > requirements.txt
```

## Configuration de MySQL

Connectez-vous à MySQL puis exécutez :

```sql
CREATE DATABASE bibliotech
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER 'bibliotech_user'@'localhost'
  IDENTIFIED BY 'CHANGEZ_CE_MOT_DE_PASSE';

GRANT ALL PRIVILEGES ON bibliotech.*
  TO 'bibliotech_user'@'localhost';

FLUSH PRIVILEGES;
```

Adaptez le nom de la base, l'utilisateur et les permissions à votre environnement.

## Variables d'environnement

Créez un fichier `.env` à la racine du projet (ou copiez `.env.example` si disponible) :

```dotenv
FLASK_APP=run.py
FLASK_DEBUG=1
SECRET_KEY=remplacez-par-une-cle-aleatoire
JWT_SECRET_KEY=remplacez-par-une-autre-cle-aleatoire
DATABASE_URL=mysql+pymysql://bibliotech_user:CHANGEZ_CE_MOT_DE_PASSE@localhost:3306/bibliotech
```

La configuration doit correspondre au code de l'application. Ne publiez jamais `.env` ni vos clés secrètes. Ajoutez `.env` à `.gitignore`. En production, désactivez le mode debug et utilisez des secrets forts.

## Lancement

Si `run.py` expose l'application Flask, lancez :

```bash
flask --app run.py run --debug
```

L'application sera généralement accessible à l'adresse :

```text
http://127.0.0.1:5000
```

Si votre projet utilise un autre point d'entrée, adaptez la commande.

### Migrations de base de données

Si Flask-Migrate est configuré :

```bash
flask --app run.py db init
flask --app run.py db migrate -m "Initialisation de la base"
flask --app run.py db upgrade
```

N'exécutez `db init` qu'une seule fois, lorsque le dossier `migrations/` n'existe pas encore. Vérifiez les migrations avant de les appliquer.

## API REST — endpoints proposés

Les routes ci-dessous sont des exemples de conception et ne garantissent pas que ces endpoints existent déjà dans le code.

| Méthode | Endpoint proposé | Description |
|---|---|---|
| `POST` | `/api/auth/login` | Authentifier un utilisateur |
| `GET` | `/api/books` | Lister ou rechercher les livres |
| `GET` | `/api/books/<id>` | Consulter un livre |
| `POST` | `/api/books` | Ajouter un livre (accès autorisé) |
| `PUT` | `/api/books/<id>` | Modifier un livre |
| `DELETE` | `/api/books/<id>` | Archiver ou supprimer un livre selon les règles |
| `GET` | `/api/readers` | Lister les lecteurs (accès autorisé) |
| `POST` | `/api/loans` | Enregistrer un emprunt |
| `PATCH` | `/api/loans/<id>/return` | Enregistrer un retour |
| `GET` | `/api/reservations` | Consulter les réservations selon les droits |

Pour tester l'API, utilisez Postman, Insomnia ou `curl`. Consultez les routes réelles du projet pour connaître les champs et codes de réponse exacts.

## Tests

Si le projet utilise pytest :

```bash
pytest
pytest -v
```

Les tests devraient couvrir l'authentification, les permissions par rôle, la recherche, la disponibilité des exemplaires, les emprunts, les retours et les réservations.

## Sécurité

- Hacher les mots de passe ; ne jamais les stocker en clair.
- Protéger les routes selon les rôles et permissions.
- Valider les données reçues par l'API.
- Ne pas exposer les secrets ni les données personnelles dans les logs.
- Utiliser HTTPS en production.
- Désactiver le mode debug en production.
- Sauvegarder régulièrement la base de données.

## Contribution

1. Créez une branche pour votre fonctionnalité :

   ```bash
   git checkout -b feature/nom-fonctionnalite
   ```

2. Implémentez la fonctionnalité et ajoutez des tests.
3. Vérifiez que les tests passent.
4. Soumettez vos changements selon le processus du dépôt.

## Licence

Aucune licence n'est définie ici. Ajoutez un fichier `LICENSE` et précisez la licence choisie avant de diffuser publiquement le projet.

---

Projet académique — Licence 3.  
**BiblioTech : une gestion plus simple et organisée de la bibliothèque.**
