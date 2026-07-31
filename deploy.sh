#!/bin/bash
# What2eat 一键部署脚本（在 Ubuntu 24.04 服务器上跑）
# 用法：
#   1. 编辑下面 REPO_URL / DOMAIN / APP_USER 三个变量
#   2. bash deploy.sh
#
# 假设：
#   - 服务器已有非 root 用户（推荐 deploy，脚本里默认用 deploy）
#   - 服务器能联网（git clone + pip install + apt 都要）
#   - 80/443 端口没被占

set -e

# ============================================================
# 用户必须改的 3 个变量
# ============================================================
REPO_URL="https://github.com/f6bvmp289f-sudo/What2eat.git"
APP_DIR="/home/ubuntu/what2eat"
APP_USER="ubuntu"            # 部署用户（你服务器上的）
DOMAIN=""                   # 域名（没域名留空，用 IP）

# ============================================================
# 派生变量
# ============================================================
FRONTEND_DIR="$APP_DIR/frontend"
BACKEND_DIR="$APP_DIR/backend"
NGINX_CONF="/etc/nginx/sites-available/what2eat"
SYSTEMD_SERVICE="/etc/systemd/system/what2eat-backend.service"
SERVER_NAME="${DOMAIN:-_}"  # 没有域名时用 _ 兜底

echo "=========================================="
echo "  What2eat 部署"
echo "  REPO:   $REPO_URL"
echo "  APPDIR: $APP_DIR"
echo "  USER:   $APP_USER"
echo "  DOMAIN: ${DOMAIN:-<未配置，用 IP>}"
echo "=========================================="

# ============================================================
# 0. 装基础包（apt）
# ============================================================
echo ""
echo "=== 0. 装基础包 ==="
sudo apt update -qq
sudo apt install -y python3-pip python3-venv nginx git

# ============================================================
# 1. clone 代码
# ============================================================
echo ""
echo "=== 1. clone 代码 ==="
if [ -d "$APP_DIR" ]; then
    echo "目录已存在，git pull"
    cd "$APP_DIR"
    git pull
else
    sudo -u $APP_USER git clone "$REPO_URL" "$APP_DIR"
    cd "$APP_DIR"
fi

# ============================================================
# 2. 后端 venv + 依赖
# ============================================================
echo ""
echo "=== 2. 后端 venv + 依赖 ==="
cd "$BACKEND_DIR"
[ ! -d "venv" ] && sudo -u $APP_USER python3 -m venv venv
sudo -u $APP_USER bash -c "source venv/bin/activate && pip install --upgrade pip -q && pip install -r requirements.txt -q"

# ============================================================
# 3. .env 配置
# ============================================================
echo ""
echo "=== 3. .env 配置 ==="
if [ ! -f ".env" ]; then
    sudo -u $APP_USER cp .env.example .env
    echo ""
    echo "⚠️  .env 已创建，请编辑填入 MiniMax_API_KEY："
    echo "    sudo -u $APP_USER nano $BACKEND_DIR/.env"
    echo ""
    echo "填完后再跑一次这个脚本。"
    exit 1
fi

# ============================================================
# 4. systemd 服务
# ============================================================
echo ""
echo "=== 4. systemd 服务 ==="
sudo tee "$SYSTEMD_SERVICE" > /dev/null <<EOF
[Unit]
Description=What2eat Backend (FastAPI)
After=network.target

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$BACKEND_DIR
Environment="PATH=$BACKEND_DIR/venv/bin"
ExecStart=$BACKEND_DIR/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=3
StandardOutput=append:/var/log/what2eat-backend.log
StandardError=append:/var/log/what2eat-backend.error.log

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable what2eat-backend
sudo systemctl restart what2eat-backend
sleep 2
sudo systemctl status what2eat-backend --no-pager
echo ""

# ============================================================
# 5. 验证后端
# ============================================================
echo "=== 5. 验证后端 ==="
curl -s http://127.0.0.1:8000/ready
echo ""

# ============================================================
# 6. 构建前端（如果还没构建）
# ============================================================
echo ""
echo "=== 6. 构建前端（pnpm build）==="
if ! command -v pnpm &> /dev/null; then
    echo "pnpm 未安装，先装 Node.js + pnpm"
    curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
    sudo apt install -y nodejs
    sudo npm install -g pnpm
fi

if [ ! -d "$FRONTEND_DIR" ]; then
    echo "前端目录不存在：$FRONTEND_DIR"
    exit 1
fi

cd "$FRONTEND_DIR"
sudo -u $APP_USER pnpm install --silent
sudo -u $APP_USER pnpm run build

# ============================================================
# 7. nginx 配置
# ============================================================
echo ""
echo "=== 7. nginx 配置 ==="
sudo tee "$NGINX_CONF" > /dev/null <<EOF
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name $SERVER_NAME;

    # 前端静态资源
    root $FRONTEND_DIR/dist;
    index index.html;

    # 前端 SPA 路由 fallback
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # 后端 API 反代
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # SSE 必需
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;  # image-01 可能慢
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$ {
        expires 7d;
        add_header Cache-Control "public, max-age=604800, immutable";
    }

    # gzip
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/css application/javascript application/json image/svg+xml;
}
EOF

# 启用站点
sudo ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/what2eat
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx

# ============================================================
# 8. 防火墙
# ============================================================
echo ""
echo "=== 8. 防火墙 ==="
if command -v ufw &> /dev/null; then
    sudo ufw allow OpenSSH || true
    sudo ufw allow 'Nginx Full' || true
    sudo ufw --force enable || true
    sudo ufw status || true
fi

# ============================================================
# 完成
# ============================================================
SERVER_IP=$(curl -s http://ifconfig.me 2>/dev/null || echo "<未知>")
echo ""
echo "=========================================="
echo "  部署完成 ✅"
echo "=========================================="
echo "  服务器 IP: $SERVER_IP"
echo "  前端:      http://$SERVER_IP/"
echo "  后端 ready: http://$SERVER_IP/api/ready"
echo "  API 文档:   http://$SERVER_IP/docs"
echo ""
echo "后续更新（git pull + 重启）："
echo "  cd $APP_DIR && git pull"
echo "  sudo systemctl restart what2eat-backend"
echo "  cd $FRONTEND_DIR && sudo -u $APP_USER pnpm run build"
echo "  sudo systemctl reload nginx"
echo "=========================================="
