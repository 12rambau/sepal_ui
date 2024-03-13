"""Test the AssetSelect widget."""

from pathlib import Path
from typing import List

import ee
import pytest

from sepal_ui import sepalwidgets as sw
from sepal_ui.message import ms


@pytest.mark.skipif(not ee.data._credentials, reason="GEE is not set")
def test_init(gee_dir: Path, gee_user_dir: Path) -> None:
    """Init the widget.

    Args:
        gee_dir: the session defined GEE directory
        gee_user_dir: the gee_dir without the project information
    """
    # create an asset select that points to the folder I created for testing
    asset_select = sw.AssetSelect(folder=str(gee_dir))
    assert isinstance(asset_select, sw.AssetSelect)
    assert str(gee_user_dir / "image") in asset_select.items

    # create an asset select with an undefined type
    asset_select = sw.AssetSelect(folder=str(gee_dir), types=["toto"])

    # zero assets are represented by a disabled item
    no_asset_item = [
        {
            "text": ms.widgets.asset_select.no_assets.format(str(gee_dir)),
            "disabled": True,
        }
    ]
    assert asset_select.items == no_asset_item

    return


@pytest.mark.skipif(not ee.data._credentials, reason="GEE is not set")
def test_add_default(asset_select: sw.AssetSelect, default_items: List[str]) -> None:
    """Check that user can add default assets to the list.

    Args:
        asset_select: a fully defined asset widget
        default_items: a list of default assetId
    """
    # add a partial list of asset
    asset_select.default_asset = default_items[1:]
    assert default_items[1] in asset_select.items

    # add the full list
    asset_select.default_asset = default_items
    assert default_items[0] in asset_select.items

    # add one item as a string
    asset_select.default_asset = default_items[0]
    assert default_items[0] in asset_select.items

    return


@pytest.mark.skipif(not ee.data._credentials, reason="GEE is not set")
def test_validate(asset_select: sw.AssetSelect, default_items: List[str]) -> None:
    """Check asset that user cannot read cannot be selected.

    Args:
        asset_select: a fully defined asset widget
        default_items: a list of default assetId
    """
    # set a legit asset
    asset_select.v_model = default_items[0]
    assert asset_select.valid is True
    assert asset_select.error_messages is None
    assert asset_select.error is False

    # set a fake asset
    asset_select.v_model = "toto/tutu"
    assert asset_select.error_messages is not None
    assert asset_select.valid is False
    assert asset_select.error is True

    # set a real asset but with wrong type
    asset_select.types = ["TABLE"]
    asset_select.v_model = default_items[0]
    assert asset_select.error_messages is not None
    assert asset_select.valid is False
    assert asset_select.error is True

    return


@pytest.mark.skipif(not ee.data._credentials, reason="GEE is not set")
def test_check_types(asset_select: sw.AssetSelect, gee_user_dir: Path) -> None:
    """Check only the specified types are displayed to the need user.

    Args:
        asset_select: a fully defined asset widget
        gee_user_dir: the path to the GEE directory
    """
    # check that the list of asset is complete
    assert str(gee_user_dir / "image") in asset_select.items
    assert str(gee_user_dir / "feature_collection") in asset_select.items
    assert (
        str(gee_user_dir / "subfolder/subfolder_feature_collection")
        in asset_select.items
    )

    # set an IMAGE type
    asset_select.types = ["IMAGE"]
    assert str(gee_user_dir / "image") in asset_select.items
    assert str(gee_user_dir / "feature_collection") not in asset_select.items
    assert (
        str(gee_user_dir / "subfolder/subfolder_feature_collection")
        not in asset_select.items
    )

    # set a type list with a non legit asset type
    asset_select.types = ["IMAGE", "toto"]
    assert asset_select.types == ["IMAGE"]

    return


@pytest.mark.skipif(not ee.data._credentials, reason="GEE is not set")
def test_get_items(asset_select: sw.AssetSelect, gee_user_dir: Path) -> None:
    """Get items from a specific folder.

    Args:
        asset_select: a fully defined asset widget
        gee_user_dir: the path to the GEE directory
    """
    # test function itself
    asset_select.items = []
    asset_select._get_items()

    assert str(gee_user_dir / "image") in asset_select.items

    # Test button event
    # we should export an extra asset and check if the new one is here but
    # that is 30 extra seconds so we cannot afford yet
    asset_select.items = []
    asset_select.fire_event("click:prepend", None)

    assert str(gee_user_dir / "image") in asset_select.items


@pytest.fixture(scope="session")
def default_items() -> List[str]:
    """Some default public data from GEE.

    Returns:
        list of DEM, L1, SKYSAT images
    """
    return [
        "OSU/GIMP/DEM",
        "ASTER/AST_L1T_003",
        "SKYSAT/GEN-A/PUBLIC/ORTHO/RGB",
    ]


@pytest.fixture(scope="function")
def asset_select(gee_dir: Path) -> sw.AssetSelect:
    """Create a default assetSelect.

    Args:
        gee_dir: the path to the session defined GEE directory

    Returns:
        The assertSelected wired to the session folder
    """
    return sw.AssetSelect(folder=str(gee_dir))
