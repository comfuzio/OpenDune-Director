import os
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
import uvicorn

# Internal Modular Dependency Imports
import config_editor
import k8s_monitor
import db_connector
import map_service

app = FastAPI(title="OpenDune-Director API Backend")

class GameplayConfigPayload(BaseModel):
    force_pvp: bool
    security_zones: bool
    coriolis_storm: bool

# -------------------------------------------------------------------------
# LIVE MAP API ENDPOINTS 
# -------------------------------------------------------------------------
@app.get("/api/map-markers")
async def get_live_map_markers(map: str = map_service.DEFAULT_MAP_KEY):
    """Provides full live JSON data to the Admin mapping script."""
    try:
        map_cfg = map_service.MAP_CONFIGS.get(map, map_service.MAP_CONFIGS[map_service.DEFAULT_MAP_KEY])
        markers = map_service.get_map_markers(map_cfg["key"])
        
        return {
            "ok": True,
            "map": map_cfg,
            "maps": map_service.MAP_CONFIGS,
            "default_map": map_service.DEFAULT_MAP_KEY,
            "markers": markers,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")

@app.get("/api/public-map-markers")
async def get_public_base_map_markers():
    """Provides ONLY base locations for the public UI."""
    try:
        map_cfg = map_service.MAP_CONFIGS["HaggaBasin"]
        markers = map_service.get_public_base_markers()
        return {"ok": True, "map": map_cfg, "markers": markers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------------------------------
# ADMIN DB TOOLS (VEHICLES & REPAIR)
# -------------------------------------------------------------------------
@app.get("/api/teleportable-vehicles")
async def get_admin_vehicles():
    try:
        return {"ok": True, "vehicles": map_service.get_teleportable_vehicles()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/teleport-vehicle")
async def admin_teleport_vehicle(
    actor_id: str = Form(...), map_key: str = Form(...), partition_id: str = Form(...),
    x: str = Form(...), y: str = Form(...), z: str = Form(...)
):
    try:
        sql = map_service.build_vehicle_teleport_sql(actor_id, map_key, partition_id, x, y, z)
        output = db_connector.run_psql(sql)
        return {"ok": True, "output": output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vehicle Teleport failed: {str(e)}")

@app.post("/api/overrepair")
async def admin_overrepair(
    character_actor_id: str = Form(...), inventory_id: str = Form(...), durability: str = Form(...)
):
    try:
        sql = map_service.build_overrepair_sql(character_actor_id, inventory_id, durability)
        output = db_connector.run_psql(sql)
        return {"ok": True, "output": output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Overrepair failed: {str(e)}")

# -------------------------------------------------------------------------
# CORE METRICS & INFRASTRUCTURE MONITOR ENDPOINTS
# -------------------------------------------------------------------------
@app.get("/api/status")
async def get_cluster_status_endpoint():
    return k8s_monitor.get_cluster_and_metrics()

# -------------------------------------------------------------------------
# COMPONENT DIRECTIVE CONTROLLERS (START / STOP / RESTART)
# -------------------------------------------------------------------------
@app.post("/api/zone/{action}/{map_target}")
async def targeted_zone_action_endpoint(action: str, map_target: str):
    if action not in ["start", "stop", "restart"]:
        raise HTTPException(status_code=400, detail="Invalid action directive.")
    result = k8s_monitor.execute_battlegroup_action(action, map_target)
    if isinstance(result, dict) and not result.get("success", True):
        raise HTTPException(status_code=500, detail=result.get("error", "Action failure."))
    return result

@app.post("/api/zone/{action}")
async def global_cluster_action_endpoint(action: str):
    if action not in ["start", "stop", "restart"]:
        raise HTTPException(status_code=400, detail="Invalid global action directive.")
    result = k8s_monitor.execute_battlegroup_action(action)
    if isinstance(result, dict) and not result.get("success", True):
        raise HTTPException(status_code=500, detail=result.get("error", "Global action failure."))
    return result

# -------------------------------------------------------------------------
# PERSISTENT STORAGE SCALING CONTROLLERS
# -------------------------------------------------------------------------
@app.post("/api/zone/persistence/{action}/{map_target}")
async def toggle_zone_persistence_endpoint(action: str, map_target: str):
    if action not in ["make-persistent", "make-dynamic"]:
        raise HTTPException(status_code=400, detail="Invalid persistence modifications.")
    result = k8s_monitor.execute_battlegroup_action(action, map_target)
    if isinstance(result, dict) and not result.get("success", True):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to alter scaling."))
    return result

# -------------------------------------------------------------------------
# CONFIGURATION INI HANDLING ENDPOINTS
# -------------------------------------------------------------------------
@app.get("/api/config")
async def read_gameplay_config_endpoint():
    data = config_editor.read_game_config()
    return {"success": True, "data": data}

@app.post("/api/config")
async def write_gameplay_config_endpoint(payload: GameplayConfigPayload):
    success = config_editor.write_game_config(
        force_pvp=payload.force_pvp,
        security_zones=payload.security_zones,
        coriolis_storm=payload.coriolis_storm
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to write values.")
    return {"success": True}

@app.get("/api/stream-update")
async def stream_server_update_logs_endpoint():
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
# FRONTEND PRESENTATION SHEET ROUTER (PUBLIC VS ADMIN)
# -------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def serve_public_dashboard_view():
    """Loads the PUBLIC presentation asset (Status & Map only, no controls)."""
    html_path = os.path.join(os.path.dirname(__file__), "../frontend/public_index.html")
    try:
        with open(html_path, "r", encoding="utf-8") as file:
            return HTMLResponse(content=file.read(), status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Public View missing. Rename index.html to public_index.html: {str(e)}")

@app.get("/admin", response_class=HTMLResponse)
async def serve_admin_dashboard_view():
    """Loads the ADMIN presentation asset (Full Controls)."""
    html_path = os.path.join(os.path.dirname(__file__), "../frontend/admin_index.html")
    try:
        with open(html_path, "r", encoding="utf-8") as file:
            return HTMLResponse(content=file.read(), status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Admin View missing: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False)
