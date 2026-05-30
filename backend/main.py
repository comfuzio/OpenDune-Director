import os
import subprocess
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
import uvicorn

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
# MAP ENDPOINTS 
# -------------------------------------------------------------------------
@app.get("/api/map-markers")
async def get_live_map_markers(map: str = map_service.DEFAULT_MAP_KEY):
    try:
        map_cfg = map_service.MAP_CONFIGS.get(map, map_service.MAP_CONFIGS[map_service.DEFAULT_MAP_KEY])
        return {"ok": True, "map": map_cfg, "maps": map_service.MAP_CONFIGS, "markers": map_service.get_map_markers(map_cfg["key"])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/public-map-markers")
async def get_public_base_map_markers():
    try:
        return {"ok": True, "map": map_service.MAP_CONFIGS["HaggaBasin"], "markers": map_service.get_public_base_markers()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------------------------------
# ADMIN DB TOOLS (VEHICLES, GRANTS, REPAIRS, BACKUPS)
# -------------------------------------------------------------------------
@app.get("/api/teleportable-vehicles")
async def get_admin_vehicles():
    try: return {"ok": True, "vehicles": map_service.get_teleportable_vehicles()}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/teleport-vehicle")
async def admin_teleport_vehicle(actor_id: str=Form(...), map_key: str=Form(...), partition_id: str=Form(...), x: str=Form(...), y: str=Form(...), z: str=Form(...)):
    try: return {"ok": True, "output": db_connector.run_psql(map_service.build_vehicle_teleport_sql(actor_id, map_key, partition_id, x, y, z))}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/overrepair")
async def admin_overrepair(character_actor_id: str=Form(...), inventory_id: str=Form(...), durability: str=Form(...)):
    try: return {"ok": True, "output": db_connector.run_psql(map_service.build_overrepair_sql(character_actor_id, inventory_id, durability))}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/grant-item")
async def admin_grant_item(fls_id: str=Form(...), template_id: str=Form(...), quantity: str=Form(...), grade: str=Form(...), durability: str=Form(...)):
    try: return {"ok": True, "output": db_connector.run_psql(map_service.build_item_grant_sql(fls_id, template_id, quantity, grade, durability))}
    except Exception as e: raise HTTPException(status_code=500, detail=f"Grant failed: {str(e)}")

@app.post("/api/grant-thopter")
async def admin_grant_thopter(fls_id: str=Form(...)):
    try: return {"ok": True, "output": db_connector.run_psql(map_service.build_thopter_kit_sql(fls_id))}
    except Exception as e: raise HTTPException(status_code=500, detail=f"Thopter grant failed: {str(e)}")

@app.post("/api/db-backup")
async def admin_db_backup():
    """Triggers a pg_dump inside the active postgres pod."""
    try:
        pod_name = db_connector.get_postgres_pod()
        cmd = ["kubectl", "exec", "-n", db_connector.K8S_NAMESPACE, pod_name, "--", "pg_dump", "-U", "dune", "-d", "dune", "-F", "c", "-f", "/var/lib/postgresql/data/manual_backup.dump"]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0: raise Exception(proc.stderr)
        return {"success": True, "message": "Backup created successfully at /var/lib/postgresql/data/manual_backup.dump inside the pod."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")

# -------------------------------------------------------------------------
# CORE METRICS & INFRASTRUCTURE MONITOR
# -------------------------------------------------------------------------
@app.get("/api/status")
async def get_cluster_status_endpoint():
    return k8s_monitor.get_cluster_and_metrics()

@app.post("/api/zone/{action}/{map_target}")
async def targeted_zone_action_endpoint(action: str, map_target: str):
    return k8s_monitor.execute_battlegroup_action(action, map_target)

@app.post("/api/zone/{action}")
async def global_cluster_action_endpoint(action: str):
    return k8s_monitor.execute_battlegroup_action(action)

@app.post("/api/zone/persistence/{action}/{map_target}")
async def toggle_zone_persistence_endpoint(action: str, map_target: str):
    return k8s_monitor.execute_battlegroup_action(action, map_target)

@app.get("/api/config")
async def read_gameplay_config_endpoint():
    return {"success": True, "data": config_editor.read_game_config()}

@app.post("/api/config")
async def write_gameplay_config_endpoint(payload: GameplayConfigPayload):
    if not config_editor.write_game_config(payload.force_pvp, payload.security_zones, payload.coriolis_storm):
        raise HTTPException(status_code=500, detail="Failed to write values.")
    return {"success": True}

@app.get("/api/stream-update")
async def stream_server_update_logs_endpoint():
    process = k8s_monitor.execute_battlegroup_action("update")
    def generate_log_chunks():
        try:
            for line in process.stdout: yield line
        finally:
            process.stdout.close(); process.wait()
    return StreamingResponse(generate_log_chunks(), media_type="text/plain")

# -------------------------------------------------------------------------
# FRONTEND ROUTER
# -------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def serve_public_dashboard_view():
    with open(os.path.join(os.path.dirname(__file__), "../frontend/public_index.html"), "r", encoding="utf-8") as file:
        return HTMLResponse(content=file.read(), status_code=200)

@app.get("/admin", response_class=HTMLResponse)
async def serve_admin_dashboard_view():
    with open(os.path.join(os.path.dirname(__file__), "../frontend/admin_index.html"), "r", encoding="utf-8") as file:
        return HTMLResponse(content=file.read(), status_code=200)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False)
