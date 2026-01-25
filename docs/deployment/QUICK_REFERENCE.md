# LendFlow Deployment - Quick Reference

## One-Time Initial Setup

### 1. Connect to EC2

```bash
ssh -i /path/to/your-key.pem ubuntu@your-ec2-public-ip
```

### 2. Run Initial Setup Script

```bash
# Download and run the setup script
curl -O https://raw.githubusercontent.com/jossieT/LendFlow/main/docs/deployment/deploy_initial_setup.sh
chmod +x deploy_initial_setup.sh
bash deploy_initial_setup.sh
```

OR manually follow these commands:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv postgresql nginx git

# Clone repository
git clone https://github.com/jossieT/LendFlow.git
cd LendFlow

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install packages
pip install -r requirements.txt gunicorn psycopg2-binary

# Setup database (see full guide for PostgreSQL setup)
# Create .env file (see full guide)
# Run migrations
python manage.py migrate
python manage.py collectstatic --no-input
python manage.py createsuperuser
```

---

## Configure Gunicorn Service

```bash
# Create gunicorn.socket
sudo nano /etc/systemd/system/gunicorn.socket
```

```ini
[Unit]
Description=gunicorn socket

[Socket]
ListenStream=/run/gunicorn.sock

[Install]
WantedBy=sockets.target
```

```bash
# Create gunicorn.service
sudo nano /etc/systemd/system/gunicorn.service
```

```ini
[Unit]
Description=gunicorn daemon for LendFlow
Requires=gunicorn.socket
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/LendFlow
Environment="PATH=/home/ubuntu/LendFlow/venv/bin"
EnvironmentFile=/home/ubuntu/LendFlow/.env
ExecStart=/home/ubuntu/LendFlow/venv/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --bind unix:/run/gunicorn.sock \
          config.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket
```

---

## Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/lendflow
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /static/ {
        alias /home/ubuntu/LendFlow/staticfiles/;
    }

    location /media/ {
        alias /home/ubuntu/LendFlow/media/;
    }

    location / {
        proxy_pass http://unix:/run/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    client_max_body_size 10M;
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/lendflow /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

---

## SSL Setup (Let's Encrypt)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal is configured automatically
```

---

## Application Updates

```bash
# Standard update workflow
cd ~/LendFlow
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --no-input
sudo systemctl restart gunicorn

# One-liner update
cd ~/LendFlow && git pull && source venv/bin/activate && pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --no-input && sudo systemctl restart gunicorn
```

---

## Service Management

```bash
# Restart services
sudo systemctl restart gunicorn
sudo systemctl restart nginx
sudo systemctl restart postgresql

# Check status
sudo systemctl status gunicorn
sudo systemctl status nginx
sudo systemctl status postgresql

# Enable on boot
sudo systemctl enable gunicorn nginx postgresql
```

---

## Logs and Debugging

```bash
# Gunicorn logs
sudo journalctl -u gunicorn -f           # Follow logs
sudo journalctl -u gunicorn -n 50        # Last 50 lines
sudo journalctl -u gunicorn --since today

# Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Application logs (if configured)
tail -f ~/LendFlow/logs/django.log

# Check socket
sudo systemctl status gunicorn.socket
ls -l /run/gunicorn.sock
```

---

## Database Management

```bash
# Connect to database
psql -U lendflow_user -h localhost -d lendflow_db

# Backup database
pg_dump -U lendflow_user -h localhost lendflow_db | gzip > backup_$(date +%Y%m%d).sql.gz

# Restore database
gunzip -c backup_20260125.sql.gz | psql -U lendflow_user -h localhost lendflow_db

# Django database shell
cd ~/LendFlow
source venv/bin/activate
python manage.py dbshell
```

---

## Common Issues

### 502 Bad Gateway

```bash
# Check Gunicorn is running
sudo systemctl status gunicorn
sudo systemctl restart gunicorn
sudo systemctl restart nginx

# Check socket permissions
ls -l /run/gunicorn.sock
```

### Static files not loading

```bash
cd ~/LendFlow
source venv/bin/activate
python manage.py collectstatic --no-input
sudo systemctl restart gunicorn
```

### Database connection error

```bash
# Check PostgreSQL running
sudo systemctl status postgresql
sudo systemctl restart postgresql

# Verify .env credentials
cat ~/LendFlow/.env | grep DB_
```

### Permission issues

```bash
sudo chown -R ubuntu:www-data ~/LendFlow
sudo chmod -R 755 ~/LendFlow/staticfiles
sudo chmod -R 775 ~/LendFlow/media
```

---

## Server Monitoring

```bash
# System resources
htop                    # Interactive process viewer
df -h                   # Disk usage
free -m                 # Memory usage
netstat -tulpn          # Active connections

# Application health check
curl http://localhost
curl http://your-domain.com
```

---

## Backup and Maintenance

```bash
# Create backup script
nano ~/backup_db.sh
```

```bash
#!/bin/bash
pg_dump -U lendflow_user -h localhost lendflow_db | gzip > ~/backups/db_$(date +%Y%m%d_%H%M%S).sql.gz
find ~/backups -name "db_*.sql.gz" -mtime +7 -delete
```

```bash
# Make executable
chmod +x ~/backup_db.sh

# Schedule with cron (daily at 2 AM)
crontab -e
# Add: 0 2 * * * /home/ubuntu/backup_db.sh >> /home/ubuntu/backup.log 2>&1
```

---

## Environment Variables (.env)

```bash
SECRET_KEY='your-secret-key'
DEBUG=False
ALLOWED_HOSTS='your-domain.com,www.your-domain.com,your-ec2-ip'

DB_NAME=lendflow_db
DB_USER=lendflow_user
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432

CSRF_TRUSTED_ORIGINS='https://your-domain.com'
SECURE_SSL_REDIRECT=True

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

---

## Security Checklist

- [ ] Update ALLOWED_HOSTS in .env
- [ ] Set DEBUG=False in production
- [ ] Use strong database passwords
- [ ] Configure AWS Security Groups properly
- [ ] Enable SSL/HTTPS
- [ ] Set up regular backups
- [ ] Keep system packages updated
- [ ] Monitor application logs
- [ ] Restrict SSH access to specific IPs
- [ ] Use environment variables for secrets

---

## Quick Test Commands

```bash
# Test Gunicorn directly
cd ~/LendFlow
source venv/bin/activate
gunicorn --bind 0.0.0.0:8000 config.wsgi:application

# Test Nginx configuration
sudo nginx -t

# Test database connection
python manage.py check --database default

# Test application
python manage.py runserver 0.0.0.0:8000
```

---

**For complete step-by-step instructions, refer to the full EC2 Deployment Guide.**
