import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import config_editor
import k8s_monitor

app = FastAPI(title="OpenDune-Director Web Engine")

class ConfigUpdate(BaseModel):
    force_pvp: bool
    security_zones: bool
    coriolis_storm: bool

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="Dashboard index.html file not found.")
    with open(index_path, "r") as f:
        return f.read()

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

@app.get("/api/status")
async def get_cluster_status_endpoint():
    return k8s_monitor.get_cluster_and_metrics()

# 🛠️ FLEXIBLE ROUTER FOR TARGETED OR GLOBAL CONTROL COMMANDS
@app.post("/api/zone/{action}")
async def global_cluster_action(action: str, map_target: str = None):
    """Handles global commands directly (e.g., stopping/starting the entire environment)."""
    result = k8s_monitor.execute_battlegroup_action(action, map_target)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@app.post("/api/zone/{action}/{map_target}")
async def targeted_instance_action(action: str, map_target: str):
    """Handles instance-specific actions triggered right from the row buttons."""
    result = k8s_monitor.execute_battlegroup_action(action, map_target)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@app.post("/api/safe-update")
async def safe_update_cluster_endpoint():
    """Triggers the safe programmatic stop -> update -> start macro loop globally."""
    try:
        # 1. Bring down the cluster
        k8s_monitor.execute_battlegroup_action("stop")
        # 2. Update server source files via root execution parameters
        result = k8s_monitor.execute_battlegroup_action("update")
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        # 3. Bring the entire ecosystem back online
        k8s_monitor.execute_battlegroup_action("start")
        return {"success": True, "message": "Global cluster files updated and deployments re-initialized successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
