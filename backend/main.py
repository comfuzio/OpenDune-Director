import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Import the custom modules we built earlier
import k8s_monitor
import config_editor

app = FastAPI(title="OpenDune-Director API")

# Define a Pydantic data model to safely validate incoming config updates
class ConfigUpdate(BaseModel):
    force_pvp: bool
    security_zones: bool
    coriolis_storm: bool

# -------------------------------------------------------------------------
# 1. API ENDPOINTS (The plumbing between frontend and backend)
# -------------------------------------------------------------------------

@app.get("/api/status")
async def get_cluster_status():
    """Returns real-time Kubernetes pod statuses to the dashboard."""
    result = k8s_monitor.get_zone_status()
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@app.post("/api/restart/{zone_type}")
async def restart_cluster_zone(zone_type: str):
    """Triggers a rolling deployment restart for the requested zone."""
    result = k8s_monitor.restart_zone(zone_type)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/api/config")
async def get_server_config():
    """Reads the local UserGame.ini file and passes values to the frontend UI."""
    result = config_editor.read_server_config()
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@app.post("/api/config")
async def update_server_config(payload: ConfigUpdate):
    """Overwrites server settings inside UserGame.ini with new UI inputs."""
    result = config_editor.write_server_config(
        world_name=payload.world_name,
        password=payload.password,
        max_players=payload.max_players
    )
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@app.post("/api/zone/{zone_type}/start")
async def start_zone(zone_type: str):
    """Scales deployment up to 1 replica."""
    result = k8s_monitor.set_zone_scale(zone_type, 1)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@app.post("/api/zone/{zone_type}/stop")
async def stop_zone(zone_type: str):
    """Scales deployment down to 0 replicas (Stops the instance)."""
    result = k8s_monitor.set_zone_scale(zone_type, 0)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@app.post("/api/zone/{zone_type}/safe-update")
async def safe_update_zone(zone_type: str):
    """Triggers the strict Stop -> Update -> Start sequence."""
    result = k8s_monitor.run_sequential_update(zone_type)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

# -------------------------------------------------------------------------
# 2. FRONTEND ROUTING (Serving the dashboard page)
# -------------------------------------------------------------------------

# Define absolute paths to your frontend assets
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend"))

@app.get("/")
async def serve_dashboard():
    """Serves your index.html dashboard file when hitting http://server-ip:8080/"""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "Dashboard index.html file missing from frontend folder."}

# If you ever create an external style.css or javascript assets later, 
# this line mounts the whole folder so they load automatically.
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# -------------------------------------------------------------------------
# 3. RUNNER EXECUTION
# -------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    # Listens globally on port 8080 so your Windows PC can reach it
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
