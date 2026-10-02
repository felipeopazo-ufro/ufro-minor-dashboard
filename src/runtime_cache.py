"""Version-keyed loading and calculation cache for the private snapshot."""
import streamlit as st

from .storage import make_storage

CACHE_TTL_SECONDS = 3600
CACHE_MAX_ENTRIES = 4
# Bump this when a calculation dependency changes without changing the snapshot.
CALCULATION_CACHE_SCHEMA = "academic-calculation-v1"


class SnapshotVersionChanged(ValueError):
    """The snapshot changed between the version check and the download."""


@st.cache_data(show_spinner=False, max_entries=CACHE_MAX_ENTRIES, ttl=CACHE_TTL_SECONDS)
def load_snapshot_calculation(
    storage_mode,
    snapshot_file_id,
    snapshot_version,
    local_path,
    calculation_config_key,
    _google_service_account=None,
    _compute_func=None,
):
    """Read, unpack and calculate once for a file id/version/configuration key.

    Credentials and the optional test function are underscore-prefixed so
    Streamlit excludes them from the cache key. Only the data result is cached.
    """
    storage_settings = {
        "storage": {
            "mode": storage_mode,
            "snapshot_file_id": snapshot_file_id,
            "local_path": local_path,
        }
    }
    if _google_service_account is not None:
        storage_settings["google_service_account"] = _google_service_account

    files, loaded_version = make_storage(storage_settings).read()
    if str(loaded_version) != str(snapshot_version):
        raise SnapshotVersionChanged(
            "El snapshot cambió durante la lectura. Vuelva a cargar los datos."
        )

    if _compute_func is None:
        from .ui import compute

        _compute_func = compute
    result, sources = _compute_func(files)
    return files, str(loaded_version), result, sources


def clear_snapshot_calculation_cache():
    """Drop cached snapshots and derived results after an explicit update."""
    load_snapshot_calculation.clear()


def snapshot_cache_key(storage_mode, snapshot_file_id, version, local_path):
    """Return the non-secret session key used to show progress only on misses."""
    return (
        storage_mode,
        snapshot_file_id or "",
        str(version),
        local_path or "",
        CALCULATION_CACHE_SCHEMA,
    )
