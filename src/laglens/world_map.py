import json
import os

import pyproj
import rtree
from rich.text import Text
from shapely.geometry import Point, shape
from shapely.ops import transform


class WorldMap:
    """A class to handle world map data and generate ASCII representations."""

    def __init__(
        self, data_file: str, crs_from: str = "EPSG:4326", crs_to: str = "EPSG:3857"
    ):
        """Initialize the WorldMap instance.

        Args:
            data_file (str): Path to the GeoJSON file containing world countries data.
            crs_from (str): Source coordinate reference system (default: WGS84).
            crs_to (str): Target coordinate reference system (default: Web Mercator).

        """
        self.data_file = os.path.join(os.path.dirname(__file__), data_file)
        self.crs_from = crs_from
        self.crs_to = crs_to

        # Load and transform geometries
        self.geoms = self._load_geometries()
        self.transformer = pyproj.Transformer.from_crs(crs_from, crs_to, always_xy=True)
        self.geoms = [
            transform(self.transformer.transform, geom) for geom in self.geoms
        ]

        # Create spatial index
        self.index = rtree.index.Index(
            (n, geom.bounds, geom) for n, geom in enumerate(self.geoms)
        )

        # Define map boundaries
        self.xmin, self.ymin = self.transformer.transform(-180, -75)
        self.xmax, self.ymax = self.transformer.transform(180, 85)

        # Cache for land/water grid
        self._land_grid_cache = {}

    def _load_geometries(self) -> list:
        """Load geometries from the GeoJSON file."""
        with open(self.data_file) as f:
            data = json.load(f)
        return [shape(feature["geometry"]) for feature in data["features"]]

    def _is_land_cell(self, x: float, y: float) -> bool:
        """Return True if the given coordinates are land, else False."""
        return any(
            (geom := n_obj.object) and geom.intersects(Point(x, y))
            for n_obj in self.index.intersection((x, y, x, y), objects=True)
        )

    def _get_server_grid_positions(
        self,
        servers: list,
        pixel_width: float,
        pixel_height: float,
        columns: int,
        lines: int,
    ) -> dict:
        """Map server lat/lon to grid positions and return a dict of (row, col): indicator."""
        server_positions = {}
        for server in servers:
            x, y = self.transformer.transform(server["longitude"], server["latitude"])
            col = int((x - self.xmin) / pixel_width)
            row = int((self.ymax - y) / pixel_height)
            if 0 <= col < columns and 0 <= row < lines:
                server_positions[(row, col)] = server.get("indicator", "●")
        return server_positions

    def _get_indicator_style(
        self, indicator: str, indicator_styles: dict
    ) -> str | None:
        """Return the style for a given indicator, or None if not found."""
        return indicator_styles.get(indicator)

    def _create_land_grid(
        self, columns: int, lines: int, pixel_width: float, pixel_height: float
    ):
        """Create and cache the land/water grid for the map."""
        cache_key = (columns, lines)
        if cache_key in self._land_grid_cache:
            return self._land_grid_cache[cache_key]

        def land_grid_gen():
            xmin, ymax = self.xmin, self.ymax
            for line in range(lines):
                y = ymax - (line + 0.5) * pixel_height
                row = []
                for col in range(columns):
                    x = xmin + (col + 0.5) * pixel_width
                    row.append(self._is_land_cell(x, y))
                yield row

        land_grid = list(land_grid_gen())
        self._land_grid_cache[cache_key] = land_grid
        return land_grid

    def _render_map_row(
        self, line: int, columns: int, land_grid, server_positions, indicator_styles
    ):
        """Render a single row of the map."""
        result_text = Text()
        for col in range(columns):
            pos = (line, col)
            if pos in server_positions:
                indicator = server_positions[pos]
                style = self._get_indicator_style(indicator, indicator_styles)
                if style:
                    result_text.append(indicator, style=style)
                else:
                    result_text.append(indicator)
            else:
                is_land = land_grid[line][col]
                char = "*" if is_land else " "
                style = "dim white" if is_land else ""
                result_text.append(char, style=style)
        return result_text

    def draw(self, columns: int, lines: int, servers: list | None = None) -> Text:
        """Draw an ASCII representation of the world map with server indicators."""
        if columns <= 0 or lines <= 0:
            raise ValueError("Columns and lines must be greater than zero.")

        pixel_width = (self.xmax - self.xmin) / columns
        pixel_height = (self.ymax - self.ymin) / lines

        # Create land/water grid
        land_grid = self._create_land_grid(columns, lines, pixel_width, pixel_height)

        # Map server positions
        server_positions = (
            self._get_server_grid_positions(
                servers, pixel_width, pixel_height, columns, lines
            )
            if servers
            else {}
        )

        indicator_styles = {
            "🟢": "green",
            "🟡": "yellow",
            "🔴": "red",
        }

        result_text = Text()
        for line in range(lines):
            row_text = self._render_map_row(
                line, columns, land_grid, server_positions, indicator_styles
            )
            result_text.append(row_text)
            if line < lines - 1:
                result_text.append("\n")

        return result_text
