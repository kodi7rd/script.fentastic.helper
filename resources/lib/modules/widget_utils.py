import xbmc
import xbmcgui


def widget_monitor(list_id):
    """
    Monitors the widget state and updates the display label based on the current focus and folder path.

    Args:
        list_id (str): The ID of the widget list to monitor.

    Raises:
        ValueError: If the list_id is not 5 characters long.
    """
    if len(list_id) != 5:
        raise ValueError("list_id must be 5 characters long.")

    monitor = xbmc.Monitor()
    window = None

    # Get the delay for updating the widget
    delay = max(float(xbmc.getInfoLabel("Skin.String(category_widget_delay)")) / 1000, 0.75)
    display_delay = xbmc.getInfoLabel("Skin.HasSetting(category_widget_display_delay)") == "True"
    stack_id = list_id + "1"
    poster_toggle, landscape_toggle = True, False

    while not monitor.abortRequested():
        window_id = xbmcgui.getCurrentWindowId()
        if window_id not in [10000, 11121]:
            break

        window = xbmcgui.Window(window_id)
        stack_control = window.getControl(int(stack_id))

        # Collect possible stack label controls
        stack_label_control = next(
            (window.getControl(int(stack_id + str(i))) for i in range(666, 673)
             if window.getControl(int(stack_id + str(i)))), None
        )

        # Shortened wait for abort before focus check
        monitor.waitForAbort(0.25)

        if list_id != str(window.getFocusId()):
            break

        last_path = window.getProperty(f"fentastic.{list_id}.path")
        cpath_path = xbmc.getInfoLabel("ListItem.FolderPath")

        if last_path == cpath_path or xbmc.getCondVisibility("System.HasActiveModalDialog"):
            continue

        switch_widget = True
        countdown = delay

        while not monitor.abortRequested() and countdown >= 0 and switch_widget:
            monitor.waitForAbort(0.25)
            countdown -= 0.25

            # Check conditions to switch the widget
            if any([
                list_id != str(window.getFocusId()),
                last_path == cpath_path,
                xbmc.getInfoLabel("ListItem.FolderPath") != cpath_path,
                xbmc.getCondVisibility("System.HasActiveModalDialog"),
                xbmcgui.getCurrentWindowId() not in [10000, 11121]
            ]):
                switch_widget = False

            if switch_widget:
                widget_label = xbmc.getInfoLabel("ListItem.Label")
                if display_delay:
                    stack_label_control.setLabel(
                        f"Loading [COLOR accent_color][B]{widget_label}[/B][/COLOR] in [B]{countdown:.2f}[/B] seconds"
                    )

        if switch_widget:
            cpath_label = xbmc.getInfoLabel("ListItem.Label")
            stack_label_control.setLabel(cpath_label)
            window.setProperty(f"fentastic.{list_id}.label", cpath_label)
            window.setProperty(f"fentastic.{list_id}.path", cpath_path)
            monitor.waitForAbort(0.2)

            # Wait for the container to finish updating
            update_wait_time = 0
            while xbmc.getCondVisibility(f"Container({stack_id}).IsUpdating") and update_wait_time <= 3:
                monitor.waitForAbort(0.10)
                update_wait_time += 0.10

            monitor.waitForAbort(0.50)

            try:
                stack_control.selectItem(0)
            except Exception as e:
                xbmc.log(f"Error selecting item: {e}", level=xbmc.LOGERROR)
        else:
            stack_label_control.setLabel(window.getProperty(f"fentastic.{list_id}.label"))
            monitor.waitForAbort(0.25)

    # Cleanup
    del monitor
    del window
