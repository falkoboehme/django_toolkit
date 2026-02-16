from ..functions.files import get_project_name, insert_lines_in_file

class SettingsCreatorMixin:
    """Handles Settings creation and synchronization"""

    settings_path = f"{get_project_name()}/settings.py"
    dt_settings_header = [
        "",
        "",
        "# =============================================================================",
        "# Django Toolkit Configuration (DT_)",
        "# =============================================================================",
    ]
    dt_settings_lines = [
        "DEBUG = config('DT_DEBUG', default=False, cast=bool)",
        "DT_TOOLKIT_DEVELOPMENT_MODE = config('DT_TOOLKIT_DEVELOPMENT_MODE', default=False, cast=bool)",
        "DT_PROJECT_NAME = config('DT_PROJECT_NAME', default='My Project', cast=str)",
        "DT_PROJECT_VERSION = config('DT_PROJECT_VERSION', default='0.1', cast=str)",
        "DT_DISPLAY_NONE = config('DT_DISPLAY_NONE', default='—', cast=str)",
        "DT_ITEMS_PER_PAGE_MAX = config('DT_ITEMS_PER_PAGE_MAX', default=100, cast=int)",
        "DT_ITEMS_PER_PAGE_DEFAULT = config('DT_ITEMS_PER_PAGE_DEFAULT', default=25, cast=int)",
    ]
    dt_settings_end_anchor = "# End of Django Toolkit settings (auto-generated, do not edit manually)"
    

    def _auto_create_stettings(self) -> set:
        """Auto-sync settings. Returns list of modified files."""
        files = set()
        
        # Add Header
        file = insert_lines_in_file(
            file_path=self.settings_path,
            anchor="SECRET_KEY =",
            lines_to_insert=self.dt_settings_header,
            check_as_block=True,
        )
        files.add(file) if file else None

        # Add end anchor if not exists
        file = insert_lines_in_file(
            file_path=self.settings_path,
            anchor="\n".join(self.dt_settings_header),
            lines_to_insert=[self.dt_settings_end_anchor],
        )
        files.add(file) if file else None

        # Add DT_ settings lines (if any)
        for line in self.dt_settings_lines:
            file = self._add_configuration_in_settings(line)
            files.add(file) if file else None

        # Add Development Mode settings lines (if any)
        file = insert_lines_in_file(
            file_path=self.settings_path,
            anchor=self.dt_settings_end_anchor,
            lines_to_insert=[
                "",
                "",
                "if DT_TOOLKIT_DEVELOPMENT_MODE:",
                "    # Add django_toolkit to path for direct development (no reinstall needed)",
                "    DJANGO_TOOLKIT_PATH = BASE_DIR.parent / 'django_toolkit'",
                "    if DJANGO_TOOLKIT_PATH.exists():",
                "        sys.path.insert(0, str(DJANGO_TOOLKIT_PATH))",
                "        print(f'Using local django_toolkit from: {DJANGO_TOOLKIT_PATH}')",
            ],
            position="before",
            check_as_block=True,
        )
        files.add(file) if file else None
    
        return files


    def _add_configuration_in_settings(self, line: str):
        """Check if a specific setting is already defined in settings.py"""
        insert_lines_in_file(
            file_path=self.settings_path,
            anchor=self.dt_settings_end_anchor,
            lines_to_insert=[line],
            position="before",
        )
