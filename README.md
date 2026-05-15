# 🏜️ OpenDune-Director

OpenDune-Director is a lightweight, independent, and **100% open-source** web management menu designed specifically for self-hosted *Dune: Awakening* server clusters. 

Unlike restrictive, closed-off, or "source-available" tools that limit community innovation, OpenDune-Director is built entirely from scratch from raw infrastructure fundamentals. It is licensed under the **GNU AGPLv3**, ensuring that this tool—and any future modifications or dashboards built upon it, will remain completely free, collaborative, and open to everyone forever. No splitters allowed.

This is a work in progress, please join the community's discord: https://discord.gg/rgR79rfnRZ

---

## 🚀 Key Features

* **Real-Time Sector Monitoring:** Interacts seamlessly with the official Funcom game cluster binary to visually track the live deployment phase status of individual map instance pods (Overmap, Survival Sectors, Hub Cities, Dungeons, etc.).
* **Network Peer Interceptor Radar:** Implements a direct connection tracking bypass that reads the Linux Kernel's packet tables to grab true, raw player IP footprints over connectionless UDP game streams—bypassing internal Kubernetes proxy masking.
* **Live Streaming Update Terminal:** Converts your backend programmatic maintenance update requests into an asynchronous live log stream, giving administrators full visual insight into the background process as it safely stops deployments, updates game source files, and cycles clusters back online.
* **Sleek OS Hardware Telemetry Strip:** Displays a real-time tracking bar running across your dashboard infrastructure that monitors your physical host VM's CPU usage, RAM allocation parameters, live Disk I/O read/write velocities, and network gateway bandwidth metrics.
* **Visual Gameplay Toggle Manager:** A clean web menu to safely read and write global mechanics variables (such as forcing PvP overrides, security trading zones, or auto-spawning Coriolis storms) directly to your system's localized `.ini` files.

---

## 🛠️ Architecture & Independence (Clean-Room Design)

This project was built using a **Clean-Room Design** method. It contains absolutely zero code, structure, or assets from third-party proprietary utilities. It interfaces natively with:
1. **The Funcom Cluster Binary:** Intercepts localized console outputs via programmatic background subsystem loops.
2. **The Netfilter Firewall Framework:** Queries the local Linux kernel network tracking memory space directly to capture client socket connections.
3. **The Kubernetes CRD State Controllers:** Interrogates your custom resource sheets via background API parameters to fetch true player cap thresholds dynamically.

---

## ⚠️ Prerequisites

To deploy this web menu, your infrastructure must meet the following criteria:
* A self-hosted *Dune: Awakening* server deployed on a Linux base (Ubuntu 22.04 / 24.04 LTS preferred).
* An active `k3s` / Kubernetes game cluster managed via the official `battlegroup` management binary located at `/home/dune/.dune/bin/battlegroup`.
* Administrative (`sudo`) accessibility to configure security privilege rules.

---

## 📦 Installation & Setup

### Step 1: Install System OS Dependencies
Before configuring the application workspace, install the required network state tracking utilities on your Ubuntu host environment:
```bash
sudo apt update && sudo apt install conntrack -y
```
Step 2: Clone the Project Workspace
Ensure your files match the strict directory layout under your dune system home path:

```Bash
git clone [https://github.com/comfuzio/OpenDune-Director.git](https://github.com/comfuzio/OpenDune-Director.git)
cd OpenDune-Director
```
Step 3: Install Framework Packages
Install the lightweight application tracking layers. We pass the break parameter to safely step through modern Ubuntu managed environment environment blocks:

```Bash
pip install -r requirements.txt --break-system-packages
```
Step 4: Overhaul Game File Permissions
Grant the dune system profile explicit read and write properties over the global server gameplay configuration script sheets:

```Bash
sudo chown dune:dune /home/dune/.dune/download/scripts/setup/config/UserGame.ini
sudo chmod 664 /home/dune/.dune/download/scripts/setup/config/UserGame.ini
```
Step 5: Configure Elevated Passwordless Sudo Bypass Policies
Because the dashboard executes programmatic maintenance tasks (like stopping clusters, monitoring raw packet layers, and running update routines), you must authorize the dune user to run these specific binaries without a password challenge.

Open a dedicated configuration file inside the system's security configuration directory:

```Bash
sudo visudo -f /etc/sudoers.d/dune-battlegroup
```
Paste this explicit allowed paths block into the editor, then save and exit:

```Plaintext
dune ALL=(ALL) NOPASSWD: /home/dune/.dune/bin/battlegroup, /usr/sbin/conntrack, /usr/local/bin/kubectl
```
⚙️ Running as a Permanent Background Daemon
To ensure your web manager stays active 24/7—even if you exit your SSH connection workspace or your host reboots—register it natively with the Ubuntu service manager.

1. Create the systemd service file:
```Bash
sudo nano /etc/systemd/system/dune-director.service
```
2. Populate the configuration manifest:
```Ini, TOML
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
```Bash
# Force the service controller to index your new configuration file
sudo systemctl daemon-reload
```
# Enable automatic engine startup during server boot events
```sudo systemctl enable dune-director.service```

# Spin up the application tracking worker immediately
```sudo systemctl start dune-director.service```

# Check on runtime health logs to verify success
```sudo systemctl status dune-director.service```
🌐 Accessing the Dashboard UI: Access your live management dashboard panel from any local computer network node by pointing your web browser to http://<YOUR_SERVER_VM_IP>:8080

✅ Final Notes
Parts of this project ecosystem layout and engine loop orchestration architecture have been meticulously polished alongside AI (Gemini).

Happy management. 🏜️
