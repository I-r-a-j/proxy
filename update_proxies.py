import requests
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
TEST_URL = "https://httpbin.org/ip"
TIMEOUT = 8
MAX_THREADS = 50

# 🔽 Proxy list sources
PROXY_URLS = [
    "https://raw.githubusercontent.com/I-r-a-j/proxy/refs/heads/main/working_proxies.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/hookzof/socks5_list/refs/heads/master/proxy.txt",
    "https://raw.githubusercontent.com/shiftytr/proxy-list/master/proxy.txt",
    "https://raw.githubusercontent.com/proxifly/free-proxy-list/refs/heads/main/proxies/all/data.txt"
]

OUTPUT_FILE = "working_proxies.txt"


def extract_ip_port(proxy: str):
    """Extract IP:PORT from a proxy string"""
    proxy = proxy.strip()
    if not proxy or proxy.startswith('#'):
        return None, None
    match = re.search(r'(\d{1,3}(?:\.\d{1,3}){3}):(\d+)', proxy)
    if match:
        ip, port = match.groups()
        if all(0 <= int(part) <= 255 for part in ip.split('.')) and 1 <= int(port) <= 65535:
            return ip, port
    return None, None


def test_proxy(proxy: str):
    """Check if a proxy works by sending request"""
    ip, port = extract_ip_port(proxy)
    if not ip or not port:
        return None

    clean_proxy = f"{ip}:{port}"

    schemes = ['http', 'socks5', 'socks4']  # fallback order

    for scheme in schemes:
        try:
            proxies = {
                'http': f'{scheme}://{clean_proxy}',
                'https': f'{scheme}://{clean_proxy}',
            }
            response = requests.get(TEST_URL, proxies=proxies, timeout=TIMEOUT, verify=True)
            if response.status_code == 200:
                return clean_proxy
        except Exception:
            continue
    return None


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

    # Deduplicate valid proxies
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

    # Save results
    with open(OUTPUT_FILE, "w") as f:
        for proxy in working_proxies:
            f.write(proxy + "\n")

    print(f"\n🎉 Done! {len(working_proxies)} working proxies saved to '{OUTPUT_FILE}'")


if __name__ == "__main__":
    main()
