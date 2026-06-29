#!/bin/bash
# SnowAI — Kaldırma Scripti
# Kullanım: sudo bash uninstall.sh
# ==========================================================================

set -e

ZBXROOT="/usr/share/zabbix"
LAYOUT="${ZBXROOT}/app/views/layout.htmlpage.php"
APACHE_CONF="/etc/apache2/conf-enabled/zabbix.conf"

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

info()    { echo -e "${BLUE}[*]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[✗]${NC} sudo ile çalıştırın: sudo bash uninstall.sh"
    exit 1
fi

# Repo dizin kontrolü — snowai dosyaları burada olmalı
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ ! -f "${SCRIPT_DIR}/app.py" ] || [ ! -f "${SCRIPT_DIR}/snowai.js" ]; then
    echo -e "${RED}[✗]${NC} Bu script snowai repo dizininden çalıştırılmalıdır."
    echo -e "    Kullanım: cd /path/to/snowai && sudo bash uninstall.sh"
    exit 1
fi

echo ""
echo -e "${RED}SnowAI kaldırılıyor...${NC}"
echo ""

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
        # Yedek varsa direkt geri yükle — en güvenli yöntem
        cp "${LAYOUT}.bak" "$LAYOUT"
        success "Layout yedekten geri yüklendi."
    else
        # Yedek yoksa sadece snowai satırlarını sil
        # CSS satırı: <link rel="stylesheet" href="/assets/styles/snowai.css">
        # JS satırı:  <script src="/js/snowai.js"></script>
        sed -i '/assets\/styles\/snowai\.css/d' "$LAYOUT"
        sed -i '/js\/snowai\.js/d' "$LAYOUT"
        success "Layout temizlendi."
    fi
fi

# ── Apache config ─────────────────────────────────────────────────────────
info "Apache config temizleniyor..."
if [ -f "$APACHE_CONF" ]; then
    # SnowAI proxy bloğunu sil
    sed -i '/# ---- SnowAI Proxy ----/,/# ---- SnowAI Proxy Sonu ----/d' "$APACHE_CONF"
    # Alias ve Directory bloklarını sil
    sed -i '/Alias \/js \/usr\/share\/zabbix\/js/d' "$APACHE_CONF"
    sed -i '/Alias \/assets \/usr\/share\/zabbix\/assets/d' "$APACHE_CONF"
    sed -i '/"\/usr\/share\/zabbix\/js"/,/^<\/Directory>/d' "$APACHE_CONF"
    sed -i '/"\/usr\/share\/zabbix\/assets"/,/^<\/Directory>/d' "$APACHE_CONF"
    apache2ctl configtest 2>/dev/null && systemctl reload apache2 2>/dev/null || true
    success "Apache config temizlendi."
fi

echo ""
echo -e "${GREEN}SnowAI başarıyla kaldırıldı.${NC}"
echo ""
