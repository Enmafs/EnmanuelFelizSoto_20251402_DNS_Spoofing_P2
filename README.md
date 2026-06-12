# DNS Spoofing + ARP Poisoning — itla.edu.do
**Estudiante:** Enmanuel Feliz Soto | **Matrícula:** 20251402
**Institución:** ITLA | **Curso:** Seguridad en Redes | **Práctica:** P2

## 📹 Video Demostración
🔗 [▶ DNS Spoofing + Poisoning — Ver en YouTube](https://youtu.be/NbU1oIHrnOo)
🔗 [Playlist completa NetSec](https://www.youtube.com/playlist?list=PLn9wGcsdOtleB6unDjCUvq4LdJYgd4TTj)

## 🎯 Objetivo del Laboratorio
Demostrar DNS Spoofing/Poisoning haciendo que `itla.edu.do` resuelva a un servidor web del atacante, mediante ARP Poisoning como vector de intercepción.

## 🎯 Objetivo del Script
1. Envenenar ARP entre víctima y DNS server para interceptar consultas
2. Responder queries DNS para `itla.edu.do` con IP del atacante
3. Servir página web falsa de ITLA al cliente engañado

## 🗺️ Topología
![Topología](https://raw.githubusercontent.com/Enmafs/EnmanuelFelizSoto_20251402_DNS_Spoofing_P2/main/topologia.png)

| Dispositivo | Rol | IP | VLAN |
|-------------|-----|----|------|
| R1-CORE | Router / GW | 14.2.0.1 | — |
| DNS Server | DNS legítimo | 14.2.0.11/25 | VLAN10 |
| Docker atacante | ARP+DNS spoofer | 14.2.0.13/25 | VLAN10 |
| Docker víctima | Objetivo | 14.2.0.12/25 | VLAN10 |

**Entorno:** PNetLab — Cisco IOL + Docker | **Base IP:** Matrícula 20251402 → 14.2.0.0

## 🔥 Reglas iptables (requeridas antes de lanzar el script)
```bash
sudo iptables -F && sudo iptables -t nat -F
sudo iptables -A FORWARD -p udp --dport 53 -j DROP
sudo iptables -A FORWARD -p tcp --dport 53 -j DROP
sudo iptables -A OUTPUT  -p udp --dport 53 ! -d 14.2.0.13 -j DROP
sudo iptables -A OUTPUT  -p tcp --dport 53 ! -d 14.2.0.13 -j DROP
echo 1 > /proc/sys/net/ipv4/ip_forward
```

## ⚙️ Requisitos
```bash
pip install scapy
sudo python3 EnmanuelFelizSoto_20251402_DNS_Spoofing_P2.py
```

## 📋 Parámetros (interactivos)
| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| Interfaz | Interfaz de red | `eth1` |
| IP víctima | Host a engañar | `14.2.0.12` |
| IP gateway/DNS | DNS a interceptar | `14.2.0.11` |
| Tu IP | IP falsa para la víctima | `14.2.0.13` |
| Dominio | Dominio a spoofear | `itla.edu.do` |
| Puerto web | Servidor HTTP local | `80` |

## 🔧 Uso
```bash
# 1. Aplicar reglas iptables (arriba)
# 2. Ejecutar
sudo python3 EnmanuelFelizSoto_20251402_DNS_Spoofing_P2.py
# 3. Seleccionar opción 4 — Ataque completo
```

## 🔍 Demostración — Script activo
![Terminal del ataque](https://raw.githubusercontent.com/Enmafs/EnmanuelFelizSoto_20251402_DNS_Spoofing_P2/main/dns_terminal.png)

## 🔍 Resultado — nslookup en la víctima
![nslookup resultado](https://raw.githubusercontent.com/Enmafs/EnmanuelFelizSoto_20251402_DNS_Spoofing_P2/main/dns_nslookup.png)

## 🔍 Resultado — Página falsa en navegador
![Página web falsa](https://raw.githubusercontent.com/Enmafs/EnmanuelFelizSoto_20251402_DNS_Spoofing_P2/main/dns_browser.png)

## 🔍 Flujo del ataque
```
Víctima (.12)
    │ consulta DNS itla.edu.do
    ▼
Atacante (.13)  ← ARP Poisoning: .12 cree que .13 es el DNS
    │ intercepta query UDP port 53
    │ responde: itla.edu.do → 14.2.0.13 (TTL 300)
    ▼
Víctima abre navegador → carga página del atacante
```

## 🛡️ Contramedida
```
SW(config)# ip dhcp snooping
SW(config)# ip arp inspection vlan 10
SW(config-if)# ip arp inspection trust
! DNSSEC en resolvers
! DNS-over-HTTPS / DNS-over-TLS
! HSTS en servidor web
```

> ⚠️ Solo para uso en laboratorio controlado con contrato de ética firmado.
