# SnowAI Configuration
# /opt/snowai/config.py

CLOUDFLARE_API_TOKEN  = "BURAYA_CLOUDFLARE_API_TOKEN_YAZIN"
CLOUDFLARE_ACCOUNT_ID = "BURAYA_ACCOUNT_ID_YAZIN"
CLOUDFLARE_MODEL      = "@cf/meta/llama-3.1-8b-instruct"

SNOWAI_HOST = "0.0.0.0"
SNOWAI_PORT = 5055

SEVERITY_MAP = {
    "0": "Not classified",
    "1": "Information",
    "2": "Warning",
    "3": "Average",
    "4": "High",
    "5": "Disaster"
}
