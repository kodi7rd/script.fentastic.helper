import xbmc
import xbmcgui
import xbmcvfs
import sqlite3 as database
from modules import xmls
from urllib.parse import quote
from threading import Thread, Event

# Path settings
settings_path = xbmcvfs.translatePath(
    "special://profile/addon_data/script.fentastic.helper/"
)

spath_database_path = xbmcvfs.translatePath(
    "special://profile/addon_data/script.fentastic.helper/spath_cache.db"
)

search_history_xml = "script-fentastic-search_history"

default_xmls = {
    "search_history": (search_history_xml, xmls.default_history, "SearchHistory")
}

default_path = "addons://sources/video"


class SPaths:
    """Handles search paths and their management in the Kodi environment."""

    def __init__(self, spaths=None):
        self.connect_database()
        self.spaths = spaths if spaths is not None else []
        self.refresh_spaths = False

    def connect_database(self):
        """Establish a connection to the SQLite database and create the table if it doesn't exist."""
        if not xbmcvfs.exists(settings_path):
            xbmcvfs.mkdir(settings_path)
        with database.connect(spath_database_path, timeout=20) as self.dbcon:
            self.dbcur = self.dbcon.cursor()
            self.dbcur.execute(
                "CREATE TABLE IF NOT EXISTS spath (spath_id INTEGER PRIMARY KEY AUTOINCREMENT, spath TEXT)"
            )

    def update_spath_in_database(self, spath, is_addition=True):
        """Update a search path in the database (add or remove)."""
        self.refresh_spaths = True
        if is_addition:
            self.dbcur.execute("INSERT INTO spath (spath) VALUES (?)", (spath,))
        else:
            self.dbcur.execute("DELETE FROM spath WHERE spath = ?", (spath,))
        self.dbcon.commit()

    def is_database_empty(self):
        """Check if the database is empty."""
        self.dbcur.execute("SELECT 1 FROM spath LIMIT 1")
        return self.dbcur.fetchone() is None

    def remove_all_spaths(self):
        """Remove all search paths from the database and reload the skin."""
        dialog = xbmcgui.Dialog()
        title = "FENtastic"
        prompt = "Are you sure you want to clear all search history? Once cleared, these items cannot be recovered. Proceed?"
        self.fetch_all_spaths()
        if dialog.yesno(title, prompt):
            self.refresh_spaths = True
            self.dbcur.execute("DELETE FROM spath")
            self.dbcur.execute("DELETE FROM sqlite_sequence WHERE name='spath'")
            self.dbcon.commit()
            self.make_default_xml()
            Thread(target=self.update_settings_and_reload_skin).start()

    def fetch_all_spaths(self):
        """Fetch all search paths from the database."""
        return self.dbcur.execute(
            "SELECT * FROM spath ORDER BY spath_id DESC"
        ).fetchall()

    def update_settings_and_reload_skin(self):
        """Update settings and reload the Kodi skin."""
        xbmc.executebuiltin("Skin.SetString(SearchInput,)")
        xbmc.executebuiltin("Skin.SetString(SearchInputEncoded,)")
        xbmc.executebuiltin("Skin.SetString(SearchInputTraktEncoded, 'none')")
        xbmc.executebuiltin("Skin.SetString(DatabaseStatus, 'Empty')")
        xbmc.sleep(300)
        xbmc.executebuiltin("ReloadSkin()")
        xbmc.sleep(200)
        xbmc.executebuiltin("SetFocus(27400)")

    def make_search_history_xml(self, active_spaths, event=None):
        """Create or update the search history XML file."""
        if not self.refresh_spaths:
            return
        if not active_spaths:
            self.make_default_xml()
        xml_file = f"special://skin/xml/{search_history_xml}.xml"
        final_format = xmls.media_xml_start.format(main_include="SearchHistory")
        for _, spath in active_spaths:
            body = xmls.history_xml_body.format(spath=spath)
            final_format += body
        final_format += xmls.media_xml_end
        self.write_xml(xml_file, final_format)
        xbmc.executebuiltin("ReloadSkin()")
        if event is not None:
            event.set()

    def write_xml(self, xml_file, final_format):
        """Write the XML data to a specified file."""
        with xbmcvfs.File(xml_file, "w") as f:
            f.write(final_format)

    def make_default_xml(self):
        """Create a default XML file for search history."""
        item = default_xmls["search_history"]
        final_format = item[1].format(includes_type=item[2])
        xml_file = f"special://skin/xml/{item[0]}.xml"
        self.write_xml(xml_file, final_format)

    def check_spath_exists(self, spath):
        """Check if a search path exists in the database."""
        result = self.dbcur.execute(
            "SELECT spath_id FROM spath WHERE spath = ?", (spath,)
        ).fetchone()
        return result[0] if result else None

    def open_search_window(self):
        """Open the search window and update the UI accordingly."""
        if xbmcgui.getCurrentWindowId() == 10000:
            xbmc.executebuiltin("ActivateWindow(1121)")
        if self.is_database_empty():
            self.update_empty_database_ui()
        else:
            self.remake_search_history()
            self.reset_search_ui()

    def update_empty_database_ui(self):
        """Update the UI to reflect an empty database status."""
        xbmc.executebuiltin("Skin.SetString(DatabaseStatus, 'Empty')")
        xbmc.executebuiltin("Skin.SetString(SearchInputTraktEncoded, 'none')")
        xbmc.executebuiltin("ReloadSkin()")
        xbmc.sleep(200)
        xbmc.executebuiltin("SetFocus(27400)")

    def reset_search_ui(self):
        """Reset the search UI elements."""
        xbmc.executebuiltin("Skin.Reset(DatabaseStatus)")
        xbmc.executebuiltin("Skin.SetString(SearchInput,)")
        xbmc.executebuiltin("Skin.SetString(SearchInputEncoded,)")
        xbmc.executebuiltin("Skin.SetString(SearchInputTraktEncoded, 'none')")
        xbmc.executebuiltin("ReloadSkin()")
        xbmc.sleep(200)
        xbmc.executebuiltin("SetFocus(803)")

    def search_input(self, search_term=None):
        """Handle the search input process, including user prompts and database updates."""
        search_term = self.get_search_term(search_term)
        if search_term is None:
            return
        encoded_search_term = quote(search_term)
        if xbmcgui.getCurrentWindowId() == 10000:
            xbmc.executebuiltin("ActivateWindow(1121)")
        existing_spath = self.check_spath_exists(search_term)
        if existing_spath:
            self.update_spath_in_database(search_term, is_addition=False)
        self.update_spath_in_database(search_term, is_addition=True)
        self.update_search_history(encoded_search_term, search_term)

    def get_search_term(self, search_term):
        """Prompt the user for a search term if none is provided."""
        if not search_term or not search_term.strip():
            prompt = "Search" if xbmcgui.getCurrentWindowId() == 10000 else "New Search"
            keyboard = xbmc.Keyboard("", prompt, False)
            keyboard.doModal()
            return keyboard.getText() if keyboard.isConfirmed() else None
        return search_term.strip()

    def update_search_history(self, encoded_search_term, search_term):
        """Update the search history XML and Kodi UI elements."""
        if xbmcgui.getCurrentWindowId() == 10000:
            self.make_search_history_xml(self.fetch_all_spaths())
        else:
            event = Event()
            Thread(
                target=self.make_search_history_xml,
                args=(self.fetch_all_spaths(), event),
            ).start()
            event.wait()
        xbmc.executebuiltin(f"Skin.SetString(SearchInputEncoded,{encoded_search_term})")
        xbmc.executebuiltin(f"Skin.SetString(SearchInputTraktEncoded,{encoded_search_term})")
        xbmc.executebuiltin(f"Skin.SetString(SearchInput,{search_term})")
        xbmc.executebuiltin("SetFocus(2000)")

    def re_search(self):
        """Re-execute a search with the current ListItem label."""
        search_term = xbmc.getInfoLabel("ListItem.Label")
        self.search_input(search_term)

    def remake_search_history(self):
        """Recreate the search history XML from active search paths."""
        self.refresh_spaths = True
        active_spaths = self.fetch_all_spaths()
        if active_spaths:
            self.make_search_history_xml(active_spaths)
        else:
            self.make_default_xml()