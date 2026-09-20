from importlib.resources import files


def test_installed_roadmap_tools_declares_inline_types() -> None:
    assert files("roadmap_tools").joinpath("py.typed").is_file()
