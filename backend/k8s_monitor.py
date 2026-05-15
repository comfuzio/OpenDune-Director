import subprocess
import re

BATTLEGROUP_BIN = "/home/dune/.dune/bin/battlegroup"

def get_cluster_and_metrics():
    """
    Executes the official Funcom battlegroup binary, dynamically grabs the true
    global state (Healthy, Stopped, etc.), and collects player limits.
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
    max_capacity = 40  
    parsing_servers = False
    
    # Default fallback state
    cluster_healthy = "Unknown State"

    # Step 1: Scan explicitly for the Global Battlegroup Status Row
    for idx, line in enumerate(lines):
        line = line.strip()
        if "----------" in line and idx > 0:
            # The actual data values sit directly underneath the dashed line column headers
            data_row = lines[idx + 1].strip()
            row_parts = re.split(r'\s+', data_row)
            if row_parts:
                global_status = row_parts[0] # Grabs 'Healthy', 'Stopped', or 'Stopping'
                if global_status == "Healthy":
                    cluster_healthy = "Cluster Running"
                elif global_status == "Stopped":
                    cluster_healthy = "Cluster Stopped"
                elif global_status == "Stopping":
                    cluster_healthy = "Cluster Stopping"
                else:
                    cluster_healthy = f"Cluster: {global_status}"
            break

    # Step 2: Parse individual map instance states
    for line in lines:
        line = line.strip()
        if not line:
            continue

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

                display_name = map_name.replace("_", " Sector ")
                
                detected_zones[map_name] = {
                    "display_name": display_name,
                    "status": phase,
                    "players": players_count  
                }

    # Step 3: Extract True Cap Space
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
