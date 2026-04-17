from django.db import models


class CIDRQuerySet(models.QuerySet):
    def containing_ip(self, field_name, ip):
        return self.filter(**{f"{field_name}__contains_ip": ip})

    def containing_network(self, field_name, network):
        return self.filter(**{f"{field_name}__contains_network": network})


class CIDRManager(models.Manager):
    def get_queryset(self):
        return CIDRQuerySet(self.model, using=self._db)

    def containing_ip(self, field_name, ip):
        return self.get_queryset().containing_ip(field_name, ip)

    def containing_network(self, field_name, network):
        return self.get_queryset().containing_network(field_name, network)