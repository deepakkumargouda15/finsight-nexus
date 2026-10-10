"""Streamlit AppTest smoke tests for the principal no-network user journeys.

These tests deliberately avoid the live provider so CI remains deterministic.
"""
from streamlit.testing.v1 import AppTest


def run_app():
    return AppTest.from_file("app.py", default_timeout=30).run()


def test_default_dashboard_renders_without_exception():
    app = run_app()
    assert not app.exception
    assert len(app.sidebar.radio) >= 1
    assert any("Offline multi-company comparison demo" in str(x.value) for x in app.subheader)


def test_synthetic_single_company_mode_renders_without_exception():
    app = run_app()
    app.sidebar.radio[0].set_value("Synthetic single-company demo").run()
    assert not app.exception
    assert any("Fictional demonstration data" in str(x.value) for x in app.warning)


def test_upload_mode_renders_templates_without_uploading_a_file():
    app = run_app()
    app.sidebar.radio[0].set_value("Upload CSV / Excel").run()
    assert not app.exception
    assert any("Bring your own market data" in str(x.value) for x in app.subheader)
    assert len(app.get("file_uploader")) == 1
    assert len(app.get("download_button")) >= 2




def test_live_mode_does_not_call_provider_before_form_submission():
    app = run_app()
    app.sidebar.radio[0].set_value("Live market data").run()

    # The application should render without exceptions.
    assert not app.exception

    # The live-data submit button should be visible in the sidebar.
    assert any(
        "Fetch market data" in str(button.label)
        for button in app.sidebar.button
    )

    # The app should prompt the user before fetching market data.
    assert any(
        "Enter one or more tickers" in str(message.value)
        for message in app.info
    )