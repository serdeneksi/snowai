#!/bin/bash
# SnowAI — Tek Komut Kurulum Scripti
# Kullanım: sudo bash install.sh
# ==========================================================================

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="/opt/snowai"
ZBXROOT="/usr/share/zabbix"
SERVICE_FILE="/etc/systemd/system/snowai.service"
APACHE_CONF="/etc/apache2/conf-enabled/zabbix.conf"
LOG_FILE="/var/log/snowai.log"
LAYOUT="${ZBXROOT}/app/views/layout.htmlpage.php"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()    { echo -e "${BLUE}[*]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
warn()    { echo -e "${YELLOW}[!]${NC} $1"; }
error()   { echo -e "${RED}[✗]${NC} $1"; exit 1; }

echo ""
echo -e "${BLUE}╔══════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        SnowAI Kurulum Scripti        ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════╝${NC}"
echo ""

# Root kontrolü
if [ "$EUID" -ne 0 ]; then
    error "Bu scripti root veya sudo ile çalıştırın: sudo bash install.sh"
fi

# API bilgilerini al
echo -e "${YELLOW}Cloudflare Account ID girin:${NC}"
read -r -p "> " CF_ACCOUNT_ID

if [ -z "$CF_ACCOUNT_ID" ]; then
    error "Account ID boş olamaz."
fi

echo -e "${YELLOW}Cloudflare API Token girin:${NC}"
read -r -p "> " CF_API_TOKEN

if [ -z "$CF_API_TOKEN" ]; then
    error "API Token boş olamaz."
fi

echo ""

# ── AŞAMA 1: Python Backend ──────────────────────────────────────────────
info "Python bağımlılıkları kontrol ediliyor..."
if ! command -v python3 &>/dev/null; then
    error "Python3 bulunamadı. Önce Python3 kurun."
fi

if ! command -v pip3 &>/dev/null; then
    info "pip3 kuruluyor..."
    apt-get install -y python3-pip -q
fi

info "Flask bağımlılıkları kuruluyor..."
pip3 install flask flask-cors -q
success "Python bağımlılıkları hazır."

# ── AŞAMA 2: Servis Dosyaları ─────────────────────────────────────────────
info "SnowAI servis dizini oluşturuluyor: ${INSTALL_DIR}"
mkdir -p "$INSTALL_DIR"

cp "${REPO_DIR}/app.py"   "$INSTALL_DIR/"
cp "${REPO_DIR}/teams.py" "$INSTALL_DIR/"

# config.py — API bilgilerini yerleştir
sed -e "s|BURAYA_CLOUDFLARE_API_TOKEN_YAZIN|${CF_API_TOKEN}|g" \
    -e "s|BURAYA_ACCOUNT_ID_YAZIN|${CF_ACCOUNT_ID}|g" \
    "${REPO_DIR}/config.py" > "${INSTALL_DIR}/config.py"

success "Backend dosyaları kopyalandı."

# Log dosyası
touch "$LOG_FILE"
chmod 644 "$LOG_FILE"

# ── AŞAMA 3: Systemd Servisi ──────────────────────────────────────────────
info "Systemd servisi kuruluyor..."
cp "${REPO_DIR}/snowai.service" "$SERVICE_FILE"
systemctl daemon-reload
systemctl enable snowai -q
systemctl restart snowai
sleep 2

if systemctl is-active --quiet snowai; then
    success "SnowAI servisi çalışıyor."
else
    error "SnowAI servisi başlatılamadı. Kontrol: journalctl -u snowai -n 20"
fi

# ── AŞAMA 4: Apache Proxy ────────────────────────────────────────────────
info "Apache proxy yapılandırılıyor..."

if [ ! -f "$APACHE_CONF" ]; then
    error "Apache Zabbix config bulunamadı: ${APACHE_CONF}"
fi

# Proxy modüllerini etkinleştir
info "Apache proxy modülleri etkinleştiriliyor..."
a2enmod proxy proxy_http headers -q 2>/dev/null || true
success "Apache proxy modülleri hazır."

# Daha önce eklendi mi?
if grep -q "SnowAI Proxy" "$APACHE_CONF"; then
    warn "Apache proxy satırları zaten mevcut, atlanıyor."
else
    # Alias /js ve /assets ekle (yoksa)
    if ! grep -q "Alias /js" "$APACHE_CONF"; then
        cat >> "$APACHE_CONF" << 'APACHEEOF'

Alias /js /usr/share/zabbix/js
Alias /assets /usr/share/zabbix/assets

<Directory "/usr/share/zabbix/js">
    Options FollowSymLinks
    AllowOverride None
    Require all granted
</Directory>

<Directory "/usr/share/zabbix/assets">
    Options FollowSymLinks
    AllowOverride None
    Require all granted
</Directory>
APACHEEOF
    fi

    cat >> "$APACHE_CONF" << 'APACHEEOF'

# ---- SnowAI Proxy ----
ProxyPreserveHost On
ProxyPass        /ai/analyze  http://127.0.0.1:5055/analyze
ProxyPassReverse /ai/analyze  http://127.0.0.1:5055/analyze
ProxyPass        /ai/health   http://127.0.0.1:5055/health
ProxyPassReverse /ai/health   http://127.0.0.1:5055/health
# ---- SnowAI Proxy Sonu ----
APACHEEOF
    success "Apache proxy satırları eklendi."
fi

# Syntax kontrolü
apache2ctl configtest 2>/dev/null || error "Apache config hatası. Kontrol edin: apache2ctl configtest"
systemctl restart apache2
success "Apache yeniden başlatıldı."

# ── AŞAMA 5: Zabbix Frontend ─────────────────────────────────────────────
info "Zabbix frontend dosyaları kopyalanıyor..."

if [ ! -d "$ZBXROOT" ]; then
    error "Zabbix frontend dizini bulunamadı: ${ZBXROOT}"
fi

cp "${REPO_DIR}/snowai.css" "${ZBXROOT}/assets/styles/snowai.css"
cp "${REPO_DIR}/snowai.js"  "${ZBXROOT}/js/snowai.js"
chmod 644 "${ZBXROOT}/assets/styles/snowai.css"
chmod 644 "${ZBXROOT}/js/snowai.js"
success "CSS ve JS kopyalandı."

# layout.htmlpage.php
if [ ! -f "$LAYOUT" ]; then
    error "Zabbix layout dosyası bulunamadı: ${LAYOUT}"
fi

if grep -q "snowai.css" "$LAYOUT"; then
    warn "Layout dosyasında snowai zaten mevcut, atlanıyor."
else
    cp "$LAYOUT" "${LAYOUT}.bak"
    sed -i 's|</body>|<link rel="stylesheet" href="/assets/styles/snowai.css">\n<script src="/js/snowai.js"></script>\n</body>|' "$LAYOUT"
    success "Layout dosyası güncellendi."
fi

# ── Kaldırma için dizini ve scripti kaydet ───────────────────────────────
echo "$REPO_DIR" > /opt/snowai/.install_path
cp "${REPO_DIR}/uninstall.sh" /opt/snowai/uninstall.sh
chmod +x /opt/snowai/uninstall.sh

# ── AŞAMA 6: Doğrulama ───────────────────────────────────────────────────
echo ""
info "Kurulum doğrulanıyor..."

HEALTH=$(curl -s http://127.0.0.1/ai/health 2>/dev/null || true)
if echo "$HEALTH" | grep -q "ok"; then
    success "API sağlık kontrolü geçti."
else
    warn "API sağlık kontrolü başarısız. Servis durumu: systemctl status snowai"
fi

JS_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/js/snowai.js 2>/dev/null || true)
if [ "$JS_CODE" = "200" ]; then
    success "JS dosyası erişilebilir."
else
    warn "JS dosyasına erişilemiyor (HTTP ${JS_CODE})."
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║      SnowAI kurulumu tamamlandı!     ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"
echo ""
echo -e "  Zabbix → Monitoring → Problems sayfasını açın"
echo -e "  Her alarm satırında ${BLUE}[AI Analiz]${NC} butonu görünmeli"
echo -e "  Log izleme: ${YELLOW}tail -f /var/log/snowai.log${NC}"
echo ""
echo -e "  Kaldırmak için:"
echo -e "  ${YELLOW}sudo bash /opt/snowai/uninstall.sh${NC}"
echo ""
