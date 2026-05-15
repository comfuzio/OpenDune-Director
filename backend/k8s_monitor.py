import subprocess
import json

def get_zone_status():
    """
    Queries the local K3s cluster for game server pods.
    Returns a clean dictionary of statuses for the frontend.
    """
    try:
        # Run the standard kubectl command to get pods in JSON format
        # Adjust '-n default' if Funcom uses a specific namespace (e.g., -n dune)
        result = subprocess.run(
            ["sudo", "kubectl", "get", "pods", "-n", "default", "-o", "json"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse the JSON payload from Kubernetes
        pod_data = json.loads(result.stdout)
        zones = {}

        for pod in pod_data.get("items", []):
            pod_name = pod["metadata"]["name"]
            
            # Filter for Funcom battlegroup server pods
            if "seabass-server-bg" in pod_name:
                # Determine which map/zone this pod belongs to
                if "hb1" in pod_name:
                    display_name = "Judean People's Front (HB-1)"
                elif "hb2" in pod_name:
                    display_name = "Judean Popular Front (HB-2)"
                elif "deepdesert" in pod_name:
                    display_name = "Deep Desert"
                else:
                    display_name = pod_name # Fallback to raw name if unique custom zone
                
                # Extract the execution status phase (Running, Pending, Failed, etc.)
                status_phase = pod.get("status", {}).get("phase", "Unknown")
                
                zones[pod_name] = {
                    "display_name": display_name,
                    "status": status_phase
                }
                
        return {"success": True, "zones": zones}

    except subprocess.CalledProcessError as e:
        return {"success": False, "error": f"Kubectl execution failed: {e.stderr}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def restart_zone(zone_type):
    """
    Triggers a rolling restart for a specified zone deployment.
    zone_type should be 'hb1', 'hb2', or 'deepdesert'.
    """
    # Map the short identifier to the actual deployment name Funcom uses
    deployment_map = {
        "hb1": "seabass-server-bg-hb1",
        "hb2": "seabass-server-bg-hb2",
        "deepdesert": "seabass-server-bg-deepdesert"
    }
    
    target_deployment = deployment_map.get(zone_type)
    if not target_deployment:
        return {"success": False, "error": "Invalid zone type specified."}
        
    try:
        # Force Kubernetes to recreate the pods cleanly
        subprocess.run(
            ["sudo", "kubectl", "rollout", "restart", f"deployment/{target_deployment}", "-n", "default"],
            check=True,
            capture_output=True,
            text=True
        )
        return {"success": True, "message": f"Restart signal sent to {target_deployment}."}
        
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": f"Failed to restart deployment: {e.stderr}"}
