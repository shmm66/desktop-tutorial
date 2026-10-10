from pathlib import Path
import tempfile

from PIL import Image
from logo_3d import create_logo_image


def create_icon(path="app.ico"):
    """Build every Windows shortcut size from the same revisioned application mark."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    source = Path(tempfile.gettempdir()) / "TraderPlannerPro_3D" / "shortcut-logo-v3.png"
    create_logo_image(source, 512)
    with Image.open(source) as image:
        icon = image.convert("RGBA")
        icon.save(output, format="ICO", sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
    return output


if __name__ == "__main__":
    create_icon()
