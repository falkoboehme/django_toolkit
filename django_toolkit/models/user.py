from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import Permission
from django.urls import reverse
from .base_models import DTHistoryChangeLoggingModel
from .group import DTGroup
from ..template_context.card import Card


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
            [  # Column 0
                Card(
                    header=_('User'),
                    fields=['email', 'groups']
                ),
                Card(
                    header=_('Special Rights'),
                    fields=['is_active', 'is_staff', 'user_permissions']
                ),
            ],
            [  # Column 1
                Card(
                    header=_('Comments'),
                    fields=['comment']
                ),
                Card(
                    header=_('Internal'),
                    fields=['created', 'created_user', 'last_updated', 'last_updated_user', 'is_superuser'],
                    read_only=['created', 'created_user', 'last_updated', 'last_updated_user', 'is_superuser']
                ),
            ]
        ]


    def __str__(self):
        return self.email
    
    def get_absolute_url(self):
        return reverse('user:user-detail', args=[self.pk])
    
    # def get_user_permissions(self, obj=None):
    #     return user_get_permissions(self, obj, "user")

    # def get_group_permissions(self, obj=None):
    #     return user_get_permissions(self, obj, "group")

    # def get_all_permissions(self, obj=None):
    #     return user_get_permissions(self, obj, "all")

    # def has_perm(self, perm, obj=None):
    #     # Active superusers have all permissions.
    #     if self.is_active and self.is_superuser:
    #         return True

    #     # Otherwise we need to check the backends.
    #     return user_has_perm(self, perm, obj)

    # def has_perms(self, perm_list, obj=None):
    #     if not isinstance(perm_list, Iterable) or isinstance(perm_list, str):
    #         raise ValueError("perm_list must be an iterable of permissions.")
    #     return all(self.has_perm(perm, obj) for perm in perm_list)

    # def has_module_perms(self, app_label):
    #     """
    #     Return True if the user has any permissions in the given app label.
    #     Use similar logic as has_perm(), above.
    #     """
    #     # Active superusers have all permissions.
    #     if self.is_active and self.is_superuser:
    #         return True

    #     return user_has_module_perms(self, app_label)
