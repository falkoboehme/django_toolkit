from django.conf import settings

def to_bool(value):
    lowered = str(value).strip().lower()
    mapping = {
        'true': True,
        '1': True,
        'yes': True,
        'ja': True,
        'false': False,
        '0': False,
        'no': False,
        'nein': False,
    }
    return mapping.get(lowered)


def to_number(value):
    value_as_string = str(value).strip()
    if value_as_string == "":
        return None
    try:
        if "." in value_as_string:
            return float(value_as_string)
        return int(value_as_string)
    except (TypeError, ValueError):
        return None


def get_project_module_name() -> str:
    root_urlconf = getattr(settings, "ROOT_URLCONF", "")
    if root_urlconf:
        return root_urlconf.split(".")[0]

    settings_module = getattr(settings, "SETTINGS_MODULE", "") or getattr(settings, "SETTINGS_FILE_PATH", "")
    if settings_module:
        return settings_module.split(".")[0]

    env_settings_module = getattr(settings, "DJANGO_SETTINGS_MODULE", "")
    if env_settings_module:
        return env_settings_module.split(".")[0]

    return settings.BASE_DIR.name