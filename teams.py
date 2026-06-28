# SnowAI Ekip Yönlendirme Tablosu
# /opt/snowai/teams.py
#
# Alarm adı veya host adında anahtar kelime geçiyorsa
# ilgili ekip ve bildirim kanalı eşleştirilir.
# Sıraya göre ilk eşleşen kural geçerlidir.

TEAM_RULES = [
    {
        "keywords": ["cpu", "processor", "load average", "yük"],
        "team": "Sistem Ekibi",
        "channel": "sistem-alerts",
        "action": "Sunucu kaynak kullanımını kontrol edin. Gerekirse proses analizi yapın (top/htop). Kalıcı sorunlarda kapasite artırımı için Altyapı Ekibi ile koordine edin."
    },
    {
        "keywords": ["memory", "ram", "heap", "out of memory", "oom", "bellek"],
        "team": "Sistem Ekibi",
        "channel": "sistem-alerts",
        "action": "Bellek kullanımını izleyin. Yüksek tüketen proses tespit edilirse yeniden başlatmayı değerlendirin. Swap kullanımını kontrol edin."
    },
    {
        "keywords": ["disk", "filesystem", "storage", "inode", "depolama"],
        "team": "Sistem Ekibi",
        "channel": "sistem-alerts",
        "action": "Disk doluluk oranını ve büyük dosyaları kontrol edin (du -sh). Log rotasyon ve temizlik politikasını gözden geçirin."
    },
    {
        "keywords": ["network", "interface", "bandwidth", "packet loss", "latency", "ping", "ağ"],
        "team": "Ağ Ekibi",
        "channel": "network-alerts",
        "action": "Ağ bağlantısını ve trafik yoğunluğunu kontrol edin. Switch/router loglarını inceleyin. Gerekirse ISP ile iletişime geçin."
    },
    {
        "keywords": ["switch", "port", "vlan", "router", "firewall", "bgp", "ospf"],
        "team": "Ağ Ekibi",
        "channel": "network-alerts",
        "action": "İlgili ağ cihazının durumunu kontrol edin. Konfigürasyon değişikliği varsa değişiklik kaydını inceleyin."
    },
    {
        "keywords": ["database", "sql", "oracle", "mysql", "mssql", "postgres", "veritabanı"],
        "team": "Veritabanı Ekibi",
        "channel": "dba-alerts",
        "action": "Veritabanı bağlantı sayısını ve sorgu sürelerini kontrol edin. Uzun süren transactionları tespit edin."
    },
    {
        "keywords": ["exchange", "mail", "smtp", "imap", "pop3", "e-posta"],
        "team": "Mesajlaşma Ekibi",
        "channel": "messaging-alerts",
        "action": "Exchange servis durumunu kontrol edin. Mail kuyruğunu ve bağlantı durumunu inceleyin."
    },
    {
        "keywords": ["active directory", "ldap", "domain", "kdc", "kerberos", "ad"],
        "team": "Kimlik Yönetimi Ekibi",
        "channel": "iam-alerts",
        "action": "Domain Controller durumunu ve replikasyonunu kontrol edin (repadmin /replsummary). DNS ve NTP senkronizasyonunu doğrulayın."
    },
    {
        "keywords": ["web", "http", "https", "iis", "apache", "nginx", "ssl", "certificate"],
        "team": "Uygulama Ekibi",
        "channel": "app-alerts",
        "action": "Web servisi durumunu ve uygulama loglarını kontrol edin. SSL sertifika geçerlilik tarihini doğrulayın."
    },
    {
        "keywords": ["backup", "yedek", "veeam", "snapshot"],
        "team": "Sistem Ekibi",
        "channel": "sistem-alerts",
        "action": "Yedekleme loglarını inceleyin. Başarısız yedekleme varsa depolama alanı ve kaynak sunucu erişimini kontrol edin."
    },
    {
        "keywords": ["ups", "power", "elektrik", "güç", "battery"],
        "team": "Donanım Ekibi",
        "channel": "hardware-alerts",
        "action": "UPS durumunu fiziksel olarak kontrol edin. Güç kesintisi riski varsa Tesis Yönetimi ile koordine edin."
    },
    {
        "keywords": ["temperature", "sıcaklık", "fan", "cooling", "thermal"],
        "team": "Donanım Ekibi",
        "channel": "hardware-alerts",
        "action": "Sunucu odası sıcaklığını ve iklimlendirme sistemini kontrol edin. Fiziksel fan durumunu doğrulayın."
    },
    {
        "keywords": ["service", "servis", "process", "daemon", "stopped", "durdu"],
        "team": "Sistem Ekibi",
        "channel": "sistem-alerts",
        "action": "İlgili servisi kontrol edin (systemctl status). Servis loglarından hata nedenini tespit edin ve yeniden başlatın."
    },
    {
        "keywords": ["zabbix", "proxy", "agent", "monitoring"],
        "team": "İzleme Ekibi",
        "channel": "monitoring-alerts",
        "action": "Zabbix proxy/agent bağlantısını kontrol edin. Ağ erişilebilirliğini ve agent servis durumunu doğrulayın."
    },
]

DEFAULT_TEAM = {
    "team": "Sistem Ekibi",
    "channel": "genel-alerts",
    "action": "Alarm detaylarını inceleyip ilgili kaynağı kontrol edin. Gerekirse üst seviyeye eskalasyon yapın."
}


def get_team(problem_name: str, host_name: str = "") -> dict:
    """
    Alarm adı ve host adına göre sorumlu ekibi döndürür.
    """
    text = (problem_name + " " + host_name).lower()
    for rule in TEAM_RULES:
        for kw in rule["keywords"]:
            if kw in text:
                return {
                    "team": rule["team"],
                    "channel": rule["channel"],
                    "action": rule["action"]
                }
    return DEFAULT_TEAM
