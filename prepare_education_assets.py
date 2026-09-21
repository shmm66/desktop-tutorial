from __future__ import annotations

from pathlib import Path
from urllib.request import Request, urlopen

from academy_visuals import REMOTE_IMAGES, remote_extension

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "education_sources"  # exact source assets, downloaded during CI
USER_AGENT = "TraderPlannerPro/7.6.0 (+https://github.com/shmm66/desktop-tutorial)"


def main():
    TARGET.mkdir(parents=True, exist_ok=True)
    for key, url in REMOTE_IMAGES.items():
        target = TARGET / f"{key}{remote_extension(url)}"
        request = Request(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "image/avif,image/webp,image/png,image/jpeg,*/*"},
        )
        last_error = None
        payload = None
        for attempt in range(3):
            try:
                with urlopen(request, timeout=20) as response:
                    payload = response.read()
                if len(payload) >= 5000:
                    break
                last_error = RuntimeError(f"Source image too small for {key}: {len(payload)} bytes")
            except Exception as exc:
                last_error = exc
        if payload is None or len(payload) < 5000:
            raise RuntimeError(f"Could not fetch exact source image for {key}") from last_error
        target.write_bytes(payload)
        print(f"{key}: {len(payload)} bytes -> {target}")


if __name__ == "__main__":
    main()
