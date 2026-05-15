import subprocess
import re
import psutil
import time

BATTLEGROUP_BIN = "/home/dune/.dune/bin/battlegroup"

# Cache dictionary to compute real-time disk and network delta velocities
_metrics_cache = {
    "last_time": time.time(),
    "disk_read": psutil.disk_io_counters().read_bytes if psutil.disk_io_counters() else 0,
    "disk_write": psutil.disk_io_counters().write_bytes if psutil.disk_io_counters() else 0,
    "net_sent": psutil.net_io_counters().bytes_sent,
    "net_recv": psutil.net_io_counters().bytes_recv
}

def get_system_telemetry():
    """Calculates granular host OS infrastructure resource data and transmission velocities."""
    global _metrics_cache
    current_time = time.time()
    time_delta = max(current_time - _metrics_cache["last_time"], 0.1)
    
    # 1. Core Metrics
    cpu_pct = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory()
    
    # 2. Disk Velocity Deltas
    disk_io = psutil.disk_io_counters()
    read_speed = 0.0
    write_speed = 0.0
    if disk_io:
        read_speed = (disk_io.read_bytes - _metrics_cache["disk_read"]) / time_delta / (1024 * 1024)
        write_speed = (disk_io.write_bytes - _metrics_cache["disk_write"]) / time_delta / (1024 * 1024)
        _metrics_cache["disk_read"] = disk_io.read_bytes
        _metrics_cache["disk_write"] = disk_io.write_bytes

    # 3. Network Throughput Deltas
    net_io = psutil.net_io_counters()
    sent_speed = (net_io.bytes_sent - _metrics_cache["net_sent"]) / time_delta / 1024
    recv_speed = (net_io.bytes_recv - _metrics_cache["net_recv"]) / time_delta / 1024
    _metrics_cache["net_sent"] = net_io.bytes_sent
    _metrics_cache["net_recv"] = net_io.bytes_recv
    
    _metrics_cache["last_time"] = current_time

    return {
        "cpu": f"{cpu_pct}%",
        "ram": f"{ram.percent}% ({round(ram.used/(1024**3), 1)}GB / {round(ram.total/(1024**3), 1)}GB)",
        "disk": f"R: {round(read_speed, 1)} MB/s | W: {round(write_speed, 1)} MB/s",
        "network": f"▲ {round(sent_speed, 1)} KB/s | ▼ {round(recv_speed, 1)} KB/s"
    }

def get_connected_player_ips():
    """
    Queries the Linux Kernel connection tracking table directly via sudo to isolate 
    true external player IPs actively sending UDP replication streams.
    """
    connected_ips = []
    try:
        # Query conntrack for all active UDP streams hitting your Dune game server ports
        game_ports = ["7777", "7778", "27015"]
        result = subprocess.run(
            ["sudo", "conntrack", "-L", "-p", "udp"],
            capture_output=True, text=True, check=True
        )
        
        for line in result.stdout.split("\n"):
            # Ensure the packet log is tracking traffic bound for a game port
            if any(f"dport={port}" in line for port in game_ports):
                # Use regex to extract the initial source IP of the packet trail
                match = re.search(r"src=([\d\.]+)", line)
                if match:
                    ip = match.group(1)
                    # Exclude standard local system loops and internal K3s proxy routing noise
                    if ip not in ["127.0.0.1", "0.0.0.0"]:
                        if not (ip.startswith("10.") and ((".42." in ip) or (".244." in ip))):
                            if ip not in connected_ips:
                                connected_ips.append(ip)
    except:
        pass
    return connected_ips

def get_cluster_and_metrics():
    try:
        result = subprocess.run(
            [BATTLEGROUP_BIN, "status"],
            check=True, capture_output=True, text=True
        )
        lines = result.stdout.split("\n")
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to execute battlegroup binary: {str(e)}",
            "zones": {},
            "total_players": "0",
            "max_capacity": "40",
            "cluster_healthy": "Offline",
            "telemetry": {"cpu": "0%", "ram": "0%", "disk": "0 MB/s", "network": "0 KB/s"},
            "player_ips": []
        }

    detected_zones = {}
    total_players = 0
    max_capacity = 40  
    parsing_servers = False
    cluster_healthy = "Unknown State"

    for idx, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        # 1. Capture the Global State (Check first dashed divider boundary safely)
        if "----------" in line and not parsing_servers and cluster_healthy == "Unknown State":
            data_row = lines[idx + 1].strip()
            row_parts = re.split(r'\s+', data_row)
            if row_parts:
                global_status = row_parts[0]  # Healthy, Stopped, or Stopping
                cluster_healthy = f"Cluster {global_status}" if global_status in ["Stopped", "Stopping"] else "Cluster Running" if global_status == "Healthy" else f"Cluster: {global_status}"

        # 2. Trigger individual game server mapping blocks
        if "Map" in line and "Phase" in line and "Players" in line:
            parsing_servers = True
            continue
        
        if parsing_servers and (line.startswith("---") or "No resources found" in line):
            continue

        if parsing_servers:
            parts = re.split(r'\s{2,}', line)
            if len(parts) >= 4:
                map_name = parts[0]      
                phase = parts[1]         
                players_str = parts[3]   
                
                try:
                    players_count = int(players_str)
                    total_players += players_count
                except ValueError:
                    players_count = 0

                detected_zones[map_name] = {
                    "display_name": map_name.replace("_", " Sector "),
                    "status": phase,
                    "players": players_count  
                }

    # 3. Dynamic Live Cluster Cap Check Space
    try:
        cap_query = subprocess.run(
            ["sudo", "kubectl", "get", "battlegroups", "-o", "jsonpath={.items[*].spec.gameServers.maxPlayers}"],
            capture_output=True, text=True
        )
        parsed_cap = cap_query.stdout.strip()
        if parsed_cap and parsed_cap.isdigit():
            max_capacity = int(parsed_cap)
    except:
        pass 

    return {
        "success": True,
        "cluster_healthy": cluster_healthy,
        "zones": detected_zones,
        "total_players": str(total_players),
        "max_capacity": str(max_capacity),
        "telemetry": get_system_telemetry(),
        "player_ips": get_connected_player_ips()
    }

def execute_battlegroup_action(action, map_name=None):
    try:
        if action == "update":
            return subprocess.Popen(
                ["sudo", BATTLEGROUP_BIN, "update"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
        
        # PERSISTENCE INJECTION MECHANICS
        if action == "make-persistent" and map_name:
            cmd = ["sudo", BATTLEGROUP_BIN, "config", "set", f"gameServers.{map_name}.minServers=1"]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return {"success": True, "message": f"Successfully forced persistent background state for {map_name}."}
            
        if action == "make-dynamic" and map_name:
            cmd = ["sudo", BATTLEGROUP_BIN, "config", "set", f"gameServers.{map_name}.minServers=0"]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return {"success": True, "message": f"Successfully restored adaptive hibernation rules for {map_name}."}

        cmd = [BATTLEGROUP_BIN, action, map_name] if map_name else [BATTLEGROUP_BIN, action]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return {"success": True, "message": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": e.stderr or e.stdout}
    except Exception as e:
        return {"success": False, "error": str(e)}
