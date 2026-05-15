# 🏜️ OpenDune-Director

OpenDune-Director is a lightweight, independent, and **100% open-source** web management menu designed specifically for self-hosted *Dune: Awakening* server clusters. 

Unlike restrictive, closed-off, or "source-available" tools that limit community innovation, OpenSietch is built entirely from scratch from raw infrastructure fundamentals. It is licensed under the **GNU AGPLv3**, ensuring that this tool—and any future modifications or dashboards built upon it—will remain completely free, collaborative, and open to everyone forever. No splitters allowed.

This is work in progress, please join the community's discord: https://discord.gg/rgR79rfnRZ

---

## 🚀 Key Features

* **Real-Time Zone Monitoring:** Queries your internal K3s cluster (`kubectl`) directly to track the live status of all active server map pods (Hagga Basin, Deep Desert, Arrakeen, etc.).
* **Instant Player Metrics:** Uses the native Valve A2S_INFO UDP query protocol to fetch accurate player counts, server names, and active map details instantly—without parsing massive log files.
* **Visual Config Manager:** A simple, clean web menu to safely read and write server variables (like Sietch Names, Passwords, or Hibernation settings) directly to your system's `.ini` files.
* **Resource Optimization:** Easily toggle massive zones like the Deep Desert between "Hot" (always running) and "Dynamic Scaling" based on your hardware's RAM constraints.

---

## 🛠️ Architecture & Independence (Clean-Room Design)

This project was built using a **Clean-Room Design** method. It contains absolutely zero code, structure, or assets from third-party proprietary utilities. It interfaces natively with:
1. **The Kubernetes API:** Communicates directly with the local `k3s` master node to check pod health.
2. **The Unreal Engine 5 Network Layer:** Queries the native game server query ports (`UDP 27015 / 7777` range).
3. **Standard Linux Filesystem:** Safely manages localized text configuration blocks under `/home/dune/.dune/`.

---

## ⚠️ Prerequisites

To deploy this web menu, your infrastructure must meet the following criteria:
* A self-hosted *Dune: Awakening* server deployed on a Linux base (Ubuntu 24.04/26.04 preferred).
* Active `k3s` / Kubernetes cluster privileges.
* Basic familiarity with the Linux command line and network port management.

---

## 📦 Installation & Setup

*(Stay tuned! Provide step-by-step instructions here for how users will clone your repository, run the lightweight web app node/script, and open it in their browser via `http://<YOUR_VM_IP>:port`)*

```bash
git clone [https://github.com/comfuzio/OpenDune-Director.git](https://github.com/comfuzio/OpenDune-Director.git)
cd OpenDune-Director
```
# Detail your startup/service commands here

# ✅ Final Notes

Parts of this guide have been written by AI (gemini), mostly the visual parts and the details of the guide. Most of the work is based on template I am working to import .vhdx .qcow2 and other formats to my proxmox hosts.

Happy management. 🏜️
