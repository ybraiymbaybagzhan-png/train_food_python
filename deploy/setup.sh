#!/usr/bin/env bash
# DAR | RES group - Ubuntu 22.04/24.04 (Oracle Cloud) орнату және жаңарту скрипті.
#
# Қолдану (серверде, жоба папкасының ішінен):
#   sudo DOMAIN=example.com EMAIL=you@mail.com bash deploy/setup.sh
# Құпиясөздерді өзіңіз бергіңіз келсе (бірінші іске қосуда ғана):
#   sudo ADMIN_PASSWORD=... KITCHEN_PASSWORD=... STAFF_PASSWORD=... bash deploy/setup.sh
# Скрипт қайта іске қосуға қауіпсіз: база мен жүктелген суреттерге тиіспейді.
set -euo pipefail

APP_USER="darres"
APP_DIR="/opt/dar-res"
ENV_FILE="/etc/dar-res.env"
DOMAIN="${DOMAIN:-}"
EMAIL="${EMAIL:-}"

if [[ $EUID -ne 0 ]]; then
  echo "Қате: скриптті sudo арқылы іске қосыңыз: sudo bash deploy/setup.sh"
  exit 1
fi

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ ! -f "$SRC_DIR/app/main.py" ]]; then
  echo "Қате: $SRC_DIR ішінде app/main.py табылмады. Скриптті жоба папкасынан іске қосыңыз."
  exit 1
fi

echo "==> 1/8 Жүйелік пакеттер"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y python3 python3-venv python3-pip nginx rsync curl sqlite3 certbot python3-certbot-nginx

echo "==> 2/8 Swap (1 ГБ RAM-ға қор)"
if [[ -z "$(swapon --show)" ]]; then
  fallocate -l 1G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile >/dev/null
  swapon /swapfile
  grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

echo "==> 3/8 Firewall: 80 және 443 порттарын ашу (Oracle Ubuntu iptables)"
RULES="$(iptables -S INPUT 2>/dev/null || true)"
if [[ "$RULES" == *REJECT* ]]; then
  LIST="$(iptables -L INPUT --line-numbers -n)"
  N="$(awk '/REJECT/ {print $1; exit}' <<<"$LIST")"
  for P in 80 443; do
    if ! iptables -C INPUT -p tcp --dport "$P" -j ACCEPT 2>/dev/null; then
      iptables -I INPUT "$N" -p tcp --dport "$P" -j ACCEPT
      N=$((N + 1))
    fi
  done
  apt-get install -y iptables-persistent
  netfilter-persistent save
fi

echo "==> 4/8 Қолданбаны $APP_DIR ішіне көшіру"
id "$APP_USER" >/dev/null 2>&1 || useradd --system --home "$APP_DIR" --shell /usr/sbin/nologin "$APP_USER"
mkdir -p "$APP_DIR"
rsync -a \
  --exclude '.git' --exclude '.venv' --exclude '__pycache__' --exclude 'scratch' \
  --exclude '*.db' --exclude 'app/static/uploads' \
  --exclude '*.docx' --exclude '*.pdf' --exclude 'WhatsApp Image*' --exclude 'кіру.txt' \
  "$SRC_DIR"/ "$APP_DIR"/
mkdir -p "$APP_DIR/app/static/uploads/menu"

echo "==> 5/8 Python ортасы мен тәуелділіктер"
if [[ ! -x "$APP_DIR/.venv/bin/python" ]]; then
  python3 -m venv "$APP_DIR/.venv"
fi
"$APP_DIR/.venv/bin/pip" install --upgrade pip wheel
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"
chown -R "$APP_USER":"$APP_USER" "$APP_DIR"

echo "==> 6/8 Баптаулар (құпиясөздер) және systemd қызметі"
NEW_ENV=0
if [[ ! -f "$ENV_FILE" ]]; then
  NEW_ENV=1
  ADMIN_PASSWORD="${ADMIN_PASSWORD:-$(python3 -c 'import secrets;print(secrets.token_hex(6))')}"
  KITCHEN_PASSWORD="${KITCHEN_PASSWORD:-$(python3 -c 'import secrets;print(secrets.token_hex(6))')}"
  STAFF_PASSWORD="${STAFF_PASSWORD:-$(python3 -c 'import secrets;print(secrets.token_hex(6))')}"
  SESSION_SECRET="$(python3 -c 'import secrets;print(secrets.token_urlsafe(48))')"
  umask 077
  cat > "$ENV_FILE" <<ENVEOF
SESSION_SECRET=$SESSION_SECRET
ADMIN_PASSWORD=$ADMIN_PASSWORD
KITCHEN_PASSWORD=$KITCHEN_PASSWORD
STAFF_PASSWORD=$STAFF_PASSWORD
WHATSAPP_DEFAULT_PHONE=${WHATSAPP_DEFAULT_PHONE:-77772141601}
ENVEOF
  umask 022
fi
chown root:root "$ENV_FILE"
chmod 600 "$ENV_FILE"

# --workers 1 міндетті: WebSocket қосылымдарының тізімі процесс жадында сақталады.
cat > /etc/systemd/system/dar-res.service <<UNIT
[Unit]
Description=DAR | RES group (FastAPI)
After=network.target

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$ENV_FILE
ExecStart=$APP_DIR/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1 --proxy-headers --forwarded-allow-ips=127.0.0.1
Restart=always
RestartSec=3
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable dar-res >/dev/null
systemctl restart dar-res

echo "==> 7/8 nginx"
cat > /etc/nginx/conf.d/dar-res-map.conf <<'MAPEOF'
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}
MAPEOF

if [[ ! -f /etc/nginx/sites-available/dar-res ]]; then
  cat > /etc/nginx/sites-available/dar-res <<'NGINXEOF'
server {
    listen 80;
    server_name __SERVER_NAME__;
    client_max_body_size 10m;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        # WebSocket (/ws) үшін
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_read_timeout 3600s;
    }
}
NGINXEOF
  sed -i "s/__SERVER_NAME__/${DOMAIN:-_}/" /etc/nginx/sites-available/dar-res
fi
ln -sf /etc/nginx/sites-available/dar-res /etc/nginx/sites-enabled/dar-res
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

if [[ -n "$DOMAIN" && -n "$EMAIL" && ! -d "/etc/letsencrypt/live/$DOMAIN" ]]; then
  echo "    SSL сертификатын алу (Let's Encrypt)..."
  certbot --nginx -d "$DOMAIN" -m "$EMAIL" --agree-tos --no-eff-email --redirect -n \
    || echo "    ЕСКЕРТУ: SSL алынбады. Домен A-жазбасы осы серверге қарап тұрғанын тексеріп, команданы қайта іске қосыңыз."
fi

echo "==> 8/8 Күнделікті резервтік көшірме"
cat > /etc/cron.daily/dar-res-backup <<'BAKEOF'
#!/bin/bash
# train_food.db мен жүктелген суреттердің көшірмесі, соңғы 7 күн сақталады.
D=/var/backups/dar-res
TS="$(date +%F)"
mkdir -p "$D"
if [ -f /opt/dar-res/train_food.db ]; then
  sqlite3 /opt/dar-res/train_food.db ".backup '$D/train_food-$TS.db'"
fi
tar -czf "$D/uploads-$TS.tar.gz" -C /opt/dar-res/app/static uploads 2>/dev/null
find "$D" -type f -mtime +7 -delete
BAKEOF
chmod +x /etc/cron.daily/dar-res-backup

OK=0
for _ in $(seq 1 20); do
  if curl -fsS -o /dev/null http://127.0.0.1:8000/login; then OK=1; break; fi
  sleep 2
done

echo
if [[ $OK -eq 1 ]]; then
  echo "ДАЙЫН: қолданба жұмыс істеп тұр."
else
  echo "ЕСКЕРТУ: қолданба жауап бермеді. Логты қараңыз: sudo journalctl -u dar-res -n 50 --no-pager"
fi
if [[ -n "$DOMAIN" ]]; then
  echo "Сайт: https://$DOMAIN/   (SSL алынбаса: http://$DOMAIN/)"
else
  echo "Сайт: http://<PUBLIC_IP>/"
fi
if [[ $NEW_ENV -eq 1 ]]; then
  echo
  echo "Құпиясөздер (қазір ғана көрсетіледі, қауіпсіз жерге жазып алыңыз):"
  echo "  admin   : $ADMIN_PASSWORD"
  echo "  kitchen : $KITCHEN_PASSWORD"
  echo "  staff   : $STAFF_PASSWORD"
  echo "  (файл: $ENV_FILE)"
fi
