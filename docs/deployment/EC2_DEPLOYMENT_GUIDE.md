# LendFlow Django Application - AWS EC2 Deployment Guide

## Table of Contents

- [Prerequisites](#prerequisites)
- [Step 1: EC2 Instance Setup](#step-1-ec2-instance-setup)
- [Step 2: Server Initial Configuration](#step-2-server-initial-configuration)
- [Step 3: Install System Dependencies](#step-3-install-system-dependencies)
- [Step 4: PostgreSQL Database Setup](#step-4-postgresql-database-setup)
- [Step 5: Application Deployment](#step-5-application-deployment)
- [Step 6: Gunicorn Configuration](#step-6-gunicorn-configuration)
- [Step 7: Nginx Web Server Setup](#step-7-nginx-web-server-setup)
- [Step 8: SSL Certificate (Let's Encrypt)](#step-8-ssl-certificate-lets-encrypt)
- [Step 9: Systemd Services](#step-9-systemd-services)
- [Step 10: Post-Deployment Tasks](#step-10-post-deployment-tasks)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before starting, ensure you have:

- AWS account with EC2 access
- Domain name (optional, for SSL)
- SSH key pair for EC2 access
- Basic knowledge of Linux command line

---

## Step 1: EC2 Instance Setup

### 1.1 Launch EC2 Instance

1. **Login to AWS Console** → Navigate to EC2 Dashboard
2. **Launch Instance** with the following configuration:

   - **AMI**: Ubuntu Server 22.04 LTS (or 20.04 LTS)
   - **Instance Type**: t2.small (minimum) or t2.medium (recommended for production)
   - **Storage**: 20 GB gp3 SSD (minimum)
   - **Security Group**: Configure inbound rules:

     | Type       | Protocol | Port Range | Source                       |
     | ---------- | -------- | ---------- | ---------------------------- |
     | SSH        | TCP      | 22         | Your IP or 0.0.0.0/0         |
     | HTTP       | TCP      | 80         | 0.0.0.0/0                    |
     | HTTPS      | TCP      | 443        | 0.0.0.0/0                    |
     | PostgreSQL | TCP      | 5432       | Security Group ID (optional) |

3. **Download** your `.pem` key file and save it securely

### 1.2 Connect to Your Instance

```bash
# Set correct permissions for your key
chmod 400 /path/to/your-key.pem

# Connect via SSH
ssh -i /path/to/your-key.pem ubuntu@your-ec2-public-ip
```

---

## Step 2: Server Initial Configuration

### 2.1 Update System Packages

```bash
sudo apt update && sudo apt upgrade -y
```

### 2.2 Set Timezone

```bash
sudo timedatectl set-timezone Africa/Addis_Ababa
# Or use: sudo dpkg-reconfigure tzdata
```

### 2.3 Create Application User (Optional but Recommended)

```bash
# Create a dedicated user for the application
sudo adduser lendflow --disabled-password --gecos ""

# Add user to sudo group if needed
sudo usermod -aG sudo lendflow

# Switch to the new user
sudo su - lendflow
```

---

## Step 3: Install System Dependencies

### 3.1 Install Python and Development Tools

```bash
sudo apt install -y python3 python3-pip python3-dev python3-venv
sudo apt install -y build-essential libpq-dev git curl
```

### 3.2 Verify Installation

```bash
python3 --version  # Should show Python 3.8+
pip3 --version
```

---

## Step 4: PostgreSQL Database Setup

### 4.1 Install PostgreSQL

```bash
sudo apt install -y postgresql postgresql-contrib
```

### 4.2 Start and Enable PostgreSQL

```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
sudo systemctl status postgresql  # Verify it's running
```

### 4.3 Create Database and User

```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL shell, run:
CREATE DATABASE lendflow_db;
CREATE USER lendflow_user WITH PASSWORD 'your_strong_password_here';
ALTER ROLE lendflow_user SET client_encoding TO 'utf8';
ALTER ROLE lendflow_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE lendflow_user SET timezone TO 'Africa/Addis_Ababa';
GRANT ALL PRIVILEGES ON DATABASE lendflow_db TO lendflow_user;
\q
```

> **IMPORTANT:** Replace `your_strong_password_here` with a strong, unique password. Save this password securely.

### 4.4 Configure PostgreSQL for Local Connections (Optional)

```bash
# Edit pg_hba.conf if needed
sudo nano /etc/postgresql/14/main/pg_hba.conf

# Ensure this line exists for local connections:
# local   all             all                                     peer
```

---

## Step 5: Application Deployment

### 5.1 Clone Repository

```bash
# Navigate to home directory
cd ~

# Clone your repository
git clone https://github.com/jossieT/LendFlow.git
cd LendFlow

# Checkout the desired branch
git checkout feature/risk-compliance  # Or main/master
```

### 5.2 Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### 5.3 Install Python Dependencies

```bash
# Install from requirements.txt
pip install -r requirements.txt

# Install additional production packages
pip install gunicorn psycopg2-binary
```

### 5.4 Configure Environment Variables

```bash
# Create environment file
nano ~/LendFlow/.env
```

Add the following configuration:

```bash
# Django Settings
SECRET_KEY='your-secret-key-here-generate-a-strong-one'
DEBUG=False
ALLOWED_HOSTS='your-domain.com,your-ec2-public-ip,localhost'

# Database Configuration
DB_NAME=lendflow_db
DB_USER=lendflow_user
DB_PASSWORD=your_strong_password_here
DB_HOST=localhost
DB_PORT=5432

# Security Settings
CSRF_TRUSTED_ORIGINS='https://your-domain.com,http://your-ec2-public-ip'
SECURE_SSL_REDIRECT=False  # Set to True after SSL setup

# Email Configuration (Optional - Update with your SMTP settings)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Payment Gateway (if applicable)
PAYMENT_GATEWAY_API_KEY=your-api-key
```

> **CAUTION:** Never commit the `.env` file to version control. Ensure it's in `.gitignore`.

### 5.5 Generate Secret Key

```bash
# Generate a new Django secret key
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output and use it as your `SECRET_KEY` in `.env`.

### 5.6 Update Django Settings

Ensure `config/settings.py` loads environment variables:

```python
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}
```

### 5.7 Run Migrations and Create Superuser

```bash
# Make sure you're in the project directory with venv activated
cd ~/LendFlow
source venv/bin/activate

# Run migrations
python manage.py migrate

# Create superuser for admin access
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --no-input
```

---

## Step 6: Gunicorn Configuration

### 6.1 Test Gunicorn

```bash
# Test if Gunicorn works
cd ~/LendFlow
source venv/bin/activate
gunicorn --bind 0.0.0.0:8000 config.wsgi:application
```

Visit `http://your-ec2-public-ip:8000` to verify. Press `Ctrl+C` to stop.

### 6.2 Create Gunicorn Systemd Socket

```bash
sudo nano /etc/systemd/system/gunicorn.socket
```

Add the following:

```ini
[Unit]
Description=gunicorn socket

[Socket]
ListenStream=/run/gunicorn.sock

[Install]
WantedBy=sockets.target
```

### 6.3 Create Gunicorn Systemd Service

```bash
sudo nano /etc/systemd/system/gunicorn.service
```

Add the following (adjust paths if using a different user):

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

> **NOTE:** Adjust `User`, `WorkingDirectory`, and paths if you created a different application user.

### 6.4 Start and Enable Gunicorn

```bash
# Start and enable socket
sudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket

# Check socket status
sudo systemctl status gunicorn.socket

# Test socket activation
curl --unix-socket /run/gunicorn.sock localhost
```

---

## Step 7: Nginx Web Server Setup

### 7.1 Install Nginx

```bash
sudo apt install -y nginx
```

### 7.2 Create Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/lendflow
```

Add the following configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;  # Or EC2 public IP

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Static files
    location /static/ {
        alias /home/ubuntu/LendFlow/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /home/ubuntu/LendFlow/media/;
        expires 7d;
    }

    # Proxy to Gunicorn
    location / {
        proxy_pass http://unix:/run/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Client body size limit
    client_max_body_size 10M;
}
```

### 7.3 Enable Nginx Configuration

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/lendflow /etc/nginx/sites-enabled/

# Remove default configuration
sudo rm /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### 7.4 Adjust Firewall (if UFW is enabled)

```bash
sudo ufw allow 'Nginx Full'
sudo ufw status
```

---

## Step 8: SSL Certificate (Let's Encrypt)

### 8.1 Install Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 8.2 Obtain SSL Certificate

> **IMPORTANT:** Ensure your domain is pointing to your EC2 instance's public IP before proceeding.

```bash
# Obtain and install certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Follow the prompts:
# - Enter email address
# - Agree to terms
# - Choose whether to redirect HTTP to HTTPS (recommended: yes)
```

### 8.3 Auto-Renewal Setup

```bash
# Test renewal
sudo certbot renew --dry-run

# Certbot automatically sets up a cron job for renewal
# Verify by checking:
sudo systemctl status certbot.timer
```

### 8.4 Update Django Settings for HTTPS

Edit `.env`:

```bash
nano ~/LendFlow/.env
```

Update:

```bash
SECURE_SSL_REDIRECT=True
CSRF_TRUSTED_ORIGINS='https://your-domain.com'
```

Restart Gunicorn:

```bash
sudo systemctl restart gunicorn
```

---

## Step 9: Systemd Services

### 9.1 Restart All Services

```bash
# Restart Gunicorn
sudo systemctl daemon-reload
sudo systemctl restart gunicorn

# Restart Nginx
sudo systemctl restart nginx

# Check status
sudo systemctl status gunicorn
sudo systemctl status nginx
```

### 9.2 Enable Services on Boot

```bash
sudo systemctl enable gunicorn
sudo systemctl enable nginx
sudo systemctl enable postgresql
```

---

## Step 10: Post-Deployment Tasks

### 10.1 Create Media Directory

```bash
mkdir -p ~/LendFlow/media
sudo chown -R ubuntu:www-data ~/LendFlow/media
sudo chmod -R 775 ~/LendFlow/media
```

### 10.2 Set Proper Permissions

```bash
# Set ownership
sudo chown -R ubuntu:www-data ~/LendFlow

# Set directory permissions
sudo find ~/LendFlow -type d -exec chmod 755 {} \;

# Set file permissions
sudo find ~/LendFlow -type f -exec chmod 644 {} \;

# Make manage.py executable
chmod +x ~/LendFlow/manage.py
```

### 10.3 Configure Log Rotation

```bash
sudo nano /etc/logrotate.d/lendflow
```

Add:

```
/home/ubuntu/LendFlow/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 ubuntu www-data
    sharedscripts
    postrotate
        systemctl reload gunicorn > /dev/null 2>&1 || true
    endscript
}
```

### 10.4 Create Logs Directory

```bash
mkdir -p ~/LendFlow/logs
sudo chown -R ubuntu:www-data ~/LendFlow/logs
```

### 10.5 Setup Database Backups

Create backup script:

```bash
nano ~/backup_db.sh
```

Add:

```bash
#!/bin/bash
BACKUP_DIR="/home/ubuntu/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
pg_dump -U lendflow_user -h localhost lendflow_db | gzip > $BACKUP_DIR/lendflow_db_$DATE.sql.gz

# Keep only last 7 days of backups
find $BACKUP_DIR -name "lendflow_db_*.sql.gz" -mtime +7 -delete

echo "Backup completed: lendflow_db_$DATE.sql.gz"
```

Make executable and schedule:

```bash
chmod +x ~/backup_db.sh

# Add to crontab (daily at 2 AM)
crontab -e

# Add this line:
0 2 * * * /home/ubuntu/backup_db.sh >> /home/ubuntu/backup.log 2>&1
```

---

## Troubleshooting

### Check Gunicorn Logs

```bash
# Check socket
sudo journalctl -u gunicorn.socket

# Check service
sudo journalctl -u gunicorn -n 50 --no-pager

# Real-time logs
sudo journalctl -u gunicorn -f
```

### Check Nginx Logs

```bash
# Error log
sudo tail -f /var/log/nginx/error.log

# Access log
sudo tail -f /var/log/nginx/access.log
```

### Check Application Logs

```bash
# If you configured Django logging
tail -f ~/LendFlow/logs/django.log
```

### Common Issues

#### 502 Bad Gateway

```bash
# Check if Gunicorn is running
sudo systemctl status gunicorn

# Check socket permissions
ls -l /run/gunicorn.sock

# Restart services
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

#### Static Files Not Loading

```bash
# Re-collect static files
cd ~/LendFlow
source venv/bin/activate
python manage.py collectstatic --no-input

# Check permissions
sudo chown -R ubuntu:www-data ~/LendFlow/staticfiles
sudo chmod -R 755 ~/LendFlow/staticfiles
```

#### Database Connection Error

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test database connection
psql -U lendflow_user -h localhost -d lendflow_db

# Check .env file has correct credentials
cat ~/LendFlow/.env | grep DB_
```

### Useful Commands

```bash
# Restart all services
sudo systemctl restart gunicorn nginx postgresql

# Pull latest code and update
cd ~/LendFlow
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --no-input
sudo systemctl restart gunicorn

# View system resources
htop  # or: top
df -h  # disk usage
free -m  # memory usage
```

---

## Security Best Practices

> **WARNING:** Always follow these security practices:

- ✅ Keep your `.env` file secure and never commit it to version control
- ✅ Use strong passwords for database and admin accounts
- ✅ Regularly update system packages: `sudo apt update && sudo apt upgrade`
- ✅ Configure AWS Security Groups to restrict SSH access to your IP only
- ✅ Enable AWS CloudWatch for monitoring
- ✅ Set up regular database backups
- ✅ Use HTTPS in production (Let's Encrypt is free)
- ✅ Monitor application logs regularly
- ✅ Keep Django and dependencies updated

---

## Quick Reference Commands

```bash
# Application update workflow
cd ~/LendFlow && git pull && source venv/bin/activate && \
pip install -r requirements.txt && python manage.py migrate && \
python manage.py collectstatic --no-input && sudo systemctl restart gunicorn

# View logs
sudo journalctl -u gunicorn -f

# Restart services
sudo systemctl restart gunicorn nginx

# Database backup (manual)
~/backup_db.sh

# Check service status
sudo systemctl status gunicorn nginx postgresql
```

---

## Next Steps

After successful deployment:

1. **Configure monitoring** - Set up AWS CloudWatch or a third-party monitoring service
2. **Set up CI/CD** - Automate deployments using GitHub Actions or AWS CodeDeploy
3. **Configure email** - Set up email service for password resets and notifications
4. **Set up Redis** (optional) - For caching and improved performance
5. **Configure CDN** (optional) - Use AWS CloudFront for static files
6. **Set up staging environment** - Create a separate instance for testing

---

**Deployment Complete! 🚀**

Your LendFlow application should now be live and accessible at your domain or EC2 public IP.
