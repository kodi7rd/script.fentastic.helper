import os
import json
from xbmcgui import Window
from xbmc import sleep, getInfoLabel
from xbmcvfs import translatePath
from xbmcaddon import Addon
from modules.cpath_maker import remake_all_cpaths, starting_widgets

# Initialize the main window
window = Window(10000)

# Define the profile path for the current profile JSON file
PROFILE_PATH = os.path.join(
    translatePath("special://userdata/addon_data/script.fentastic.helper"),
    "current_profile.json",
)


def check_for_update(skin_id: str) -> None:
    """
    Checks if there is a version update for the specified skin.

    Args:
        skin_id (str): The ID of the skin to check for updates.
    """
    property_version = window.getProperty(f"{skin_id}.installed_version")
    installed_version = Addon(id=skin_id).getAddonInfo("version")

    if not property_version:
        set_installed_version(skin_id, installed_version)
        return  # Stop further execution

    if property_version != installed_version:
        set_installed_version(skin_id, installed_version)
        sleep(1000)  # Sleep for a second to ensure the update process is initiated
        remake_all_cpaths(silent=True)  # Remake all custom paths
        starting_widgets()  # Start all widgets



def set_installed_version(skin_id: str, installed_version: str) -> None:
    """
    Sets the installed version property for the specified skin.

    Args:
        skin_id (str): The ID of the skin.
        installed_version (str): The version to set as installed.
    """
    window.setProperty(f"{skin_id}.installed_version", installed_version)


def set_current_profile(skin_id: str, current_profile: str) -> None:
    """
    Saves the current profile to a JSON file and updates the property in Kodi.

    Args:
        skin_id (str): The ID of the skin.
        current_profile (str): The current profile name.
    """
    dir_path = os.path.dirname(PROFILE_PATH)
    os.makedirs(dir_path, exist_ok=True)  # Create directory if it doesn't exist

    with open(PROFILE_PATH, "w") as f:
        json.dump(current_profile, f)  # Write the current profile to the JSON file

    window.setProperty(f"{skin_id}.current_profile", current_profile)


def check_for_profile_change(skin_id: str) -> None:
    """
    Checks if the current profile has changed and updates accordingly.

    Args:
        skin_id (str): The ID of the skin.
    """
    current_profile = getInfoLabel("System.ProfileName")
    try:
        with open(PROFILE_PATH, "r") as f:
            saved_profile = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        saved_profile = None

    if not saved_profile:
        set_current_profile(skin_id, current_profile)
        return

    if saved_profile != current_profile:
        set_current_profile(skin_id, current_profile)
        sleep(200)  # Sleep briefly before remaking paths
        remake_all_cpaths(silent=True)  # Remake all custom paths