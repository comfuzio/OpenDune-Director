import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

# Internal Local Dependency Imports
import config_editor
import k8s_monitor

app = FastAPI(title="OpenDune-Director API Backend")

# Data Models for configuration adjustments
class GameplayConfigPayload(BaseModel):
    force_pvp: bool
    security_zones: bool
    coriolis_storm: bool

# -------------------------------------------------------------------------
# CORE METRICS & INFRASTRUCTURE MONITOR ENDPOINTS
# -------------------------------------------------------------------------

@app.get("/api/status")
async def get_cluster_status_endpoint():
    """Fetches combined data matrix for cluster health, metrics, and telemetries."""
    return k8s_monitor.get_cluster_and_metrics()

# -------------------------------------------------------------------------
# COMPONENT DIRECTIVE CONTROLLERS (START / STOP / RESTART)
# -------------------------------------------------------------------------

@app.post("/api/zone/{action}/{map_target}")
async def targeted_zone_action_endpoint(action: str, map_target: str):
    """Executes targeted lifecycle actions on individual server sectors."""
    if action not in ["start", "stop", "restart"]:
        raise HTTPException(status_code=400, detail="Invalid action directive.")
    
    result = k8s_monitor.execute_battlegroup_action(action, map_target)
    if isinstance(result, dict) and not result.get("success", True):
        raise HTTPException(status_code=500, detail=result.get("error", "Action execution failure."))
    return result

@app.post("/api/zone/{action}")
async def global_cluster_action_endpoint(action: str):
    """Executes cluster-wide lifecycle operations across all map sectors."""
    if action not in ["start", "stop", "restart"]:
        raise HTTPException(status_code=400, detail="Invalid global action directive.")
    
    result = k8s_monitor.execute_battlegroup_action(action)
    if isinstance(result, dict) and not result.get("success", True):
        raise HTTPException(status_code=500, detail=result.get("error", "Global action execution failure."))
    return result

# -------------------------------------------------------------------------
# PERSISTENT STORAGE SCALING CONTROLLERS
# -------------------------------------------------------------------------

@app.post("/api/zone/persistence/{action}/{map_target}")
async def toggle_zone_persistence_endpoint(action: str, map_target: str):
    """Routes MinServers overrides to the underlying cluster config data matrix."""
    if action not in ["make-persistent", "make-dynamic"]:
        raise HTTPException(status_code=400, detail="Invalid persistence modifications.")
        
    result = k8s_monitor.execute_battlegroup_action(action, map_target)
    if isinstance(result, dict) and not result.get("success", True):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to alter scaling policy."))
    return result

# -------------------------------------------------------------------------
# CONFIGURATION INI HANDLING ENDPOINTS
# -------------------------------------------------------------------------

@app.get("/api/config")
async def read_gameplay_config_endpoint():
    """Reads current parsed rules values out of UserGame.ini."""
    data = config_editor.read_game_config()
    return {"success": True, "data": data}

@app.post("/api/config")
async def write_gameplay_config_endpoint(payload: GameplayConfigPayload):
    """Writes updated configuration variables safely back to UserGame.ini."""
    success = config_editor.write_game_config(
        force_pvp=payload.force_pvp,
        security_zones=payload.security_zones,
        coriolis_storm=payload.coriolis_storm
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to write values to file database.")
    return {"success": True}

# -------------------------------------------------------------------------
# LIVE STREAMING TERMINAL CONSOLE LOGGER
# -------------------------------------------------------------------------

@app.get("/api/stream-update")
async def stream_server_update_logs_endpoint():
    """Streams live update logs as an asynchronous text transfer event."""
    process = k8s_monitor.execute_battlegroup_action("update")
    if not process or not hasattr(process, "stdout"):
        raise HTTPException(status_code=500, detail="Failed to hook background update stream.")
        
    def generate_log_chunks():
        try:
            for line in process.stdout:
                yield line
        finally:
            process.stdout.close()
            process.wait()

    return StreamingResponse(generate_log_chunks(), media_type="text/plain")

# -------------------------------------------------------------------------
# FRONTEND PRESENTATION SHEET ROUTER
# -------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard_index_view():
    """Loads HTML presentation asset directly from local folder space."""
    html_path = os.path.join(os.path.dirname(__file__), "../frontend/index.html")
    try:
        with open(html_path, "r", encoding="utf-8") as file:
            return HTMLResponse(content=file.read(), status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Frontend view asset missing: {str(e)}")

if __name__ == "__main__":
    # Force production execution properties (Disabled automatic auto-reloader loop completely)
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False)
