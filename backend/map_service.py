import re
import db_connector

# -------------------------------------------------------------------------
# MAP CONFIGURATIONS & BOUNDS
# -------------------------------------------------------------------------
MAP_CONFIGS = {
    "HaggaBasin": {
        "key": "HaggaBasin",
        "label": "Arrakis - Hagga Basin",
        "image": "arrakis_hb.webp",
        "width": 8000,
        "height": 8000,
        "min_x": -456752.21,
        "max_x": 354547.46,
        "min_y": -450630.14,
        "max_y": 353821.95,
        "flip_y": False,
        "default_partition_id": 1,
    },
    "DeepDesert": {
        "key": "DeepDesert",
        "label": "The Deep Desert",
        "image": "deep_desert.webp",
        "width": 8000,
        "height": 8000,
        "min_x": -1268624.82,
        "max_x": 1163312.83,
        "min_y": -1266548.17,
        "max_y": 1162416.13,
        "flip_y": False,
        "default_partition_id": "8",
    },
}

DEFAULT_MAP_KEY = "HaggaBasin"

# -------------------------------------------------------------------------
# MATH & PARSING HELPERS
# -------------------------------------------------------------------------
def parse_transform(transform_value):
    """Parses X,Y,Z coordinates from Dune's string transform format."""
    if not transform_value:
        return None
    match = re.search(r'\(([0-9.eE+\-]+),([0-9.eE+\-]+),([0-9.eE+\-]+)\)', str(transform_value))
    if not match:
        return None
    return {
        "x": float(match.group(1)),
        "y": float(match.group(2)),
        "z": float(match.group(3)),
    }

def world_to_map_pixels(x, y, map_cfg):
    """Converts world coordinates to UI image pixel percentages."""
    min_x, max_x = map_cfg["min_x"], map_cfg["max_x"]
    min_y, max_y = map_cfg["min_y"], map_cfg["max_y"]
    width, height = map_cfg["width"], map_cfg["height"]

    if max_x == min_x or max_y == min_y:
        return None

    px = ((x - min_x) / (max_x - min_x)) * width
    py = ((y - min_y) / (max_y - min_y)) * height

    if map_cfg.get("flip_y"):
        py = height - py

    return {
        "px": px,
        "py": py,
        "in_bounds": 0 <= px <= width and 0 <= py <= height,
    }

# -------------------------------------------------------------------------
# DATABASE FETCHING LOGIC
# -------------------------------------------------------------------------
def get_map_markers(map_key=None):
    """Queries the k3s Postgres DB for live Player, Vehicle, and Base locations."""
    map_key = map_key or DEFAULT_MAP_KEY
    map_cfg = MAP_CONFIGS.get(map_key, MAP_CONFIGS[DEFAULT_MAP_KEY])
    map_key = map_cfg["key"]

    players_sql = f"""
    SELECT a.id, COALESCE(NULLIF(ps.character_name, ''), 'Unknown') AS name, 
           ps.online_status::text AS online_status, acc."user" AS fls_id, a.map, a.transform::text
    FROM dune.actors a
    JOIN dune.player_state ps ON a.id = ps.player_pawn_id
    LEFT JOIN dune.accounts acc ON ps.account_id = acc.id
    WHERE a.transform IS NOT NULL AND a.map = '{map_key}'
    ORDER BY ps.character_name;
    """

    vehicles_sql = f"""
    SELECT v.id, a.class, a.map, a.transform::text
    FROM dune.vehicles v
    JOIN dune.actors a ON v.id = a.id
    WHERE a.transform IS NOT NULL AND a.map = '{map_key}'
    ORDER BY a.class;
    """

    markers = []

    # Parse Players
    for line in db_connector.run_tab_query(players_sql):
        parts = line.split("\t")
        if len(parts) < 6: continue
        coords = parse_transform(parts[5])
        if not coords: continue
        pixel = world_to_map_pixels(coords["x"], coords["y"], map_cfg)
        if not pixel: continue
        markers.append({
            "id": parts[0], "name": parts[1], "online_status": parts[2],
            "map": parts[4], "type": "player", **coords, **pixel,
        }) # We omit fls_id here to protect player data on the public map

    # Parse Vehicles
    for line in db_connector.run_tab_query(vehicles_sql):
        parts = line.split("\t")
        if len(parts) < 4: continue
        coords = parse_transform(parts[3])
        if not coords: continue
        pixel = world_to_map_pixels(coords["x"], coords["y"], map_cfg)
        if not pixel: continue
        short_class = parts[1].split("/")[-1] if parts[1] else "Vehicle"
        markers.append({
            "id": parts[0], "name": short_class, "map": parts[2],
            "type": "vehicle", **coords, **pixel,
        })

    return markers
