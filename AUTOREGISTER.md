# Auto-Registration System - Verwendungsbeispiele

## 1. Model definieren mit Auto-Registration

```python
# models.py
from django.db import models
from django_toolkit.autoregister import auto_register_model

@auto_register_model()
class MyModel(models.Model):
    name = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
```

## 2. Mit benutzerdefinierten Optionen

```python
@auto_register_model(
    list_display=['name', 'created', 'is_active'],
    search_fields=['name', 'description'],
    list_filter=['created', 'is_active'],
    auto_urls=True,
    auto_admin=True
)
class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
```

## 3. URLs automatisch generieren

```python
# urls.py (Hauptprojekt)
from django.urls import path, include
from django_toolkit.autoregister import ModelRegistry

urlpatterns = [
    # ... andere URLs
    
    # Automatisch generierte URLs für alle registrierten Models
    *ModelRegistry.get_urls(),
]
```

## 4. Admin automatisch registrieren

```python
# admin.py oder in AppConfig.ready()
from django.contrib import admin
from django_toolkit.autoregister import ModelRegistry

# Alle registrierten Models automatisch im Admin registrieren
for model, admin_class in ModelRegistry.get_admin_classes().items():
    admin.site.register(model, admin_class)
```

## 5. Ohne Auto-URLs oder Auto-Admin

```python
@auto_register_model(
    auto_urls=False,  # Keine automatischen URLs
    auto_admin=False  # Kein automatisches Admin
)
class InternalModel(models.Model):
    # Wird nur registriert, aber keine URLs/Admin generiert
    pass
```

## Wie es funktioniert:

1. **Decorator wird beim Import ausgeführt**: Sobald Python die Datei lädt, wird der Decorator aufgerufen
2. **Model wird in Registry gespeichert**: Das Model wird in einer zentralen Registry mit allen Optionen gespeichert
3. **URLs/Admin werden generiert**: Beim Start der App werden aus der Registry automatisch URLs und Admin-Klassen generiert
4. **Keine Dateiänderungen nötig**: Alles passiert zur Laufzeit, keine Dateien werden modifiziert

## Vorteile:

- ✅ Keine Dateimodifikationen
- ✅ Sauber und testbar
- ✅ Einfach zu deaktivieren
- ✅ Konfigurierbar per Model
- ✅ Zentrale Kontrolle über alle Models
- ✅ Funktioniert mit Django's Lifecycle

## Weitere Möglichkeiten:

```python
# Alle registrierten Models abrufen
all_models = ModelRegistry.get_all_models()

# Eigene Logik für registrierte Models
for model in all_models:
    print(f"Registered: {model._meta.label}")
```
