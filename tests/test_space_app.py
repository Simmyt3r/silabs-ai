def test_space_app_imports():
    import app

    assert app.demo is not None
    assert app.settings.app_name == "Silabs AI"
