from cli import main


def test_cli_module_imports():
    assert callable(main)
