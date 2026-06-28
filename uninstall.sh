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

echo ""
echo -e "${RED}SnowAI kaldırılıyor...${NC}"
echo ""

info "Servis durduruluyor..."
systemctl stop snowai 2>/dev/null || true
systemctl disable snowai 2>/dev/null || true
rm -f /etc/systemd/system/snowai.service
systemctl daemon-reload
success "Servis kaldırıldı."

info "Backend dosyaları siliniyor..."
rm -rf /opt/snowai
rm -f /var/log/snowai.log
success "Backend silindi."

info "Frontend dosyaları siliniyor..."
rm -f "${ZBXROOT}/js/snowai.js"
rm -f "${ZBXROOT}/assets/styles/snowai.css"
success "Frontend dosyaları silindi."

info "Layout dosyasından snowai satırları kaldırılıyor..."
if [ -f "$LAYOUT" ]; then
    sed -i '/snowai/d' "$LAYOUT"
    success "Layout temizlendi."
fi

info "Apache config temizleniyor..."
if [ -f "$APACHE_CONF" ]; then
    sed -i '/SnowAI Proxy/d' "$APACHE_CONF"
    sed -i '/5055/d' "$APACHE_CONF"
    sed -i '/ai\/analyze/d' "$APACHE_CONF"
    sed -i '/ai\/health/d' "$APACHE_CONF"
    systemctl reload apache2 2>/dev/null || true
    success "Apache config temizlendi."
fi

echo ""
echo -e "${GREEN}SnowAI başarıyla kaldırıldı.${NC}"
echo ""
