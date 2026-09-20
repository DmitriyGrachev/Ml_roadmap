import logging
from pathlib import Path

import pytest

from support_api.app import create_app
from support_api.config import SupportSettings
from support_api.observability import log_ticket_event


def test_settings_load_prefixed_environment_values(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SUPPORT_APP_NAME", "helpdesk")
    monkeypatch.setenv("SUPPORT_LOG_LEVEL", "DEBUG")

    settings = SupportSettings()

    assert settings.app_name == "helpdesk"
    assert settings.log_level == "DEBUG"


def test_settings_are_injected_at_application_composition() -> None:
    settings = SupportSettings(app_name="Configured helpdesk")

    app = create_app(settings=settings)

    assert app.title == "Configured helpdesk"


def test_structured_ticket_log_exposes_searchable_context(
    caplog: pytest.LogCaptureFixture,
) -> None:
    logger = logging.getLogger("support-api-example")

    with caplog.at_level(logging.INFO, logger=logger.name):
        log_ticket_event(logger, ticket_id="ticket-42", event="created")

    [record] = caplog.records
    assert record.getMessage() == "support_ticket_event"
    assert record.__dict__["ticket_id"] == "ticket-42"
    assert record.__dict__["event"] == "created"
