import ipaddress
from django.core.exceptions import ValidationError
from django.db.models import Lookup


def _parse_ip(value):
    if isinstance(value, (ipaddress.IPv4Address, ipaddress.IPv6Address)):
        return value

    if isinstance(value, (ipaddress.IPv4Network, ipaddress.IPv6Network)):
        if value.num_addresses == 1:
            return value.network_address
        raise ValidationError(f"Expected a single IP address, got network: {value}")

    try:
        value_str = str(value).strip()

        if "/" in value_str:
            network = ipaddress.ip_network(value_str, strict=False)
            if network.num_addresses == 1:
                return network.network_address
            raise ValidationError(f"Expected a single IP address, got network: {value}")

        return ipaddress.ip_address(value_str)
    except ValueError as exc:
        raise ValidationError(f"Invalid IP address: {value}") from exc


def _parse_network(value):
    if isinstance(value, (ipaddress.IPv4Network, ipaddress.IPv6Network)):
        return value
    try:
        return ipaddress.ip_network(str(value), strict=False)
    except ValueError as exc:
        raise ValidationError(f"Invalid CIDR network: {value}") from exc


def _canonical_network_strings_containing_ip(ip_value):
    ip = _parse_ip(ip_value)
    max_prefix = ip.max_prefixlen
    results = []
    for prefix in range(max_prefix, -1, -1):
        network = ipaddress.ip_network(f"{ip}/{prefix}", strict=False)
        results.append(str(network))
    return results


def _canonical_supernet_strings_of_network(network_value):
    network = _parse_network(network_value)
    results = [str(network)]

    current = network
    while current.prefixlen > 0:
        current = current.supernet(prefixlen_diff=1)
        results.append(str(current))

    return results


class BaseCIDRInLookup(Lookup):
    """
    Portable lookup implemented as:
        <lhs> IN (%s, %s, ...)
    """

    def _rhs_values(self):
        raise NotImplementedError

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        values = self._rhs_values()

        if not values:
            return "0=1", []

        placeholders = ", ".join(["%s"] * len(values))
        sql = f"{lhs} IN ({placeholders})"
        params = list(lhs_params) + values
        return sql, params


class ContainsIPLookup(BaseCIDRInLookup):
    lookup_name = "contains_ip"

    def _rhs_values(self):
        return _canonical_network_strings_containing_ip(self.rhs)


class ContainsNetworkLookup(BaseCIDRInLookup):
    lookup_name = "contains_network"

    def _rhs_values(self):
        return _canonical_supernet_strings_of_network(self.rhs)