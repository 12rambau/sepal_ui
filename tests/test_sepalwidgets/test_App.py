"""Test the App widget."""

import os

import ipyvuetify as v
import pytest

from sepal_ui import sepalwidgets as sw


def test_init() -> None:
    """Init the widget."""
    # default init
    app = sw.App()
    assert isinstance(app, sw.App)
    assert len(app.children) == 3
    assert isinstance(app.children[0], v.Overlay)
    assert isinstance(app.children[1], sw.AppBar)
    assert isinstance(app.children[2], v.Content)
    assert app.appBar.toggle_button.class_ == "d-none"

    # exhaustive
    navDrawer = sw.NavDrawer([sw.DrawerItem(f"title {i}") for i in range(5)])
    appBar = sw.AppBar()
    tiles = []
    for i in range(5):
        tiles.append(sw.Tile(f"id_{i}", f"title_{i}"))
    footer = sw.Footer()

    app = sw.App(tiles, appBar, footer, navDrawer)
    assert isinstance(app, sw.App)
    assert len(app.children) == 5
    assert isinstance(app.children[0], v.Overlay)
    assert isinstance(app.children[1], sw.AppBar)
    assert isinstance(app.children[2], sw.NavDrawer)
    assert isinstance(app.children[3], v.Content)
    assert isinstance(app.children[4], sw.Footer)

    return


def test_show_tile() -> None:
    """Check that tiles are shown when licking a drawerItem."""
    tiles = [sw.Tile(f"id_{i}", f"title_{i}") for i in range(5)]
    drawer_items = [sw.DrawerItem(f"title {i}", card=f"id_{i}") for i in range(5)]
    appBar = sw.AppBar()
    footer = sw.Footer()

    title = "main_title"
    id_ = "main_id"
    main_tile = sw.Tile(id_, title)
    main_drawer = sw.DrawerItem(title, card=id_)
    tiles.append(main_tile)
    drawer_items.append(main_drawer)

    app = sw.App(tiles, appBar, footer, sw.NavDrawer(drawer_items))
    res = app.show_tile(id_)

    assert res == app

    for tile in tiles:
        if tile == main_tile:
            assert tile.viz is True
        else:
            assert tile.viz is False

    for di in drawer_items:
        if di._metadata["card_id"] == id_:
            assert di.input_value is True
        else:
            assert di.input_value is False

    return


def test_add_banner(app: sw.App) -> None:
    """Add a banner to the application.

    Args:
        app: an fully defined App instance
    """
    # without type
    msg = "toto"
    res = app.add_banner(msg, id_="test_info")

    alert = next(
        (c for c in app.content.children if c.attributes.get("id") == "test_info"),
        False,
    )

    assert res == app
    assert isinstance(alert, v.Snackbar)
    assert alert.color == "info"
    assert alert.children[0] == msg

    # with type
    type_ = "error"
    res = app.add_banner(msg, id_="test_error", type=type_)
    alert = next(
        (c for c in app.content.children if c.attributes.get("id") == "test_error"),
        False,
    )

    assert res == app
    assert isinstance(alert, v.Snackbar)
    assert alert.color == "error"
    assert alert.children[0] == msg

    return


def test_close_banner(app: sw.App) -> None:
    """Test closing banner event.

    Args:
        app: an fully defined App instance
    """
    msg = "test"
    app.add_banner(msg, id_="test_close")

    alert = next(
        (c for c in app.content.children if c.attributes.get("id") == "test_close"),
        False,
    )

    # Check if banner is active
    assert alert.v_model is True

    # Close banner
    alert.children[1].fire_event("click", None)

    assert alert.v_model is False

    return


def test_version_card(repo_dir) -> None:
    """Test the drawer of the app."""
    # arrange
    app_version = "999.999.1"
    changelog_text = "# Changelog"

    # Change current working directory to dummy repo
    os.chdir(repo_dir)

    # Check that if there is no pyproject.toml file, the version card is not present
    navigation_drawer = sw.NavDrawer([], repo_folder=repo_dir)

    assert navigation_drawer.v_slots == []

    # Create a pyproject.toml file and a changelog
    pyproject_file = repo_dir / "pyproject.toml"

    # create a temporary pyproject.toml file
    with open(pyproject_file, "w") as f:
        f.write(f"[project]\nversion = '{app_version}'")

    # Create a dummy changelog file and write some text in it
    changelog_file = repo_dir / "CHANGELOG.md"
    changelog_file.touch()
    changelog_file.write_text(f"{changelog_text}")

    navigation_drawer = sw.NavDrawer([], repo_folder=repo_dir)

    # Check if the version card is present

    assert len(navigation_drawer.v_slots) == 1

    version_card = navigation_drawer.v_slots[0]["children"][0]

    # Check if the version card has the right content
    displayed_version = version_card.children[0].children[0]
    assert displayed_version == f"Version: {app_version}"


@pytest.fixture(scope="function")
def app() -> sw.App:
    """Create a default App.

    Returns:
        App instance with 5 tiles and associated drawers
    """
    # create default widgets
    tiles = [sw.Tile(f"id_{i}", f"title_{i}") for i in range(5)]
    drawer_items = [sw.DrawerItem(f"title {i}", card=f"id_{i}") for i in range(5)]
    appBar = sw.AppBar()
    footer = sw.Footer()

    return sw.App(tiles, appBar, footer, sw.NavDrawer(drawer_items))
