from xbmc import executebuiltin, getInfoLabel

def person_search(params):
    """
    Executes a person search within the Kodi plugin 'plugin.video.twilight' using the provided query parameter.

    Args:
        params (dict): A dictionary containing 'query' as a key with the search term as the value.

    Raises:
        ValueError: If the 'query' parameter is missing or empty.

    Example:
        person_search({"query": "John Doe"})
    """
    query = params.get("query", "")
    if not query:
        raise ValueError("Query parameter is missing or empty.")
    return executebuiltin(f"RunPlugin(plugin://plugin.video.twilight/?mode=person_search_choice&query={query})")

def extras(params):
    """
    Executes an action based on extra parameters retrieved from a property in the current Kodi ListItem.
    Args:
        params (dict): A dictionary containing parameters (unused in this function).
    Raises:
        ValueError: If the extra parameters are not found.

    Example:
        extras({})
    """
    extras_params = getInfoLabel("ListItem.Property(twilight.extras_params)")
    if not extras_params:
        raise ValueError("No extras params found in twilight.extras_params.")
    return executebuiltin(f"RunPlugin({extras_params})")
