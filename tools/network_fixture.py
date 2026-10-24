"""Only replace sandbox-unavailable network adapter enumeration, never HA logic."""
from unittest.mock import patch

def sandbox_network():
    return patch('ifaddr.get_adapters', return_value=[])
