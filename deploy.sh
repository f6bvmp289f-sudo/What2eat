#!/bin/bash
# eatv.0 一键部署脚本（在 Ubuntu 24.04 服务器上跑）
# 用法：ssh deploy@<服务器IP>，然后 bash deploy.sh

set -e

REPO_URL="https://github.com/你的用户名/eatv.0.git"  # 改这里
APP_DIR="/home/deploy/eat"
DOMAIN="yourdomain.com"  # 改这里，没域名就用 IP

echo "=== 1. 克隆代码 ==="
if [ -d "$APP_DIR" ]; then
    echo "目录已存在，git pull 更新"
    cd "$APP_DIR"
    git pull
else
    git clone "$REPO_URL" "$APP_DIR"
    cd "$APP_DIR"
fi

echo "=== 2. 后端 venv + 依赖 ==="
cd "$APP_DIR/backend"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo "=== 3. .env 配置 ==="
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "⚠️  请编辑 .env 填入你的 MiniMax_API_KEY："
    echo "    nano .env"
    echo "然后重新跑这个脚本。"
    exit 1
fi

echo "=== 4. systemd 服务 ==="
sudo tee /etc/systemd/system/eat-backend.service > /dev/null <<EOF
[Unit]
Description=Kaifan Backend (FastAPI)
After=network.target

[Service]
Type=simple
User=deploy
WorkingDirectory=$APP_DIR/backend
Environment="PATH=$APP_DIR/backend/venv/bin"
ExecStart=$APP_DIR/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=3
StandardOutput=append:/var/log/eat-backend.log
StandardError=append:/var/log/eat-backend.error.log

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable eat-backend
sudo systemctl restart eat-backend
sleep 2
sudo systemctl status eat-backend --no-pager

echo "=== 5. 验证后端 ==="
curl -s http://127.0.0.1:8000/ready
echo ""

echo "=== 6. nginx 配置 ==="
sudo tee /etc/nginx/sites-available/eat > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    root $APP_DIR/frontend/dist;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)\$ {
        expires 7d;
    }

    gzip on;
    gzip_types text/css application/javascript application/json image/svg+xml;
}
EOF

# 启用站点
sudo ln -sf /etc/nginx/sites-available/eat /etc/nginx/sites-enabled/eat
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx

echo ""
echo "🎉 部署完成！"
echo "前端: http://$DOMAIN"
echo "后端: http://$DOMAIN/api/ready"
echo ""
echo "⚠️  前端 dist/ 还没构建！请在本地："
echo "    cd $APP_DIR/frontend"
echo "    pnpm install"
echo "    pnpm build"
echo "然后 scp dist/* deploy@<服务器IP>:$APP_DIR/frontend/dist/"
