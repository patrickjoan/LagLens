import json
import os

import pyproj
import rtree
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

    def draw(self, columns: int, lines: int) -> str:
        """Draw an ASCII representation of the world map.

        Args:
            columns (int): The number of columns (width) for the ASCII map.
            lines (int): The number of lines (height) for the ASCII map.

        Returns:
            str: A string representation of the world map in ASCII format.

        Raises:
            ValueError: If columns or lines are less than or equal to zero.

        """
        if columns <= 0 or lines <= 0:
            raise ValueError("Columns and lines must be greater than zero.")

        land = "*"
        water = " "
        map_lines = []

        # Calculate pixel dimensions
        pixel_width = (self.xmax - self.xmin) / columns
        pixel_height = (self.ymax - self.ymin) / lines

        for line in range(lines):
            line_chars = []
            for col in range(columns):
                x = self.xmin + (col + 0.5) * pixel_width
                y = self.ymax - (line + 0.5) * pixel_height

                is_land = any(
                    geom.intersects(Point(x, y))
                    for n_obj in self.index.intersection((x, y, x, y), objects=True)
                    if (geom := n_obj.object)
                )
                line_chars.append(land if is_land else water)
            map_lines.append("".join(line_chars))

        return "\n".join(map_lines)
