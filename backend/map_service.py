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
    if not transform_value: return None
    match = re.search(r'\(([0-9.eE+\-]+),([0-9.eE+\-]+),([0-9.eE+\-]+)\)', str(transform_value))
    if not match: return None
    return {"x": float(match.group(1)), "y": float(match.group(2)), "z": float(match.group(3))}

def world_to_map_pixels(x, y, map_cfg):
    min_x, max_x, min_y, max_y = map_cfg["min_x"], map_cfg["max_x"], map_cfg["min_y"], map_cfg["max_y"]
    width, height = map_cfg["width"], map_cfg["height"]
    if max_x == min_x or max_y == min_y: return None

    px = ((x - min_x) / (max_x - min_x)) * width
    py = ((y - min_y) / (max_y - min_y)) * height
    if map_cfg.get("flip_y"): py = height - py

    return {"px": px, "py": py, "in_bounds": 0 <= px <= width and 0 <= py <= height}

# -------------------------------------------------------------------------
# DATABASE FETCHING LOGIC (MAPS & VEHICLES)
# -------------------------------------------------------------------------
def get_map_markers(map_key=None):
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
    WHERE a.transform IS NOT NULL AND a.map = '{map_key}';
    """

    markers = []
    for line in db_connector.run_tab_query(players_sql):
        parts = line.split("\t")
        if len(parts) < 6: continue
        coords = parse_transform(parts[5])
        if not coords: continue
        pixel = world_to_map_pixels(coords["x"], coords["y"], map_cfg)
        if not pixel: continue
        markers.append({"id": parts[0], "name": parts[1], "online_status": parts[2], "fls_id": parts[3], "map": parts[4], "type": "player", **coords, **pixel})

    for line in db_connector.run_tab_query(vehicles_sql):
        parts = line.split("\t")
        if len(parts) < 4: continue
        coords = parse_transform(parts[3])
        if not coords: continue
        pixel = world_to_map_pixels(coords["x"], coords["y"], map_cfg)
        if not pixel: continue
        markers.append({"id": parts[0], "name": parts[1].split("/")[-1] if parts[1] else "Vehicle", "map": parts[2], "type": "vehicle", **coords, **pixel})

    return markers

def get_public_base_markers():
    map_cfg = MAP_CONFIGS["HaggaBasin"]
    bases_sql = """
    SELECT b.id, a.class, a.map, a.transform::text, COALESCE(ps.character_name, 'Unknown Builder') as owner_name
    FROM dune.buildings b
    JOIN dune.actors a ON b.id = a.id
    LEFT JOIN dune.player_state ps ON a.owner_account_id = ps.account_id
    WHERE a.transform IS NOT NULL AND a.map = 'HaggaBasin' LIMIT 1000;
    """
    markers = []
    for line in db_connector.run_tab_query(bases_sql):
        parts = line.split("\t")
        if len(parts) < 5: continue
        coords = parse_transform(parts[3])
        pixel = world_to_map_pixels(coords["x"], coords["y"], map_cfg) if coords else None
        if not pixel: continue
        markers.append({"id": parts[0], "name": f"{parts[4]}'s Base", "type": "base", **coords, **pixel})
    return markers

def get_teleportable_vehicles():
    sql = """
    SELECT id, class, COALESCE(map, '') AS map, COALESCE(partition_id::text, '') AS partition_id, transform::text
    FROM dune.actors WHERE (class ILIKE '%Ornithopter%' OR class ILIKE '%Sandbike%' OR class ILIKE '%Buggy%' OR class ILIKE '%SandCrawler%') AND transform IS NOT NULL;
    """
    vehicles = []
    for line in db_connector.run_tab_query(sql):
        parts = line.split("\t")
        if len(parts) < 5: continue
        coords = parse_transform(parts[4]) or {}
        vehicles.append({"actor_id": parts[0], "short_class": parts[1].split("/")[-1], "map": parts[2], "partition_id": parts[3], "x": coords.get("x", ""), "y": coords.get("y", ""), "z": coords.get("z", "")})
    return vehicles

# -------------------------------------------------------------------------
# DATABASE ACTION BUILDERS (TOOLS, GRANTS, BACKUPS)
# -------------------------------------------------------------------------
def build_vehicle_teleport_sql(actor_id, map_key, partition_id, x, y, z):
    actor_sql = f"SELECT transform::text FROM dune.actors WHERE id = {int(actor_id)} LIMIT 1;"
    existing_transform = db_connector.run_tab_query(actor_sql)[0] if db_connector.run_tab_query(actor_sql) else None
    if not existing_transform: raise ValueError("Vehicle not found.")
    
    match = re.search(r'\(([0-9.eE+\-]+),([0-9.eE+\-]+),([0-9.eE+\-]+),([0-9.eE+\-]+)\)', existing_transform)
    rotation = f"({match.group(1)},{match.group(2)},{match.group(3)},{match.group(4)})" if match else "(0,0,0,1)"
    return f"UPDATE dune.actors SET map = '{map_key}', partition_id = {int(partition_id)}, transform = '(\"({float(x)},{float(y)},{float(z)})\",\"{rotation}\")' WHERE id = {int(actor_id)};"

def build_overrepair_sql(character_actor_id, inventory_id, durability):
    return f"""
    UPDATE dune.items i
    SET stats = jsonb_set(jsonb_set(jsonb_set(i.stats, '{{FItemStackAndDurabilityStats,1,CurrentDurability}}', to_jsonb({float(durability)}::numeric), true), '{{FItemStackAndDurabilityStats,1,DecayedMaxDurability}}', to_jsonb({float(durability)}::numeric), true), '{{FItemStackAndDurabilityStats,1,MaxDurability}}', to_jsonb({float(durability)}::numeric), true)
    FROM dune.inventories inv WHERE i.inventory_id = inv.id AND inv.id = {int(inventory_id)} AND inv.actor_id = {int(character_actor_id)} AND i.stats #> '{{FItemStackAndDurabilityStats,1,CurrentDurability}}' IS NOT NULL;
    """

def get_player_inventory_id(fls_id):
    """Fetches the main backpack inventory ID (Type 1) for a specific FLS ID."""
    sql = f"""
    SELECT i.id FROM dune.inventories i
    JOIN dune.actors a ON i.actor_id = a.id
    JOIN dune.player_state ps ON a.id = ps.player_pawn_id
    JOIN dune.accounts acc ON ps.account_id = acc.id
    WHERE acc."user" = '{fls_id}' AND i.inventory_type = 1 LIMIT 1;
    """
    result = db_connector.run_tab_query(sql)
    if not result: raise ValueError(f"No active inventory found for FLS: {fls_id}. Ensure player is offline.")
    return int(result[0])

def build_item_grant_sql(fls_id, template_id, quantity, grade, durability):
    """Creates a single stacked item row, bypassing game slot math, and assigns a Grade."""
    inv_id = get_player_inventory_id(fls_id)
    
    # Constructing the JSONB stats block safely
    stats_json = f"""{{
        "FItemStackAndDurabilityStats": [
            {{"MaxDurability": {float(durability)}, "CurrentDurability": {float(durability)}}}, 
            {{"StackCount": {int(quantity)}, "MaxStackCount": 10000}}
        ], 
        "FItemGradeStats": [
            {{"Grade": {int(grade)}}}
        ]
    }}"""
    
    return f"INSERT INTO dune.items (inventory_id, template, stats) VALUES ({inv_id}, '{template_id}', '{stats_json}'::jsonb);"

def build_thopter_kit_sql(fls_id):
    """Grants all necessary parts for a MK6 Medium Thopter directly to inventory."""
    inv_id = get_player_inventory_id(fls_id)
    parts = [
        "Vehicle_MediumOrnithopter_Chassis_Item_C",
        "Vehicle_MediumOrnithopter_Engine_Item_C",
        "Vehicle_MediumOrnithopter_Cockpit_Item_C",
        "Vehicle_MediumOrnithopter_Wings_Item_C",
        "Vehicle_MediumOrnithopter_Tail_Item_C"
    ]
    
    stats_json = '{"FItemStackAndDurabilityStats": [{"MaxDurability": 1.0, "CurrentDurability": 1.0}, {"StackCount": 1, "MaxStackCount": 1}], "FItemGradeStats": [{"Grade": 0}]}'
    
    sql_statements = [
        f"INSERT INTO dune.items (inventory_id, template, stats) VALUES ({inv_id}, '{part}', '{stats_json}'::jsonb);"
        for part in parts
    ]
    return "\n".join(sql_statements)
