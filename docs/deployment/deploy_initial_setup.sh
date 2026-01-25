#!/bin/bash

# LendFlow EC2 Deployment Script
# Run this script on a fresh Ubuntu 22.04 EC2 instance
# Usage: bash deploy_initial_setup.sh

set -e  # Exit on error

echo "=================================="
echo "LendFlow Initial Deployment Setup"
echo "=================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Update system
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies
print_status "Installing system dependencies..."
sudo apt install -y python3 python3-pip python3-dev python3-venv \
    build-essential libpq-dev git curl nginx \
    postgresql postgresql-contrib

# Set timezone
print_status "Setting timezone to Africa/Addis_Ababa..."
sudo timedatectl set-timezone Africa/Addis_Ababa

# Start and enable PostgreSQL
print_status "Starting PostgreSQL..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Prompt for database configuration
print_warning "Database Configuration Required"
read -p "Enter database name [lendflow_db]: " DB_NAME
DB_NAME=${DB_NAME:-lendflow_db}

read -p "Enter database user [lendflow_user]: " DB_USER
DB_USER=${DB_USER:-lendflow_user}

read -sp "Enter database password: " DB_PASSWORD
echo ""

# Create database and user
print_status "Creating PostgreSQL database and user..."
sudo -u postgres psql <<EOF
CREATE DATABASE $DB_NAME;
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
ALTER ROLE $DB_USER SET client_encoding TO 'utf8';
ALTER ROLE $DB_USER SET default_transaction_isolation TO 'read committed';
ALTER ROLE $DB_USER SET timezone TO 'Africa/Addis_Ababa';
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
\q
EOF

print_status "Database created successfully!"

# Clone repository
print_status "Setting up application directory..."
cd ~

if [ -d "LendFlow" ]; then
    print_warning "LendFlow directory already exists. Skipping clone."
else
    read -p "Enter GitHub repository URL [https://github.com/jossieT/LendFlow.git]: " REPO_URL
    REPO_URL=${REPO_URL:-https://github.com/jossieT/LendFlow.git}
    git clone $REPO_URL
fi

cd LendFlow

# Create virtual environment
print_status "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt
pip install gunicorn psycopg2-binary python-dotenv

# Create .env file
print_status "Creating .env configuration file..."
cat > .env <<EOF
# Django Settings
SECRET_KEY='$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")'
DEBUG=False
ALLOWED_HOSTS='localhost,127.0.0.1'

# Database Configuration
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=localhost
DB_PORT=5432

# Security Settings
CSRF_TRUSTED_ORIGINS='http://localhost'
SECURE_SSL_REDIRECT=False

# Email Configuration (Update these with your settings)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EOF

print_status ".env file created!"

# Create necessary directories
print_status "Creating application directories..."
mkdir -p media logs backups

# Run migrations
print_status "Running database migrations..."
python manage.py migrate

# Collect static files
print_status "Collecting static files..."
python manage.py collectstatic --no-input

# Create superuser
print_warning "Now you need to create a Django superuser account"
python manage.py createsuperuser

# Set permissions
print_status "Setting proper file permissions..."
sudo chown -R $USER:www-data ~/LendFlow
sudo find ~/LendFlow -type d -exec chmod 755 {} \;
sudo find ~/LendFlow -type f -exec chmod 644 {} \;
chmod +x ~/LendFlow/manage.py

echo ""
echo "=================================="
print_status "Initial setup complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Update ALLOWED_HOSTS in .env with your domain/IP"
echo "2. Configure Gunicorn systemd service"
echo "3. Configure Nginx"
echo "4. (Optional) Set up SSL with Let's Encrypt"
echo ""
echo "See the full deployment guide for detailed instructions."
echo ""
