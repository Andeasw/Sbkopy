```bash
# Configuration for Subscription Upload URL
export UPLOAD_URL=""

# Project Keep-alive URL
export PROJECT_URL=""

# Auto Keep-alive setting (Set to "true" to enable auto keep-alive, default is "false")
export AUTO_ACCESS="false"

# Running path (default is ".cache", can be customized)
export FILE_PATH=".cache"

# Subscription token route (default is "sub")
export SUB_PATH="sub"

# Unique Identifier (UUID, default is "60a44bd5-a07b-4ab4-a61f-0eb6f64cfc22", can be customized)
export UUID="f929c4da-dc2e-4e0d-9a6f-1799036af214"

# Nezha panel domain, port, and key
export NEZHA_SERVER=""
export NEZHA_PORT=""
export NEZHA_KEY=""

# Komari panel address and key
export KOMARI_SERVER=""
export KOMARI_KEY=""

# Argo tunnel domain, auth key, and port
export ARGO_DOMAIN=""
export ARGO_AUTH=""
export ARGO_PORT="8001"

# SOCKS5, TUIC, HY2, AnyTLS, Reality, and AnyReality protocol ports (leave empty or set to required port)
export S5_PORT=""
export TUIC_PORT=""
export HY2_PORT=""
export ANYTLS_PORT=""
export REALITY_PORT=""
export ANYREALITY_PORT=""

# Cloudflare preferred IP or domain (default is "sub.danfeng.eu.org")
export CFIP="cdns.doon.eu.org"

# Cloudflare preferred port (default is 443)
export CFPORT="443"

# HTTP service/subscription port (default is 3000)
export PORT="3000"

# Node name (leave empty or fill as required)
export NAME=""

# Telegram chat_id and bot_token for Telegram bot interaction
export CHAT_ID=""
export BOT_TOKEN=""

# Disable Argo tunnel setting (default is "false")
export DISABLE_ARGO="false"

# Custom certificate domain and certificate download links
export DOMAIN_NAME=""
export DOMAIN_CERT=""
export DOMAIN_KEY=""
```

### Configuration Explanation

* **UPLOAD_URL**: Subscription upload URL, leave empty or fill in the appropriate URL.
* **PROJECT_URL**: Project keep-alive URL, set according to your needs.
* **AUTO_ACCESS**: Whether to enable auto keep-alive. Set to `true` to enable, default is `false`.
* **FILE_PATH**: The path for storing running files, default is `.cache`, can be customized.
* **SUB_PATH**: Subscription token route, default is `sub`.
* **UUID**: Unique identifier, default is `60a44bd5-a07b-4ab4-a61f-0eb6f64cfc22`, can be customized.
* **NEZHA_SERVER**, **NEZHA_PORT**, **NEZHA_KEY**: Configuration for Nezha panel's address, port, and key.
* **KOMARI_SERVER**, **KOMARI_KEY**: Configuration for Komari panel's address and key.
* **ARGO_DOMAIN**, **ARGO_AUTH**, **ARGO_PORT**: Configuration for Argo tunnel's domain, auth key, and port.
* **S5_PORT**, **TUIC_PORT**, **HY2_PORT**, **ANYTLS_PORT**, **REALITY_PORT**, **ANYREALITY_PORT**: Configure ports for different protocols, leave empty or set the required port.
* **CFIP**: Preferred Cloudflare IP or domain, default is `sub.danfeng.eu.org`.
* **CFPORT**: Preferred port, default is `443`.
* **PORT**: HTTP service/subscription port, default is `3000`.
* **NAME**: Node name, leave empty or fill in as required.
* **CHAT_ID**, **BOT_TOKEN**: Telegram `chat_id` and `bot_token` for interacting with Telegram Bot.
* **DISABLE_ARGO**: Whether to disable the Argo tunnel, default is `false`.
* **DOMAIN_NAME**, **DOMAIN_CERT**, **DOMAIN_KEY**: Configuration for custom domain and certificate download links.

---

**Fork** from [eooce/python-xray-argo](https://github.com/eooce/python-xray-argo).
