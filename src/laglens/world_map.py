import json
import pyproj
import rtree
from shapely.geometry import Point, shape
from shapely.ops import transform
import os

# Load world countries data
file_path = os.path.join(os.path.dirname(__file__), "data/world_countries.json")
with open(file_path) as f:
    data = json.load(f)
geoms = [shape(feature["geometry"]) for feature in data["features"]]

# Create a transformer for WGS84 to Web Mercator
transformer = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)

# Transform geometries into Web Mercator
geoms = [transform(transformer.transform, geom) for geom in geoms]

# Create spatial index
index = rtree.index.Index((n, geom.bounds, geom) for n, geom in enumerate(geoms))

# Calculate pixel dimensions
xmin, ymin = transformer.transform(-180, -85)
xmax, ymax = transformer.transform(180, 85)


def draw_world_map(columns: int, lines: int) -> str:
    """
    Draws a simple ASCII world map based on the given dimensions.

    Args:
        columns (int): The number of columns (width) for the ASCII map.
        lines (int): The number of lines (height) for the ASCII map.

    Returns:
        str: A string representation of the world map in ASCII format.

    Raises:
        ValueError: If columns or lines are less than or equal to zero.
    """
    land = "*"
    water = " "
    map_lines = []

    # Calculate pixel dimensions based on the provided columns and lines
    pixel_width = (xmax - xmin) / columns
    pixel_height = (ymax - ymin) / lines

    for line in range(lines):
        line_chars = []
        for col in range(columns):
            x = xmin + (col + 0.5) * pixel_width
            y = ymax - (line + 0.5) * pixel_height

            is_land = any(
                geom.intersects(Point(x, y))
                for n_obj in index.intersection((x, y, x, y), objects=True)
                if (geom := n_obj.object)
            )
            line_chars.append(land if is_land else water)
        map_lines.append("".join(line_chars))

    return "\n".join(map_lines)