# 🏜️ OpenDune-Director

OpenDune-Director is a lightweight, independent, and **100% open-source** web management menu designed specifically for self-hosted *Dune: Awakening* server clusters. 

Unlike restrictive, closed-off, or "source-available" tools that limit community innovation, OpenDune-Director is built entirely from scratch from raw infrastructure fundamentals. It is licensed under the **GNU AGPLv3**, ensuring that this tool — and any future modifications or dashboards built upon it, will remain completely free, collaborative, and open to everyone forever. No splitters allowed.

**Acknowledgments:** This project proudly incorporates map rendering architecture and database concepts originally pioneered by the [Easy-Dune-Admin](https://github.com/valknight/Easy-Dune-Admin) project. By merging their dependency-free frontend map canvas and SQL manipulation logic with our lightweight FastAPI backend, we deliver a powerful, unified command center.

This is a work in progress, please join the community's discord: https://discord.gg/rgR79rfnRZ

---

## 🚀 Key Features

* **Dual-Dashboard System (Public vs. Admin):** Serve a safe, read-only Public page (`/`) for your community showing live server stats, population limits, and a minimal map showing discovered base locations. Keep your high-level controls, player tracking, and vehicle radar strictly hidden on the secure `/admin` route.
* **Interactive Live Map & Radar:** A completely dependency-free HTML5 map canvas that tracks live coordinates for players, vehicles, and bases across both Hagga Basin and the Deep Desert.
* **Database Teleportation & Over-repair:** Instantly relocate offline players or fetch and teleport stuck vehicles across map partitions. Inject custom structural durability stats directly into character inventories using the Over-repair module.
* **Real-Time Sector Monitoring:** Interacts seamlessly with the official Funcom game cluster binary to visually track the live deployment phase status of individual map instance pods.
* **Network Peer Interceptor Radar:** Implements a direct connection tracking bypass that reads the Linux Kernel's packet tables to grab true, raw player IP footprints over connectionless UDP game streams.
* **Live Streaming Update Terminal:** Converts your backend programmatic maintenance update requests into an asynchronous live log stream.
* **Sleek OS Hardware Telemetry Strip:** Displays a real-time tracking bar that monitors your physical host VM's CPU usage, RAM allocation, live Disk I/O, and network gateway bandwidth.

---

## 🛠️ Architecture & Independence (Clean-Room Design)

This project was built using a **Clean-Room Design** method. It interfaces natively with:
1. **The Funcom Cluster Binary:** Intercepts localized console outputs via programmatic background loops.
2. **The Netfilter Firewall Framework:** Queries the local Linux kernel network tracking memory space directly to capture client socket connections.
3. **The Kubernetes CRD State Controllers:** Interrogates your custom resource sheets to fetch true player cap thresholds dynamically.
4. **The PostgreSQL Database:** Executes direct SQL manipulation sequences to move actors and inject item durability arrays via background `psql` channels.

---

## ⚠️ Prerequisites

To deploy this web menu, your infrastructure must meet the following criteria:
* A self-hosted *Dune: Awakening* server deployed on a Linux base (Ubuntu 24.04 / 26.04 LTS preferred).
* An active `k3s` / Kubernetes game cluster managed via the official `battlegroup` binary located at `/home/dune/.dune/bin/battlegroup`.
* Administrative (`sudo`) accessibility to configure security privilege rules.
* Map image files (`arrakis_hb.webp` and `deep_desert.webp`) placed inside the `/frontend/static/` directory.

---

## 📦 Installation & Setup

### Step 1: Install System OS Dependencies
Before configuring the application workspace, install the required network state tracking utilities on your Ubuntu host environment:
```bash
sudo apt install python3-pip conntrack -y
```
### Step 2: Clone the Project Workspace
Ensure your files match the strict directory layout under your dune system home path:
```
git clone https://github.com/comfuzio/OpenDune-Director.git
cd OpenDune-Director
```
### Step 3: Install Framework Packages
Install the lightweight application tracking layers. We pass the break parameter to safely step through modern Ubuntu managed environment blocks:

```
pip install -r requirements.txt --break-system-packages
```
### Step 4: Overhaul Game File Permissions
Grant the dune system profile explicit read and write properties over the global server gameplay configuration script sheets:

```
sudo chown dune:dune /home/dune/.dune/download/scripts/setup/config/UserGame.ini
sudo chmod 664 /home/dune/.dune/download/scripts/setup/config/UserGame.ini
```

### Step 5: Configure Elevated Passwordless Sudo Bypass Policies
Because the dashboard executes programmatic maintenance tasks (like stopping clusters, monitoring raw packet layers, and running background database psql commands), you must authorize the dune user to run these specific binaries without a password challenge.

Open a dedicated configuration file inside the system's security configuration directory:

```
sudo visudo -f /etc/sudoers.d/dune-battlegroup
```
Paste this explicit allowed paths block into the editor, then save and exit:
```
dune ALL=(ALL) NOPASSWD: /home/dune/.dune/bin/battlegroup, /usr/sbin/conntrack, /usr/local/bin/kubectl, /usr/bin/psql
```
⚙️ Running as a Permanent Background Daemon
To ensure your web manager stays active 24/7—even if you exit your SSH connection workspace or your host reboots—register it natively with the Ubuntu service manager.

1. Create the systemd service file:

```
sudo nano /etc/systemd/system/dune-director.service
```
2. Populate the configuration manifest:
```
[Unit]
Description=OpenDune-Director Shadows Dashboard Service
After=network.target

[Service]
User=dune
WorkingDirectory=/home/dune/OpenDune-Director
ExecStart=/usr/bin/python3 backend/main.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```
3. Ignite the service engine:
```
sudo systemctl daemon-reload
sudo systemctl enable dune-director.service
sudo systemctl start dune-director.service
sudo systemctl status dune-director.service
```
🌐 Accessing the Dashboard UI
Access your live management dashboard panels from any local computer network node by pointing your web browser to:

Public Dashboard: http://<YOUR_SERVER_VM_IP>:8080/

Admin Command Center: http://<YOUR_SERVER_VM_IP>:8080/admin

✅ Final Notes
Parts of this project ecosystem layout and engine loop orchestration architecture have been meticulously polished alongside AI (Gemini).

Happy management. 🏜️
