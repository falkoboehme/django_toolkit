
# General
## Database
If you choose PostgreSQL as database backend, you could enable change tracking with the Meta-attribute ```history=True```

## Models
### DTBaseModel
Extends the Meta information of model by:
- history
- read_only
- base_url
- cards
### DTReadOnlyModel
### DTHistoryModel
### DTHistoryChangeLoggingModel
### DTEnumModel
### DTReadOnlyEnumModel


# User management
## Models
### DTUser
### DTGroup

## Custom Group permissions related_name
Wenn ein eigenes `Group`-Modell mit eigenem `permissions.related_name` genutzt wird, muss
`ModelBackend._get_group_permissions` angepasst werden (z. B. in `user.apps.UserConfig.ready`).

Empfohlene Konfiguration in `settings.py`:

```python
DT_GROUP_RELATED_NAME_FOR_PERMISSION = "dtgroup"
```


# Mixins
## Models
### DTModelChangeLoggingMixin
Adds created, created_user, last_updated last_updated_user to a model to track creation and changes


# Templates
You can use the django_toolkit template system which is build on bootstram and HTML-cards