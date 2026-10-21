# BiblioTech API — backend complet v2

Ce ZIP complète le backend existant avec les modules exemplaires, emprunts/retours, réservations, pénalités, notifications, profil, tableau de bord, audit et paramètres. Il garde le fichier `.env` et le dossier `migrations/` déjà présents dans ton projet.

## Installation dans le projet existant

1. Extraire le ZIP dans `E:\Projet\Bibliotekako` et accepter le remplacement des fichiers.
2. Ne pas remplacer ni supprimer `.env`.
3. Dans PowerShell, à la racine du projet avec `.venv` activé :

```powershell
pip install -r requirements.txt
flask --app run db migrate -m "Add circulation and operations"
flask --app run db upgrade
python run.py
```

Ne lance pas `flask db init` une deuxième fois. La migration ajoute les nouvelles tables. Si elle affiche des changements inattendus sur `users`, `books`, `authors`, `categories` ou `publishers`, arrête-toi et examine le fichier généré avant `db upgrade`.

API locale : `http://127.0.0.1:5000/api`. Pour les routes protégées, envoyer `Authorization: Bearer <access_token>`. Inscription publique = rôle `reader` uniquement. Rôles : `admin`, `librarian`, `reader`.

## Endpoints

### Santé
- `GET /api/health`
- `GET /api/health/database`

### Authentification et utilisateurs (déjà présents)
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `GET /api/auth/me`
- `GET /api/users` (admin)
- `PATCH /api/users/<id>/status` (admin), JSON `{"is_active":false}`
- `PATCH /api/users/<id>/role` (admin), JSON `{"role":"librarian"}`

### Catalogue (déjà présent)
- `GET /api/books?search=&category_id=&author_id=&page=1&limit=20`
- `GET /api/books/<id>`
- `POST /api/books` (admin/bibliothécaire)
- `PUT /api/books/<id>` (admin/bibliothécaire)
- `DELETE /api/books/<id>` (archivage logique)
- `GET|POST /api/authors`
- `GET|POST /api/categories`
- `GET|POST /api/publishers`

### Exemplaires (admin/bibliothécaire sauf lecture publique des exemplaires d'un livre)
- `GET /api/copies?book_id=&status=`
- `GET /api/copies/<id>`
- `POST /api/copies` JSON `{"book_id":1,"inventory_code":"INV-0001"}`
- `PUT /api/copies/<id>`
- `PATCH /api/copies/<id>/status` JSON `{"status":"damaged"}`
- `GET /api/books/<id>/copies`
- Statuts : `available`, `borrowed`, `reserved`, `damaged`, `lost`

### Emprunts et retours
- `GET /api/loans` (staff)
- `GET /api/loans/<id>` (propriétaire ou staff)
- `POST /api/loans` (staff), JSON `{"reader_id":1,"copy_id":1}`
- `POST /api/loans/<id>/return` (staff)
- `PATCH /api/loans/<id>/extend` (staff)
- `GET /api/loans/overdue` (staff)
- `GET /api/me/loans` (emprunts actifs)
- `GET /api/me/loans/history` (historique)

### Réservations
- `GET /api/reservations` (staff)
- `GET /api/reservations/<id>` (propriétaire ou staff)
- `POST /api/reservations` JSON `{"book_id":1}`
- `POST /api/reservations/<id>/cancel`
- `PATCH /api/reservations/<id>/status` (staff), JSON `{"status":"ready"}`
- `GET /api/me/reservations`
- Statuts : `waiting`, `ready`, `fulfilled`, `cancelled`, `expired`

### Pénalités
- `GET /api/fines` (staff)
- `GET /api/fines/<id>` (propriétaire ou staff)
- `GET /api/me/fines`
- `POST /api/fines/<id>/payment` (staff, enregistre un règlement hors ligne)
- `POST /api/fines/<id>/waive` (admin)

### Notifications et profil
- `GET /api/notifications`
- `GET /api/notifications/unread-count`
- `PATCH /api/notifications/<id>/read`
- `PATCH /api/notifications/read-all`
- `PUT /api/me` JSON `{"full_name":"Nouveau nom","email":"nouveau@example.com"}`
- `PATCH /api/me/password` JSON `{"current_password":"ancien","new_password":"nouveau123"}`

### Dashboard, audit et paramètres
- `GET /api/dashboard` (staff)
- `GET /api/dashboard/loans?year=2026` (staff)
- `GET /api/dashboard/monthly?year=2026` (staff)
- `GET /api/dashboard/overdue` (staff)
- `GET /api/dashboard/popular-books` (staff)
- `GET /api/dashboard/yearly` (staff)
- `GET /api/audit-logs?limit=50` (admin)
- `GET /api/audit-logs/<id>` (admin)
- `GET /api/settings` (staff)
- `PUT /api/settings` (admin), ex. `{"loan_duration_days":14,"max_active_loans":5,"fine_per_day":500,"reservation_hold_days":2}`

## Variables de configuration optionnelles

```dotenv
LOAN_DURATION_DAYS=14
MAX_ACTIVE_LOANS=5
FINE_PER_DAY=500
RESERVATION_HOLD_DAYS=2
```

## Notes

Ceci est une base complète pour l'intégration et les tests, mais elle doit encore passer des tests fonctionnels et de sécurité avant toute mise en production. Les règles de prêt simultané doivent être testées sous concurrence réelle. Les horodatages sont stockés en UTC sans fuseau. Ne jamais pousser `.env` sur GitHub. Les paiements en ligne et notifications SMS/e-mail ne sont pas implémentés.
