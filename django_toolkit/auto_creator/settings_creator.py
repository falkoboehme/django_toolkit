from ..functions.files import get_project_name, insert_lines_in_file, insert_line_in_file

class SettingsCreatorMixin:
    """Handles Settings creation and synchronization"""

    project_name = get_project_name()
    settings_path = f"{project_name}/settings.py"
    dt_settings_header = [
        "",
        "",
        "# =============================================================================",
        "# Django Toolkit Configuration (DT_)",
        "# =============================================================================",
    ]
    dt_settings_lines = [
        "DT_ENVIRONMENT = str(config('DT_ENVIRONMENT', default='production', cast=str)).strip().lower()",
        "DEBUG = DT_ENVIRONMENT == 'development'",
        "DT_LOGIN_REQUIRED = config('DT_LOGIN_REQUIRED', default=True, cast=bool)",
        "DATETIME_FORMAT = config('DT_DATETIME_FORMAT', default='Y-m-d H:i:s', cast=str)",
        "DATE_FORMAT = config('DT_DATE_FORMAT', default='Y-m-d', cast=str)",
        "TIME_FORMAT = config('DT_TIME_FORMAT', default='H:i:s', cast=str)",
        "DT_PROJECT_NAME = config('DT_PROJECT_NAME', default='My Project', cast=str)",
        "DT_PROJECT_VERSION = config('DT_PROJECT_VERSION', default='0.1', cast=str)",
        "DT_AUTO_CREATE_API = DT_ENVIRONMENT == 'development' and config('DT_AUTO_CREATE_API', default=True, cast=bool)",
        "DT_AUTO_CREATE_VIEWS = DT_ENVIRONMENT == 'development' and config('DT_AUTO_CREATE_VIEWS', default=True, cast=bool)",
        "DT_AUTO_CREATE_MENU = DT_ENVIRONMENT == 'development' and config('DT_AUTO_CREATE_MENU', default=True, cast=bool)",
        "DT_AUTO_CREATE_ADMIN_AREA = DT_ENVIRONMENT == 'development' and config('DT_AUTO_CREATE_ADMIN_AREA', default=True, cast=bool)",
        f"DT_USER_BASED_QUERYSET_CLASS = config('DT_USER_BASED_QUERYSET_CLASS', default='{project_name}.request_based_queryset.ProjectRequestBasedQueryset', cast=str)",
        "DT_USER_BASED_QUERYSET_DEFAULT = config('DT_USER_BASED_QUERYSET_DEFAULT', default='none', cast=str)",
        "DT_DISPLAY_NONE = config('DT_DISPLAY_NONE', default='—', cast=str)",
        "DT_FORM_TEXTAREA_SIZE = config('DT_FORM_TEXTAREA_SIZE', default=4, cast=int)",
        "DT_FORM_SELECT_MULTIPLE_SIZE = config('DT_FORM_SELECT_MULTIPLE_SIZE', default=8, cast=int)",
        "DT_FORM_SELECT_SEARCH_LIMIT = config('DT_FORM_SELECT_SEARCH_LIMIT', default=10, cast=int)",
        "DT_ITEMS_PER_PAGE_MAX = config('DT_ITEMS_PER_PAGE_MAX', default=100, cast=int)",
        "DT_ITEMS_PER_PAGE_DEFAULT = config('DT_ITEMS_PER_PAGE_DEFAULT', default=25, cast=int)",
        "DT_GROUP_RELATED_NAME_FOR_PERMISSION = config('DT_GROUP_RELATED_NAME_FOR_PERMISSION', default='dtgroup', cast=str)",
    ]
    dt_settings_end_anchor = "# End of Django Toolkit settings (auto-generated, do not edit manually)"
    

    def _auto_create_stettings(self) -> set:
        """Auto-sync settings. Returns list of modified files."""
        files = set()

        # Ensure required imports for toolkit development mode block
        file = insert_line_in_file(
            file_path=self.settings_path,
            anchor="from pathlib import Path",
            line_to_insert="import os",
            position="after",
            check_string="import os",
        )
        files.add(file) if file else None

        file = insert_line_in_file(
            file_path=self.settings_path,
            anchor="from pathlib import Path",
            line_to_insert="import sys",
            position="after",
            check_string="import sys",
        )
        files.add(file) if file else None
        
        # Add Header
        file = insert_lines_in_file(
            file_path=self.settings_path,
            anchor="SECRET_KEY =",
            lines_to_insert=self.dt_settings_header,
            check_as_block=True,
        )
        files.add(file) if file else None

        # Add end anchor if not exists
        file = insert_line_in_file(
            file_path=self.settings_path,
            anchor="\n".join(self.dt_settings_header),
            line_to_insert=self.dt_settings_end_anchor,
            check_string=self.dt_settings_end_anchor,
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
                "if DEBUG:",
                "    # Add django_toolkit to path for direct development (no reinstall needed)",
                "    DJANGO_TOOLKIT_PATH = BASE_DIR.parent / 'django_toolkit'",
                "    if DJANGO_TOOLKIT_PATH.exists():",
                "        sys.path.insert(0, str(DJANGO_TOOLKIT_PATH))",
                "        if os.environ.get('RUN_MAIN') == 'true':",
                "            print(f'Using local django_toolkit from: {DJANGO_TOOLKIT_PATH}')",
            ],
            position="before",
            check_as_block=True,
        )
        files.add(file) if file else None

        # Add logging configuration for django_toolkit
        file = insert_lines_in_file(
            file_path=self.settings_path,
            anchor=self.dt_settings_end_anchor,
            lines_to_insert=[
                "LOGGING = {",
                "    'version': 1,",
                "    'disable_existing_loggers': False,",
                "    'handlers': {",
                "        'console': {",
                "            'class': 'logging.StreamHandler',",
                "            'formatter': 'standard',",
                "        },",
                f"        'file': {{",
                f"            'class': 'django_toolkit.functions.logging_handler.DTProjectDailyFileHandler',",
                f"            'filename': str(BASE_DIR / 'logs' / '{self.project_name}.log'),",
                f"            'formatter': 'standard',",
                f"            'when': 'midnight',",
                f"            'interval': 1,",
                f"            'backupCount': 100,",
                f"            'encoding': 'utf-8',",
                f"        }},",
                "    },",
                "    'formatters': {",
                "        'standard': {",
                "            'format' : \"%(asctime)s [%(levelname)s] [%(name)s] (%(module)s:%(lineno)s): %(message)s\",",
                "        },",
                "    },",
                "    'loggers': {",
                "        'toolkit': {",
                "            'handlers': ['console'],",
                "            'level': 'INFO',",
                "        },",
                "    },",
                "}",
            ],
            position="before",
            check_as_block=True,
        )
        files.add(file) if file else None
    
        return files


    def _add_configuration_in_settings(self, line: str):
        """Insert setting line if the setting key is not already defined in settings.py."""
        setting_key = line.split("=", 1)[0].strip()
        check_string = f"{setting_key} ="
        return insert_line_in_file(
            file_path=self.settings_path,
            anchor=self.dt_settings_end_anchor,
            line_to_insert=line,
            position="before",
            check_string=check_string,
        )
