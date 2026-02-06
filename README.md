# Django Toolkit

Ein wiederverwendbares Django-Paket mit hilfreichen Komponenten und Utilities.

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
