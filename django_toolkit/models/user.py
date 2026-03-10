from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import Permission
from .base_models import DTHistoryChangeLoggingModel, DTModelManager
from .group import DTGroup
from ..template_context.card_definition import CardDefinition
from ..functions.permissions import get_permission_for_model_action, permissions_to_strings, PERMISSION_ACTION



class DTUserManager(DTModelManager, BaseUserManager):
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
                    fields=['is_staff', 'is_superuser', 'user_permissions', 'all_permissions', ],
                    ro_fields=['all_permissions', ],
                ),
            ],
            [
                CardDefinition(
                    header=_('Comment'),
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
        group_related_name = getattr(settings, 'DT_GROUP_RELATED_NAME_FOR_PERMISSION', 'dtgroup')
        group_filter = {f"{group_related_name}__in": self.groups.all()}
        return Permission.objects.filter(models.Q(**group_filter)).distinct()
    
    @property
    def all_permissions(self):
        group_related_name = getattr(settings, 'DT_GROUP_RELATED_NAME_FOR_PERMISSION', 'dtgroup')
        group_filter = {f"{group_related_name}__in": self.groups.all()}
        return Permission.objects.filter(models.Q(user=self) | models.Q(**group_filter)).distinct()
    
