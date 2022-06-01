from ipyleaflet import WidgetControl, GeoJSON, LocalTileLayer
import ee
import geopandas as gpd
from shapely import geometry as sg
import rioxarray
import xarray_leaflet
from rasterio.crs import CRS
import rasterio as rio
import ipyvuetify as v

from sepal_ui import color
from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import utils as su
from sepal_ui.mapping.layer import EELayer
from sepal_ui.mapping.map_btn import MapBtn
from sepal_ui.frontend.styles import COMPONENTS
from sepal_ui.message import ms

# call x_array leaflet at least once
# flake8 will complain as it's a pluggin (i.e. never called)
# We don't want to ignore testing F401
xarray_leaflet


class ValueInspector(WidgetControl):
    """
    Widget control displaying a btn on the map. When clicked the menu expand to show the values of each layer available on the map. The menu values will be change when the user click on a location on the map. It can digest any Layer added on a SepalMap.

    Args:
        m (ipyleaflet.Map): the map on which he vinspector is displayed to interact with it's layers
    """

    m = None
    "(ipyleaflet.Map) the map on which he vinspector is displayed to interact with it's layers"

    w_loading = None
    "(vuetify.ProgressLinear): the progress bar on top of the Card"

    menu = None
    "(vuetify.Menu): the menu displayed when the map btn is clicked"

    text = None
    "(vuetify.CardText): the text element from the card that is edited when the user click on the map"

    def __init__(self, m, **kwargs):

        # load the map
        self.m = m

        # set some default parameters
        kwargs["position"] = kwargs.pop("position", "bottomright")

        # create a loading to place it on top of the card. It will always be visible
        # even when the card is scrolled
        self.w_loading = sw.ProgressLinear(
            indeterminate=False,
            background_color=color.menu,
            color=COMPONENTS["PROGRESS_BAR"]["color"][v.theme.dark],
        )

        # create a clickable btn
        btn = MapBtn(logo="fas fa-crosshairs", v_on="menu.on")
        slot = {"name": "activator", "variable": "menu", "children": btn}
        close_btn = sw.Icon(children=["fas fa-times"], small=True)
        title = sw.Html(tag="h4", children=[ms.v_inspector.title])
        card_title = sw.CardTitle(children=[title, sw.Spacer(), close_btn])
        self.text = sw.CardText(children=[ms.v_inspector.landing])
        card = sw.Card(
            tile=True,
            color=color.menu,
            max_height="40vh",
            children=[card_title, self.text],
            min_width="400px",
            style_="overflow: auto",
        )

        # assemble everything in a menu
        self.menu = sw.Menu(
            v_model=False,
            value=False,
            close_on_click=False,
            close_on_content_click=False,
            children=[self.w_loading, card],
            v_slots=[slot],
            offset_x=True,
            top="bottom" in kwargs["position"],
            bottom="top" in kwargs["position"],
            left="right" in kwargs["position"],
            right="left" in kwargs["position"],
        )

        super().__init__(widget=self.menu, **kwargs)

        # add js behaviour
        self.menu.observe(self.toggle_cursor, "v_model")
        self.m.on_interaction(self.read_data)
        close_btn.on_event("click", lambda *_: setattr(self.menu, "v_model", False))

    def toggle_cursor(self, change):
        """
        Toggle the cursor display on the map to notify to the user that the inspector
        mode is activated
        """

        cursors = [{"cursor": "grab"}, {"cursor": "crosshair"}]
        self.m.default_style = cursors[self.menu.v_model]

        return

    def read_data(self, **kwargs):
        """
        Read the data when the map is clicked with the vinspector activated

        Args:
            kwargs: any arguments from the map interaction
        """
        # check if the v_inspector is active
        is_click = kwargs.get("type") == "click"
        is_active = self.menu.v_model is True
        if not (is_click and is_active):
            return

        # set the loading mode. Cannot be done as a decorator to avoid
        # flickering while moving the cursor on the map
        self.w_loading.indeterminate = True
        self.m.default_style = {"cursor": "wait"}

        # init the text children
        children = []

        # get the coordinates as (x, y)
        lng, lat = coords = [c for c in reversed(kwargs.get("coordinates"))]

        # write the coordinates and the scale
        txt = ms.v_inspector.coords.format(round(self.m.get_scale()))
        children.append(sw.Html(tag="h4", children=[txt]))
        children.append(sw.Html(tag="p", children=[f"[{lng:.3f}, {lat:.3f}]"]))

        # write the layers data
        children.append(sw.Html(tag="h4", children=["Layers"]))
        layers = [lyr for lyr in self.m.layers if not lyr.base]
        for lyr in layers:
            children.append(sw.Html(tag="h5", children=[lyr.name]))

            if isinstance(lyr, EELayer):
                data = self._from_eelayer(lyr.ee_object, coords)
            elif isinstance(lyr, GeoJSON):
                data = self._from_geojson(lyr.data, coords)
            elif isinstance(lyr, LocalTileLayer):
                data = self._from_raster(lyr.raster, coords)
            else:
                data = {ms.v_inspector.info.header: ms.v_inspector.info.text}

            for k, val in data.items():
                children.append(sw.Html(tag="span", children=[f"{k}: {val}"]))
                children.append(sw.Html(tag="br", children=[]))

        # set them in the card
        self.text.children = children

        # set back the cursor to crosshair
        self.w_loading.indeterminate = False
        self.m.default_style = {"cursor": "crosshair"}

        # one last flicker to replace the menu next to the btn
        # if not it goes below the map
        # i've try playing with the styles but it didn't worked out well
        # lost hours on this issue : 1h
        self.menu.v_model = False
        self.menu.v_model = True

        return

    @su.need_ee
    def _from_eelayer(self, ee_obj, coords):
        """
        extract the values of the ee_object for the considered point

        Args:
            ee_obj (ee.object): the ee object to reduce to a single point
            coords (tuple): the coordinates of the point (lng, lat).

        Return:
            (dict): tke value associated to the image/feature names
        """

        # create a gee point
        ee_point = ee.Geometry.Point(*coords)

        if isinstance(ee_obj, ee.FeatureCollection):

            # filter all the value to the point
            features = ee_obj.filterBounds(ee_point)

            # if there is none, print non for every property
            if features.size().getInfo() == 0:
                cols = ee_obj.first().propertyNames().getInfo()
                pixel_values = {c: None for c in cols if c not in ["system:index"]}

            # else simply return all the values of the first element
            else:
                pixel_values = features.first().toDictionary().getInfo()

        elif isinstance(ee_obj, ee.Image):

            # reduce the layer region using mean
            pixel_values = ee_obj.reduceRegion(
                geometry=ee_point,
                scale=self.m.get_scale(),
                reducer=ee.Reducer.mean(),
            ).getInfo()

        else:
            raise ValueError(
                f'the layer object is a "{type(ee_obj)}" which is not accepted.'
            )

        return pixel_values

    def _from_geojson(self, data, coords):
        """
        extract the values of the data for the considered point

        Args:
            data (GeoJSON): the shape to reduce to a single point
            coords (tuple): the coordinates of the point (lng, lat).

        Return:
            (dict): tke value associated to the feature names
        """

        # extract the coordinates as a poin
        point = sg.Point(*coords)

        # filter the data to 1 point
        gdf = gpd.GeoDataFrame.from_features(data)
        gdf_filtered = gdf[gdf.contains(point)]
        skip_cols = ["geometry", "style"]

        # only display the columns name if empty
        if len(gdf_filtered) == 0:
            cols = gdf.columns.to_list()
            return {c: None for c in cols if c not in skip_cols}

        # else print the values of the first element
        else:
            return gdf_filtered.iloc[0, ~gdf.columns.isin(skip_cols)].to_dict()

    def _from_raster(self, raster, coords):
        """
        extract the values of the data-array for the considered point

        Args:
            raster (str): the path to the image to reduce to a single point
            coords (tuple): the coordinates of the point (lng, lat).

        Return:
            (dict): tke value associated to the feature names
        """

        # extract the coordinates as a point
        point = sg.Point(*coords)

        # extract the pixel size in degrees (equatorial appoximation)
        scale = self.m.get_scale() * 0.00001

        # open the image and unproject it
        da = rioxarray.open_rasterio(raster, masked=True)
        da = da.chunk((1000, 1000))
        if da.rio.crs != CRS.from_string("EPSG:4326"):
            da = da.rio.reproject("EPSG:4326")

        # sample is not available for da so I do as in GEE a mean reducer around 1px
        # is it an overkill ? yes
        if sg.box(*da.rio.bounds()).contains(point):
            bounds = point.buffer(scale).bounds
            window = rio.windows.from_bounds(*bounds, transform=da.rio.transform())
            da_filtered = da.rio.isel_window(window)
            means = da_filtered.mean(axis=(1, 2)).to_numpy()
            pixel_values = {
                ms.v_inspector.band.format(i + 1): v for i, v in enumerate(means)
            }

        # if the point is out of the image display None
        else:
            pixel_values = {
                ms.v_inspector.band.format(i + 1): None for i in range(da.rio.count)
            }

        return pixel_values