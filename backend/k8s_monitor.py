import subprocess
import re

BATTLEGROUP_BIN = "/home/dune/.dune/bin/battlegroup"

def get_cluster_and_metrics():
    """
    Executes the official Funcom battlegroup binary, detects runtime statuses,
    maps active server cells dynamically, collects player metrics, and extracts true caps.
    """
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
    max_capacity = 40  # Reliable fallback cap value matching standard private guidelines
    parsing_servers = False
    cluster_healthy = "Error"

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if "Healthy" in line or "Ready" in line:
            if "Database" not in line and "Phase" not in line:
                cluster_healthy = "Cluster Online (K3s)"

        if "Map" in line and "Phase" in line and "Players" in line:
            parsing_servers = True
            continue
        
        if parsing_servers and line.startswith("---"):
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

                display_name = map_name.replace("_", " Sector ")
                
                detected_zones[map_name] = {
                    "display_name": display_name,
                    "status": phase,
                    "players": players_count  
                }

    # DYNAMIC SEARCH: Query kubectl for the true custom cap defined inside your active cluster
    try:
        cap_query = subprocess.run(
            ["sudo", "kubectl", "get", "battlegroups", "-o", "jsonpath={.items[*].spec.gameServers.maxPlayers}"],
            capture_output=True, text=True
        )
        parsed_cap = cap_query.stdout.strip()
        if parsed_cap and parsed_cap.isdigit():
            max_capacity = int(parsed_cap)
    except:
        pass # Fall back calmly to 40 if the custom resource definition layer is hidden

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
            cmd = ["sudo", BATTLEGROUP_BIN, "update"]
        elif map_name:
            cmd = [BATTLEGROUP_BIN, action, map_name]
        else:
            cmd = [BATTLEGROUP_BIN, action]
            
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return {"success": True, "message": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": e.stderr or e.stdout}
    except Exception as e:
        return {"success": False, "error": str(e)}
