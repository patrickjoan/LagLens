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

    def _load_geometries(self) -> list:
        """Load geometries from the GeoJSON file."""
        with open(self.data_file) as f:
            data = json.load(f)
        return [shape(feature["geometry"]) for feature in data["features"]]

    def draw(self, columns: int, lines: int, servers: list = None) -> Text:
        """Draw an ASCII representation of the world map with server indicators.

        Args:
            columns (int): The number of columns (width) for the ASCII map.
            lines (int): The number of lines (height) for the ASCII map.
            servers (list): List of server dictionaries with latitude, longitude, and indicator.

        Returns:
            Text: A Rich Text object representation of the world map in ASCII format.

        Raises:
            ValueError: If columns or lines are less than or equal to zero.

        """
        if columns <= 0 or lines <= 0:
            raise ValueError("Columns and lines must be greater than zero.")

        land = "*"
        water = " "
        result_text = Text()

        # Calculate pixel dimensions
        pixel_width = (self.xmax - self.xmin) / columns
        pixel_height = (self.ymax - self.ymin) / lines

        # Create a mapping of server positions to indicators
        server_positions = {}
        if servers:
            for server in servers:
                # Transform lat/lon to map coordinates
                x, y = self.transformer.transform(server["longitude"], server["latitude"])

                # Convert to grid coordinates
                col = int((x - self.xmin) / pixel_width)
                row = int((self.ymax - y) / pixel_height)

                # Ensure coordinates are within bounds
                if 0 <= col < columns and 0 <= row < lines:
                    server_positions[(row, col)] = server.get("indicator", "●")

        for line in range(lines):
            for col in range(columns):
                # Check if there's a server at this position
                if (line, col) in server_positions:
                    indicator = server_positions[(line, col)]
                    # Add the indicator with appropriate styling
                    if "🟢" in indicator:
                        result_text.append(indicator, style="green")
                    elif "🟡" in indicator:
                        result_text.append(indicator, style="yellow")
                    elif "🔴" in indicator:
                        result_text.append(indicator, style="red")
                    else:
                        result_text.append(indicator)
                else:
                    x = self.xmin + (col + 0.5) * pixel_width
                    y = self.ymax - (line + 0.5) * pixel_height

                    is_land = any(
                        geom.intersects(Point(x, y))
                        for n_obj in self.index.intersection((x, y, x, y), objects=True)
                        if (geom := n_obj.object)
                    )
                    char = land if is_land else water
                    result_text.append(char, style="dim white" if is_land else "")

            # Add newline at the end of each row (except the last one)
            if line < lines - 1:
                result_text.append("\n")

        return result_text
