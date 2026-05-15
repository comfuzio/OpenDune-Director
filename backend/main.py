import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import config_editor
import k8s_monitor

app = FastAPI(title="OpenDune-Director Web Engine")

# DATA SCHEMES FOR PAYLOAD VALIDATION
class ConfigUpdate(BaseModel):
    force_pvp: bool
    security_zones: bool
    coriolis_storm: bool

# 1. SERVE FRONTEND INTERFACE DASHBOARD
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="Dashboard index.html file not found.")
    with open(index_path, "r") as f:
        return f.read()

# 2. CONFIGURATION HANDLERS (.INI READ / WRITE)
@app.get("/api/config")
async def get_config_endpoint():
    result = config_editor.read_server_config()
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@app.post("/api/config")
async def save_config_endpoint(payload: ConfigUpdate):
    result = config_editor.write_server_config(
        force_pvp=payload.force_pvp,
        security_zones=payload.security_zones,
        coriolis_storm=payload.coriolis_storm
    )
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

# 3. CONSOLIDATED DYNAMIC TELEMETRY ROUTER (CLUSTERS & PLAYERS)
@app.get("/api/status")
async def get_cluster_status_endpoint():
    return k8s_monitor.get_cluster_and_metrics()

# 4. ENVIRONMENT COMMAND CONTROL ENDPOINTS (DIRECT COMMAND ROUTING)
@app.post("/api/zone/{zone_type}/start")
async def start_zone(zone_type: str):
    # Maps 'hb1' dashboard button target to your real 'Survival_1' sector
    target_map = "Survival_1" if zone_type == "hb1" else zone_type
    result = k8s_monitor.execute_battlegroup_action("start", target_map)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@app.post("/api/zone/{zone_type}/stop")
async def stop_zone(zone_type: str):
    target_map = "Survival_1" if zone_type == "hb1" else zone_type
    result = k8s_monitor.execute_battlegroup_action("stop", target_map)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@app.post("/api/zone/{zone_type}/restart")
async def restart_zone(zone_type: str):
    target_map = "Survival_1" if zone_type == "hb1" else zone_type
    result = k8s_monitor.execute_battlegroup_action("restart", target_map)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@app.post("/api/zone/{zone_type}/safe-update")
async def safe_update_zone(zone_type: str):
    target_map = "Survival_1" if zone_type == "hb1" else zone_type
    
    # 1. Stop the target map safely
    k8s_monitor.execute_battlegroup_action("stop", target_map)
    
    # 2. Run the update with sudo privileges
    result = k8s_monitor.execute_battlegroup_action("update")
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
        
    # 3. Start the target map sector back up
    k8s_monitor.execute_battlegroup_action("start", target_map)
    return {"success": True, "message": "Cluster server file update completed successfully via root execution parameters."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
