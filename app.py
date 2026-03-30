import os
import re
import json
import time
import base64
import shutil
import asyncio
import requests
import platform
import subprocess
import threading
from threading import Thread
from dotenv import load_dotenv
from http.server import BaseHTTPRequestHandler, HTTPServer

load_dotenv()

# Environment variables
UPLOAD_URL = os.environ.get('UPLOAD_URL', '')          # 节点或订阅上传地址
PROJECT_URL = os.environ.get('PROJECT_URL', '')        # 项目url
AUTO_ACCESS = os.environ.get('AUTO_ACCESS', 'false').lower() == 'true'  # 自动保活
FILE_PATH = os.environ.get('FILE_PATH', '.cache')      # 运行路径
SUB_PATH = os.environ.get('SUB_PATH', 'sub')           # 订阅token路由
UUID = os.environ.get('UUID', 'f929c4da-dc2e-4e0d-9a6f-1799036af214')  # UUID
NEZHA_SERVER = os.environ.get('NEZHA_SERVER', '')      # 哪吒面板域名或ip
NEZHA_PORT = os.environ.get('NEZHA_PORT', '')          # 哪吒端口
NEZHA_KEY = os.environ.get('NEZHA_KEY', '')            # 哪吒密钥
KOMARI_SERVER = os.environ.get('KOMARI_SERVER', '')    # Komari面板地址
KOMARI_KEY = os.environ.get('KOMARI_KEY', '')          # Komari探针密钥 Token
ARGO_DOMAIN = os.environ.get('ARGO_DOMAIN', '')        # Argo固定隧道域名
ARGO_AUTH = os.environ.get('ARGO_AUTH', '')            # Argo固定隧道密钥
ARGO_PORT = int(os.environ.get('ARGO_PORT', '8001'))   # Argo本地端口
S5_PORT_STR = os.environ.get('S5_PORT', '')            # socks5端口
TUIC_PORT_STR = os.environ.get('TUIC_PORT', '')        # tuic端口
HY2_PORT_STR = os.environ.get('HY2_PORT', '')          # hy2端口
ANYTLS_PORT_STR = os.environ.get('ANYTLS_PORT', '')    # AnyTLS端口
REALITY_PORT_STR = os.environ.get('REALITY_PORT', '')  # Reality端口
ANYREALITY_PORT_STR = os.environ.get('ANYREALITY_PORT', '')  # AnyReality端口
CFIP = os.environ.get('CFIP', 'cdns.doon.eu.org')      # 优选ip或域名
CFPORT = int(os.environ.get('CFPORT', '443'))          # 优选端口
PORT = int(os.environ.get('PORT', '3000'))             # HTTP服务/订阅端口
NAME = os.environ.get('NAME', '')                      # 节点名称
CHAT_ID = os.environ.get('CHAT_ID', '')                # Telegram chat_id
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')            # Telegram bot_token
DISABLE_ARGO = os.environ.get('DISABLE_ARGO', 'false').lower() == 'true'  # 禁用argo开关
DOMAIN_NAME = os.environ.get('DOMAIN_NAME', '')        # 自定义证书绑定的域名
DOMAIN_CERT = os.environ.get('DOMAIN_CERT', '')        # 证书公钥(pem/crt)下载直链
DOMAIN_KEY = os.environ.get('DOMAIN_KEY', '')          # 证书私钥(key)下载直链

S5_PORT = int(S5_PORT_STR) if S5_PORT_STR and S5_PORT_STR.isdigit() else None
TUIC_PORT = int(TUIC_PORT_STR) if TUIC_PORT_STR and TUIC_PORT_STR.isdigit() else None
HY2_PORT = int(HY2_PORT_STR) if HY2_PORT_STR and HY2_PORT_STR.isdigit() else None
ANYTLS_PORT = int(ANYTLS_PORT_STR) if ANYTLS_PORT_STR and ANYTLS_PORT_STR.isdigit() else None
REALITY_PORT = int(REALITY_PORT_STR) if REALITY_PORT_STR and REALITY_PORT_STR.isdigit() else None
ANYREALITY_PORT = int(ANYREALITY_PORT_STR) if ANYREALITY_PORT_STR and ANYREALITY_PORT_STR.isdigit() else None

# Global variables
private_key = ''
public_key = ''
short_id = ''
tuic_password = ''
socks_password = ''
use_custom_cert = False
domain_name = ''

npm_path = os.path.join(FILE_PATH, 'npm')
php_path = os.path.join(FILE_PATH, 'php')
web_path = os.path.join(FILE_PATH, 'web')
bot_path = os.path.join(FILE_PATH, 'bot')
km_path = os.path.join(FILE_PATH, 'km')
sub_path = os.path.join(FILE_PATH, 'sub.txt')
list_path = os.path.join(FILE_PATH, 'list.txt')
boot_log_path = os.path.join(FILE_PATH, 'boot.log')
config_path = os.path.join(FILE_PATH, 'config.json')

def create_directory():
    print('\033c', end='')
    if not os.path.exists(FILE_PATH):
        os.makedirs(FILE_PATH)
        print(f"{FILE_PATH} is created")
    else:
        print(f"{FILE_PATH} already exists")

def delete_nodes():
    try:
        if not UPLOAD_URL or not os.path.exists(sub_path):
            return
        try:
            with open(sub_path, 'r') as file:
                file_content = file.read()
        except:
            return None

        decoded = base64.b64decode(file_content).decode('utf-8')
        nodes =[line for line in decoded.split('\n') if any(protocol in line for protocol in['vless://', 'vmess://', 'trojan://', 'hysteria2://', 'tuic://', 'anytls://', 'socks://'])]

        if not nodes:
            return
        try:
            requests.post(f"{UPLOAD_URL}/api/delete-nodes", 
                          data=json.dumps({"nodes": nodes}),
                          headers={"Content-Type": "application/json"})
        except:
            return None
    except Exception as e:
        print(f"Error in delete_nodes: {e}")
        return None

def cleanup_old_files():
    paths_to_delete =['web', 'bot', 'npm', 'km', 'boot.log', 'list.txt']
    for file in paths_to_delete:
        file_path = os.path.join(FILE_PATH, file)
        try:
            if os.path.exists(file_path):
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
        except Exception as e:
            pass

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            try:
                index_path = os.path.join(FILE_PATH, 'index.html')
                if os.path.exists(index_path):
                    with open(index_path, 'rb') as f:
                        content = f.read()
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(content)
                else:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b'Hello world!<br><br>You can visit /{SUB_PATH}(Default: /sub) get your nodes!')
            except Exception:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'Hello world!<br><br>You can visit /{SUB_PATH}(Default: /sub) get your nodes!')
            
        elif self.path == f'/{SUB_PATH}':
            try:
                with open(sub_path, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(content)
            except:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass
    
def get_system_architecture():
    architecture = platform.machine().lower()
    if 'arm' in architecture or 'aarch64' in architecture:
        return 'arm'
    else:
        return 'amd'

def download_file(file_name, file_url):
    file_path = os.path.join(FILE_PATH, file_name)
    try:
        response = requests.get(file_url, stream=True, timeout=15)
        response.raise_for_status()
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Download {file_name} successfully")
        return True
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        print(f"Download {file_name} failed: {e}")
        return False

def get_files_for_architecture(architecture):
    if architecture == 'arm':
        base_files =[
            {"fileName": "web", "fileUrl": "https://arm64.ssss.nyc.mn/sb"},
            {"fileName": "bot", "fileUrl": "https://arm64.ssss.nyc.mn/2go"}
        ]
    else:
        base_files =[
            {"fileName": "web", "fileUrl": "https://amd64.ssss.nyc.mn/sb"},
            {"fileName": "bot", "fileUrl": "https://amd64.ssss.nyc.mn/2go"}
        ]

    if NEZHA_SERVER and NEZHA_KEY:
        if NEZHA_PORT:
            npm_url = "https://arm64.ssss.nyc.mn/agent" if architecture == 'arm' else "https://amd64.ssss.nyc.mn/agent"
            base_files.insert(0, {"fileName": "npm", "fileUrl": npm_url})
        else:
            php_url = "https://arm64.ssss.nyc.mn/v1" if architecture == 'arm' else "https://amd64.ssss.nyc.mn/v1"
            base_files.insert(0, {"fileName": "php", "fileUrl": php_url})

    if KOMARI_SERVER and KOMARI_KEY:
        km_url = "https://rt.jp.eu.org/nucleusp/K/Karm" if architecture == 'arm' else "https://rt.jp.eu.org/nucleusp/K/Kamd"
        base_files.append({"fileName": "km", "fileUrl": km_url})

    return base_files

def authorize_files(file_paths):
    for relative_file_path in file_paths:
        absolute_file_path = os.path.join(FILE_PATH, relative_file_path)
        if os.path.exists(absolute_file_path):
            try:
                os.chmod(absolute_file_path, 0o775)
                print(f"Empowerment success for {absolute_file_path}: 775")
            except Exception as e:
                pass

def argo_type():
    if DISABLE_ARGO:
        print("DISABLE_ARGO is set to true, disable argo tunnel")
        return
    if not ARGO_AUTH or not ARGO_DOMAIN:
        print("ARGO_DOMAIN or ARGO_AUTH variable is empty, use quick tunnels")
        return

    if "TunnelSecret" in ARGO_AUTH:
        with open(os.path.join(FILE_PATH, 'tunnel.json'), 'w') as f:
            f.write(ARGO_AUTH)
        
        tunnel_id = ARGO_AUTH.split('"')[11]
        tunnel_yml = f"""
tunnel: {tunnel_id}
credentials-file: {os.path.join(FILE_PATH, 'tunnel.json')}
protocol: http2

ingress:
  - hostname: {ARGO_DOMAIN}
    service: http://localhost:{ARGO_PORT}
    originRequest:
      noTLSVerify: true
  - service: http_status:404
"""
        with open(os.path.join(FILE_PATH, 'tunnel.yml'), 'w') as f:
            f.write(tunnel_yml)
    else:
        print("ARGO_AUTH mismatch TunnelSecret, use token connect to tunnel")

def exec_cmd(command):
    try:
        process = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        stdout, stderr = process.communicate()
        return stdout + stderr
    except Exception as e:
        return str(e)

async def download_files_and_run():
    global private_key, public_key, short_id, tuic_password, socks_password, use_custom_cert, domain_name
    
    architecture = get_system_architecture()
    files_to_download = get_files_for_architecture(architecture)
    if not files_to_download:
        return
    
    download_success = True
    for file_info in files_to_download:
        if not download_file(file_info["fileName"], file_info["fileUrl"]):
            download_success = False
            
    if not download_success:
        print("Error downloading files")
        return
    
    files_to_authorize =['npm', 'web', 'bot'] if NEZHA_PORT else ['php', 'web', 'bot']
    if KOMARI_SERVER and KOMARI_KEY:
        files_to_authorize.append('km')
    authorize_files(files_to_authorize)
    
    persist_file = os.path.join(FILE_PATH, 'persist.json')
    need_generate = True

    if os.path.exists(persist_file):
        try:
            with open(persist_file, 'r') as f:
                data = json.load(f)
            private_key = data.get('private_key')
            public_key = data.get('public_key')
            short_id = data.get('short_id')
            tuic_password = data.get('tuic_password')
            socks_password = data.get('socks_password')
            if private_key and public_key and short_id and tuic_password and socks_password:
                need_generate = False
                print("Successfully loaded persisted keys and passwords.")
        except Exception as e:
            print(f"Error reading persist file: {e}")

    if need_generate:
        print("Generating new keys and passwords...")
        keypair_output = exec_cmd(f"{os.path.join(FILE_PATH, 'web')} generate reality-keypair")
        private_key_match = re.search(r'PrivateKey:\s*(.*)', keypair_output)
        public_key_match = re.search(r'PublicKey:\s*(.*)', keypair_output)
        
        if private_key_match and public_key_match:
            private_key = private_key_match.group(1).strip()
            public_key = public_key_match.group(1).strip()
        else:
            print('Failed to extract privateKey or publicKey from output.')
            return
        
        # [规范位优化]: short_id (16位/8Bytes), tuic_pwd (32位/16Bytes), socks_pwd (16位/8Bytes)
        short_id = os.urandom(8).hex()
        tuic_password = os.urandom(16).hex()
        socks_password = os.urandom(8).hex()

        with open(persist_file, 'w') as f:
            json.dump({
                'private_key': private_key,
                'public_key': public_key,
                'short_id': short_id,
                'tuic_password': tuic_password,
                'socks_password': socks_password
            }, f)

    cert_path = os.path.join(FILE_PATH, 'tls_cert.pem')
    key_path = os.path.join(FILE_PATH, 'tls_private.key')
    domain_name = DOMAIN_NAME if DOMAIN_NAME else "www.bing.com"

    if DOMAIN_CERT and DOMAIN_KEY and DOMAIN_NAME:
        print("Attempting to download custom certificates...")
        cert_ok = download_file('custom_cert.pem', DOMAIN_CERT)
        key_ok = download_file('custom_private.key', DOMAIN_KEY)
        
        if cert_ok and key_ok:
            use_custom_cert = True
            cert_path = os.path.join(FILE_PATH, 'custom_cert.pem')
            key_path = os.path.join(FILE_PATH, 'custom_private.key')
            domain_name = DOMAIN_NAME
            print(f"Successfully downloaded and applied custom certificate for {domain_name}")
        else:
            print("Failed to download custom certificates. Falling back to self-signed.")

    if not use_custom_cert:
        domain_name = "www.bing.com"
        print("Generating self-signed certificate...")
        exec_cmd(f'openssl ecparam -genkey -name prime256v1 -out "{key_path}"')
        exec_cmd(f'openssl req -new -x509 -days 3650 -key "{key_path}" -out "{cert_path}" -subj "/CN={domain_name}"')
    
    port = NEZHA_SERVER.split(":")[-1] if ":" in NEZHA_SERVER else ""
    nezha_tls = "tls" if port in["443", "8443", "2096", "2087", "2083", "2053"] else "false"

    if NEZHA_SERVER and NEZHA_KEY and not NEZHA_PORT:
        config_yaml = f"""
client_secret: {NEZHA_KEY}
debug: false
disable_auto_update: true
disable_command_execute: false
disable_force_update: true
disable_nat: false
disable_send_query: false
gpu: false
insecure_tls: true
ip_report_period: 1800
report_delay: 4
server: {NEZHA_SERVER}
skip_connection_count: true
skip_procs_count: true
temperature: false
tls: {nezha_tls}
use_gitee_to_upgrade: false
use_ipv6_country_code: false
uuid: {UUID}"""
        with open(os.path.join(FILE_PATH, 'config.yaml'), 'w') as f:
            f.write(config_yaml)
    
    config = {
        "log": {"disabled": True, "level": "info", "timestamp": True},
        "inbounds":[
            {
                "tag": "vmess-ws-in",
                "type": "vmess",
                "listen": "::",
                "listen_port": ARGO_PORT,
                "users":[{"uuid": UUID}],
                "transport": {
                    "type": "ws",
                    "path": "/vmess-argo",
                    "early_data_header_name": "Sec-WebSocket-Protocol"
                }
            }
        ],
        "endpoints":[
          {
              "type": "wireguard",
              "tag": "wireguard-out",
              "mtu": 1280,
              "address":["172.16.0.2/32", "2606:4700:110:8dfe:d141:69bb:6b80:925/128"],
              "private_key": "YFYOAdbw1bKTHlNNi+aEjBM3BO7unuFC5rOkMRAz9XY=",
              "peers":[
                  {
                    "address": "engage.cloudflareclient.com",
                    "port": 2408,
                    "public_key": "bmXOC+F1FxEMF9dyiK2H5/1SUtzH0JuVo51h2wPfgyo=",
                    "allowed_ips":["0.0.0.0/0", "::/0"],
                    "reserved":[78, 135, 76]
                  }
              ]
          }
        ],
        "outbounds":[{"type": "direct", "tag": "direct"}],
        "route": {
            "rule_set":[
                {
                    "tag": "netflix", "type": "remote", "format": "binary",
                    "url": "https://raw.githubusercontent.com/SagerNet/sing-geosite/rule-set/geosite-netflix.srs",
                    "download_detour": "direct"
                },
                {
                    "tag": "openai", "type": "remote", "format": "binary",
                    "url": "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geosite/openai.srs",
                    "download_detour": "direct"
                }
            ],
            "rules":[{"rule_set": ["openai", "netflix"], "outbound": "wireguard-out"}],
            "final": "direct"
        }
    }
    
    if REALITY_PORT and REALITY_PORT > 0:
        reality_config = {
            "tag": "vless-in", "type": "vless", "listen": "::", "listen_port": REALITY_PORT,
            "users":[{"uuid": UUID, "flow": "xtls-rprx-vision"}],
            "tls": {
                "enabled": True, "server_name": "www.iij.ad.jp",
                "reality": {
                    "enabled": True, "handshake": {"server": "www.iij.ad.jp", "server_port": 443},
                    "private_key": private_key, "short_id": [short_id]
                }
            }
        }
        config["inbounds"].append(reality_config)
    
    if HY2_PORT and HY2_PORT > 0:
        hysteria_config = {
            "tag": "hysteria-in", "type": "hysteria2", "listen": "::", "listen_port": HY2_PORT,
            "users":[{"password": UUID}],
            "masquerade": "https://www.bing.com",
            "tls": {"enabled": True, "certificate_path": cert_path, "key_path": key_path}
        }
        config["inbounds"].append(hysteria_config)
    
    if TUIC_PORT and TUIC_PORT > 0:
        tuic_config = {
            "tag": "tuic-in", "type": "tuic", "listen": "::", "listen_port": TUIC_PORT,
            "users":[{"uuid": UUID, "password": tuic_password}],
            "congestion_control": "bbr",
            "tls": {"enabled": True, "alpn": ["h3"], "certificate_path": cert_path, "key_path": key_path}
        }
        config["inbounds"].append(tuic_config)
    
    if S5_PORT and S5_PORT > 0:
        s5_config = {
            "tag": "s5-in", "type": "socks", "listen": "::", "listen_port": S5_PORT,
            "users":[{"username": UUID[0:8], "password": socks_password}]
        }
        config["inbounds"].append(s5_config)
    
    if ANYTLS_PORT and ANYTLS_PORT > 0:
        anytls_config = {
            "tag": "anytls-in", "type": "anytls", "listen": "::", "listen_port": ANYTLS_PORT,
            "users":[{"password": UUID}],
            "tls": {"enabled": True, "certificate_path": cert_path, "key_path": key_path}
        }
        config["inbounds"].append(anytls_config)
    
    if ANYREALITY_PORT and ANYREALITY_PORT > 0:
        anyreality_config = {
            "tag": "anyreality-in", "type": "anytls", "listen": "::", "listen_port": ANYREALITY_PORT,
            "users":[{"password": UUID}],
            "tls": {
                "enabled": True, "server_name": "www.iij.ad.jp",
                "reality": {
                    "enabled": True, "handshake": {"server": "www.iij.ad.jp", "server_port": 443},
                    "private_key": private_key, "short_id":[short_id]
                }
            }
        }
        config["inbounds"].append(anyreality_config)
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    # Run nezha
    if NEZHA_SERVER and NEZHA_PORT and NEZHA_KEY:
        tls_ports =['443', '8443', '2096', '2087', '2083', '2053']
        nezha_tls = '--tls' if NEZHA_PORT in tls_ports else ''
        command = f"nohup {os.path.join(FILE_PATH, 'npm')} -s {NEZHA_SERVER}:{NEZHA_PORT} -p {NEZHA_KEY} {nezha_tls} >/dev/null 2>&1 &"
        try:
            exec_cmd(command)
            print('npm is running')
            time.sleep(1)
        except Exception:
            pass
    elif NEZHA_SERVER and NEZHA_KEY:
        command = f"nohup {FILE_PATH}/php -c \"{FILE_PATH}/config.yaml\" >/dev/null 2>&1 &"
        try:
            exec_cmd(command)
            print('php is running')
            time.sleep(1)
        except Exception:
            pass
            
    # Run komari 
    if KOMARI_SERVER and KOMARI_KEY:
        k_server = KOMARI_SERVER if KOMARI_SERVER.startswith('http') else f"https://{KOMARI_SERVER}"
        command = f"nohup {os.path.join(FILE_PATH, 'km')} -e {k_server} -t {KOMARI_KEY} >/dev/null 2>&1 &"
        try:
            exec_cmd(command)
            print('komari probe is running')
            time.sleep(1)
        except Exception:
            pass
    
    # Run Core
    command = f"nohup {os.path.join(FILE_PATH, 'web')} run -c {os.path.join(FILE_PATH, 'config.json')} >/dev/null 2>&1 &"
    try:
        exec_cmd(command)
        print('web is running')
        time.sleep(1)
    except Exception:
        pass
    
    # Run CF
    if not DISABLE_ARGO:
        if os.path.exists(os.path.join(FILE_PATH, 'bot')):
            if re.match(r'^[A-Z0-9a-z=]{120,250}$', ARGO_AUTH):
                args = f"tunnel --edge-ip-version auto --no-autoupdate --protocol http2 run --token {ARGO_AUTH}"
            elif "TunnelSecret" in ARGO_AUTH:
                args = f"tunnel --edge-ip-version auto --config {os.path.join(FILE_PATH, 'tunnel.yml')} run"
            else:
                args = f"tunnel --edge-ip-version auto --no-autoupdate --protocol http2 --logfile {os.path.join(FILE_PATH, 'boot.log')} --loglevel info --url http://localhost:{ARGO_PORT}"
            try:
                exec_cmd(f"nohup {os.path.join(FILE_PATH, 'bot')} {args} >/dev/null 2>&1 &")
                print('bot is running')
                time.sleep(2)
            except Exception:
                pass
    
    time.sleep(5)
    await extract_domains()

async def extract_domains():
    if DISABLE_ARGO:
        await generate_links(None)
        return

    if ARGO_AUTH and ARGO_DOMAIN:
        await generate_links(ARGO_DOMAIN)
    else:
        try:
            with open(boot_log_path, 'r') as f:
                file_content = f.read()
            lines = file_content.split('\n')
            argo_domains =[]
            for line in lines:
                domain_match = re.search(r'https?://([^ ]*trycloudflare\.com)/?', line)
                if domain_match:
                    argo_domains.append(domain_match.group(1))
            
            if argo_domains:
                await generate_links(argo_domains[0])
            else:
                print('ArgoDomain not found, re-running bot to obtain ArgoDomain')
                if os.path.exists(boot_log_path):
                    os.remove(boot_log_path)
                try: exec_cmd('pkill -f "[b]ot" > /dev/null 2>&1')
                except: pass
                time.sleep(1)
                args = f'tunnel --edge-ip-version auto --no-autoupdate --protocol http2 --logfile {FILE_PATH}/boot.log --loglevel info --url http://localhost:{ARGO_PORT}'
                exec_cmd(f'nohup {os.path.join(FILE_PATH, "bot")} {args} >/dev/null 2>&1 &')
                time.sleep(6)
                await extract_domains()
        except Exception:
            pass

def upload_nodes():
    if UPLOAD_URL and PROJECT_URL:
        try:
            requests.post(f"{UPLOAD_URL}/api/add-subscriptions",
                          json={"subscription": [f"{PROJECT_URL}/{SUB_PATH}"]},
                          headers={"Content-Type": "application/json"})
        except Exception:
            pass
    elif UPLOAD_URL:
        if not os.path.exists(list_path): return
        with open(list_path, 'r') as f: content = f.read()
        nodes =[line for line in content.split('\n') if any(protocol in line for protocol in['vless://', 'vmess://', 'trojan://', 'hysteria2://', 'tuic://', 'anytls://', 'socks://'])]
        if not nodes: return
        try:
            requests.post(f"{UPLOAD_URL}/api/add-nodes",
                          data=json.dumps({"nodes": nodes}),
                          headers={"Content-Type": "application/json"})
        except: pass

def send_telegram():
    if not BOT_TOKEN or not CHAT_ID:
        return
    try:
        with open(sub_path, 'r') as f:
            message = f.read()
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        escaped_name = re.sub(r'([_*\[\]()~>#+=|{}.!\-])', r'\\\1', NAME)
        params = {"chat_id": CHAT_ID, "text": f"**{escaped_name}节点推送通知**\n{message}", "parse_mode": "MarkdownV2"}
        requests.post(url, params=params)
    except:
        pass

async def generate_links(argo_domain):
    SERVER_IP = ''
    try: SERVER_IP = subprocess.check_output('curl -s --max-time 2 ipv4.ip.sb', shell=True).decode().strip()
    except:
        try: SERVER_IP = f"[{subprocess.check_output('curl -s --max-time 1 ipv6.ip.sb', shell=True).decode().strip()}]"
        except: pass

    try:
        cmd = '''curl -sm 3 -H 'User-Agent: Mozilla/5.0' 'https://api.ip.sb/geoip' | tr -d '\n' | awk -F'"' '{c="";i="";for(x=1;x<=NF;x++){if($x=="country_code")c=$(x+2);if($x=="isp")i=$(x+2)};if(c&&i)print c"-"i}' | sed 's/ /_/g' '''
        ISP = subprocess.check_output(cmd, shell=True).decode().strip()
    except: ISP = "Unknown"

    Nodename = f"{NAME.strip()}-{ISP}" if (NAME and NAME.strip()) else f"{ISP}"

    sub_txt = ""
    if not DISABLE_ARGO and argo_domain:
        vmess_config = {
            "v": "2","ps": f"{Nodename}","add": CFIP,"port": CFPORT,"id": UUID,"aid": "0","scy": "auto","net": "ws","type": "none",
            "host": argo_domain,"path": "/vmess-argo?ed=2560","tls": "tls","sni": argo_domain,"alpn": "","fp": "firefox"
        }
        sub_txt = f"vmess://{base64.b64encode(json.dumps(vmess_config).encode()).decode()}"

    if TUIC_PORT is not None:
        insecure_flag = "" if use_custom_cert else "&allow_insecure=1"
        tuic_node = f"\ntuic://{UUID}:{tuic_password}@{SERVER_IP}:{TUIC_PORT}?sni={domain_name}&congestion_control=bbr&udp_relay_mode=native&alpn=h3{insecure_flag}#{Nodename}"
        sub_txt = (sub_txt + tuic_node) if sub_txt else tuic_node

    if HY2_PORT is not None:
        insecure_flag = "" if use_custom_cert else "&insecure=1"
        hysteria_node = f"\nhysteria2://{UUID}@{SERVER_IP}:{HY2_PORT}/?sni={domain_name}&obfs=none{insecure_flag}#{Nodename}"
        sub_txt = (sub_txt + hysteria_node) if sub_txt else hysteria_node

    if REALITY_PORT is not None:
        vless_node = f"\nvless://{UUID}@{SERVER_IP}:{REALITY_PORT}?encryption=none&flow=xtls-rprx-vision&security=reality&sni=www.iij.ad.jp&fp=firefox&pbk={public_key}&sid={short_id}&type=tcp&headerType=none#{Nodename}"
        sub_txt = (sub_txt + vless_node) if sub_txt else vless_node

    if ANYTLS_PORT is not None:
        insecure_flag = "" if use_custom_cert else "&insecure=1&allowInsecure=1"
        anytls_node = f"\nanytls://{UUID}@{SERVER_IP}:{ANYTLS_PORT}?security=tls&sni={domain_name}{insecure_flag}#{Nodename}"
        sub_txt = (sub_txt + anytls_node) if sub_txt else anytls_node

    if ANYREALITY_PORT is not None:
        anyreality_node = f"\nanytls://{UUID}@{SERVER_IP}:{ANYREALITY_PORT}?security=reality&sni=www.iij.ad.jp&fp=firefox&pbk={public_key}&sid={short_id}&type=tcp&headerType=none#{Nodename}"
        sub_txt = (sub_txt + anyreality_node) if sub_txt else anyreality_node

    if S5_PORT is not None:
        S5_AUTH = base64.b64encode(f"{UUID[0:8]}:{socks_password}".encode()).decode()
        s5_node = f"\nsocks://{S5_AUTH}@{SERVER_IP}:{S5_PORT}#{Nodename}"
        sub_txt = (sub_txt + s5_node) if sub_txt else s5_node

    with open(sub_path, 'w') as f: f.write(base64.b64encode(sub_txt.encode()).decode())
    with open(list_path, 'w') as f: f.write(sub_txt)
    
    print('\033[32m' + base64.b64encode(sub_txt.encode()).decode() + '\033[0m')
    print(f"\nLogs will be deleted in 90 seconds,you can copy the above nodes")
    send_telegram()
    upload_nodes()
    return sub_txt   
 
def add_visit_task():
    if not AUTO_ACCESS or not PROJECT_URL: return
    try:
        requests.post('https://keep.gvrander.eu.org/add-url', json={"url": PROJECT_URL}, headers={"Content-Type": "application/json"})
    except: pass

def clean_files():
    def _cleanup():
        time.sleep(90)
        files_to_delete =[boot_log_path, config_path, list_path, web_path, bot_path, php_path, npm_path, km_path]
        if NEZHA_PORT: files_to_delete.append(npm_path)
        elif NEZHA_SERVER and NEZHA_KEY: files_to_delete.append(php_path)
        for file in files_to_delete:
            try:
                if os.path.exists(file):
                    if os.path.isdir(file): shutil.rmtree(file)
                    else: os.remove(file)
            except: pass
        print('\033c', end='')
        print('App is running\nThank you for using this script, enjoy!')
    threading.Thread(target=_cleanup, daemon=True).start()
    
async def start_server():
    delete_nodes()
    cleanup_old_files()
    create_directory()
    argo_type()
    await download_files_and_run()
    add_visit_task()
    server_thread = Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()   
    clean_files()
    
def run_server():
    server = HTTPServer(('0.0.0.0', PORT), RequestHandler)
    print(f"Server is running on port {PORT}\nRunning done！")
    server.serve_forever()
    
def run_async():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_server()) 
    while True: time.sleep(3600)
        
if __name__ == "__main__":
    run_async()