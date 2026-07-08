# SnowAI Ekip Yönlendirme Tablosu
# /opt/snowai/teams.py
#
# Alarm adı veya host adında anahtar kelime geçiyorsa
# ilgili ekip ve bildirim kanalı eşleştirilir.
# Sıraya göre ilk eşleşen kural geçerlidir.
#
# Not: Bazı kurallar host adına bakarak Linux/DevOps sunucularını
# ayrı bir ekibe yönlendirir (Bulut ve DevOps Çözümleri).

LINUX_DEVOPS_HINTS = [
    "linux", "ubuntu", "centos", "rhel", "debian",
    "docker", "k8s", "kubernetes", "devops", "cicd", "ci-cd",
    "jenkins", "gitlab", "container", "elasticsearch", "elastic",
    "elk", "opensearch", "kafka", "redis", "mongodb", "nginx"
]

# Problem metninde root-relative path (Linux dosya sistemi göstergesi)
LINUX_PATH_PATTERN = ("fs [/", "fs:/", " / ", "/var", "/boot", "/home", "/etc", "/usr", "/opt", "/tmp")


def _is_linux_devops_host(host_name: str, problem_name: str = "") -> bool:
    h = host_name.lower()
    p = problem_name.lower()
    combined = h + " " + p

    if any(hint in combined for hint in LINUX_DEVOPS_HINTS):
        return True

    if any(pattern in p for pattern in LINUX_PATH_PATTERN):
        return True

    return False


TEAM_RULES = [
    {
        "keywords": ["cpu", "processor", "load average", "yük"],
        "team": "Sistem ve Altyapı",
        "channel": "sistem-alerts",
        "action": "Sunucu kaynak kullanımını işletim sistemine uygun araçlarla kontrol edin (Linux: top/htop, Windows: Task Manager/Resource Monitor). Kalıcı sorunlarda kapasite artırımı için Altyapı Ekibi ile koordine edin."
    },
    {
        "keywords": ["memory", "ram", "heap", "out of memory", "oom", "bellek"],
        "team": "Sistem ve Altyapı",
        "channel": "sistem-alerts",
        "action": "Bellek kullanımını izleyin. Yüksek tüketen proses tespit edilirse yeniden başlatmayı değerlendirin. Swap kullanımını kontrol edin."
    },
    {
        "keywords": ["disk", "filesystem", "storage", "inode", "depolama", "fs [", "fs:", "space is low", "alan"],
        "team": "Sistem ve Altyapı",
        "channel": "sistem-alerts",
        "action": "Disk doluluk oranını ve büyük dosyaları kontrol edin (du -sh). Log rotasyon ve temizlik politikasını gözden geçirin."
    },
    {
        "keywords": ["network", "interface", "bandwidth", "packet loss", "latency", "ping", "ağ"],
        "team": "Network ve Güvenlik",
        "channel": "network-alerts",
        "action": "Ağ bağlantısını ve trafik yoğunluğunu kontrol edin. Switch/router loglarını inceleyin. Gerekirse ISP ile iletişime geçin."
    },
    {
        "keywords": ["switch", "port", "vlan", "router", "firewall", "bgp", "ospf"],
        "team": "Network ve Güvenlik",
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
        "keywords": ["elasticsearch", "elastic", "elk", "opensearch", "cluster", "shard", "es:"],
        "team": "Bulut ve DevOps Çözümleri",
        "channel": "devops-alerts",
        "action": "Elasticsearch/OpenSearch cluster health durumunu kontrol edin (green/yellow/red). Unassigned shard sayısını ve node durumlarını inceleyin. Disk alanı ve heap kullanımını gözden geçirin."
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
        "team": "Sistem ve Altyapı",
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
        "team": "Sistem ve Altyapı",
        "channel": "sistem-alerts",
        "action": "İlgili servisi işletim sistemine uygun araçla kontrol edin (Linux: systemctl status, Windows: services.msc). Servis loglarından hata nedenini tespit edin ve yeniden başlatın."
    },
    {
        "keywords": ["zabbix", "proxy", "agent", "monitoring"],
        "team": "Yönetilen Hizmetler / Monitoring",
        "channel": "monitoring-alerts",
        "action": "Zabbix proxy/agent bağlantısını kontrol edin. Ağ erişilebilirliğini ve agent servis durumunu doğrulayın."
    },
]

# Sistemde tanımlı geçerli ekip isimleri.
# AI fallback devreye girdiğinde sadece bu listeden seçim yapabilir,
# rastgele yeni bir ekip adı üretemez.
VALID_TEAMS = [
    "Sistem ve Altyapı",
    "Network ve Güvenlik",
    "Veritabanı Ekibi",
    "Bulut ve DevOps Çözümleri",
    "Mesajlaşma Ekibi",
    "Kimlik Yönetimi Ekibi",
    "Uygulama Ekibi",
    "Donanım Ekibi",
    "Yönetilen Hizmetler / Monitoring",
]

DEFAULT_TEAM = {
    "team": "Sistem ve Altyapı",
    "channel": "genel-alerts",
    "action": "Alarm detaylarını inceleyip ilgili kaynağı kontrol edin. Gerekirse üst seviyeye eskalasyon yapın."
}

# Ekip adı -> kanal eşleştirmesi (AI fallback sonucu için)
TEAM_CHANNEL_MAP = {
    "Sistem ve Altyapı": "sistem-alerts",
    "Network ve Güvenlik": "network-alerts",
    "Veritabanı Ekibi": "dba-alerts",
    "Bulut ve DevOps Çözümleri": "devops-alerts",
    "Mesajlaşma Ekibi": "messaging-alerts",
    "Kimlik Yönetimi Ekibi": "iam-alerts",
    "Uygulama Ekibi": "app-alerts",
    "Donanım Ekibi": "hardware-alerts",
    "Yönetilen Hizmetler / Monitoring": "monitoring-alerts",
}


def get_team(problem_name: str, host_name: str = "") -> dict:
    """
    Alarm adı ve host adına göre sorumlu ekibi döndürür.
    Host adı Linux/DevOps işaretleri taşıyorsa (linux, docker, k8s, devops vb.)
    sistem/uygulama kategorisindeki alarmlar 'Bulut ve DevOps Çözümleri'
    ekibine yönlendirilir.

    Hiçbir keyword eşleşmezse 'matched': False döner — bu durumda
    app.py, AI'dan VALID_TEAMS listesinden bir tahmin ister.
    """
    text = problem_name.lower()
    is_devops_host = _is_linux_devops_host(host_name, problem_name)

    for rule in TEAM_RULES:
        for kw in rule["keywords"]:
            if kw in text:
                team = rule["team"]
                channel = rule["channel"]

                # Linux/DevOps host ise sistem ve uygulama kategorisindeki
                # alarmları Bulut ve DevOps Çözümleri ekibine yönlendir
                if is_devops_host and team in ("Sistem ve Altyapı", "Uygulama Ekibi", "Veritabanı Ekibi"):
                    team = "Bulut ve DevOps Çözümleri"
                    channel = "devops-alerts"

                return {
                    "team": team,
                    "channel": channel,
                    "action": rule["action"],
                    "matched": True
                }

    if is_devops_host:
        return {
            "team": "Bulut ve DevOps Çözümleri",
            "channel": "devops-alerts",
            "action": DEFAULT_TEAM["action"],
            "matched": True
        }

    # Hiçbir kural eşleşmedi — AI fallback gerekiyor
    return {
        "team": None,
        "channel": None,
        "action": DEFAULT_TEAM["action"],
        "matched": False
    }


def resolve_ai_team(ai_team_guess: str) -> dict:
    """
    AI'nın tahmin ettiği ekip adını VALID_TEAMS listesiyle doğrular.
    Geçerli bir ekip değilse DEFAULT_TEAM'e düşer.
    """
    if ai_team_guess in VALID_TEAMS:
        return {
            "team": ai_team_guess,
            "channel": TEAM_CHANNEL_MAP.get(ai_team_guess, "genel-alerts")
        }
    return {
        "team": DEFAULT_TEAM["team"],
        "channel": DEFAULT_TEAM["channel"]
    }
