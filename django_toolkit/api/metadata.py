from rest_framework.metadata import SimpleMetadata
from rest_framework.fields import ChoiceField, BooleanField, CharField, IntegerField
from django.db.models.fields import NOT_PROVIDED

class Metadata(SimpleMetadata):
    """
    Adds additional data as metadata for OPTIONS-Request
    """
    def get_field_info(self, field):
        field_info = super().get_field_info(field)
        
        # Default values, if defined
        if type(field) in [ChoiceField, BooleanField, CharField, IntegerField]:
            model = field.parent.Meta.model
            model_field = getattr(model, field.field_name)
            if model_field.field.default == NOT_PROVIDED:
                #field_info["default"] = None
                pass
            else:
                field_info["default"] = model_field.field.default
        
        # Choices for content_type
        if field.field_name == "content_type":
            field_info["choices"] = []
            for value, display in field.choices.items():
                field_info["choices"].append(
                    {
                        "value": value,
                        "display_name": display,
                    }
                )
        # elif field.field_name == "db_type":
        #     field_info["choices"] = []
        #     for value, display in DBType.choices:
        #         field_info["choices"].append(
        #             {
        #                 "value": value,
        #                 "display_name": display,
        #             }
        #         )
        
        # elif field.field_name == "db_relation_type":
        #     field_info["valid_choices"] = DBRelations.valid_relations

        return field_info