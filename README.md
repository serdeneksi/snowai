# SnowAI

Zabbix Problems sayfasına yapay zeka destekli alarm analizi ekleyen hafif bir entegrasyon servisi.

Her alarm satırına **AI Analiz** butonu ekler. Butona tıklandığında Google Gemini API üzerinden:
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
- Google Gemini API anahtarı (ücretsiz — [aistudio.google.com](https://aistudio.google.com))

---

## Kurulum

```bash
git clone https://github.com/KULLANICI_ADIN/snowai.git
cd snowai
sudo bash install.sh
```

Script çalışırken Gemini API anahtarınızı (`AIza...`) soracak, geri kalan her şeyi otomatik yapar.

---

## Kaldırma

```bash
sudo bash uninstall.sh
```

---

## Dosya Yapısı

```
snowai/
├── app.py            # Flask backend (Google Gemini entegrasyonu)
├── config.py         # API anahtarı ve model ayarları
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
