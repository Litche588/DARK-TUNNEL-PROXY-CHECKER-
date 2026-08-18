import socket
import time
import concurrent.futures
import argparse

# ═══════════════════════════════════════════════════════════════
#                       LITCHE DARK TUNNEL
#                  Proxy Stability Checker
# ═══════════════════════════════════════════════════════════════

VERSION = "1.0"
AUTHOR = "Litche"
TELEGRAM_GROUP = "https://t.me/DZTEAMDEV"
TELEGRAM_USER = "https://web.telegram.org/k/#@litcheeeee"

WORKING_PROXIES_FILE = "dark_tunnel_stable.txt"
TIMEOUT = 5
MAX_THREADS = 30


def banner():
    print(r"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║                  ██╗     ██╗████████╗ ██████╗██╗  ██╗       ║
║                  ██║     ██║╚══██╔══╝██╔════╝██║  ██║       ║
║                  ██║     ██║   ██║   ██║     ███████║       ║
║                  ██║     ██║   ██║   ██║     ██╔══██║       ║
║                  ███████╗██║   ██║   ╚██████╗██║  ██║       ║
║                  ╚══════╝╚═╝   ╚═╝    ╚═════╝╚═╝  ╚═╝       ║
║                                                              ║
║                 DARK TUNNEL PROXY CHECKER                    ║
║                                                              ║
║                  Author : Litche                              ║
║                  Version: 1.0                                ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

   Telegram Group : https://t.me/DZTEAMDEV
   Telegram       : @litcheeeee

   [!] هذه الأداة مخصصة لفحص استقرار البروكسيات
       التي يمكن استخدامها مع Dark Tunnel.

   [!] بعض البروكسيات قد لا تعمل إلا بعد تفعيل
       وضع الطيران ثم إعادة الاتصال بالشبكة.

""")


def build_payload(ssh_host, ssh_port):
    return (
        f"CONNECT {ssh_host}:{ssh_port} HTTP/1.0\r\n"
        f"Host: youtube.com\r\n\r\n"
    ).encode("utf-8")


def test_proxy_stability(args_tuple):
    proxy_line, ssh_host, ssh_port = args_tuple

    proxy_line = proxy_line.strip()

    if not proxy_line or ":" not in proxy_line:
        return None

    try:
        proxy_ip, proxy_port = proxy_line.split(":")[:2]
        proxy_port = int(proxy_port)
    except ValueError:
        return None

    sock = None

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)

        start_time = time.time()

        # الاتصال بالبروكسي
        sock.connect((proxy_ip, proxy_port))

        # إرسال CONNECT
        sock.sendall(build_payload(ssh_host, ssh_port))

        data = sock.recv(1024)

        if b"200" in data:

            if b"SSH-" not in data:
                sock.settimeout(3)

                try:
                    data += sock.recv(1024)
                except Exception:
                    pass

            # التأكد من وجود SSH
            if b"SSH-" in data:

                # اختبار الاستقرار
                time.sleep(4)

                try:
                    sock.sendall(b"\x00")
                except Exception:
                    return None

                latency = int((time.time() - start_time) * 1000)

                print(
                    f"[+] Stable -> {proxy_ip}:{proxy_port} "
                    f"| Latency: {latency}ms"
                )

                return f"{proxy_ip}:{proxy_port}"

    except Exception:
        pass

    finally:
        if sock:
            try:
                sock.close()
            except Exception:
                pass

    return None


def main():

    banner()

    parser = argparse.ArgumentParser(
        add_help=False,
        description="Litche Dark Tunnel Proxy Stability Checker"
    )

    parser.add_argument(
        "-h",
        "--host",
        dest="host",
        required=False,
        help="SSH Host"
    )

    parser.add_argument(
        "-p",
        "--port",
        dest="port",
        type=int,
        required=False,
        help="SSH Port"
    )

    parser.add_argument(
        "-w",
        "--wordlist",
        dest="wordlist",
        required=False,
        help="Proxy wordlist"
    )

    parser.add_argument(
        "--help",
        action="help",
        help="Show this help message"
    )

    args = parser.parse_args()

    # التحقق من المدخلات
    if not args.host or not args.port or not args.wordlist:
        print("""
Usage:

    python3 script.py -h <SSH_HOST> -p <SSH_PORT> -w <PROXY_FILE>

Example:

    python3 script.py -h fr1.sshtun.site -p 80 -w proxies.txt

Options:

    -h, --host       SSH Host
    -p, --port       SSH Port
    -w, --wordlist   Proxy list
    --help           Show help

Output:

    dark_tunnel_stable.txt
""")
        return

    # قراءة البروكسيات
    try:
        with open(args.wordlist, "r", encoding="utf-8") as f:
            proxies = f.readlines()

    except FileNotFoundError:
        print(f"\n[-] الملف غير موجود: {args.wordlist}")
        return

    except PermissionError:
        print(f"\n[-] لا توجد صلاحية لقراءة الملف: {args.wordlist}")
        return

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                    SCAN INFORMATION                         ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    print(f"[*] Host      : {args.host}")
    print(f"[*] Port      : {args.port}")
    print(f"[*] Proxies   : {len(proxies)}")
    print(f"[*] Threads   : {MAX_THREADS}")
    print(f"[*] Timeout   : {TIMEOUT}s")
    print()

    tasks = [
        (proxy, args.host, args.port)
        for proxy in proxies
    ]

    working = []

    print("[*] Starting proxy stability scan...\n")

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=MAX_THREADS
    ) as executor:

        results = executor.map(
            test_proxy_stability,
            tasks
        )

        for result in results:
            if result:
                working.append(result)

    # حفظ النتائج
    with open(
        WORKING_PROXIES_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        for proxy in working:
            f.write(f"{proxy}\n")

    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║                         SCAN DONE                            ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    print(f"[+] Stable proxies : {len(working)}")
    print(f"[+] Saved to       : {WORKING_PROXIES_FILE}")
    print()
    print(f"[+] Telegram Group : {TELEGRAM_GROUP}")
    print(f"[+] Telegram User  : {TELEGRAM_USER}")
    print()


if __name__ == "__main__":
    main()
