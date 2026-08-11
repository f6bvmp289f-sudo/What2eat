#!/bin/bash
# 开饭 · 服务器更新脚本（不重装，仅拉代码 + 重启）
# 用法：
#   1. 编辑下面 APP_DIR 变量（如已部署可不动）
#   2. bash update.sh
#
# 假设：
#   - 已按 deploy.sh 部署过一遍（venv / systemd / nginx 都已就绪）
#   - 服务器能联网（git pull + pnpm install + pip install 都要）
#   - 本地 main 分支已有你想要的更新

set -e

# ============================================================
# 配置（与 deploy.sh 保持一致）
# ============================================================
APP_DIR="/home/ubuntu/what2eat"
APP_USER="ubuntu"
BACKEND_DIR="$APP_DIR/backend"
FRONTEND_DIR="$APP_DIR/frontend"

# ============================================================
# 1. 拉取最新代码
# ============================================================
echo ""
echo "=== 1. git pull ==="
cd "$APP_DIR"
sudo -u $APP_USER git pull

# ============================================================
# 2. 后端：装依赖 + 重启服务
# ============================================================
echo ""
echo "=== 2. 后端 pip install + systemctl restart ==="
cd "$BACKEND_DIR"
sudo -u $APP_USER bash -c "source venv/bin/activate && pip install -r requirements.txt -q"
sudo systemctl restart what2eat-backend
sleep 2
sudo systemctl status what2eat-backend --no-pager | head -10
echo ""
echo "=== 3. 验证后端 ready ==="
curl -s -m 5 http://127.0.0.1:8000/ready
echo ""

# ============================================================
# 3. 前端：清理旧 build → pnpm install → pnpm build
# ============================================================
echo ""
echo "=== 4. 前端清理旧 build + pnpm install + build ==="
cd "$FRONTEND_DIR"
# 关键：旧 dist 是 www-data 拥有，ubuntu 没权限删除
sudo rm -rf dist
sudo -u $APP_USER pnpm install --silent
sudo -u $APP_USER pnpm run build

# ============================================================
# 4. 修权限 + reload nginx
# ============================================================
echo ""
echo "=== 5. 权限 + nginx reload ==="
sudo chown -R www-data:www-data "$FRONTEND_DIR/dist"
sudo chmod o+x /home /home/ubuntu /home/ubuntu/what2eat /home/ubuntu/what2eat/frontend /home/ubuntu/what2eat/frontend/dist
sudo nginx -t
sudo systemctl reload nginx

# ============================================================
# 完成
# ============================================================
SERVER_IP=$(curl -s http://ifconfig.me 2>/dev/null || echo "<未知>")
echo ""
echo "=========================================="
echo "  更新完成 ✅"
echo "=========================================="
echo "  服务器 IP: $SERVER_IP"
echo "  前端:      http://$SERVER_IP/"
echo "  API:       http://$SERVER_IP/api/"
echo ""
echo "如果前端样式不对，浏览器强制刷新 (Ctrl+Shift+R)"
echo "=========================================="