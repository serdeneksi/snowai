#!/bin/bash
# SnowAI — Kaldırma Scripti
# Kullanım: sudo bash /opt/snowai/uninstall.sh
# ==========================================================================

set -e

ZBXROOT="/usr/share/zabbix"
LAYOUT="${ZBXROOT}/app/views/layout.htmlpage.php"
APACHE_CONF="/etc/apache2/conf-enabled/zabbix.conf"
INSTALL_PATH_FILE="/opt/snowai/.install_path"

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()    { echo -e "${BLUE}[*]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
warn()    { echo -e "${YELLOW}[!]${NC} $1"; }

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[✗]${NC} sudo ile çalıştırın: sudo bash /opt/snowai/uninstall.sh"
    exit 1
fi

echo ""
echo -e "${RED}SnowAI kaldırılıyor...${NC}"
echo ""

# ── Clone dizinini tespit et ──────────────────────────────────────────────
CLONE_DIR=""
if [ -f "$INSTALL_PATH_FILE" ]; then
    CLONE_DIR=$(cat "$INSTALL_PATH_FILE")
fi

# ── Servis ───────────────────────────────────────────────────────────────
info "Servis durduruluyor..."
systemctl stop snowai 2>/dev/null || true
systemctl disable snowai 2>/dev/null || true
rm -f /etc/systemd/system/snowai.service
systemctl daemon-reload
success "Servis kaldırıldı."

# ── Backend ───────────────────────────────────────────────────────────────
info "Backend dosyaları siliniyor..."
rm -rf /opt/snowai
rm -f /var/log/snowai.log
success "Backend silindi."

# ── Frontend dosyaları ────────────────────────────────────────────────────
info "Frontend dosyaları siliniyor..."
rm -f "${ZBXROOT}/js/snowai.js"
rm -f "${ZBXROOT}/assets/styles/snowai.css"
success "Frontend dosyaları silindi."

# ── Layout dosyası ────────────────────────────────────────────────────────
info "Layout dosyasından snowai satırları kaldırılıyor..."
if [ -f "$LAYOUT" ]; then
    if [ -f "${LAYOUT}.bak" ]; then
        cp "${LAYOUT}.bak" "$LAYOUT"
        rm -f "${LAYOUT}.bak"
        success "Layout yedekten geri yüklendi."
    else
        sed -i '/assets\/styles\/snowai\.css/d' "$LAYOUT"
        sed -i '/js\/snowai\.js/d' "$LAYOUT"
        success "Layout temizlendi."
    fi
fi

# ── Apache config ─────────────────────────────────────────────────────────
info "Apache config temizleniyor..."
if [ -f "$APACHE_CONF" ]; then
    sed -i '/# ---- SnowAI Proxy ----/,/# ---- SnowAI Proxy Sonu ----/d' "$APACHE_CONF"
    sed -i '/Alias \/js \/usr\/share\/zabbix\/js/d' "$APACHE_CONF"
    sed -i '/Alias \/assets \/usr\/share\/zabbix\/assets/d' "$APACHE_CONF"
    sed -i '/"\/usr\/share\/zabbix\/js"/,/^<\/Directory>/d' "$APACHE_CONF"
    sed -i '/"\/usr\/share\/zabbix\/assets"/,/^<\/Directory>/d' "$APACHE_CONF"
    apache2ctl configtest 2>/dev/null && systemctl reload apache2 2>/dev/null || true
    success "Apache config temizlendi."
fi

# ── Clone dizinini sil ────────────────────────────────────────────────────
if [ -n "$CLONE_DIR" ] && [ -d "$CLONE_DIR" ]; then
    info "Clone dizini siliniyor: ${CLONE_DIR}"
    rm -rf "$CLONE_DIR"
    success "Clone dizini silindi."
else
    warn "Clone dizini bulunamadı, manuel silmeniz gerekebilir."
fi

echo ""
echo -e "${GREEN}SnowAI tamamen kaldırıldı.${NC}"
echo -e "  Yeniden kurmak için:"
echo -e "  ${YELLOW}git clone https://github.com/serdeneksi/snowai.git && cd snowai && sudo bash install.sh${NC}"
echo ""
