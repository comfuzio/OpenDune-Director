import os
import configparser

INI_PATH = os.getenv(
    "DUNE_CONFIG_PATH", 
    "/home/dune/.dune/download/scripts/setup/config/UserGame.ini"
)

def read_server_config():
    """
    Reads the specific Funcom gameplay subsystems from UserGame.ini.
    """
    if not os.path.exists(INI_PATH):
        return {"success": False, "error": "Configuration file not found."}
    
    try:
        config = configparser.ConfigParser(strict=False, allow_no_value=True, interpolation=None)
        config.optionxform = str 
        config.read(INI_PATH)
        
        # Pull values carefully, falling back to defaults if they don't exist yet
        pvp_sec = "/Script/DuneSandbox.PvpPveSettings"
        safe_sec = "/Script/DuneSandbox.SecurityZonesSubsystem"
        storm_sec = "/Script/DuneSandbox.SandStormConfig"

        # Convert strings to actual booleans for our JavaScript frontend
        return {
            "success": True,
            "data": {
                "force_pvp": config.get(pvp_sec, "m_bShouldForceEnablePvpOnAllPartitions", fallback="False") == "True",
                "security_zones": config.get(safe_sec, "m_bAreSecurityZonesEnabled", fallback="True") == "True",
                "coriolis_storm": config.get(storm_sec, "m_bCoriolisAutoSpawnEnabled", fallback="True") == "True"
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def write_server_config(force_pvp, security_zones, coriolis_storm):
    """
    Writes updated toggles back into their specific Funcom header sections.
    """
    if not os.path.exists(INI_PATH):
        return {"success": False, "error": "Configuration file missing."}
        
    try:
        config = configparser.ConfigParser(strict=False, allow_no_value=True, interpolation=None)
        config.optionxform = str
        config.read(INI_PATH)
        
        pvp_sec = "/Script/DuneSandbox.PvpPveSettings"
        safe_sec = "/Script/DuneSandbox.SecurityZonesSubsystem"
        storm_sec = "/Script/DuneSandbox.SandStormConfig"

        # Ensure headers exist before writing
        for sec in [pvp_sec, safe_sec, storm_sec]:
            if not config.has_section(sec):
                config.add_section(sec)
                
        # Write back as standard Unreal text strings
        config.set(pvp_sec, "m_bShouldForceEnablePvpOnAllPartitions", "True" if force_pvp else "False")
        config.set(safe_sec, "m_bAreSecurityZonesEnabled", "True" if security_zones else "False")
        config.set(storm_sec, "m_bCoriolisAutoSpawnEnabled", "True" if coriolis_storm else "False")
        
        with open(INI_PATH, 'w') as configfile:
            config.write(configfile)
            
        return {"success": True, "message": "UserGame.ini mechanics updated successfully."}
    except Exception as e:
        return {"success": False, "error": str(e)}
