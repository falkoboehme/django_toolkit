# Django Toolkit

Ein wiederverwendbares Django-Paket mit hilfreichen Komponenten und Utilities.

## Quickstart

Für ein vollständiges Setup aller Features siehe [QUICKSTART.md](QUICKSTART.md).

## Installation

```bash
pip install django-toolkit
```

### Lokale Installation (Entwicklung)

```bash
# Im editable Mode installieren
pip install -e .
```

## Verwendung

```python
import django_toolkit

# Beispielverwendung hier
```

### Eigenes Group-Modell mit custom related_name für Permissions

Wenn `User.groups` auf ein eigenes `Group`-Modell zeigt und `Group.permissions` ein eigenes `related_name` nutzt,
arbeitet das Django-Standard-`ModelBackend` nicht mehr korrekt mit Gruppenrechten.

Konfiguration in `settings.py`:

```python
DT_GROUP_RELATED_NAME_FOR_PERMISSION = "dtgroup"
```

Patch in `user/apps.py`:

```python
from django.apps import AppConfig


class UserConfig(AppConfig):
    name = 'user'

    # Required to use own Group model with custom related_name for permissions
    def ready(self):
        from django.contrib.auth.models import Permission
        from django.contrib.auth.backends import ModelBackend
        from django.conf import settings

        def _get_group_permissions(self, user_obj):
            group_related_name = getattr(settings, 'DT_GROUP_RELATED_NAME_FOR_PERMISSION', 'dtgroup')
            group_filter = {f"{group_related_name}__in": user_obj.groups.all()}
            return Permission.objects.filter(**group_filter)

        ModelBackend._get_group_permissions = _get_group_permissions    # type: ignore
```

### RequestBasedQueryset (explizit)

Du kannst zentrale, benutzerabhängige Filterregeln pro Modell definieren.
Die Methodennamen folgen dem Schema `app_model` (z. B. `training_sportmodel`).

1. Eigene Filterklasse anlegen:

```python
from django_toolkit.models import RequestBasedQueryset


class ProjectRequestBasedQueryset(RequestBasedQueryset):
    def training_sportmodel(self, queryset, request):
        if request and request.user and request.user.is_superuser:
            return queryset
        return queryset.none()
```

2. In `settings.py` konfigurieren:

```python
DT_USER_BASED_QUERYSET_CLASS = "training_planner.user_based_queryset.ProjectRequestBasedQueryset"
DT_USER_BASED_QUERYSET_DEFAULT = "all"  # "all" oder "empty"
```

3. Bei Bedarf explizit anwenden:

```python
queryset = Sport.for_request(request)
```

Standardzugriffe über `Model.objects...` bleiben unverändert (z. B. im Admin).

Beispiel in einer ListView:

```python
class SportListView(DTListView):
    model = Sport

    def get_queryset(self):
    return Sport.for_request(self.request)
```

Beispiel für ein einzelnes Objekt mit User-Filter:

```python
sport = Sport.for_request(request).get(pk=pk)
```

### Logging (Loggername: toolkit)

Das Paket loggt über den Logger `toolkit`.

```python
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "loggers": {
        "toolkit": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
```

## Entwicklung

### Package bauen

```bash
python -m build
```

### Package hochladen (zu PyPI)

```bash
python -m twine upload dist/*
```

## Projekt-Struktur

```
django_toolkit/
    __init__.py         # Hauptmodul
    models/             # Wiederverwendbare Models
    views/              # Wiederverwendbare Views
    utils/              # Utility-Funktionen
    mixins/             # Django Mixins
```

## Anforderungen

- Python >= 3.8
- Django >= 4.0

## Lizenz

MIT License - siehe [LICENSE](LICENSE) Datei.
