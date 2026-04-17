import ipaddress
from django.core import exceptions
from django.db import models

from .lookup import ContainsIPLookup, ContainsNetworkLookup


class CIDRField(models.CharField):
    description = "CIDR network (IPv4 or IPv6)"

    def __init__(self, *args, **kwargs):
        # Long enough for canonical IPv6 CIDR, e.g. ffff:.../128
        kwargs.setdefault("max_length", 43)
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if kwargs.get("max_length") == 43:
            del kwargs["max_length"]
        return name, path, args, kwargs

    def get_internal_type(self):
        return "CharField"

    def to_python(self, value):
        if value is None or value == "":
            return value

        if isinstance(value, (ipaddress.IPv4Network, ipaddress.IPv6Network)):
            return str(value)

        try:
            value_str = str(value).strip()

            # If only an IP is provided (without slash), normalize to host network.
            if "/" not in value_str:
                ip_obj = ipaddress.ip_address(value_str)
                return str(ipaddress.ip_network(f"{ip_obj}/{ip_obj.max_prefixlen}", strict=False))

            return str(ipaddress.ip_network(value_str, strict=False))
        except ValueError as exc:
            raise exceptions.ValidationError(
                f"Invalid CIDR value: {value}"
            ) from exc

    def from_db_value(self, value, expression, connection):
        if value is None or value == "":
            return value
        return self.to_python(value)

    def get_prep_value(self, value):
        if value is None or value == "":
            return value

        network = self.to_python(value)
        return str(network)

    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        if value in (None, ""):
            return ""
        return str(value)

    def formfield(self, **kwargs):
        defaults = {"help_text": "Example: 192.168.10.0/24 or 2001:db8::/32"}
        defaults.update(kwargs)
        return super().formfield(**defaults)


CIDRField.register_lookup(ContainsIPLookup)
CIDRField.register_lookup(ContainsNetworkLookup)