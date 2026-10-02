from src import runtime_cache


class FakeStorage:
    def __init__(self, data, version, counts):
        self.data = data
        self.version_value = version
        self.counts = counts

    def read(self):
        self.counts['reads'] += 1
        return self.data, self.version_value


def test_same_snapshot_version_and_config_reuses_load_and_calculation(monkeypatch):
    runtime_cache.clear_snapshot_calculation_cache()
    counts = {'reads': 0, 'calculations': 0}
    monkeypatch.setattr(
        runtime_cache,
        'make_storage',
        lambda _: FakeStorage({'source': b'data'}, 'v1', counts),
    )

    def calculate(files):
        counts['calculations'] += 1
        return {'rows': len(files)}, {'loaded': True}

    args = ('LOCAL', 'private-snapshot', 'v1', '/private/snapshot.zip', 'schema-1')
    first = runtime_cache.load_snapshot_calculation(*args, _compute_func=calculate)
    second = runtime_cache.load_snapshot_calculation(
        *args, _google_service_account={'private_key': 'different'}, _compute_func=calculate
    )

    assert first == second
    assert counts == {'reads': 1, 'calculations': 1}
    runtime_cache.clear_snapshot_calculation_cache()


def test_changed_version_or_calculation_config_invalidates_cache(monkeypatch):
    runtime_cache.clear_snapshot_calculation_cache()
    counts = {'reads': 0, 'calculations': 0}
    active_version = {'value': 'v1'}

    def create_storage(_):
        return FakeStorage({'version': active_version['value']}, active_version['value'], counts)

    monkeypatch.setattr(runtime_cache, 'make_storage', create_storage)

    def calculate(files):
        counts['calculations'] += 1
        return files, {}

    base = ('LOCAL', 'private-snapshot', 'v1', '/private/snapshot.zip')
    runtime_cache.load_snapshot_calculation(*base, 'schema-1', _compute_func=calculate)
    active_version['value'] = 'v2'
    runtime_cache.load_snapshot_calculation(
        'LOCAL', 'private-snapshot', 'v2', '/private/snapshot.zip', 'schema-1',
        _compute_func=calculate,
    )
    runtime_cache.load_snapshot_calculation(
        'LOCAL', 'private-snapshot', 'v2', '/private/snapshot.zip', 'schema-2',
        _compute_func=calculate,
    )
    runtime_cache.load_snapshot_calculation(
        'LOCAL', 'replacement-snapshot', 'v2', '/private/snapshot.zip', 'schema-2',
        _compute_func=calculate,
    )

    assert counts == {'reads': 4, 'calculations': 4}
    runtime_cache.clear_snapshot_calculation_cache()


def test_explicit_clear_forces_reload_after_update(monkeypatch):
    runtime_cache.clear_snapshot_calculation_cache()
    counts = {'reads': 0, 'calculations': 0}
    active_version = {'value': 'v1'}
    monkeypatch.setattr(
        runtime_cache,
        'make_storage',
        lambda _: FakeStorage({'version': active_version['value']}, active_version['value'], counts),
    )

    def calculate(files):
        counts['calculations'] += 1
        return files, {}

    args = ('LOCAL', 'private-snapshot', 'v1', '/private/snapshot.zip', 'schema-1')
    runtime_cache.load_snapshot_calculation(*args, _compute_func=calculate)
    active_version['value'] = 'v2'
    runtime_cache.clear_snapshot_calculation_cache()
    runtime_cache.load_snapshot_calculation(
        'LOCAL', 'private-snapshot', 'v2', '/private/snapshot.zip', 'schema-1',
        _compute_func=calculate,
    )

    assert counts == {'reads': 2, 'calculations': 2}
    runtime_cache.clear_snapshot_calculation_cache()
