# Card System - Django Native Lösung

## Übersicht

Das neue Card-System arbeitet direkt mit Django Forms und Models und generiert automatisch Card-Layouts für Detail-, Create- und Update-Views.

## Verwendung

### Beispiel 1: Automatische Card-Generierung

```python
from django_toolkit.views import DTDetailView, DTCreateView, DTUpdateView

class UserDetailView(DTDetailView):
    model = User
    # Automatisch: Alle Felder in einer Card

class UserCreateView(DTCreateView):
    model = User
    fields = ['first_name', 'last_name', 'email']
    # Automatisch: Alle Felder in einer Card als Form

class UserUpdateView(DTUpdateView):
    model = User
    fields = ['first_name', 'last_name', 'email']
    # Automatisch: Alle Felder in einer Card als Form
```

### Beispiel 2: Custom Card Layout (empfohlen)

```python
from django_toolkit.cards import Card

class UserDetailView(DTDetailView):
    model = User
    cards_per_row = 2  # Optional: 1-4 cards per row
    card_layout = [
        Card(header='Persönliche Informationen', fields=['first_name', 'last_name', 'email']),
        Card(header='Adresse', fields=['street', 'city', 'zip_code']),
        Card(header='Weitere Infos', fields=['phone', 'website']),
    ]
    # Cards werden automatisch auf 2 Spalten verteilt

# Gleiches Layout funktioniert auch für Create/Update Views:
class UserCreateView(DTCreateView):
    model = User
    card_layout = [
        Card(header='Persönliche Informationen', fields=['first_name', 'last_name', 'email']),
        Card(header='Adresse', fields=['street', 'city', 'zip_code']),
    ]
    # Felder werden als Formular-Inputs gerendert

class UserUpdateView(DTUpdateView):
    model = User
    card_layout = [
        Card(header='Persönliche Informationen', fields=['first_name', 'last_name', 'email']),
        Card(
            header='System Info', 
            fields=['created_at', 'updated_at'],
            read_only=['created_at', 'updated_at']  # Werden angezeigt aber nicht editierbar
        ),
    ]
```

### Beispiel 2b: Dict-Format (backwards compatible)

```python
class UserDetailView(DTDetailView):
    model = User
    card_layout = [
        {'header': 'Persönliche Informationen', 'fields': ['first_name', 'last_name', 'email']},
        {'header': 'Adresse', 'fields': ['street', 'city', 'zip_code']},
    ]
```

### Beispiel 3: Explizite Spalten

```python
from django_toolkit.cards import Card

class UserDetailView(DTDetailView):
    model = User
    
    def get_card_layout(self):
        # Dynamisches Layout basierend auf User-Permissions
        layout = [
            Card(header='Basic Info', fields=['username', 'email'])
        ]
        
        if self.request.user.is_staff:
            layout.append(
                Card(header='Admin Info', fields=['is_active', 'date_joined'])
            
```python
class UserDetailView(DTDetailView):
    model = User
    
    def get_card_layout(self):
        # Dynamisches Layout basierend auf User-Permissions
        layout = [
            {'header': 'Basic Info', 'fields': ['username', 'email']}
        ]
        
        if self.request.user.is_staff:
            layout.append({
                'header': 'Admin Info',
                'fields': ['is_active', 'date_joined']
            })
        
        return layout
```

## Vorteile der neuen Lösung

1. **Django-Native**: Nutzt BoundFields, Forms, Widgets direkt
2. **Weniger Code**: Keine manuelle Row-Erstellung
3. **Automatische Validierung**: Django Form-Validierung funktioniert out-of-the-box
4. **Widget-Unterstützung**: Automatisches Mapping von Django Widgets zu Templates
5. **DRY**: Ein Layout für DetailView und UpdateView
6. **Flexible Spalten**: Cards werden automatisch verteilt
8. **Type-Safe**: Card-Objekte mit IDE-Support und Validierung
7. **User-anpassbar**: Anzahl der Spalten kann pro User konfiguriert werden

## Cards per Row Konfiguration

Die Anzahl der Cards pro Zeile kann auf 3 Ebenen gesteuert werden:

### 1. Global (Settings)
```python
# settings.py oder .env
DT_CARDS_PER_ROW = 2  # Standard: 2 Cards nebeneinander (1-4)
```

### 2. Pro View
```python
class UserDetailView(DTDetailView):
    model = User
    cards_per_row = 3  # Überschreibt Settings für diese View
```

### 3. Pro User (geplant)
```python
# Im User-Profil Model
class UserProfile(models.Model):
    cards_per_row = models.IntegerField(default=2, choices=[(i, i) for i in range(1, 5)])
```

**Priorität**: View-Attribut > User-Profil > Settings Default

## Template-Kompatibilität

Die Templates bleiben kompatibel. `CardRow` hat jetzt Properties, die automatisch von Django Fields gefüllt werden:

- `row.id` → Field ID
- `row.display` → Field Label (verbose_name)
- `row.value` → Field Value
- `row.required` → Field.required
- `row.help` → Field.help_text
- `row.form` → Widget-Typ (automatisch gemappt)
- `row.render_formular` → True für Forms, False für DetailView
- `row.field` → Direkter Zugriff auf BoundField

## Migration von alter zu neuer Lösung

### Alt (manuell):
```python
card = CardTemplate(header="Info")
card.add_row(CardRow(
    id="email",
    display="E-Mail",
    value=user.email,
    form="input_text",
    required=True
))
``` mit Card-Objekten):
```python
from django_toolkit.cards import Card

# In der View:
card_layout = [
    Card(header='Info', fields=['email'])
]
# Fertig! Labels, Widgets, Validierung automatisch.
# + Type Safety, IDE Autocomplete, Validierung zur Definition-Zeit
]
# Fertig! Labels, Widgets, Validierung automatisch.
```
