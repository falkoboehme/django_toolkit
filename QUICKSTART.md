# Django Toolkit Quickstart (alle Features)

Diese Anleitung zeigt ein vollständiges Setup, damit du **alle Kernfeatures** von `django_toolkit` nutzen kannst:

- generische CRUD-Views + Tabellen
- Karten-/Detail-Rendering über `Meta.cards`
- Auto-Creator (URLs, Views, API, Serializer, Menu, Admin, Settings)
- Request-basiertes Queryset-Filtering (`for_request`)
- API mit DRF + JWT + Swagger v2/v3
- Berechtigungsprüfung für WebGUI + API
- Custom `User`/`Group` auf Basis `DTUser`/`DTGroup`

## TL;DR: Was ist manuell, was macht der Auto-Creator?

Du hast recht: **der Großteil wird automatisch erstellt**.

### Manuell nötig (einmalig)

- Pakete installieren
- `INSTALLED_APPS` + Basis-Settings setzen
- `AUTH_USER_MODEL` konfigurieren (wenn du `DTUser` nutzt)
- eigene Modelle mit `@model_auto_creator()` markieren
- optional: `user.apps.UserConfig.ready()` Patch, wenn eigenes `Group.permissions.related_name` verwendet wird

### Automatisch (bei `DEBUG=True` und aktiven `DT_AUTO_CREATE_*` Flags)

- DT-Settings-Blöcke ergänzen
- `menu.py` erzeugen/ergänzen
- `request_based_queryset.py` (Projekt + Apps) erzeugen/ergänzen
- GUI-URLs (Projekt + Apps) ergänzen
- API-URLs (Projekt + Apps) ergänzen
- Views, Tables, Admin für registrierte Modelle erzeugen/ergänzen
- API-Views, API-Serializer, Nested-Serializer für registrierte Modelle erzeugen/ergänzen

### Wichtig

- Der Auto-Creator ist auf **Sync fehlender Bausteine** ausgelegt, nicht auf hartes Überschreiben bestehender Business-Logik.
- In Production (`DEBUG=False`) läuft die Auto-Synchronisierung nicht.

## 1) Voraussetzungen

- Python 3.10+
- Django-Projekt vorhanden
- Empfohlene Pakete für **vollen** Funktionsumfang:

```bash
pip install django django-tables2 django-filter python-decouple djangorestframework djangorestframework-simplejwt drf-yasg drf-spectacular drf-spectacular-sidecar
```

Wenn du lokal am Toolkit entwickelst:

```bash
pip install -e ../django_toolkit
```

---

## 2) `settings.py` einrichten

### 2.1 Imports

```python
from pathlib import Path
from decouple import config
import os
import sys
```

### 2.2 DT-Konfiguration

```python
DT_ENVIRONMENT = str(config('DT_ENVIRONMENT', default='production', cast=str)).strip().lower()
DEBUG = DT_ENVIRONMENT == 'development'

if DEBUG:
    DJANGO_TOOLKIT_PATH = BASE_DIR.parent / 'django_toolkit'
    if DJANGO_TOOLKIT_PATH.exists():
        sys.path.insert(0, str(DJANGO_TOOLKIT_PATH))

DT_PROJECT_NAME = config('DT_PROJECT_NAME', default='My Project', cast=str)
DT_PROJECT_VERSION = config('DT_PROJECT_VERSION', default='0.1', cast=str)
DT_DISPLAY_NONE = config('DT_DISPLAY_NONE', default='—', cast=str)

DT_LOGIN_REQUIRED = config('DT_LOGIN_REQUIRED', default=True, cast=bool)

DT_ITEMS_PER_PAGE_DEFAULT = config('DT_ITEMS_PER_PAGE_DEFAULT', default=25, cast=int)
DT_ITEMS_PER_PAGE_MAX = config('DT_ITEMS_PER_PAGE_MAX', default=100, cast=int)

DT_AUTO_CREATE_API = DT_ENVIRONMENT == 'development' and config('DT_AUTO_CREATE_API', default=True, cast=bool)
DT_AUTO_CREATE_VIEWS = DT_ENVIRONMENT == 'development' and config('DT_AUTO_CREATE_VIEWS', default=True, cast=bool)
DT_AUTO_CREATE_MENU = DT_ENVIRONMENT == 'development' and config('DT_AUTO_CREATE_MENU', default=True, cast=bool)
DT_AUTO_CREATE_ADMIN_AREA = DT_ENVIRONMENT == 'development' and config('DT_AUTO_CREATE_ADMIN_AREA', default=True, cast=bool)

DT_USER_BASED_QUERYSET_CLASS = config(
    'DT_USER_BASED_QUERYSET_CLASS',
    default='my_project.request_based_queryset.ProjectRequestBasedQueryset',
    cast=str,
)
DT_USER_BASED_QUERYSET_DEFAULT = config('DT_USER_BASED_QUERYSET_DEFAULT', default='none', cast=str)

DATETIME_FORMAT = config('DT_DATETIME_FORMAT', default='Y-m-d H:i:s', cast=str)
DATE_FORMAT = config('DT_DATE_FORMAT', default='Y-m-d', cast=str)
TIME_FORMAT = config('DT_TIME_FORMAT', default='H:i:s', cast=str)

# Wichtig für eigenes Group-Modell
DT_GROUP_RELATED_NAME_FOR_PERMISSION = config('DT_GROUP_RELATED_NAME_FOR_PERMISSION', default='dtgroup', cast=str)
```

### 2.3 INSTALLED_APPS

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django_tables2',
    'django_filters',
    'rest_framework',
    'drf_yasg',
    'drf_spectacular',
    'drf_spectacular_sidecar',

    'django_toolkit',

    # Deine Apps
    'training',
    'user.apps.UserConfig',
]
```

### 2.4 Auth + Login

```python
AUTH_USER_MODEL = 'user.User'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'
```

### 2.5 Static (für Toolkit CSS/Icons)

```python
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'static'
```

### 2.6 Logging (empfohlen)

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'loggers': {
        'toolkit': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}
```

---

## 3) Projekt-URLs einrichten (nur falls nicht bereits auto-generiert)

In `my_project/urls.py`:

```python
from django.contrib import admin
from django.urls import path, include
from django_toolkit.views import HomeView, UserLoginView, UserLogoutView
from django_toolkit.api.views import APIRootView, DocsView, TokenAuthView
from django_toolkit.api.swagger import schema_view
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    # API
    path('api/', APIRootView.as_view(), name='api-root'),
    path('api/docs/', DocsView.as_view(), name='api-docs'),
    path('api/token/', TokenAuthView.as_view(), name='token-obtain-pair'),

    path('api/docs/swagger-v2/', schema_view.with_ui('swagger', cache_timeout=86400), name='api-swagger-v2'),
    path('api/docs/swagger-v3/', SpectacularSwaggerView.as_view(url_name='api-swagger-v3-download'), name='api-swagger-v3'),
    path('api/docs/swagger-v3/download/', SpectacularAPIView.as_view(), name='api-swagger-v3-download'),
    path('api/docs/swagger-v3/redoc/', SpectacularRedocView.as_view(url_name='api-swagger-v3-download'), name='api-swagger-v3-redoc'),

    # App APIs
    path('api/user/', include('user.api.urls')),
    path('api/training/', include('training.api.urls')),

    # GUI
    path('', HomeView.as_view(), name='home'),
    path('login', UserLoginView.as_view(), name='login'),
    path('logout', UserLogoutView.as_view(), name='logout'),

    path('user/', include('user.urls')),
    path('training/', include('training.urls')),
    path('admin/', admin.site.urls),
]
```

---

## 4) Custom `User` + `Group` für volle Permissions-/Menu-Features

### 4.1 `user/models/group.py`

```python
from django_toolkit.models import DTGroup
from django_toolkit.auto_creator import model_auto_creator

@model_auto_creator()
class Group(DTGroup):
    pass
```

### 4.2 `user/models/user.py`

```python
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_toolkit.models import DTUser
from django_toolkit.auto_creator import model_auto_creator
from .group import Group

@model_auto_creator()
class User(DTUser):
    groups = models.ManyToManyField(
        to=Group,
        blank=True,
        related_name='user',
        verbose_name=_('Groups'),
        help_text=_('The groups this user belongs to. A user will get all permissions granted to each of their groups.'),
    )
```

### 4.3 Backend-Patch für eigenes Group-`related_name`

In `user/apps.py`:

```python
from django.apps import AppConfig

class UserConfig(AppConfig):
    name = 'user'

    def ready(self):
        from django.contrib.auth.models import Permission
        from django.contrib.auth.backends import ModelBackend
        from django.conf import settings

        def _get_group_permissions(self, user_obj):
            group_related_name = getattr(settings, 'DT_GROUP_RELATED_NAME_FOR_PERMISSION', 'dtgroup')
            group_filter = {f"{group_related_name}__in": user_obj.groups.all()}
            return Permission.objects.filter(**group_filter)

        ModelBackend._get_group_permissions = _get_group_permissions  # type: ignore
```

Ohne diesen Patch schlägt `has_perm()`/`get_all_permissions()` bei Custom-`Group` häufig fehl.

---

## 5) Request-basiertes Queryset-Filtering aktivieren

### 5.1 App-spezifische Filterklassen

`training/request_based_queryset.py`

```python
from django_toolkit.models import DTRequestBasedQueryset

class TrainingRequestBasedQueryset(DTRequestBasedQueryset):
    def training_sport(self, queryset, request):
        return queryset
```

`user/request_based_queryset.py`

```python
from django_toolkit.models import DTRequestBasedQueryset

class UserRequestBasedQueryset(DTRequestBasedQueryset):
    def user_group(self, queryset, request):
        return queryset.filter(pk__in=request.user.groups.values_list('pk', flat=True))
```

### 5.2 Projektweite Aggregation

`my_project/request_based_queryset.py`

```python
from django_toolkit.models import DTRequestBasedQueryset
from training.request_based_queryset import TrainingRequestBasedQueryset
from user.request_based_queryset import UserRequestBasedQueryset

class ProjectRequestBasedQueryset(
    TrainingRequestBasedQueryset,
    UserRequestBasedQueryset,
    DTRequestBasedQueryset,
):
    pass
```

Alle Toolkit-Querysets laufen dann über `Model.objects.for_request(request)`.

---

## 6) Modelle registrieren (Auto-Creator)

Beispiel:

```python
from django.db import models
from django_toolkit.models import DTHistoryChangeLoggingModel
from django_toolkit.auto_creator import model_auto_creator

@model_auto_creator()
class Exercise(DTHistoryChangeLoggingModel):
    name = models.CharField(max_length=100)

    class Meta(DTHistoryChangeLoggingModel.Meta):
        base_url = 'exercises'
        verbose_name = 'Exercise'
        verbose_name_plural = 'Exercises'
```

Wenn `DEBUG=True` und Auto-Create-Flags aktiv sind, erzeugt/synchronisiert das Toolkit automatisch:

- app URLs
- Views
- Admin
- Tables
- API URLs
- API Serializer + Nested Serializer
- API ViewSets
- `menu.py`
- `request_based_queryset.py`
- DT-Settings-Block

---

## 7) API-Feature-Setup (inkl. Nested FK + M2M Write)

### 7.1 Serializer

```python
from rest_framework import serializers
from django_toolkit.api.serializers import DTAPISerializer
from .nested_serializers import NestedSportSerializer
from ...models import Exercise

class ExerciseSerializer(DTAPISerializer):
    url = serializers.HyperlinkedIdentityField(view_name='training-api:exercise-detail')
    sport = NestedSportSerializer()  # write + read

    class Meta(DTAPISerializer.Meta):
        model = Exercise
        fields = '__all__'
```

`DTAPINestedSerializer` kann bei Foreign Keys sowohl `id` als auch Dict-Filter auflösen, z. B.:

```json
{
  "sport": {"name": "Volleyball"},
  "name": "Pritschen",
  "description": "Technik"
}
```

### 7.2 ViewSet

```python
from django_toolkit.api.views import DTAPIViewSet
from ..models import Exercise
from .serializers import ExerciseSerializer

class ExerciseViewSet(DTAPIViewSet):
    model = Exercise
    serializer_class = ExerciseSerializer
```

---

## 8) Menü aktivieren

`my_project/menu.py`

```python
from django_toolkit.template_context.menu_entry import MenuEntry
from training.models import Exercise, Sport
from user.models import Group, User, UserProfile


def get_side_menu_items(request):
    return [
        MenuEntry(title='Home', url='/', view_permission=True),
        MenuEntry(title='Training', is_header=True, view_permission=True),
        MenuEntry(model=Exercise, request=request),
        MenuEntry(model=Sport, request=request),
        MenuEntry(title='User', is_header=True, view_permission=True),
        MenuEntry(model=Group, request=request),
        MenuEntry(model=User, request=request),
        MenuEntry(model=UserProfile, request=request),
    ]
```

---

## 9) Datenbank + Start

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Optional (Produktion):

```bash
python manage.py collectstatic
```

---

## 10) Feature-Checkliste

Wenn alles korrekt eingerichtet ist, hast du:

- Login/Logout + Home-View
- generische CRUD-GUI für registrierte Modelle
- Sortierung/Filter/Pagination in Tabellen
- Karten-Rendering aus `Meta.cards`
- Rechteprüfung in GUI (`PermissionRequiredMixin`) und API (`CheckPermissionMixin`)
- API Root + JWT + Swagger v2/v3
- Nested FK-Write und M2M-Write in Serializern
- Request-basiertes Queryset-Filtering pro Modell
- Auto-Creator-Synchronisierung im Dev-Modus

---

## Häufige Stolpersteine

1. **`Group`/Permissions-Fehler bei `has_perm()`**  
   `User.groups` zeigt auf Custom-Group, aber Backend ist nicht angepasst → `ready()`-Patch in `user/apps.py` prüfen.

2. **Keine Auto-Generierung passiert**  
   `DEBUG=False` oder Auto-Flags deaktiviert.

3. **Menü ist leer**  
   `menu.py` fehlt oder `request.user.all_permissions` liefert nicht die erwarteten Rechte.

4. **API Nested FK-POST schlägt fehl**  
   FK-Feld im Serializer ist `read_only=True` oder übergebener Dict-Filter findet kein Objekt.

---

## Weiterführende Doku

- `README.md`
- `FEATURES.md`
- `AUTOREGISTER.md`
- `CARD_SYSTEM.md`
- `HTML_COMPONENTS.md`
