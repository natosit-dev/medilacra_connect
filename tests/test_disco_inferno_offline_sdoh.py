from __future__ import annotations

import requests
import pytest
from requests import get as imported_requests_get

from experiments.disco_inferno.offline_sdoh import (
    OfflineSDOHNetworkError,
    install_offline_sdoh,
)
from hl7_demo import messages as hl7_messages
from hl7_demo import sdoh as sdoh_module


def test_offline_sdoh_blocks_network_and_replaces_message_aliases():
    original = {
        "sdoh_requests": sdoh_module.requests,
        "sdoh_time": sdoh_module.time,
        "sdoh_air": sdoh_module.get_air_quality_by_zip,
        "sdoh_poverty": sdoh_module.get_poverty_pct_by_zcta,
        "messages_air": hl7_messages.get_air_quality_by_zip,
        "messages_poverty": hl7_messages.get_poverty_pct_by_zcta,
        "requests_session_request": requests.sessions.Session.request,
    }
    optional_names = [
        "get_places_measure_by_zcta",
        "get_unemployment_rate_by_zip",
        "zip_to_county_fips",
        "_airnow_observation",
        "_http_get_json_with_retries",
    ]
    for name in optional_names:
        if hasattr(sdoh_module, name):
            original[name] = getattr(sdoh_module, name)

    try:
        install_offline_sdoh()

        assert hl7_messages.get_air_quality_by_zip("02139") == {}
        assert hl7_messages.get_poverty_pct_by_zcta("02139") is None
        assert sdoh_module.get_air_quality_by_zip("02139") == {}
        assert sdoh_module.get_poverty_pct_by_zcta("02139") is None

        if hasattr(sdoh_module, "get_places_measure_by_zcta"):
            assert sdoh_module.get_places_measure_by_zcta("02139") is None
        if hasattr(sdoh_module, "get_unemployment_rate_by_zip"):
            assert sdoh_module.get_unemployment_rate_by_zip("02139") is None

        # The SDOH module itself is blocked.
        with pytest.raises(OfflineSDOHNetworkError):
            sdoh_module.requests.get("https://api.census.gov/")

        # The worker-wide Requests boundary also catches callers outside the
        # SDOH module, including a get() alias imported before offline mode.
        with pytest.raises(OfflineSDOHNetworkError):
            requests.get("https://example.com/")
        with pytest.raises(OfflineSDOHNetworkError):
            imported_requests_get("https://example.com/")
    finally:
        requests.sessions.Session.request = original["requests_session_request"]
        sdoh_module.requests = original["sdoh_requests"]
        sdoh_module.time = original["sdoh_time"]
        sdoh_module.get_air_quality_by_zip = original["sdoh_air"]
        sdoh_module.get_poverty_pct_by_zcta = original["sdoh_poverty"]
        hl7_messages.get_air_quality_by_zip = original["messages_air"]
        hl7_messages.get_poverty_pct_by_zcta = original["messages_poverty"]
        for name in optional_names:
            if name in original:
                setattr(sdoh_module, name, original[name])
