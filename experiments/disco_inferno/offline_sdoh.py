from __future__ import annotations

from types import SimpleNamespace


class OfflineSDOHNetworkError(RuntimeError):
    pass


def install_offline_sdoh() -> None:
    """Force the current Disco Inferno worker into a no-network SDOH mode.

    Disco Inferno runs in its own worker process, so the offline boundary can be
    stronger than the shared MediLacra code. Public SDOH lookups return neutral
    local values, direct SDOH HTTP helpers are disabled, and Requests is blocked
    process-wide so a previously imported alias cannot escape the boundary.
    """

    import requests

    from hl7_demo import messages as hl7_messages
    from hl7_demo import sdoh as sdoh_module

    def no_air_quality(*_args, **_kwargs):
        return {}

    def no_poverty(*_args, **_kwargs):
        return None

    def no_places(*_args, **_kwargs):
        return None

    def no_unemployment(*_args, **_kwargs):
        return None

    def no_county(*_args, **_kwargs):
        return None

    def blocked_http(*_args, **_kwargs):
        raise OfflineSDOHNetworkError(
            "Outbound HTTP is disabled for this Disco Inferno worker while SDOH is off."
        )

    # Public SDOH entry points.
    sdoh_module.get_air_quality_by_zip = no_air_quality
    sdoh_module.get_poverty_pct_by_zcta = no_poverty
    if hasattr(sdoh_module, "get_places_measure_by_zcta"):
        sdoh_module.get_places_measure_by_zcta = no_places
    if hasattr(sdoh_module, "get_unemployment_rate_by_zip"):
        sdoh_module.get_unemployment_rate_by_zip = no_unemployment
    if hasattr(sdoh_module, "zip_to_county_fips"):
        sdoh_module.zip_to_county_fips = no_county

    # Lower-level SDOH helpers are disabled as defense in depth.
    if hasattr(sdoh_module, "_airnow_observation"):
        sdoh_module._airnow_observation = no_air_quality
    if hasattr(sdoh_module, "_http_get_json_with_retries"):
        sdoh_module._http_get_json_with_retries = lambda *_args, **_kwargs: None

    # build_adt imported these functions directly, so replace its aliases too.
    hl7_messages.get_air_quality_by_zip = no_air_quality
    hl7_messages.get_poverty_pct_by_zcta = no_poverty

    # Important: replacing only sdoh_module.requests is not enough because a
    # different module may already hold `requests` or `requests.get`. Blocking
    # Session.request closes that escape path for every Requests caller inside
    # this isolated worker process without touching the parent Streamlit process.
    requests.sessions.Session.request = blocked_http

    # Keep the SDOH module itself visibly offline as well.
    sdoh_module.requests = SimpleNamespace(get=blocked_http)
    sdoh_module.time = SimpleNamespace(sleep=lambda *_args, **_kwargs: None)
