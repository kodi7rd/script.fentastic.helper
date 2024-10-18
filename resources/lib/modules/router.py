import sys
from urllib.parse import parse_qsl

def routing():
    """
    Routes requests based on the provided mode parameter from the command line arguments.

    Parses the mode and executes the corresponding function from the appropriate module.

    Uses a caching mechanism to improve performance by storing imported modules.

    Raises:
        ValueError: If the mode is unknown or if required parameters are missing.
    """
    # Parse command line parameters
    params = dict(parse_qsl(sys.argv[1], keep_blank_values=True))
    _get = params.get
    mode = _get("mode", "check_for_update")

    # Dictionary for caching imported modules
    module_cache = {}

    # Function to safely import and call the appropriate function, using caching
    def handle_import(module_name, function_name, *args):
        """
        Import a module and retrieve a specified function, caching the module
        to avoid re-importing it on subsequent calls.

        Args:
            module_name (str): The name of the module to import.
            function_name (str): The name of the function to retrieve from the module.
            *args: Additional arguments to pass to the function.

        Returns:
            The result of the function call.
        """
        # Check if the module is already cached
        if module_name not in module_cache:
            # Import the module and cache it
            module_cache[module_name] = __import__(module_name, fromlist=[function_name])
        module = module_cache[module_name]
        func = getattr(module, function_name)
        return func(*args)

    # Dictionary mapping modes to their corresponding actions
    mode_actions = {
        "widget_monitor": lambda: handle_import("modules.widget_utils", "widget_monitor", params.get("list_id")),
        "check_for_update": lambda: handle_import("modules.version_monitor", "check_for_update", _get("skin_id")),
        "check_for_profile_change": lambda: handle_import("modules.version_monitor", "check_for_profile_change", _get("skin_id")),
        "manage_widgets": lambda: handle_import("modules.cpath_maker", "CPaths", _get("cpath_setting")).manage_widgets(),
        "manage_main_menu_path": lambda: handle_import("modules.cpath_maker", "CPaths", _get("cpath_setting")).manage_main_menu_path(),
        "starting_widgets": lambda: handle_import("modules.cpath_maker", "starting_widgets"),
        "remake_all_cpaths": lambda: handle_import("modules.cpath_maker", "remake_all_cpaths"),
        "search_input": lambda: handle_import("modules.search_utils", "SPaths").search_input(),
        "remove_all_spaths": lambda: handle_import("modules.search_utils", "SPaths").remove_all_spaths(),
        "re_search": lambda: handle_import("modules.search_utils", "SPaths").re_search(),
        "open_search_window": lambda: handle_import("modules.search_utils", "SPaths").open_search_window(),
        "set_api_key": lambda: handle_import("modules.MDbList", "set_api_key"),
        "delete_all_ratings": lambda: handle_import("modules.MDbList", "MDbListAPI").delete_all_ratings(),
        "set_image": lambda: handle_import("modules.custom_actions", "set_image"),
        "modify_keymap": lambda: handle_import("modules.custom_actions", "modify_keymap"),
        "play_trailer": lambda: handle_import("modules.MDbList", "play_trailer"),
        "fix_black_screen": lambda: handle_import("modules.custom_actions", "fix_black_screen"),
    }

    # Execute the corresponding action based on the mode
    action = mode_actions.get(mode)
    if action:
        return action()
    else:
        raise ValueError(f"Unknown mode: {mode}")
