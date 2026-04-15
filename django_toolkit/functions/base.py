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
