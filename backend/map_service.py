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
def get_public_base_markers():
    """Queries ONLY bases for Hagga Basin to show on the public map."""
    map_cfg = MAP_CONFIGS["HaggaBasin"]
    
    # We attempt to grab the owner_account_id to match with a player name
    bases_sql = f"""
    SELECT b.id, a.class, a.map, a.transform::text, 
           COALESCE(ps.character_name, 'Unknown Builder') as owner_name
    FROM dune.buildings b
    JOIN dune.actors a ON b.id = a.id
    LEFT JOIN dune.player_state ps ON a.owner_account_id = ps.account_id
    WHERE a.transform IS NOT NULL AND a.map = 'HaggaBasin'
    ORDER BY b.id LIMIT 1000;
    """

    markers = []
    for line in db_connector.run_tab_query(bases_sql):
        parts = line.split("\t")
        if len(parts) < 5: continue
        coords = parse_transform(parts[3])
        if not coords: continue
        pixel = world_to_map_pixels(coords["x"], coords["y"], map_cfg)
        if not pixel: continue
        
        short_class = parts[1].split("/")[-1] if parts[1] else "Base"
        markers.append({
            "id": parts[0], 
            "name": f"{parts[4]}'s {short_class}", # Shows "PlayerName's Base"
            "map": parts[2],
            "type": "base", 
            **coords, 
            **pixel,
        })
    return markers

def get_teleportable_vehicles():
    """Fetches valid vehicles for the Admin Relocation tool."""
    sql = """
    SELECT id, class, COALESCE(map, '') AS map, 
           COALESCE(partition_id::text, '') AS partition_id, transform::text
    FROM dune.actors
    WHERE (class ILIKE '%Ornithopter%' OR class ILIKE '%Sandbike%' 
           OR class ILIKE '%Buggy%' OR class ILIKE '%TreadWheel%' 
           OR class ILIKE '%SandCrawler%')
      AND transform IS NOT NULL
    ORDER BY id;
    """
    vehicles = []
    for line in db_connector.run_tab_query(sql):
        parts = line.split("\t")
        if len(parts) < 5: continue
        coords = parse_transform(parts[4]) or {}
        short_class = parts[1].split("/")[-1] if parts[1] else "Vehicle"
        vehicles.append({
            "actor_id": parts[0],
            "short_class": short_class,
            "map": parts[2],
            "partition_id": parts[3],
            "x": coords.get("x", ""),
            "y": coords.get("y", ""),
            "z": coords.get("z", "")
        })
    return vehicles

def build_vehicle_teleport_sql(actor_id, map_key, partition_id, x, y, z):
    """Generates the SQL to safely move a vehicle without rotating it."""
    # First, get existing transform to preserve rotation
    actor_sql = f"SELECT transform::text FROM dune.actors WHERE id = {int(actor_id)} LIMIT 1;"
    existing_transform = db_connector.run_tab_query(actor_sql)[0] if db_connector.run_tab_query(actor_sql) else None
    
    if not existing_transform: raise ValueError("Vehicle transform not found.")
    
    # Extract existing rotation (QX, QY, QZ, QW)
    rotation_match = re.search(r'\(([0-9.eE+\-]+),([0-9.eE+\-]+),([0-9.eE+\-]+),([0-9.eE+\-]+)\)', existing_transform)
    rotation = f"({rotation_match.group(1)},{rotation_match.group(2)},{rotation_match.group(3)},{rotation_match.group(4)})" if rotation_match else "(0,0,0,1)"
    
    safe_transform = f'("({float(x)},{float(y)},{float(z)})","{rotation}")'
    
    return f"""
    UPDATE dune.actors SET map = '{map_key}', partition_id = {int(partition_id)}, transform = '{safe_transform}'
    WHERE id = {int(actor_id)};
    """

def build_overrepair_sql(actor_id, inventory_id, durability):
    """Sets max durability for a specific inventory item."""
    return f"""
    UPDATE dune.items i
    SET stats = jsonb_set(
        jsonb_set(
            jsonb_set(i.stats, '{{FItemStackAndDurabilityStats,1,CurrentDurability}}', to_jsonb({float(durability)}::numeric), true),
            '{{FItemStackAndDurabilityStats,1,DecayedMaxDurability}}', to_jsonb({float(durability)}::numeric), true),
        '{{FItemStackAndDurabilityStats,1,MaxDurability}}', to_jsonb({float(durability)}::numeric), true)
    FROM dune.inventories inv
    WHERE i.inventory_id = inv.id AND inv.id = {int(inventory_id)} AND inv.actor_id = {int(actor_id)}
      AND i.stats #> '{{FItemStackAndDurabilityStats,1,CurrentDurability}}' IS NOT NULL;
    """
