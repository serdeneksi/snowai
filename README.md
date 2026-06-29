# SnowAI

Zabbix Problems sayfasına yapay zeka destekli alarm analizi ekleyen hafif bir entegrasyon servisi.

Her alarm satırına **AI Analiz** butonu ekler. Butona tıklandığında Cloudflare Workers AI üzerinden:

- 1-2 cümlelik teknik analiz
- Aciliyet seviyesi (Düşük / Orta / Yüksek / Kritik)
- Sorumlu ekip ve bildirim kanalı
- Önerilen aksiyon adımları

döndürür.

---

## Gereksinimler

- Zabbix 6.x veya 7.x (Apache üzerinde)
- Ubuntu / Debian tabanlı Linux
- Python 3.8+
- Cloudflare hesabı (ücretsiz — [dash.cloudflare.com](https://dash.cloudflare.com))

---

## Kurulum

```bash
git clone https://github.com/serdeneksi/snowai.git
cd snowai
sudo bash install.sh
```

Script çalışırken **Cloudflare Account ID** ve **API Token** bilgilerini sorar, geri kalan her şeyi otomatik yapar.

### Cloudflare bilgilerini nereden alırsın?

**Account ID:**
- dash.cloudflare.com → sağ taraf → Account ID

**API Token:**
- dash.cloudflare.com → My Profile → API Tokens → Create Token
- Permissions: `Account → Workers AI → Edit`

---

## Kaldırma

```bash
sudo bash uninstall.sh
```

---

## Dosya Yapısı

```
snowai/
├── app.py            # Flask backend (Cloudflare Workers AI entegrasyonu)
├── config.py         # API bilgileri ve model ayarları
├── teams.py          # Alarm → Ekip eşleştirme tablosu
├── snowai.service    # Systemd servis tanımı
├── snowai.js         # Zabbix frontend butonu ve popup
├── snowai.css        # Popup stilleri
├── install.sh        # Tek komut kurulum scripti
└── uninstall.sh      # Kaldırma scripti
```

---

## Ekip Eşleştirme

`teams.py` dosyasında alarm adı ve host adına göre sorumlu ekip belirlenir. Kendi ekip yapınıza göre düzenleyebilirsiniz.

---

## Servis Yönetimi

```bash
# Durum
systemctl status snowai

# Yeniden başlat
systemctl restart snowai

# Log izle
tail -f /var/log/snowai.log
```

---

## Lisans

MIT
