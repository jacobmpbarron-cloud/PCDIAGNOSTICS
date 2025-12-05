import os
import platform
import psutil
import socket
import subprocess
import threading
import time
import json
import re
from datetime import datetime


class MegaDiagnosticTool:

    def __init__(self):
        self.report = {
            "system_info": {},
            "network_info": {},
            "internet": {},
            "ping": {},
            "ports": {},
            "banners": {},
            "disk": {},
            "processes": {},
            "network_usage": {},
            "files_open": {},
            "logs": {},
        }

    # the system information on hardware

    def system_info(self):
        print("\n=== SYSTEM INFORMATION ===")
        os_name = f"{platform.system()}{platform.release()}"
        cpu_count = psutil.cpu_count()
        cpu_usage = psutil.cpu_percent()
        ram = psutil.virtual_memory()
        uptime_sec = time.time() - psutil.boot_time()
        uptime_hr = round(uptime_sec / 3600, 2)

        self.report["system_info"] = {
            "os": os_name,
            "cpu_count": cpu_count,
            "cpu_usage_percent": cpu_usage,
            "ram_percent": ram.percent,
            "ram_total_gb": round(ram.total / (1024 ** 3), 2),
            "uptime_hours": uptime_hr
        }

        print(self.report["system_info"])

    # network information portion

    def network_info(self):
        print("\n=== NETWORK INFORMATION ===")
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        interfaces = list(psutil.net_if_addrs().keys())

        dns_servers = []
        try:
            with open('/etc/resolv.conf', 'r') as f:
                for line in f:
                    if "nameserver" in line:
                        dns_servers.append(line.split()[1])
        except:
            dns_servers = ["unavailable"]

        self.report["network_info"] = {
            "hostname": hostname,
            "local_ip": local_ip,
            "interfaces": interfaces,
            "dns_servers": dns_servers
        }

        print(self.report["network_info"])

        # Big internet Check

    def internet_check(self):
        print("\n=== INTERNET CONNECTION ===")
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            status = "Connected"
        except:
            status = "Not Connected"

        self.report["internet"]["status"] = status
        print("Internet", status)

    # Ping Test
    def ping_test(self, host="google.com"):
        print(f"\n=== PING TEST ({host}) ===")
        param = "-n" if platform.system().lower() == "windows" else "-c"

        process = subprocess.Popen(
            ["ping", param, "4", host],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )

        out, err = process.communicate()
        output = out.decode()
        self.report["ping"] = {"output": output}

        print(output)

        # Port scanning

    def port_scan(self, ip="127.0.0.1", ports=range(1, 1024)):
        print("\n=== PORT SCAN ===")
        open_ports = {}

        def scan(port):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.3)
            try:
                if sock.connect_ex((ip, port)) == 0:
                    open_ports[port] = "open"
                    print(f"[OPEN] port {port}")
            except:
                pass
            sock.close()

        threads = []
        for p in ports:
            t = threading.Thread(target=scan, args=(p,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        self.report["ports"] = open_ports

        # Banner grabbing event

    def banner_grab(self, ip="127.0.0.1", ports=[22, 80, 443]):
        print("\n=== BANNER GRABBING ===")
        banners = {}

        for port in ports:
            try:
                s = socket.socket()
                s.setimeout(1)
                s.connect((ip, port))
                s.send(b"HEAD / HTTP/1.0\r\n\r\n")
                banner = s.recv(1024).decode(erros="ignore")
                banners[port] = banner
                print(f"[{port}] {banner[:80]}...")
                s.close()
            except:
                continue

        self.report["banners"] = banners

        # DISK INFORMATION

    def disk_info(self):
        print("\n=== DISK USAGE ===")
        disk = psutil.disk_usage('/')
        data = {
            "total_gb": disk.total // (1024 ** 3),
            "used_gb": disk.used // (1024 ** 3),
            "free_gb": disk.free // (1024 ** 3)
        }
        self.report["disk"] = data
        print(data)

        # TOP PROCESSES

    def top_processes(self, limit=15):
        print("\n=== TOP PROCESSES ===")
        procs = []

        for p in psutil.process_iter(["name", "cpu_percent", "memory_percent"]):
            try:
                procs.append(p.info)
            except:
                pass

        top = sorted(procs, key=lambda x: x["cpu_percent"], reverse=True)[:limit]
        self.report["processes"] = top

        for p in top:
            print(p)

    # Network usage
    def network_usage(self):
        print("\n=== NETWORK USAGE ===")
        counters = psutil.net_io_counters()
        usage = {
            "bytes_sent": round(counters.bytes_sent / 1_000_000, 3),
            "bytes_recv": round(counters.bytes_recv / 1_000_000, 3)
        }
        self.report["network_usage"] = usage
        print(usage)

        # OPEN FILES

    def list_open_files(self):
        print("\n=== OPEN FILES ===")
        files = []
        for p in psutil.process_iter(["name", "pid"]):
            try:
                for f in p.open_files():
                    files.append({"process": p.info["name"], "file": f.path})
                    if len(files) >= limit:
                        break
            except:
                pass

        self.report["files"] = files
        for f in files:
            print(f)

    # system logs
    def system_logs(self):
        print("\n=== SYSTEM LOGS ===")
        logs = []
        log_path = "/var/log/syslog"

        if os.path.exists(log_path):
            with open(log_path) as f:
                logs = [line.strip() for line in f.readlines()[-20:]]
        else:
            logs = ["Logs Unavailable"]

        self.report["logs"] = logs

        for l in logs:
            print(l)

            # Save the report

    def save_report(self):
        print("\n=== SAVING REPORT ===")
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        with open(f"report_{timestamp}.json", "w") as f:
            json.dump(self.report, f, indent=4)

        with open(f"report_{timestamp}.txt", "w") as f:
            for section, data in self.report.items():
                f.write(f"\n====== {section.upper()} ======\n")
                f.write(json.dumps(data, indent=4))

        print("saved as JSON and TXT")

        # Main EXECUTION


def main():
    tool = MegaDiagnosticTool()

    tool.system_info()
    tool.network_info()
    tool.internet_check()
    tool.ping_test()
    tool.disk_info()
    tool.network_usage()
    tool.port_scan()
    tool.banner_grab()
    tool.top_processes()
    tool.list_open_files()
    tool.system_logs()

    tool.save_report()


if __name__ == "__main__":
    main()
