# Step 1: Install required packages
!pip install requests[socks] > /dev/null

# Step 2: Import libraries
import requests
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

# Step 3: Configuration
TEST_URL = "https://httpbin.org/ip"
TIMEOUT = 8
MAX_THREADS = 50

# 🔽 PASTE YOUR PROXY LIST URLs HERE (as many as you want)
PROXY_URLS = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
    # Add more URLs as needed...
]

# Output file
OUTPUT_FILE = "working_proxies.txt"

# Step 4: Extract IP:PORT from any proxy string
def extract_ip_port(proxy):
    proxy = proxy.strip()
    if not proxy or proxy.startswith('#'):
        return None, None
    match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)', proxy)
    if match:
        ip, port = match.groups()
        if all(0 <= int(part) <= 255 for part in ip.split('.')) and 1 <= int(port) <= 65535:
            return ip, port
    return None, None

# Step 5: Test proxy with auto-detection of type
def test_proxy(proxy):
    ip, port = extract_ip_port(proxy)
    if not ip or not port:
        return None

    clean_proxy = f"{ip}:{port}"

    # Detect scheme from proxy string
    proxy_lower = proxy.lower()
    schemes = []

    if proxy_lower.startswith('socks5://'):
        schemes = ['socks5']
    elif proxy_lower.startswith('socks4://'):
        schemes = ['socks4']
    elif proxy_lower.startswith('http://') or proxy_lower.startswith('https://'):
        schemes = ['http']
    else:
        # Unknown scheme: try common types
        schemes = ['http', 'socks5', 'socks4']

    for scheme in schemes:
        try:
            proxies = {
                'http': f'{scheme}://{clean_proxy}',
                'https': f'{scheme}://{clean_proxy}'
            }
            response = requests.get(TEST_URL, proxies=proxies, timeout=TIMEOUT, verify=True)
            if response.status_code == 200:
                return clean_proxy
        except Exception:
            continue
    return None

# Step 6: Main function
def main():
    print("📥 Fetching and combining proxy lists...\n")
    raw_proxies = []

    for url in PROXY_URLS:
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            lines = response.text.splitlines()
            raw_proxies.extend(lines)
            print(f"✅ Fetched {len(lines)} lines from: {url}")
        except Exception as e:
            print(f"❌ Failed to fetch {url}: {e}")

    # Extract valid IP:PORT entries
    candidates = []
    seen = set()

    for line in raw_proxies:
        ip, port = extract_ip_port(line)
        if ip and port:
            proxy = f"{ip}:{port}"
            if proxy not in seen:
                seen.add(proxy)
                candidates.append(proxy)

    print(f"\n🔍 Total unique proxies to test: {len(candidates)}")

    if not candidates:
        print("❌ No valid proxies found.")
        return

    print("🧪 Testing proxies...\n")
    working_proxies = []

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        future_to_proxy = {executor.submit(test_proxy, proxy): proxy for proxy in candidates}
        for future in as_completed(future_to_proxy):
            result = future.result()
            if result:
                print(f"✅ Working: {result}")
                working_proxies.append(result)

    # Save to file
    with open(OUTPUT_FILE, "w") as f:
        for proxy in working_proxies:
            f.write(proxy + "\n")

    print(f"\n🎉 Done! {len(working_proxies)} working proxies saved to '{OUTPUT_FILE}'")
    print("📁 You can now download the file manually from the file browser (left panel), or use:")
    print(f"   !cat {OUTPUT_FILE}   to view content")

# Step 7: Run automatically
main()
