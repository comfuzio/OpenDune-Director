import subprocess
import re

BATTLEGROUP_BIN = "/home/dune/.dune/bin/battlegroup"

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
            "cluster_healthy": "Offline"
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
        "max_capacity": str(max_capacity)
    }

def execute_battlegroup_action(action, map_name=None):
    try:
        if action == "update":
            return subprocess.Popen(
                ["sudo", BATTLEGROUP_BIN, "update"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
        
        cmd = [BATTLEGROUP_BIN, action, map_name] if map_name else [BATTLEGROUP_BIN, action]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return {"success": True, "message": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": e.stderr or e.stdout}
    except Exception as e:
        return {"success": False, "error": str(e)}
