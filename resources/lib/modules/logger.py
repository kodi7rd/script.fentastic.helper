import xbmc

def logger(heading, function, level=1):
    """
    Logs a message to Kodi's log file with a custom heading and message.

    Args:
        heading (str): The heading or title for the log entry.
        function (str): The content of the log message.
        level (int, optional): The log level (default is 1, for debug/info).

    Example:
        logger("Initialization", "Starting the addon")
    """
    xbmc.log(f"###{heading}###: {function}", level)
