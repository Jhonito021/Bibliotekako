# BiblioTech API – Backend

**Version 2 – Documentation technique et guide d'intégration frontend**

BiblioTech est une application de gestion de bibliothèque développée avec Flask, MySQL et React.

Ce backend fournit une API REST permettant de gérer les utilisateurs, les livres, les exemplaires, les emprunts, les retours, les réservations, les pénalités, les notifications et les statistiques.

Ce document explique comment installer, démarrer, tester et utiliser l'API, notamment depuis le frontend React.

---

# 1. Technologies utilisées

| Technologie | Utilisation |
|---|---|
| Python / Flask | Développement de l'API |
| MySQL | Base de données |
| Flask-SQLAlchemy | Gestion des données |
| Flask-Migrate | Migrations de la base |
| Flask-JWT-Extended | Authentification JWT |
| Flask-Bcrypt | Hachage des mots de passe |
| React | Frontend |

# 2. Structure du projet

L'organisation principale du backend est la suivante :

```text
backend/
│
├── app/
│   ├── models/
│   ├── routes/
│   ├── controllers/
│   ├── services/
│   ├── repositories/
│   ├── schemas/
│   ├── utils/
│   ├── config.py
│   └── extensions.py
│
├── migrations/
├── .venv/
├── .env
├── .env.example
├── requirements.txt
└── run.py
```

# 3. Installation et configuration

## Étape 1 : Récupérer le projet

Extraire le ZIP du backend dans le projet existant :

```text
E:\Projet\Bibliotekako
```

Accepter le remplacement des fichiers concernés.

**IMPORTANT :**
- Ne pas supprimer le fichier `.env`.
- Ne pas supprimer le dossier `migrations/`.
- Ne pas supprimer le dossier `.venv/`.
- Ne jamais envoyer le fichier `.env` sur GitHub.

## Étape 2 : Ouvrir le backend

Ouvrir PowerShell et exécuter :

```powershell
cd E:\Projet\Bibliotekako\backend
```

Activer l'environnement virtuel :

```powershell
.\.venv\Scripts\Activate.ps1
```

Si l'environnement virtuel n'existe pas encore :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## Étape 3 : Installer les dépendances

```powershell
pip install -r requirements.txt
```

Attendre la fin de l'installation avant de continuer.

## Étape 4 : Configurer le fichier .env

Si le fichier `.env` n'existe pas, créer une copie de `.env.example` :

```powershell
Copy-Item .env.example .env
```

Ouvrir `.env` et configurer les variables :

```dotenv
SECRET_KEY=une_cle_secrete_longue_et_aleatoire
JWT_SECRET_KEY=une_autre_cle_secrete_longue_et_aleatoire

DATABASE_URL=mysql+pymysql://bibliotech_user:VOTRE_MOT_DE_PASSE@localhost:3306/bibliotech_db

FRONTEND_URL=http://localhost:5173

LOAN_DURATION_DAYS=14
MAX_ACTIVE_LOANS=5
FINE_PER_DAY=500
RESERVATION_HOLD_DAYS=2
```

Remplacer `VOTRE_MOT_DE_PASSE` par le mot de passe réel de l'utilisateur MySQL.

Les clés secrètes doivent être suffisamment longues et ne doivent pas être partagées.

## Étape 5 : Vérifier MySQL

S'assurer que :
- MySQL Server est démarré.
- La base `bibliotech_db` existe.
- L'utilisateur `bibliotech_user` possède les droits nécessaires.
- Les identifiants correspondent à ceux du fichier `.env`.

Tester la connexion :

```powershell
mysql -u bibliotech_user -p -h localhost -P 3306 bibliotech_db
```

Si la connexion fonctionne, quitter MySQL avec :

```sql
EXIT;
```

## Étape 6 : Mettre à jour la base de données

Dans le terminal du backend, avec l'environnement virtuel activé :

```powershell
flask --app run db migrate -m "Add circulation and operations"
```

Puis :

```powershell
flask --app run db upgrade
```

**Attention :**
- Ne pas exécuter `flask db init` une deuxième fois.
- Ne pas supprimer les anciennes migrations.
- Examiner le fichier de migration généré avant de lancer `db upgrade`.
- Si des modifications inattendues apparaissent sur les tables `users`, `books`, `authors`, `categories` ou `publishers`, arrêter et vérifier la migration.

## Étape 7 : Démarrer le serveur

```powershell
python run.py
```

L'API est accessible à l'adresse :

```text
http://127.0.0.1:5000/api
```

Garder ce terminal ouvert pendant les tests et l'utilisation du frontend.

---

# 4. Vérifier que le backend fonctionne

Avant de commencer l'intégration frontend, vérifier les endpoints suivants.

| Méthode | URL | Résultat attendu |
|---|---|---|
| GET | `/api` | API disponible |
| GET | `/api/health` | Serveur opérationnel |
| GET | `/api/health/database` | Base de données connectée |

Pour tester la base de données :

```text
GET http://127.0.0.1:5000/api/health/database
```

Résultat attendu :

```json
{
  "success": true,
  "database": "connected"
}
```

Si ces vérifications fonctionnent, le backend est prêt pour les tests fonctionnels.

---

# 5. Tester l'API avec Postman

**Base URL :**

```text
http://127.0.0.1:5000/api
```

Toutes les requêtes JSON doivent utiliser cet en-tête :

```http
Content-Type: application/json
```

## Étape 1 : Créer un compte

Endpoint :

```http
POST /api/auth/register
```

URL complète :

```text
http://127.0.0.1:5000/api/auth/register
```

Dans Postman :

1. Choisir la méthode `POST`.
2. Ouvrir l'onglet `Body`.
3. Sélectionner `raw`.
4. Choisir le format `JSON`.
5. Coller le contenu suivant :

```json
{
  "full_name": "Jean Rakoto",
  "email": "jean@example.com",
  "password": "Password123!"
}
```

Réponse attendue : `201 Created`.

```json
{
  "success": true,
  "message": "Compte lecteur créé.",
  "user": {
    "id": 1,
    "full_name": "Jean Rakoto",
    "email": "jean@example.com",
    "role": "reader"
  }
}
```

Le contenu exact de l'objet utilisateur dépend des champs exposés par `to_dict()`.

**Important :** l'inscription publique crée automatiquement un compte avec le rôle `reader`.

## Étape 2 : Se connecter

Endpoint :

```http
POST /api/auth/login
```

URL complète :

```text
http://127.0.0.1:5000/api/auth/login
```

Body JSON :

```json
{
  "email": "jean@example.com",
  "password": "Password123!"
}
```

Réponse attendue : `200 OK`.

La réponse contient notamment :

```json
{
  "success": true,
  "user": {
    "id": 1,
    "full_name": "Jean Rakoto",
    "email": "jean@example.com",
    "role": "reader"
  },
  "access_token": "VOTRE_ACCESS_TOKEN",
  "refresh_token": "VOTRE_REFRESH_TOKEN"
}
```

**Très important :**

Conserver le champ `access_token`.

Il sera utilisé pour accéder aux endpoints protégés.

Ne pas confondre :
- `access_token` : utilisé pour les requêtes authentifiées.
- `refresh_token` : utilisé pour renouveler le token d'accès.

## Étape 3 : Tester l'utilisateur connecté

Endpoint :

```http
GET /api/auth/me
```

URL :

```text
http://127.0.0.1:5000/api/auth/me
```

Dans Postman :

1. Ouvrir l'onglet `Authorization`.
2. Sélectionner `Bearer Token`.
3. Coller le contenu complet de `access_token`.
4. Ne pas ajouter manuellement le mot `Bearer`.
5. Envoyer la requête.

Réponse attendue : `200 OK`.

Cette route retourne les informations de l'utilisateur connecté.

## Étape 4 : Renouveler le token

Endpoint :

```http
POST /api/auth/refresh
```

Cette route nécessite le `refresh_token`.

Dans Postman :

1. Ouvrir `Authorization`.
2. Sélectionner `Bearer Token`.
3. Coller le `refresh_token`.
4. Envoyer la requête.

La réponse contient un nouvel `access_token`.

## Étape 5 : Tester une route protégée

Pour toutes les routes nécessitant une authentification, utiliser :

```http
Authorization: Bearer VOTRE_ACCESS_TOKEN
```

Sans token valide, l'API peut retourner :
- `401 Unauthorized` : authentification absente ou invalide.
- `422 Unprocessable Entity` : token ou requête invalide selon la validation JWT.

Un compte `reader` ne peut pas accéder automatiquement aux fonctionnalités réservées aux administrateurs ou bibliothécaires.

---

# 6. Intégration avec le frontend React

Cette partie est destinée au développeur frontend.

## Étape 1 : Configurer l'URL de l'API

Dans le projet React, créer un fichier `.env` à la racine du frontend :

```dotenv
VITE_API_URL=http://127.0.0.1:5000/api
```

Redémarrer le serveur React après toute modification du fichier `.env`.

## Étape 2 : Créer un service API

Créer le fichier :

```text
src/services/api.js
```

Contenu :

```javascript
const API_URL = import.meta.env.VITE_API_URL;

export async function apiRequest(endpoint, options = {}) {
  const token = localStorage.getItem("access_token");

  const headers = {
    ...(options.body ? { "Content-Type": "application/json" } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(
      data.message || `Erreur HTTP ${response.status}`
    );
  }

  return data;
}
```

Ce service centralise les appels HTTP et ajoute automatiquement le token lorsqu'il existe.

## Étape 3 : Créer le service d'authentification

Créer le fichier :

```text
src/services/authService.js
```

Contenu :

```javascript
import { apiRequest } from "./api";

export async function registerUser(userData) {
  return apiRequest("/auth/register", {
    method: "POST",
    body: JSON.stringify(userData),
  });
}

export async function loginUser(credentials) {
  const data = await apiRequest("/auth/login", {
    method: "POST",
    body: JSON.stringify(credentials),
  });

  if (data.access_token) {
    localStorage.setItem("access_token", data.access_token);
  }

  if (data.refresh_token) {
    localStorage.setItem("refresh_token", data.refresh_token);
  }

  return data;
}

export async function getCurrentUser() {
  return apiRequest("/auth/me");
}

export function logoutUser() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}
```

## Étape 4 : Exemple d'inscription

```javascript
import { registerUser } from "../services/authService";

async function handleRegister() {
  try {
    const result = await registerUser({
      full_name: "Jean Rakoto",
      email: "jean@example.com",
      password: "Password123!",
    });

    console.log(result.message);
  } catch (error) {
    console.error(error.message);
  }
}
```

## Étape 5 : Exemple de connexion

```javascript
import { loginUser } from "../services/authService";

async function handleLogin() {
  try {
    const result = await loginUser({
      email: "jean@example.com",
      password: "Password123!",
    });

    console.log("Connexion réussie !");
    console.log("Utilisateur :", result.user);

  } catch (error) {
    console.error(error.message);
  }
}
```

## Étape 6 : Récupérer l'utilisateur connecté

```javascript
import { getCurrentUser } from "../services/authService";

async function loadUser() {
  try {
    const result = await getCurrentUser();

    console.log(result.user);

  } catch (error) {
    console.error(error.message);
  }
}
```

**Remarque sur la sécurité :** `localStorage` est utilisé ici pour simplifier l'exemple d'intégration. Pour une application en production, il faudra notamment examiner le stockage des tokens, les risques XSS et la stratégie de renouvellement et d'expiration des sessions.

---

# 7. Rôles et autorisations

L'application utilise trois rôles :

| Rôle | Description |
|---|---|
| `admin` | Administrateur |
| `librarian` | Bibliothécaire |
| `reader` | Lecteur |

### Reader
Le lecteur peut notamment :
- Consulter le catalogue.
- Consulter son profil.
- Effectuer des réservations.
- Consulter ses emprunts.
- Consulter son historique.
- Consulter ses pénalités.
- Consulter ses notifications.

### Librarian
Le bibliothécaire peut accéder aux opérations de gestion autorisées :
- Gestion des livres et exemplaires.
- Gestion des emprunts et retours.
- Gestion des réservations.
- Gestion des pénalités et opérations associées.
- Consultation des tableaux de bord autorisés.

### Admin
L'administrateur dispose des fonctionnalités de gestion avancée :
- Gestion des utilisateurs et des rôles.
- Gestion des paramètres.
- Consultation des journaux d'audit.
- Gestion des opérations réservées à l'administration.

**Important :** les permissions sont vérifiées côté backend. Cacher un bouton dans React ne remplace jamais une vérification d'autorisation côté serveur.

L'inscription publique attribue uniquement le rôle `reader`. La création du premier administrateur doit être réalisée par une procédure d'administration sécurisée.

---

# 8. Documentation des endpoints

Toutes les routes ci-dessous utilisent le préfixe :

```text
/api
```

Sauf indication contraire, les routes protégées nécessitent un `access_token`.

## 8.1 Santé de l'API

| Méthode | Endpoint | Description |
|---|---|---|
| GET | `/health` | Vérifier le serveur |
| GET | `/health/database` | Vérifier MySQL |

## 8.2 Authentification et utilisateurs

| Méthode | Endpoint | Accès |
|---|---|---|
| POST | `/auth/register` | Public |
| POST | `/auth/login` | Public |
| POST | `/auth/refresh` | Refresh token |
| GET | `/auth/me` | Authentifié |
| GET | `/users` | Admin |
| PATCH | `/users/<id>/status` | Admin |
| PATCH | `/users/<id>/role` | Admin |

Exemple : désactiver un utilisateur.

```json
{
  "is_active": false
}
```

Exemple : changer son rôle.

```json
{
  "role": "librarian"
}
```

## 8.3 Catalogue

| Méthode | Endpoint | Accès |
|---|---|---|
| GET | `/books` | Lecture |
| GET | `/books/<id>` | Lecture |
| POST | `/books` | Admin / Bibliothécaire |
| PUT | `/books/<id>` | Admin / Bibliothécaire |
| DELETE | `/books/<id>` | Selon les permissions |
| GET / POST | `/authors` | Lecture / Gestion autorisée |
| GET / POST | `/categories` | Lecture / Gestion autorisée |
| GET / POST | `/publishers` | Lecture / Gestion autorisée |

Filtres disponibles :

```text
GET /books?search=&category_id=&author_id=&page=1&limit=20
```

Paramètres :
- `search` : recherche par texte.
- `category_id` : filtrer par catégorie.
- `author_id` : filtrer par auteur.
- `page` : numéro de page.
- `limit` : nombre de résultats.

## 8.4 Exemplaires

| Méthode | Endpoint | Accès |
|---|---|---|
| GET | `/copies` | Lecture selon permissions |
| GET | `/copies/<id>` | Lecture selon permissions |
| POST | `/copies` | Admin / Bibliothécaire |
| PUT | `/copies/<id>` | Admin / Bibliothécaire |
| PATCH | `/copies/<id>/status` | Admin / Bibliothécaire |
| GET | `/books/<id>/copies` | Lecture |

Exemple de création :

```json
{
  "book_id": 1,
  "inventory_code": "INV-0001"
}
```

Exemple de changement de statut :

```json
{
  "status": "damaged"
}
```

Statuts possibles :
- `available`
- `borrowed`
- `reserved`
- `damaged`
- `lost`

## 8.5 Emprunts et retours

| Méthode | Endpoint | Accès |
|---|---|---|
| GET | `/loans` | Staff |
| GET | `/loans/<id>` | Propriétaire / Staff |
| POST | `/loans` | Staff |
| POST | `/loans/<id>/return` | Staff |
| PATCH | `/loans/<id>/extend` | Staff |
| GET | `/loans/overdue` | Staff |
| GET | `/me/loans` | Lecteur connecté |
| GET | `/me/loans/history` | Lecteur connecté |

Exemple de création d'un emprunt :

```json
{
  "reader_id": 1,
  "copy_id": 1
}
```

## 8.6 Réservations

| Méthode | Endpoint | Accès |
|---|---|---|
| GET | `/reservations` | Staff |
| GET | `/reservations/<id>` | Propriétaire / Staff |
| POST | `/reservations` | Authentifié |
| POST | `/reservations/<id>/cancel` | Selon permissions |
| PATCH | `/reservations/<id>/status` | Staff |
| GET | `/me/reservations` | Lecteur connecté |

Exemple de réservation :

```json
{
  "book_id": 1
}
```

Exemple de changement de statut :

```json
{
  "status": "ready"
}
```

Statuts possibles :
- `waiting`
- `ready`
- `fulfilled`
- `cancelled`
- `expired`

## 8.7 Pénalités

| Méthode | Endpoint | Accès |
|---|---|---|
| GET | `/fines` | Staff |
| GET | `/fines/<id>` | Propriétaire / Staff |
| GET | `/me/fines` | Lecteur connecté |
| POST | `/fines/<id>/payment` | Staff |
| POST | `/fines/<id>/waive` | Admin |

Le paiement est enregistré comme un règlement hors ligne.

## 8.8 Notifications et profil

| Méthode | Endpoint | Accès |
|---|---|---|
| GET | `/notifications` | Authentifié |
| GET | `/notifications/unread-count` | Authentifié |
| PATCH | `/notifications/<id>/read` | Authentifié |
| PATCH | `/notifications/read-all` | Authentifié |
| PUT | `/me` | Authentifié |
| PATCH | `/me/password` | Authentifié |

Modification du profil :

```json
{
  "full_name": "Nouveau nom",
  "email": "nouveau@example.com"
}
```

Modification du mot de passe :

```json
{
  "current_password": "ancien_mot_de_passe",
  "new_password": "nouveau123"
}
```

## 8.9 Dashboard et statistiques

Toutes ces routes sont réservées au staff.

| Méthode | Endpoint | Description |
|---|---|---|
| GET | `/dashboard` | Statistiques générales |
| GET | `/dashboard/loans?year=2026` | Statistiques des emprunts |
| GET | `/dashboard/monthly?year=2026` | Statistiques mensuelles |
| GET | `/dashboard/overdue` | Emprunts en retard |
| GET | `/dashboard/popular-books` | Livres populaires |
| GET | `/dashboard/yearly` | Statistiques annuelles |

## 8.10 Audit et paramètres

| Méthode | Endpoint | Accès |
|---|---|---|
| GET | `/audit-logs?limit=50` | Admin |
| GET | `/audit-logs/<id>` | Admin |
| GET | `/settings` | Staff |
| PUT | `/settings` | Admin |

Exemple de modification des paramètres :

```json
{
  "loan_duration_days": 14,
  "max_active_loans": 5,
  "fine_per_day": 500,
  "reservation_hold_days": 2
}
```

---

# 9. Gestion des erreurs HTTP

Le frontend doit interpréter les codes HTTP pour afficher des messages adaptés.

| Code | Signification | Comportement frontend |
|---|---|---|
| 200 | Requête réussie | Afficher les données |
| 201 | Ressource créée | Confirmer la création |
| 400 | Données invalides | Afficher les erreurs de formulaire |
| 401 | Non authentifié | Demander une connexion |
| 403 | Accès interdit | Afficher un message d'accès refusé |
| 404 | Ressource introuvable | Afficher une page ou un message adapté |
| 409 | Conflit | Afficher le conflit |
| 422 | Validation JWT ou requête invalide | Vérifier les données et le token |
| 500 | Erreur serveur | Afficher une erreur générale |

Les messages retournés par l'API sont généralement disponibles dans :

```javascript
data.message
```

Exemple :

```javascript
try {
  const result = await apiRequest("/books");
  console.log(result);
} catch (error) {
  alert(error.message);
}
```

---

# 10. Configuration optionnelle

Les paramètres suivants sont configurables dans `.env` :

```dotenv
LOAN_DURATION_DAYS=14
MAX_ACTIVE_LOANS=5
FINE_PER_DAY=500
RESERVATION_HOLD_DAYS=2
```

| Variable | Description |
|---|---|
| `LOAN_DURATION_DAYS` | Durée d'un emprunt |
| `MAX_ACTIVE_LOANS` | Nombre maximal d'emprunts actifs |
| `FINE_PER_DAY` | Montant de la pénalité par jour |
| `RESERVATION_HOLD_DAYS` | Durée de conservation d'une réservation prête |

---

# 11. Procédure de test complète

Avant de considérer l'intégration terminée, suivre cet ordre :

1. Vérifier que MySQL fonctionne.
2. Vérifier que `/api/health/database` retourne `200`.
3. Créer un compte lecteur avec `/api/auth/register`.
4. Se connecter avec `/api/auth/login`.
5. Récupérer l'`access_token`.
6. Tester `/api/auth/me` avec le token.
7. Tester les routes publiques du catalogue.
8. Tester les routes protégées avec le bon rôle.
9. Tester les opérations de réservation et d'emprunt.
10. Tester les erreurs d'authentification et les autorisations.
11. Vérifier que les données sont correctement enregistrées dans MySQL.

---

# 12. Points importants pour le développeur frontend

- Toutes les communications se font en JSON.
- Toutes les URL commencent par `http://127.0.0.1:5000/api` en développement local.
- Les routes protégées nécessitent un `access_token`.
- Le token doit être envoyé dans l'en-tête `Authorization`.
- Le rôle de l'utilisateur est disponible dans les informations retournées par l'API.
- Les inscriptions publiques créent uniquement des lecteurs.
- Le frontend ne doit jamais attribuer lui-même un rôle administrateur.
- Les erreurs HTTP doivent être gérées pour éviter les pages bloquées.
- Les formulaires doivent respecter les noms exacts des champs attendus par le backend.
- Les identifiants et secrets ne doivent pas être intégrés directement dans le code source.

# 13. Limitations actuelles

Cette version constitue une base complète pour l'intégration et les tests, mais elle doit encore passer des tests fonctionnels et de sécurité avant une mise en production.

Points à prendre en compte :

- Les règles de prêt simultané doivent être testées sous concurrence réelle.
- Les horodatages sont stockés en UTC sans fuseau.
- Les paiements en ligne ne sont pas implémentés.
- Les notifications SMS et e-mail ne sont pas implémentées.
- Les tokens doivent être gérés avec précaution côté frontend.
- Les autorisations doivent être vérifiées sur chaque route protégée.

---

# 14. Démarrage rapide

Pour les prochaines utilisations, voici les commandes essentielles.

**Démarrer le backend :**

```powershell
cd E:\Projet\Bibliotekako\backend
.\.venv\Scripts\Activate.ps1
python run.py
```

**Démarrer le frontend :**

Dans un deuxième terminal :

```powershell
cd E:\Projet\Bibliotekako
npm install
npm run dev
```

Adapter le chemin si le frontend se trouve dans un sous-dossier différent.

**Adresse de l'API :**

```text
http://127.0.0.1:5000/api
```

**Documentation de référence :** ce README décrit les endpoints prévus pour l'intégration. Pour toute différence entre cette documentation et le comportement réel d'une route, vérifier son implémentation dans le backend.

---

**BiblioTech – Backend API**

Développé avec Flask et MySQL par Prosper Félix.