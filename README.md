# Asset Control Panel - Django Edition

A comprehensive asset tracking and inventory management system built with Django. This application tracks IT hardware assets through intake, testing, and disposal, with special emphasis on drive lifecycle tracking and compliance documentation.

## 🎯 What This Application Does

- **Asset Tracking**: Manage IT assets (laptops, desktops, servers) with unique asset tags
- **Hardware Scanning**: Upload `lshw` (Linux Hardware Lister) JSON files to automatically catalog hardware specs
- **Drive Management**: Track individual storage drives through their lifecycle (present, wiped, shredded, removed)
- **Audit Trail**: Complete history of every interaction with every asset
- **Auto-Creation**: Assets are automatically created on first visit - no pre-registration needed
- **Web Interface**: User-friendly forms and dashboards
- **Admin Panel**: Django's powerful admin interface for advanced management
- **JSON API**: RESTful endpoints for programmatic access

## 🏗️ Architecture

**Technology Stack:**
- **Django 5.0**: Python web framework
- **PostgreSQL 16**: Database
- **Docker Compose**: Container orchestration
- **pgAdmin4**: Database management interface
- **Tailwind CSS**: Frontend styling

**Docker Services:**
- `web` - Django application (port 8000)
- `db` - PostgreSQL database (port 5432)
- `pgadmin` - Database admin tool (port 5050)

## 📋 Prerequisites

- Docker and Docker Compose installed
- Basic familiarity with terminal/command line
- That's it! Everything else runs in containers.

## 🚀 Quick Start Guide

### Step 1: Configure Environment Variables

1. Copy the `.env` file and customize if needed (the defaults work for testing):

```bash
# The .env file is already created with default values
# For production, you MUST change the passwords!
```

**Important Environment Variables:**
- `POSTGRES_PASSWORD`: Database password
- `DJANGO_SECRET_KEY`: Django secret (change in production!)
- `DJANGO_SUPERUSER_USERNAME`: Admin username (default: admin)
- `DJANGO_SUPERUSER_PASSWORD`: Admin password (default: admin123)

### Step 2: Build and Start the Application

```bash
# Navigate to the control-panel directory
cd ~/Desktop/control-panel

# Build and start all containers
docker-compose up --build
```

**What happens during startup:**
1. Docker builds the Django container
2. PostgreSQL database starts and initializes
3. Django runs database migrations (creates tables)
4. Django auto-creates the admin user
5. Django development server starts on port 8000

**You'll see output like:**
```
✓ Superuser 'admin' created successfully!
  Login at http://localhost:8000/admin/ or http://localhost:8000/login/
  Username: admin
  Password: admin123
```

### Step 3: Access the Application

Open your browser and visit:

- **Main App**: http://localhost:8000/
- **Login Page**: http://localhost:8000/login/
- **Django Admin**: http://localhost:8000/admin/
- **pgAdmin**: http://localhost:5050/

**Default Credentials:**
- Username: `admin`
- Password: `admin123`

## 📖 How to Use

### Creating Your First Asset

Assets are **auto-created** on first visit (just like the FastAPI version):

1. Log in to http://localhost:8000/login/
2. On the home page, enter an asset tag (e.g., `LAPTOP-001`)
3. Click "Go to Asset"
4. The asset is automatically created!

### Uploading Hardware Information

1. On Linux, generate an lshw scan:
   ```bash
   sudo lshw -json > hardware-scan.json
   ```

2. On the asset detail page, find "Upload Hardware Scan"
3. Choose your `hardware-scan.json` file
4. Click "Upload Hardware Scan"

The system will automatically:
- Extract device serial number
- Detect CPU, RAM, storage
- Create Drive records for each disk
- Update the hardware summary

### Managing Asset Intake

Use the "Intake Information" form to track:
- **Status**: Intake, Testing, Ready for Sale, Sold, Recycled, Returned to Client
- **Device Type**: Laptop, Desktop, Server, Tablet, Phone, Other
- **Cosmetic Grade**: A (Excellent), B (Good), C (Fair), D (Poor)
- **Cosmetic Notes**: Any scratches, dents, damage
- **Location**: Physical location (shelf, bin, warehouse)

### Tracking Drive Status

For compliance and data security:

1. Find a drive in the "Storage Drives" section
2. Click "Update Status"
3. Set status: Present, Removed, Wiped, Shredded, Returned to Client
4. Add optional notes
5. Click "Update Drive Status"

All status changes are logged in the audit trail!

### Searching for Drives

To find a drive across all assets:

**Via API:**
```bash
curl "http://localhost:8000/api/drive/by_serial/?serial=YOUR_SERIAL_HERE"
```

**Via Admin:**
1. Go to http://localhost:8000/admin/
2. Click "Drives"
3. Use the search box to search by serial, model, or asset tag

## 🔧 Common Commands

### Stop the Application
```bash
docker-compose down
```

### View Logs
```bash
# All services
docker-compose logs

# Just Django
docker-compose logs web

# Follow logs (live)
docker-compose logs -f web
```

### Restart After Code Changes
```bash
# Django auto-reloads when you edit Python files
# But if you need to restart:
docker-compose restart web
```

### Access Django Shell
```bash
docker-compose exec web python manage.py shell
```

### Create Additional Users
```bash
docker-compose exec web python manage.py createsuperuser
```

### Run Database Migrations (after model changes)
```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

## 🎨 Django Admin Interface

The Django admin at http://localhost:8000/admin/ gives you:

- **Assets**: Full CRUD operations, filtering, search
- **Hardware Scans**: View all uploaded scans
- **Drives**: Manage drives, search by serial
- **Asset Touches**: Complete audit trail (read-only)
- **Users**: Manage user accounts and permissions

**Pro Tip:** Use the admin for bulk operations and complex queries!

## 🔐 Security Notes

### For Development/Testing:
The default passwords are fine.

### For Production:
1. **Change all passwords in `.env`**:
   - `POSTGRES_PASSWORD`
   - `DJANGO_SUPERUSER_PASSWORD`
   - `PGADMIN_PASSWORD`

2. **Generate a new Django secret key**:
   ```bash
   python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
   ```

3. **Set DEBUG to False**:
   ```
   DJANGO_DEBUG=False
   ```

4. **Configure ALLOWED_HOSTS**:
   ```
   DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   ```

5. **Use HTTPS** (add nginx with SSL certificates)

## 📊 Database Management

### Backup Database
```bash
docker-compose exec db pg_dump -U postgres asset_control > backup.sql
```

### Restore Database
```bash
cat backup.sql | docker-compose exec -T db psql -U postgres asset_control
```

### Access Database with psql
```bash
docker-compose exec db psql -U postgres -d asset_control
```

## 🐛 Troubleshooting

### "Port 8000 is already in use"
Another application is using port 8000. Either:
- Stop the other application
- Or change the port in `docker-compose.yml`:
  ```yaml
  ports:
    - "8001:8000"  # Use 8001 instead
  ```

### "Database connection failed"
Wait a few seconds - PostgreSQL might still be starting up. The Django container waits for the database to be healthy before starting.

### "Can't log in"
- Default credentials: `admin` / `admin123`
- Check the startup logs for the actual username/password
- If you changed `.env`, restart: `docker-compose down && docker-compose up`

### "Static files not loading"
Run:
```bash
docker-compose exec web python manage.py collectstatic --noinput
docker-compose restart web
```

## 📁 Project Structure

```
control-panel/
├── assets/                      # Main Django app
│   ├── models.py               # Database models (Asset, Drive, etc.)
│   ├── views.py                # View functions (endpoints)
│   ├── forms.py                # Form validation
│   ├── admin.py                # Admin interface config
│   ├── lshw_parser.py          # Hardware scan parser
│   ├── urls.py                 # URL routing
│   └── management/
│       └── commands/
│           └── create_superuser_if_none.py  # Auto-create admin
├── config/                      # Django project settings
│   ├── settings.py             # Main configuration
│   ├── urls.py                 # Root URL routing
│   └── wsgi.py                 # WSGI entry point
├── templates/                   # HTML templates
│   ├── login.html
│   ├── home.html
│   └── assets/
│       └── asset_detail.html
├── docker-compose.yml           # Docker orchestration
├── Dockerfile                   # Django container definition
├── requirements.txt             # Python dependencies
├── manage.py                    # Django management script
├── .env                         # Environment variables (passwords)
└── README.md                    # This file!
```

## 🆚 Differences from FastAPI Version

### What's Better in Django:
✅ **Django Admin** - Free, powerful data management interface
✅ **ORM** - No raw SQL queries, cleaner code
✅ **Migrations** - Database schema versioning built-in
✅ **Forms** - Automatic validation
✅ **Auth** - Proper login sessions (no HTTP Basic Auth popup)
✅ **Less Code** - Django handles a lot automatically

### What's the Same:
✅ **Auto-creates assets** on first visit
✅ **Same lshw parsing logic**
✅ **Same drive tracking**
✅ **Same audit trail**
✅ **Same HTML/CSS interface**
✅ **JSON API endpoints available**

## 🔗 API Endpoints

### Web Interface (Login Required):
- `GET /` - Home page with recent assets
- `GET /asset/{asset_tag}/` - Asset detail page (auto-creates)
- `POST /asset/{asset_tag}/intake/` - Update intake form
- `POST /asset/{asset_tag}/upload/` - Upload hardware scan
- `POST /asset/{asset_tag}/drive/{id}/status/` - Update drive status

### JSON API (Login Required):
- `GET /api/assets/` - List all assets (JSON)
- `GET /api/drive/by_serial/?serial=XXX` - Search drives by serial (JSON)

### Admin:
- `GET /admin/` - Django admin interface

### Auth:
- `GET /login/` - Login page
- `POST /logout/` - Logout

## 📚 Learning Resources

New to Django? Check these out:

- **Django Docs**: https://docs.djangoproject.com/
- **Django Admin**: https://docs.djangoproject.com/en/5.0/ref/contrib/admin/
- **Django ORM**: https://docs.djangoproject.com/en/5.0/topics/db/queries/
- **Django Forms**: https://docs.djangoproject.com/en/5.0/topics/forms/

## 🤝 Getting Help

### View Logs
```bash
docker-compose logs -f web
```

### Check Database
```bash
docker-compose exec db psql -U postgres -d asset_control -c "SELECT COUNT(*) FROM assets_asset;"
```

### Django Shell (Python REPL)
```bash
docker-compose exec web python manage.py shell
```
Then try:
```python
from assets.models import Asset
Asset.objects.all()
```

## 🎉 Next Steps

Now that your Django app is running:

1. **Create some test assets** - Visit `/asset/TEST-001/`, `/asset/TEST-002/`, etc.
2. **Upload a hardware scan** - Run `lshw -json` on a Linux machine
3. **Explore the Admin** - http://localhost:8000/admin/
4. **Customize the models** - Edit `assets/models.py` and run migrations
5. **Add more fields** - The framework makes it easy to extend

## 📝 Notes for Beginners

- **Assets auto-create**: Just type a tag and go - no need to create it first
- **Forms validate automatically**: Django checks your input
- **Audit trail logs everything**: Every action is recorded
- **Admin is your friend**: Use it to explore the database
- **Migrations track changes**: Django knows what changed in your database
- **The ORM is powerful**: You rarely need to write SQL

## 🚀 You're Ready!

Your Django Asset Control Panel is now running!

**Start here:**
1. Visit http://localhost:8000/login/
2. Login with `admin` / `admin123`
3. Enter an asset tag and explore!

Happy tracking! 📦