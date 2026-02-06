# Django Toolkit HTML Components

## Bootstrap Components System

Das django_toolkit bietet jetzt ein klassenbasiertes Component-System für Bootstrap Cards, Buttons und Modals.

### Installation

```python
from django_toolkit.html_components import Card, CardColumn, CardRow, Field, Button, Modal
```

### Verwendung

#### Einfaches Beispiel: Button

```python
button = Button(
    name='Speichern',
    href='/save/',
    color='btn-success',
    icon='<i class="bi bi-save"></i>'
)

# In der View
context = {'button': button}

# Im Template
{{ button }}  # oder button.render()
```

#### Modal

```python
modal = Modal(
    title='Bestätigung',
    body='Möchten Sie wirklich löschen?',
    footer='<button class="btn btn-danger">Löschen</button>',
    form_url='/delete/'
)

context = {'modal': modal}
```

#### Card System

```python
# Einzelne Felder erstellen
field1 = Field(
    field_id='email',
    display='E-Mail',
    form='input_text',
    required=True,
    help_text='Ihre E-Mail-Adresse'
)

field2 = Field(
    field_id='name',
    display='Name',
    form='input_text',
    required=True
)

# Card erstellen
card1 = Card(
    header='Benutzerdaten',
    rows=[field1, field2]
)

# Oder Felder nachträglich hinzufügen
card2 = Card(header='Weitere Daten')
card2.add_field(Field('phone', 'Telefon', 'input_text'))

# Spalten erstellen
column1 = CardColumn(cards=[card1])
column2 = CardColumn(cards=[card2])

# Oder nachträglich hinzufügen
column1 = CardColumn()
column1.add_card(card1).add_card(card2)

# Row erstellen (komplettes Layout)
card_row = CardRow(columns=[column1, column2])

# In der View
context = {'card_row': card_row}

# Im Template
{{ card_row }}
```

#### Fluent API

```python
card_row = (
    CardRow()
    .add_column(
        CardColumn()
        .add_card(
            Card(header='User')
            .add_field(Field('email', 'E-Mail', 'input_text'))
            .add_field(Field('name', 'Name', 'input_text'))
        )
        .add_card(
            Card(header='Details')
            .add_field(Field('phone', 'Telefon', 'input_text'))
        )
    )
    .add_column(
        CardColumn()
        .add_card(
            Card(header='Comments')
            .add_field(Field('comment', 'Kommentar', 'textarea'))
        )
    )
)

context = {'cards': card_row}
```

### Integration mit Models

#### Option 1: CardBuilderMixin verwenden (empfohlen)

Das `CardBuilderMixin` ermöglicht es, Cards direkt im Model zu definieren. Die Felder werden automatisch aus den Model-Feldern erstellt:

```python
from django.db import models
from django_toolkit.mixins import CardBuilderMixin
from django_toolkit.html_components import Card, CardColumn, CardRow

class User(CardBuilderMixin, models.Model):
    email = models.EmailField(verbose_name='E-Mail')
    name = models.CharField(max_length=100, verbose_name='Name')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Telefon')
    bio = models.TextField(blank=True, verbose_name='Biografie')
    
    @classmethod
    def get_card_layout(cls):
        return CardRow([
            CardColumn([
                Card('Benutzerdaten', [
                    cls.field('email'),  # Automatisch: 'E-Mail', input_text, required=True
                    cls.field('name')     # Automatisch: 'Name', input_text, required=True
                ])
            ]),
            CardColumn([
                Card('Kontakt', [
                    cls.field('phone')    # Automatisch: 'Telefon', input_text, required=False
                ]),
                Card('Über mich', [
                    cls.field('bio')      # Automatisch: 'Biografie', textarea, required=False
                ])
            ])
        ])

# In der View
cards = User.get_card_layout()
context = {'cards': cards}
```

**Mehrere Felder auf einmal:**

```python
@classmethod
def get_card_layout(cls):
    return CardRow([
        CardColumn([
            Card('Benutzerdaten', cls.fields('email', 'name', 'phone'))
        ])
    ])
```

**Werte überschreiben:**

```python
cls.field('email', form='select')  # Überschreibt den automatisch erkannten Typ
cls.field('name', required=False)  # Überschreibt required
```

#### Option 2: Automatisch aus Meta.cards generieren

Wenn Sie bereits `Meta.cards` definiert haben, kann das Mixin diese automatisch konvertieren:

```python
class User(CardBuilderMixin, models.Model):
    email = models.EmailField(verbose_name='E-Mail')
    name = models.CharField(max_length=100, verbose_name='Name')
    
    class Meta:
        cards = [
            [
                {
                    'header': 'Benutzerdaten',
                    'fields': ['email', 'name']
                }
            ]
        ]

# Automatisch konvertiert zu CardRow
cards = User.get_card_layout()
```

#### Option 3: Ohne Mixin (manuelle Definition)

Die `cards` Meta-Attribute in Models können jetzt auch Component-Objekte zurückgeben:

```python
class MyModel(DTBaseModel):
    class Meta:
        cards = [
            [
                {
                    'header': 'User Data',
                    'fields': ['email', 'name']
                }
            ]
        ]
```

Kann umgewandelt werden zu:

```python
@classmethod
def get_cards(cls):
    return CardRow([
        CardColumn([
            Card('User Data', [
                Field('email', 'E-Mail', 'input_text'),
                Field('name', 'Name', 'input_text')
            ])
        ])
    ])
```

### Verfügbare Field-Typen

- `input_text` - Textfeld
- `input_number` - Zahlenfeld
- `input_checkbox` - Checkbox
- `input_datetime` - Datum/Zeit Picker
- `input_date` - Datums Picker
- `textarea` - Mehrzeiliges Textfeld
- `select` - Dropdown
- `select_search` - Dropdown mit Suche
- `colorfield` - Farbwähler

### Vorteile

1. **Typsicherheit**: Python-Klassen mit klaren Parametern
2. **Wiederverwendbarkeit**: Components können gespeichert und wiederverwendet werden
3. **Fluent API**: Verkettbare Methoden für bessere Lesbarkeit
4. **Template-kompatibel**: Direkt als String in Templates verwendbar
5. **Erweiterbar**: Eigene Component-Klassen können einfach erstellt werden

### Eigene Components erstellen

```python
from django_toolkit.html_components import Component

class MyComponent(Component):
    template_name = 'my_app/my_component.html'
    
    def __init__(self, title, content):
        self.title = title
        self.content = content
    
    def get_context(self):
        return {
            'my_component': {
                'title': self.title,
                'content': self.content
            }
        }
```

## Struktur

Jede Komponente ist in einer eigenen Datei organisiert:

- `base.py` - Basis `Component` Klasse
- `button.py` - Bootstrap Button
- `modal.py` - Bootstrap Modal
- `field.py` - Formularfeld
- `card.py` - Bootstrap Card
- `card_column.py` - Card Spalte
- `card_row.py` - Card Row (komplettes Layout)
