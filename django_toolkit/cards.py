"""
Card Definition Classes for Django Toolkit
"""
from dataclasses import dataclass


@dataclass
class Card:
    """
    Defines a card layout for detail/edit views.
    
    Attributes:
        header: Card header text
        fields: List of model field names to display
        read_only: List of field names that should be read-only (not editable in forms)
    
    Example:
        Card(
            header='Personal Info', 
            fields=['first_name', 'last_name', 'email', 'created_at'],
            read_only=['created_at']  # created_at wird angezeigt, aber nicht editierbar
        )
    """
    header: str
    fields: list[str]
    read_only: list[str] = None
    
    def __post_init__(self):
        """Validate card configuration"""
        if not self.fields:
            raise ValueError(f"Card '{self.header}' must have at least one field")
        if self.read_only is None:
            self.read_only = []
        # Validate read_only fields exist in fields
        for ro_field in self.read_only:
            if ro_field not in self.fields:
                raise ValueError(f"Read-only field '{ro_field}' not in card fields: {self.fields}")
    
    def to_dict(self) -> dict:
        """Convert to dictionary format for backwards compatibility"""
        result = {
            'header': self.header,
            'fields': self.fields,
        }
        if self.read_only:
            result['read_only'] = self.read_only
        if self.column is not None:
            result['column'] = self.column
        return result
    
    def __repr__(self):
        ro_info = f", read_only={self.read_only}" if self.read_only else ""
        return f"Card(header='{self.header}', fields={self.fields}{ro_info})"






# class TemplateCard:   
#     def __init__(
#             self,
#             view,
#             request,
#             instance=None,
#             model=None,
#             fields=[],
#             header=mark_safe('&nbsp;'),
#             td_display_class=None,
#             td_value_class=None,
#             read_only=[],
#             ajax=[],
#             raw_content=None,
#             one_element_per_line=[],
#             extra_fields=[],
#         ):
#         """Class to define the content of a HTML card

#         Args:
#             view (ViewClass): The View-Class to render for (Detail|Update|Create)
#             request (class): The request sent by the browser
#             instance (ModelInstance, optional): The `model_instance` the data belongs to. If not given the model must be given. Required for detail and update. Defaults to None.
#             model (Model, optional): The `model` of the data. Required for add. Defaults to None.
#             fields (list, optional): List with the fields to show in the display order. Defaults to [].
#             header (str, optional): Text to display at the top of the card. Defaults to mark_safe('&nbsp;').
#             td_display_class (str, optional): The classes for the <td>-tag of the values. Defaults to None.
#             td_value_class (str, optional): _description_. Defaults to None.
#             read_only (list, optional): the fields of the list are read-only.
#             ajax (list, optional): AJAX objects to add in this card. Defaults to [].

#         Raises:
#             ImproperlyConfigured: instance or model mus be set
#         """
#         self.view = view
#         self.request = request
#         if not instance and not model:
#             raise ImproperlyConfigured(f"instance or model must be set in {self.__class__.__name__}")
#         self.instance = instance
#         self.model = model if model else instance._meta.model       # type: ignore
#         self.fields = fields
#         self.header = str(header)
#         if instance:
#             self.model_fields = {field.name: field for field in instance._meta.get_fields()}
#         else:
#             self.model_fields = {field.name: field for field in model._meta.get_fields()}       # type: ignore
#         self.read_only = read_only
#         self.ajax = ajax
#         self.raw_content = raw_content
#         self.one_element_per_line = one_element_per_line
#         self.extra_fields = extra_fields
#         # TODO: Are there all fields in the context and do we need them?
#         self._context = {
#             'header': self.header,
#             'rows': [],
#             'model_forms': [],
#             'td_display_class': td_display_class,
#             'td_value_class': td_value_class,
#             'read_only': read_only,
#             'fields': fields,
#             'raw_content': raw_content,
#             'one_element_per_line': one_element_per_line,
#         }


#     def __repr__(self):
#         return self.header


#     def context(self):
#         """
#         context['rows'] holds the information about each row of the card in a list (up to down)
#         """       
#         for field_name in self.fields:
#             if field_name in self.model_fields:
#                 field_info = {
#                     'name': field_name,
#                     'field': self.model_fields[field_name],
#                     'one_element_per_line': field_name in self.one_element_per_line
#                 }
#             else:
#                 # extra_content
#                 if field_name not in self.extra_fields:
#                     raise ImproperlyConfigured(f"{field_name} is not defined in model '{self.view.model}' and not defined in extra_fields")
#                 field_info = {
#                     'name': field_name,
#                     'field': fields.CharField(
#                         name=field_name,
#                         verbose_name=self.extra_fields[field_name]['verbose_name'] if 'verbose_name' in self.extra_fields[field_name] else field_name,
#                         blank=True,
#                     ),
#                     'content_function': self.extra_fields[field_name]['content_function'],
#                     'one_element_per_line': field_name in self.one_element_per_line
#                 }
#             self._context['rows'].append(
#                 FieldContext(
#                     field_info=field_info,
#                     request=self.request,
#                     render_formular=False if (isinstance(self.view, DetailView) or field_name in self.read_only) else True,
#                     instance=self.instance,
#                 ).context()
#             )
#         # Add AJAX context only for Add- and Edit-Views
#         if not isinstance(self.view, DetailView):
#             self._ajax_context()

#         # pp(self._context)
#         return self._context
    

#     def _ajax_context(self):
#         if not isinstance(self.ajax, list):
#             raise ImproperlyConfigured("ajax must be a list of ajax dictionaries")
#         if self.ajax:
#             self._context['ajax_js'] = ''
#         for ajax_instance in self.ajax:
#             self._context['ajax_js'] += ajax_instance.get_js_code(instance=self.instance)
#         if self.ajax:
#             self._context['ajax_js'] = mark_safe(self._context['ajax_js'])
        