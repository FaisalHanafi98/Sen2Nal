#!/bin/bash
# Sen2Nal — AWS Lightsail Deployment Script
# Target: sen2nal.faisalhanafi.com
#
# Prerequisites:
#   1. Lightsail instance running Ubuntu 22.04
#   2. DNS A record pointing sen2nal.faisalhanafi.com → instance IP
#   3. .env.production file with secrets (DB_PASSWORD, API keys)
#
# Usage:
#   ssh ubuntu@<lightsail-ip> 'bash -s' < infrastructure/deploy-lightsail.sh

set -euo pipefail

DOMAIN="sen2nal.faisalhanafi.com"
APP_DIR="/opt/sen2nal"
REPO_URL="https://github.com/faisalhanafi/sen2nal.git"

echo "=== Sen2Nal Lightsail Deployment ==="
echo "Domain: $DOMAIN"
echo "App directory: $APP_DIR"

# 1. System dependencies
echo "--- Installing system dependencies ---"
sudo apt-get update -qq
sudo apt-get install -y -qq docker.io docker-compose git curl

sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker "$USER"

# 2. Clone/pull repository
echo "--- Setting up application ---"
if [ -d "$APP_DIR" ]; then
    cd "$APP_DIR"
    git pull origin main
else
    sudo mkdir -p "$APP_DIR"
    sudo chown "$USER:$USER" "$APP_DIR"
    git clone "$REPO_URL" "$APP_DIR"
    cd "$APP_DIR"
fi

# 3. Environment file
if [ ! -f .env.production ]; then
    echo "ERROR: .env.production not found. Create it with:"
    echo "  DB_PASSWORD=<secure-password>"
    echo "  NEWSAPI_API_KEY=<key>"
    echo "  REDDIT_CLIENT_ID=<id>"
    echo "  REDDIT_CLIENT_SECRET=<secret>"
    echo "  OPENAI_API_KEY=<key>"
    echo "  GOOGLE_API_KEY=<key>"
    echo "  XAI_API_KEY=<key>"
    exit 1
fi

# 4. Build and start containers
echo "--- Building containers ---"
docker-compose -f docker-compose.prod.yml --env-file .env.production build

echo "--- Starting services ---"
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d

# 5. Wait for postgres to be ready
echo "--- Waiting for PostgreSQL ---"
sleep 10

# 6. Run database migrations
echo "--- Running migrations ---"
docker-compose -f docker-compose.prod.yml exec app alembic upgrade head

# 7. SSL certificate (first time only)
if [ ! -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    echo "--- Obtaining SSL certificate ---"
    docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
        --webroot --webroot-path=/var/www/certbot \
        --email admin@faisalhanafi.com \
        --agree-tos --no-eff-email \
        -d "$DOMAIN"

    # Restart nginx to pick up the cert
    docker-compose -f docker-compose.prod.yml restart nginx
fi

# 8. Verify
echo "--- Verifying deployment ---"
sleep 5
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/api/v1/health" || echo "000")
if [ "$HTTP_STATUS" = "200" ]; then
    echo "API health check: OK"
else
    echo "API health check: FAILED (HTTP $HTTP_STATUS)"
fi

echo ""
echo "=== Deployment complete ==="
echo "Dashboard: https://$DOMAIN"
echo "API docs: https://$DOMAIN/api/v1/docs"
echo "Health: https://$DOMAIN/api/v1/health"
