from __future__ import annotations

import json
from json import JSONDecodeError
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class LocationLookupError(Exception):
    """Raised when GPS coordinates cannot be resolved to a readable address."""


def reverse_geocode(latitude: float, longitude: float) -> str:
    query = urlencode({
        "format": "jsonv2",
        "lat": latitude,
        "lon": longitude,
        "zoom": 18,
        "addressdetails": 1,
    })
    request = Request(
        f"https://nominatim.openstreetmap.org/reverse?{query}",
        headers={
            "Accept": "application/json",
            "Accept-Language": "en",
            "User-Agent": "GUBAttendanceSystem/1.0",
        },
    )
    try:
        with urlopen(request, timeout=8) as response:
            result = json.load(response)
    except (HTTPError, URLError, TimeoutError, JSONDecodeError) as error:
        raise LocationLookupError("The address lookup service is unavailable.") from error

    if not isinstance(result, dict):
        raise LocationLookupError("The address lookup service returned an invalid response.")
    address = result.get("display_name")
    if not isinstance(address, str) or not address.strip():
        raise LocationLookupError("No readable address was found for these coordinates.")
    return address.strip()[:1000]
 