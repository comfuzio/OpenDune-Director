import subprocess
import re

BATTLEGROUP_BIN = "/home/dune/.dune/bin/battlegroup"

def get_cluster_and_metrics():
    """
    Executes the official Funcom battlegroup binary, detects runtime statuses,
    maps active server cells dynamically, and collects player metrics.
    """
    try:
        # Run the official status command directly
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
            "total_players": "-- / --",
            "cluster_healthy": "Offline"
        }

    detected_zones = {}
    total_players = 0
    parsing_servers = False
    cluster_healthy = "Error"

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 1. Parse Global Cluster Health States
        if "Healthy" in line or "Ready" in line:
            if "Database" not in line and "Phase" not in line:
                cluster_healthy = "Cluster Online (K3s)"

        # 2. Identify the Game Servers Data Block
        if "Map" in line and "Phase" in line and "Players" in line:
            parsing_servers = True
            continue
        
        # Skip decorative layout dividers
        if parsing_servers and line.startswith("---"):
            continue

        # 3. Dynamically Parse Map Instances, Phases, and Player Counts
        if parsing_servers:
            # Split lines cleanly by multiple spaces
            parts = re.split(r'\s{2,}', line)
            if len(parts) >= 4:
                map_name = parts[0]      # e.g., Overmap, Survival_1
                phase = parts[1]         # e.g., Running, ContainerCreating
                players_str = parts[3]   # e.g., 0, 5
                
                try:
                    players_count = int(players_str)
                    total_players += players_count
                except ValueError:
                    players_count = 0

                # Clean up display text beautifully
                display_name = map_name.replace("_", " Sector ")
                
                detected_zones[map_name] = {
                    "display_name": display_name,
                    "status": phase
                }

    return {
        "success": True,
        "cluster_healthy": cluster_healthy,
        "zones": detected_zones,
        "total_players": f"{total_players} / 100"
    }

def execute_battlegroup_action(action, map_name="Survival_1"):
    """
    Executes native commands: start, stop, restart, update.
    Forces 'sudo' strictly for the update sequence.
    """
    try:
        if action == "update":
            # Update requires sudo privilege execution
            cmd = ["sudo", BATTLEGROUP_BIN, "update"]
        else:
            # start, stop, restart run normally or via sudo if cluster permissions require it
            cmd = [BATTLEGROUP_BIN, action, map_name]
            
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return {"success": True, "message": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": e.stderr or e.stdout}
    except Exception as e:
        return {"success": False, "error": str(e)}
