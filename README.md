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
<img width="1430" height="477" alt="Captura de pantalla 2026-06-12 014740" src="https://github.com/user-attachments/assets/f6c8ac64-036c-4c7a-bd86-25994e408faf" />

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
<img width="627" height="477" alt="Captura de pantalla 2026-06-12 001721" src="https://github.com/user-attachments/assets/eb7737fa-9afe-423a-a1d9-d73c532771ad" />

## 🔍 Resultado — nslookup en la víctima antes del ataque
<img width="310" height="216" alt="Captura de pantalla 2026-06-12 000007" src="https://github.com/user-attachments/assets/4437e569-c1a9-489a-be67-646d9c9e1bd4" />

## 🔍 Captura de tramas — Spoofing
<img width="845" height="822" alt="Captura de pantalla 2026-06-12 014859" src="https://github.com/user-attachments/assets/1f157d77-887a-4770-aa43-c83d57ed785f" />

## 🔍 Resultado — nslookup en la víctima después del ataque
<img width="456" height="148" alt="Captura de pantalla 2026-06-12 015628" src="https://github.com/user-attachments/assets/553e3325-c2cf-4067-89cd-b9d5bd8be47c" />

## 🔍 Resultado — Página falsa en navegador
<img width="1710" height="920" alt="ChatGPT Image 12 jun 2026, 01_48_00" src="https://github.com/user-attachments/assets/9d666c2d-70a0-47ef-8bab-436125f9c6d5" />

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

> ⚠️ Solo para uso en laboratorio controlado.
