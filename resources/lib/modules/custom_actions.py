import xbmc, xbmcgui, xbmcvfs
import xml.etree.ElementTree as ET
from xml.dom import minidom

KEYMAP_LOCATION = "special://userdata/keymaps/"
POSSIBLE_KEYMAP_NAMES = ["gen.xml", "keyboard.xml", "keymap.xml"]

def set_image():
    """
    Prompts the user to select a custom background image and sets it in the skin.
    """
    image_file = xbmcgui.Dialog().browse(
        2, "Choose Custom Background Image", "network", ".jpg|.png|.bmp", False, False
    )
    if image_file:
        xbmc.executebuiltin(f"Skin.SetString(CustomBackground,{image_file})")

def fix_black_screen():
    """
    Toggles the 'TrailerPlaying' setting in the skin to fix the black screen issue.
    """
    if xbmc.getCondVisibility("Skin.HasSetting(TrailerPlaying)"):
        xbmc.executebuiltin("Skin.ToggleSetting(TrailerPlaying)")

def make_backup(keymap_path: str):
    """
    Creates a backup of the specified keymap file.

    Args:
        keymap_path (str): The path of the keymap file to back up.
    """
    backup_path = f"{keymap_path}.backup"
    if not xbmcvfs.exists(backup_path):
        xbmcvfs.copy(keymap_path, backup_path)

def restore_from_backup(keymap_path: str):
    """
    Restores the keymap file from its backup if it exists.

    Args:
        keymap_path (str): The path of the keymap file to restore.
    """
    backup_path = f"{keymap_path}.backup"
    if xbmcvfs.exists(backup_path):
        xbmcvfs.delete(keymap_path)
        xbmcvfs.rename(backup_path, keymap_path)

def get_all_existing_keymap_paths() -> list:
    """
    Retrieves all existing keymap file paths.

    Returns:
        list: A list of existing keymap file paths.
    """
    # existing_paths = []
    # for name in POSSIBLE_KEYMAP_NAMES:
    #     path = xbmcvfs.translatePath(f"special://profile/keymaps/{name}")
    #     if xbmcvfs.exists(path):
    #         existing_paths.append(path)
    existing_paths = [
        path
        for name in POSSIBLE_KEYMAP_NAMES
        if (path := xbmcvfs.translatePath(f"special://profile/keymaps/{name}")) and xbmcvfs.exists(path)
    ]
    return existing_paths


def create_new_keymap_file() -> str:
    """
    Creates a new keymap file with a default keymap structure.

    Returns:
        str: The path of the newly created keymap file.
    """
    default_keymap_name = "gen.xml"
    new_keymap_path = xbmcvfs.translatePath(f"{KEYMAP_LOCATION}{default_keymap_name}")
    root = ET.Element("keymap")
    ET.ElementTree(root).write(new_keymap_path)
    return new_keymap_path

def modify_keymap():
    """
    Modifies existing keymap files based on the setting for enabling One Click Trailers.
    If no keymap files exist, a new keymap file is created.
    """
    keymap_paths = get_all_existing_keymap_paths() or [create_new_keymap_file()]
    setting_value = xbmc.getCondVisibility("Skin.HasSetting(Enable.OneClickTrailers)")

    for keymap_path in keymap_paths:
        if not setting_value:
            restore_from_backup(keymap_path)
            continue
        make_backup(keymap_path)
        tree = ET.parse(keymap_path)
        root = tree.getroot()

        def has_play_trailer_tag(tag):
            return tag.text == "RunScript(script.fentastic.helper, mode=play_trailer)"

        play_pause_tags = root.findall(".//play_pause[@mod='longpress']")
        t_key_tags = root.findall(".//t")
        global_tag = root.find("global") or ET.SubElement(root, "global")
        keyboard_tag = global_tag.find("keyboard") or ET.SubElement(global_tag, "keyboard")

        if setting_value:
            if t_key_tags:
                t_key_tags[0].text = "RunScript(script.fentastic.helper, mode=play_trailer)"
                for tag in t_key_tags[1:]:
                    keyboard_tag.remove(tag)
            else:
                ET.SubElement(keyboard_tag, "t").text = "RunScript(script.fentastic.helper, mode=play_trailer)"

            if play_pause_tags:
                play_pause_tags[0].text = "RunScript(script.fentastic.helper, mode=play_trailer)"
                for tag in play_pause_tags[1:]:
                    keyboard_tag.remove(tag)
            else:
                ET.SubElement(keyboard_tag, "play_pause", mod="longpress").text =\
                    "RunScript(script.fentastic.helper, mode=play_trailer)"
        else:
            for tag_list in [play_pause_tags, t_key_tags]:
                for tag in tag_list:
                    if has_play_trailer_tag(tag):
                        keyboard_tag.remove(tag)

        xml_string = ET.tostring(root, encoding="utf-8").decode("utf-8")
        pretty_xml = minidom.parseString(xml_string).toprettyxml(indent="  ")
        pretty_xml = "\n".join(line for line in pretty_xml.split("\n") if line.strip())

        with xbmcvfs.File(keymap_path, "w") as xml_file:
            xml_file.write(pretty_xml)

    xbmc.executebuiltin("Action(reloadkeymaps)")
