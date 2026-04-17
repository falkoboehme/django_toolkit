# CIDR Support in django_toolkit

This directory contains a portable CIDR implementation based on `CharField`.

Included building blocks:

- `CIDRField` in `field.py`
- Custom Lookups in `lookup.py`
  - `contains_ip`
  - `contains_network`
- Convenience QuerySet/Manager in `query.py`
  - `CIDRQuerySet`
  - `CIDRManager`

## What does it do?

`CIDRField` stores networks canonically as strings (for example, `192.168.10.0/24` or `2001:db8::/32`) and validates input via Python `ipaddress`.

The lookups are database-portable and use `IN (...)` over possible supernet/subnet strings, so they do not require DB-specific CIDR types.

## Example: Model

```python
from django.db import models
from django_toolkit.models.cidr.field import CIDRField
from django_toolkit.models.cidr.query import CIDRManager


class NetworkEntry(models.Model):
    name = models.CharField(max_length=100)
    cidr = CIDRField()

    objects = CIDRManager()
```

## Input and Canonicalization

These inputs are supported:

- String: `"192.168.10.12/24"`
- `ipaddress.IPv4Network` / `ipaddress.IPv6Network`

Values are canonicalized on save:

- `192.168.10.12/24` -> `192.168.10.0/24`

## Direct Lookups

### 1) Contains an IP

```python
NetworkEntry.objects.filter(cidr__contains_ip="192.168.10.42")
```

### 2) Contains a Network

```python
NetworkEntry.objects.filter(cidr__contains_network="192.168.10.128/25")
```

## QuerySet/Manager Helpers

With `CIDRManager`, you can also use helper methods:

```python
# Which CIDRs in field "cidr" contain this IP?
NetworkEntry.objects.containing_ip("cidr", "192.168.10.42")

# Which CIDRs in field "cidr" contain this network?
NetworkEntry.objects.containing_network("cidr", "192.168.10.128/25")
```

## Error Behavior

For invalid values, `ValidationError` is raised, for example in cases of:

- invalid IP in `contains_ip`
- invalid network in `contains_network`
- invalid field value for `CIDRField`

## Notes

- The field is intentionally a `CharField`, making it portable across databases.
- The lookups are functional and robust, but not as performant as native CIDR operators in Postgres.
- For very large datasets, a DB-specific solution may be preferable.
