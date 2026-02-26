from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import Permission
from django.utils.safestring import mark_safe
from .base_models import DTHistoryChangeLoggingModel
from .group import DTGroup
from ..template_context.card_definition import CardDefinition
from ..functions.debug import *
from ..functions.permissions import get_perm_action_from_permission


class DTUserManager(BaseUserManager):
    """
    User model manager using email as login
    """

    def create_user(self, email, password, **extra_fields):
        """
        Create and save a user with the given email and password.
        """ 
        if not email:
            raise ValueError(_('The email must be provided'))
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user


    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a superuser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)



class DTUser(PermissionsMixin, DTHistoryChangeLoggingModel, AbstractBaseUser):
    """
    Base user (human or m2m)
    """
    email = models.EmailField(
        unique=True,
        verbose_name=_('eMail'),
        help_text=_('eMail adress of the user. Used to identify the user (must be unique)'),
    )
    password = models.CharField(
        verbose_name=_("password"),
        max_length=128,
        help_text=_("Password of the user. Will be stored in hashed form."),
    )
    groups = models.ManyToManyField(
        to=DTGroup,
        blank=True,
        related_name="user",
        verbose_name=_("Groups"),
        help_text=_("The groups this user belongs to. A user will get all permissions granted to each of their groups."),
    )
    user_permissions = models.ManyToManyField(
        to=Permission,
        blank=True,
        related_name="user",
        verbose_name=_("User permissions"),
        help_text=_("Specific permissions for this user."),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Active'),
        help_text=_('User is active and can log in'),
    )
    is_staff = models.BooleanField(
        default=False,
        verbose_name=_('Stuff'),
        help_text=_('User may use the admin site'),
    )
    is_superuser = models.BooleanField(
        default=False,
        verbose_name=_("Superuser"),
        help_text=_("This user has all permissions without explicitly assigning them"),
    )
    comment = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Comment'),
        help_text=_('Additional remarks'),
    )
    
    USERNAME_FIELD = 'email'

    objects = DTUserManager()

    class Meta(DTHistoryChangeLoggingModel.Meta):
        abstract = True
        ordering = ['email',]
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        base_url = 'users'
        cards = [
            [
                CardDefinition(
                    header=_('User'),
                    fields=['email', 'groups', 'is_active'],
                ),
                CardDefinition(
                    header=_('Special Rights'),
                    fields=['is_staff', 'is_superuser', 'user_permissions', 'permissions', ],
                    ro_fields=['permissions', ],
                ),
            ],
            [
                CardDefinition(
                    header=_('Comments'),
                    fields=['comment']
                ),
                CardDefinition(
                    header=_('Internal'),
                    fields=['last_login', 'created', 'created_user', 'last_updated', 'last_updated_user', ],
                    ro_fields=['last_login', 'created', 'created_user', 'last_updated', 'last_updated_user',]
                ),
            ]
        ]


    def __str__(self):
        return self.email
    
    @property
    def group_permissions(self):
        return Permission.objects.filter(usergroup__user=self).distinct()
    

    @property
    def permissions(self):
        """Permissions with origin (User / Group names)."""
        origins: dict[str, dict[str, set[str]]] = {}

        def model_label(perm: Permission) -> str:
            model_cls = perm.content_type.model_class()
            if model_cls is None:
                return f"{perm.content_type.app_label.title()} | {perm.content_type.model}"
            return f"{model_cls._meta.app_label.title()} | {model_cls.__name__}"

        def origin_sort_key(origin: str) -> tuple[int, str]:
            return (0, origin) if origin == "User" else (1, origin)

        for perm in self.user_permissions.all():
            label = model_label(perm)
            action = get_perm_action_from_permission(perm)
            origins.setdefault(label, {}).setdefault(action, set()).add("User")

        for group in self.groups.all().prefetch_related("permissions"):
            for perm in group.permissions.all():
                label = model_label(perm)
                action = get_perm_action_from_permission(perm)
                origins.setdefault(label, {}).setdefault(action, set()).add(group.name)

        def sort_actions(actions: set[str]) -> list[str]:
            order = ["view", "add", "change", "delete"]
            return sorted(actions, key=lambda a: order.index(a) if a in order else 99)

        lines = []
        for label in sorted(origins.keys()):
            action_parts = []
            for action in sort_actions(set(origins[label].keys())):
                origin_list = sorted(origins[label][action], key=origin_sort_key)
                action_parts.append(f"{action} ({', '.join(origin_list)})")
            lines.append(f"{label} [{', '.join(action_parts)}]")

        return mark_safe("<br>".join(lines))