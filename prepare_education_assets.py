from __future__ import annotations

from pathlib import Path
from urllib.request import Request, urlopen

from academy_visuals import REMOTE_IMAGES, remote_extension

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "education_sources"
USER_AGENT = "TraderPlannerPro/7.4.1 (+https://github.com/shmm66/desktop-tutorial)"


def main():
    TARGET.mkdir(parents=True, exist_ok=True)
    for key, url in REMOTE_IMAGES.items():
        target = TARGET / f"{key}{remote_extension(url)}"
        request = Request(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "image/avif,image/webp,image/png,image/jpeg,*/*"},
        )
        with urlopen(request, timeout=25) as response:
            payload = response.read()
        if len(payload) < 5000:
            raise RuntimeError(f"Source image too small for {key}: {len(payload)} bytes")
        target.write_bytes(payload)
        print(f"{key}: {len(payload)} bytes -> {target}")


if __name__ == "__main__":
    main()
