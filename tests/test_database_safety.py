"""Database fixture safety checks; every database operation is mocked."""

from unittest.mock import MagicMock, patch

import pytest

from tests import conftest


@pytest.fixture
def fake_database(monkeypatch):
    monkeypatch.delenv("SEN2NAL_TEST_DATABASE_URL", raising=False)
    with patch.object(conftest, "create_engine") as factory:
        with patch.object(conftest.Base.metadata, "create_all") as create:
            with patch.object(conftest.Base.metadata, "drop_all") as drop:
                yield factory, create, drop


def test_app_database_url_does_not_authorise_test_database_changes(monkeypatch, fake_database):
    factory, _, _ = fake_database
    monkeypatch.setenv("DATABASE_URL", "postgresql://synthetic:synthetic@localhost/application")
    with pytest.raises(pytest.skip.Exception):
        next(conftest.test_db_engine.__wrapped__())
    factory.assert_not_called()


@pytest.mark.parametrize("url", [
    "postgresql://synthetic:synthetic@localhost/application",
    "postgresql://synthetic:synthetic@remote.invalid/sen2nal_test",
    "sqlite:///:memory:",
    "invalid connection string",
    "postgresql://synthetic:synthetic@localhost/sen2nal_test?host=remote.invalid",
    "postgresql://synthetic:synthetic@localhost/sen2nal_test?dbname=application",
    "postgresql://synthetic:synthetic@localhost/sen2nal_test?service=external",
])
def test_unsafe_explicit_test_url_is_refused_before_connect(monkeypatch, fake_database, url):
    factory, _, _ = fake_database
    monkeypatch.setenv("SEN2NAL_TEST_DATABASE_URL", url)
    with pytest.raises(ValueError, match="local PostgreSQL test"):
        next(conftest.test_db_engine.__wrapped__())
    factory.assert_not_called()


def test_fixture_owns_a_unique_schema_and_never_drops_application_tables(monkeypatch, fake_database):
    factory, create, drop = fake_database
    monkeypatch.setenv("SEN2NAL_TEST_DATABASE_URL", "postgresql://synthetic:synthetic@127.0.0.1/sen2nal_test")
    engine = MagicMock()
    factory.return_value = engine
    fixture = conftest.test_db_engine.__wrapped__()
    assert next(fixture) is engine
    drop.assert_not_called()
    create.assert_called_once_with(bind=engine)
    schema = engine.begin.return_value.__enter__.return_value.execute.call_args.args[0].element
    assert schema.startswith("sen2nal_test_")
    assert len(schema.removeprefix("sen2nal_test_")) == 32
    assert factory.call_args.kwargs["connect_args"]["options"] == f"-csearch_path={schema}"
    fixture.close()
    dropped = engine.begin.return_value.__enter__.return_value.execute.call_args.args[0]
    assert dropped.element == schema
    assert dropped.cascade is True
    drop.assert_not_called()
    engine.dispose.assert_called_once()

    engine.reset_mock()
    second = conftest.test_db_engine.__wrapped__()
    next(second)
    other = engine.begin.return_value.__enter__.return_value.execute.call_args.args[0].element
    assert other != schema
    second.close()


def test_setup_failure_still_cleans_only_the_owned_schema(monkeypatch, fake_database):
    factory, create, drop = fake_database
    monkeypatch.setenv("SEN2NAL_TEST_DATABASE_URL", "postgresql://synthetic:synthetic@localhost/sen2nal_test")
    create.side_effect = RuntimeError("synthetic setup failure")
    engine = factory.return_value
    with pytest.raises(RuntimeError, match="synthetic setup failure"):
        next(conftest.test_db_engine.__wrapped__())
    calls = engine.begin.return_value.__enter__.return_value.execute.call_args_list
    assert len(calls) == 2
    assert calls[0].args[0].element == calls[1].args[0].element
    drop.assert_not_called()
    engine.dispose.assert_called_once()


def test_connection_cannot_inherit_postgres_routing_environment(monkeypatch, fake_database):
    factory, _, _ = fake_database
    monkeypatch.setenv("SEN2NAL_TEST_DATABASE_URL", "postgresql://synthetic:synthetic@localhost/sen2nal_test")
    monkeypatch.setenv("PGHOSTADDR", "192.0.2.1")
    monkeypatch.setenv("PGSERVICE", "synthetic_external_service")
    engine = MagicMock()

    def connect(*args, **kwargs):
        inherited = tuple(key for key in ["PGHOSTADDR", "PGSERVICE"] if key in conftest.os.environ)
        assert inherited == ()
        assert kwargs["connect_args"]["hostaddr"] == "127.0.0.1"
        return engine

    factory.side_effect = connect
    fixture = conftest.test_db_engine.__wrapped__()
    assert next(fixture) is engine
    fixture.close()
    restored_addr = conftest.os.environ["PGHOSTADDR"]
    restored_service = conftest.os.environ["PGSERVICE"]
    assert restored_addr == "192.0.2.1"
    assert restored_service == "synthetic_external_service"


def test_cleanup_failure_is_reported_and_engine_is_disposed(monkeypatch, fake_database):
    factory, _, drop = fake_database
    monkeypatch.setenv("SEN2NAL_TEST_DATABASE_URL", "postgresql://synthetic:synthetic@localhost/sen2nal_test")
    engine = factory.return_value
    engine.begin.return_value.__enter__.return_value.execute.side_effect = [None, RuntimeError("synthetic cleanup failure")]
    fixture = conftest.test_db_engine.__wrapped__()
    next(fixture)
    with pytest.raises(RuntimeError, match="synthetic cleanup failure"):
        fixture.close()
    drop.assert_not_called()
    engine.dispose.assert_called_once()
