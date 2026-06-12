# DNS Spoofing + ARP Poisoning — itla.edu.do
**Estudiante:** Enmanuel Feliz Soto | **Matrícula:** 20251402
**Institución:** ITLA | **Curso:** Seguridad en Redes | **Práctica:** P2

## 📹 Video Demostración
🔗 [Ver en YouTube — DNS Spoofing](https://youtu.be/NbU1oIHrnOo)
🔗 [Playlist completa](https://www.youtube.com/playlist?list=PLn9wGcsdOtleB6unDjCUvq4LdJYgd4TTj)

## 🎯 Objetivo del Laboratorio
Demostrar DNS Spoofing/Poisoning haciendo que el dominio `itla.edu.do` resuelva a un servidor web controlado por el atacante, mediante ARP Poisoning como vector de intercepción.

## 🎯 Objetivo del Script
1. Envenenar ARP entre víctima y DNS server para interceptar consultas
2. Responder consultas DNS para `itla.edu.do` con IP del atacante
3. Servir página web falsa de ITLA al cliente engañado

## ⚙️ Requisitos
```bash
pip install scapy
sudo python3 EnmanuelFelizSoto_20251402_DNS_Spoofing_P2.py
```
- Python 3.x / Scapy 2.5+ / Root/sudo
- IP forwarding activo (el script lo habilita automáticamente)

## 🔥 Reglas iptables necesarias
Para que el ataque funcione correctamente cuando el DNS server
está en la misma subred que la víctima, se deben aplicar estas
reglas en el atacante **antes** de lanzar el script:

```bash
# Limpiar reglas previas
sudo iptables -F
sudo iptables -t nat -F

# Bloquear todo DNS forward (impide que llegue al DNS real)
sudo iptables -A FORWARD -p udp --dport 53 -j DROP
sudo iptables -A FORWARD -p tcp --dport 53 -j DROP

# Bloquear DNS saliente hacia cualquier server que no sea el atacante
sudo iptables -A OUTPUT -p udp --dport 53 ! -d <TU_IP_ATACANTE> -j DROP
sudo iptables -A OUTPUT -p tcp --dport 53 ! -d <TU_IP_ATACANTE> -j DROP

# Habilitar IP forwarding permanente
echo 1 > /proc/sys/net/ipv4/ip_forward
```

> Reemplaza `<TU_IP_ATACANTE>` con tu IP real (ej. `14.2.0.13`)

## 📋 Parámetros (interactivos al ejecutar)
| Campo | Descripción | Ejemplo lab |
|-------|-------------|-------------|
| Interfaz | Interfaz de red | `eth1` |
| IP víctima | Host a engañar | `14.2.0.12` |
| IP gateway/DNS | DNS server a interceptar | `14.2.0.11` |
| Tu IP (fake) | IP que recibirá la víctima | `14.2.0.13` |
| Dominio | Dominio a spoofear | `itla.edu.do` |
| Puerto web | Puerto del servidor HTTP | `80` |

## 🔧 Uso
```bash
# 1. Aplicar reglas iptables (ver sección arriba)
# 2. Lanzar el script
sudo python3 EnmanuelFelizSoto_20251402_DNS_Spoofing_P2.py
# 3. Seleccionar opción 4 (Ataque completo)
```

## 🗺️ Topología de Red
| Dispositivo | Rol | IP | VLAN |
|-------------|-----|----|------|
| R1-CORE | Router Core / GW | 14.2.0.1 | — |
| DNS Server | Servidor DNS legítimo | 14.2.0.11/25 | VLAN10 |
| Docker atacante | ARP+DNS spoofer | 14.2.0.13/25 | VLAN10 |
| Docker víctima | Host objetivo | 14.2.0.12/25 | VLAN10 |

**Nota topología:** Para que el ARP Poisoning intercepte el tráfico DNS,
el DNS server debe estar en una VLAN/subred diferente a la víctima,
o bien hacer ARP Poisoning directamente contra el DNS server.

## 🔍 Funcionamiento
```
Víctima (.12)
    │ consulta DNS itla.edu.do
    ▼
Atacante (.13)  ← ARP Poisoning hace que .12 crea que .13 es el GW/DNS
    │ intercepta query UDP port 53
    │ responde con DNSRR: itla.edu.do → 14.2.0.13 (TTL 300)
    ▼
Víctima recibe IP falsa → abre navegador → carga página del atacante
```

## 🛡️ Contramedida
```
! En el switch — Dynamic ARP Inspection
SW(config)# ip dhcp snooping
SW(config)# ip dhcp snooping vlan 10
SW(config)# ip arp inspection vlan 10
SW(config-if)# ip arp inspection trust   ← solo uplinks

! En los clientes — DNSSEC
! Configurar resolvers con soporte DNSSEC: 1.1.1.1, 8.8.8.8

! DNS sobre TLS/HTTPS
! Usar DNS-over-HTTPS (DoH) o DNS-over-TLS (DoT)

! HSTS en el servidor web
! Strict-Transport-Security para prevenir downgrade HTTP
```

## 📁 Estructura
```
├── EnmanuelFelizSoto_20251402_DNS_Spoofing_P2.py
├── EnmanuelFelizSoto_20251402_Informe_P2.pdf
├── screenshots/
└── README.md
```

> ⚠️ Solo para uso en laboratorio controlado con contrato de ética firmado.
