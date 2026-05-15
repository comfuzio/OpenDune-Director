import os
import configparser

# Define the standard path to Funcom's configuration folder
# We will use an environment variable fallback so it works natively now, 
# and can easily map to a Docker volume later!
INI_PATH = os.getenv(
    "DUNE_CONFIG_PATH", 
    "/home/dune/.dune/download/scripts/setup/config/UserGame.ini"
)

def read_server_config():
    """
    Reads the UserGame.ini file and extracts specific server variables.
    """
    if not os.path.exists(INI_PATH):
        return {
            "success": False, 
            "error": f"Configuration file not found at {INI_PATH}. Check paths."
        }
    
    try:
        config = configparser.ConfigParser(strict=False, allow_no_value=True)
        # Unreal Engine sometimes uses case-sensitive keys, so we preserve case
        config.optionxform = str 
        config.read(INI_PATH)
        
        # Target the specific section Funcom uses for general server settings
        # Note: If Funcom nested these under a specific block like [/Script/Engine.GameSession],
        # adjust the section string below accordingly.
        section = "ServerSettings" 
        
        if not config.has_section(section):
            # Fallback if the section name is slightly different in your version
            return {
                "success": False, 
                "error": f"Could not find [ServerSettings] section in .ini file."
            }

        return {
            "success": True,
            "data": {
                "world_name": config.get(section, "ServerName", fallback="Romani Ite Domum"),
                "password": config.get(section, "ServerPassword", fallback=""),
                "max_players": config.getint(section, "MaxPlayers", fallback=100)
            }
        }

    except Exception as e:
        return {"success": False, "error": f"Failed to parse .ini file: {str(e)}"}


def write_server_config(world_name, password, max_players):
    """
    Safely edits and saves the specific variables back to the UserGame.ini file.
    """
    if not os.path.exists(INI_PATH):
        return {"success": False, "error": "Configuration file missing. Cannot write changes."}
        
    try:
        config = configparser.ConfigParser(strict=False, allow_no_value=True)
        config.optionxform = str
        config.read(INI_PATH)
        
        section = "ServerSettings"
        if not config.has_section(section):
            config.add_section(section)
            
        # Update only our targeted keys
        config.set(section, "ServerName", str(world_name))
        config.set(section, "ServerPassword", str(password))
        config.set(section, "MaxPlayers", str(max_players))
        
        # Write the changes back to the file safely
        with open(INI_PATH, 'w') as configfile:
            config.write(configfile)
            
        return {"success": True, "message": "UserGame.ini updated successfully."}
        
    except Exception as e:
        return {"success": False, "error": f"Failed to write to .ini file: {str(e)}"}
