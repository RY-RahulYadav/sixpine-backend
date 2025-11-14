# Database Configuration Guide

This guide explains how to configure the database for both local development (SQLite) and VPS production (PostgreSQL).

## Local Development (SQLite)

For local development, you don't need to set any database environment variables. The application will automatically use SQLite.

### Setup Steps:

1. **No database configuration needed** - Just run:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

2. The database file will be created at: `server/db.sqlite3`

## VPS/Production (PostgreSQL)

For production on your VPS, you need to configure PostgreSQL using environment variables.

### Setup Steps:

1. **Install PostgreSQL on your VPS** (if not already installed):
   ```bash
   sudo apt update
   sudo apt install postgresql postgresql-contrib
   ```

2. **Create a PostgreSQL database and user**:
   ```bash
   sudo -u postgres psql
   ```
   Then in PostgreSQL:
   ```sql
   CREATE DATABASE ecommerce_db;
   CREATE USER your_username WITH PASSWORD 'your_secure_password';
   GRANT ALL PRIVILEGES ON DATABASE ecommerce_db TO your_username;
   \q
   ```

3. **Create a `.env` file** in the `server/` directory with PostgreSQL settings:

   ```env
   SECRET_KEY=your-production-secret-key
   DEBUG=False
   ALLOWED_HOSTS=api.sixpine.in,your-domain.com,www.your-domain.com,your-vps-ip
   
   # PostgreSQL Database Settings
   DB_ENGINE=django.db.backends.postgresql
   DB_NAME=ecommerce_db
   DB_USER=your_username
   DB_PASSWORD=your_secure_password
   DB_HOST=localhost
   DB_PORT=5432
   DB_SSLMODE=prefer
   
   # Other settings...
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   FRONTEND_URL=https://your-frontend-domain.com
   ```

4. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser** (if needed):
   ```bash
   python manage.py createsuperuser
   ```

## Environment Variables Reference

### Database Variables

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `DB_ENGINE` | Database engine | `django.db.backends.postgresql` | No* |
| `DB_NAME` | Database name | `ecommerce_db` | No* |
| `DB_USER` | Database user | `postgres_user` | No* |
| `DB_PASSWORD` | Database password | `secure_password` | No* |
| `DB_HOST` | Database host | `localhost` | No* |
| `DB_PORT` | Database port | `5432` | No* |
| `DB_SSLMODE` | SSL mode (optional) | `prefer`, `require`, `disable` | No |

*If `DB_ENGINE` and `DB_NAME` are not set, SQLite will be used automatically for local development.

### Other Important Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Django secret key | Yes |
| `DEBUG` | Debug mode (False for production) | Yes |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | Yes |
| `EMAIL_HOST_USER` | Email address for sending emails | Yes |
| `EMAIL_HOST_PASSWORD` | Email app password | Yes |
| `FRONTEND_URL` | Frontend application URL | Yes |

## Testing Database Connection

To test if your database connection is working:

```bash
python manage.py dbshell
```

Or check the connection:
```bash
python manage.py check --database default
```

## Troubleshooting

### Common Issues:

1. **"FATAL: password authentication failed"**
   - Check your PostgreSQL password
   - Verify the user has correct permissions

2. **"could not connect to server"**
   - Ensure PostgreSQL is running: `sudo systemctl status postgresql`
   - Check if the host/port is correct
   - Verify firewall settings

3. **"database does not exist"**
   - Create the database: `CREATE DATABASE ecommerce_db;`

4. **"permission denied"**
   - Grant privileges: `GRANT ALL PRIVILEGES ON DATABASE ecommerce_db TO your_username;`

## Notes

- The `.env` file should never be committed to version control (it's in `.gitignore`)
- Always use strong passwords in production
- Keep your `SECRET_KEY` secret and never share it
- For production, set `DEBUG=False` and configure proper `ALLOWED_HOSTS`

