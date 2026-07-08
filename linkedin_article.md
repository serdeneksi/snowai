# Zabbix'e Yapay Zeka Entegre Ettim — SnowAI

Bir alarm geldi. Bakmak için Zabbix'i açtın, alarmın ne anlama geldiğini anlamaya çalıştın, kimin ilgilenmesi gerektiğini düşündün, ne yapılacağına karar verdin.

Bu döngü her alarm için tekrar ediyor.

Ben de bunu biraz hızlandırmak istedim. Zabbix'teki her alarm satırına bir **AI Analiz** butonu ekledim. Tıkla, saniyeler içinde şunları gör:

- Ne oluyor? (1-2 cümlelik teknik analiz)
- Ne kadar acil? (Düşük / Orta / Yüksek / Kritik)
- Kim ilgilenecek? (Sorumlu ekip ve kanal)
- Ne yapılacak? (Önerilen aksiyon adımları)

Ayrı bir uygulama yok, Zabbix'i terk etmiyorsun. Popup açılıyor, analiz geliyor, kapatıyorsun.

---

## Nasıl Çalışıyor?

Arka planda bir Python Flask servisi var. Alarm bilgilerini alıyor, Cloudflare Workers AI'a gönderiyor, dönen analizi Zabbix arayüzüne yansıtıyor. Tüm bunlar bir buton tıklamasıyla, arka planda hiçbir otomatik istek olmadan çalışıyor — kota sadece tıkladığında tükeniyor.

Cloudflare Workers AI'ı tercih etmemin nedeni basit: ücretsiz, Türkiye'den sorunsuz erişiliyor ve günlük 10.000 istek limiti production ortamı için fazlasıyla yeterli.

---

## Kurulum Tek Komut

```bash
git clone https://github.com/serdeneksi/snowai.git && cd snowai && sudo bash install.sh && cd ~
```

Script çalışırken sadece Cloudflare Account ID ve API Token soruyor. Geri kalanını otomatik hallediyor: Python bağımlılıkları, systemd servisi, Apache proxy yapılandırması, Zabbix frontend entegrasyonu.

Kaldırmak da tek komut:

```bash
sudo bash ~/snowai/uninstall.sh
```

Kurduğu her şeyi temizliyor.

---

## Ekip Eşleştirme

Projedeki `teams.py` dosyasında alarm türüne göre sorumlu ekip belirleniyor. CPU alarmı → Sistem Ekibi, network alarmı → Network Ekibi gibi. Kendi yapınıza göre düzenleyip kullanabilirsiniz.

---

## Açık Kaynak

Projeyi açık kaynak olarak paylaşıyorum. Zabbix kullanan ekiplerin işine yarayacağını düşünüyorum. Katkı, öneri ve geri bildirimler memnuniyetle karşılanır.

🔗 github.com/serdeneksi/snowai

---

Benzer bir ihtiyacınız olduysa ya da farklı bir yöntemle çözdüyseniz yorumlarda buluşalım.

#Zabbix #AI #OpenSource #DevOps #Monitoring #SysAdmin #Python
