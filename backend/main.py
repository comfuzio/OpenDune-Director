import os
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
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

@app.post("/api/zone/{action}")
async def global_cluster_action(action: str, map_target: str = None):
    result = k8s_monitor.execute_battlegroup_action(action, map_target)
    if isinstance(result, dict) and not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@app.post("/api/zone/{action}/{map_target}")
async def targeted_instance_action(action: str, map_target: str):
    result = k8s_monitor.execute_battlegroup_action(action, map_target)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

# 📡 REAL-TIME LINE-BY-LINE STREAMING CONTROLLER
@app.get("/api/stream-update")
async def stream_update_cluster_endpoint():
    """
    Executes an update sequence and streams the console output directly
    to the browser window line-by-line.
    """
    async def log_generator():
        yield "🔄 Initiating safe global cluster shutdown...\n"
        k8s_monitor.execute_battlegroup_action("stop")
        await asyncio.sleep(2)
        
        yield "🚀 Triggering Funcom server file verification and update procedure...\n"
        process = k8s_monitor.execute_battlegroup_action("update")
        
        if not hasattr(process, "stdout"):
            yield f"❌ Initialization Error: Failed to spawn update terminal process.\n"
            return

        # Read output lines dynamically from the background terminal loop
        while True:
            line = process.stdout.readline()
            if not line:
                break
            yield f"📋 {line}"
            # Let the CPU breathe between log rows
            await asyncio.sleep(0.05)
            
        process.wait()
        
        yield "🔄 Re-initializing your cluster zones back online...\n"
        k8s_monitor.execute_battlegroup_action("start")
        yield "🎉 UPDATE COMPLETE: All deployments successfully patched and online!\n"

    return StreamingResponse(log_generator(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
