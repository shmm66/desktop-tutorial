from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.request import Request, urlopen

from academy_visuals import REMOTE_IMAGES, remote_extension

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "education_sources"
USER_AGENT = "TraderPlannerPro/10.1.0 (+https://github.com/shmm66/desktop-tutorial)"
MIN_BYTES = 5000


def _prepare_one(key: str, url: str) -> tuple[str, str]:
    target = TARGET / f"{key}{remote_extension(url)}"
    try:
        if target.is_file() and target.stat().st_size >= MIN_BYTES:
            return key, "cached"
    except OSError:
        pass

    last_error = None
    for attempt in range(2):
        request = Request(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "image/avif,image/webp,image/png,image/jpeg,*/*"},
        )
        try:
            with urlopen(request, timeout=10) as response:
                payload = response.read()
            if len(payload) < MIN_BYTES:
                raise ValueError(f"image too small ({len(payload)} bytes)")
            temporary = target.with_suffix(target.suffix + ".tmp")
            temporary.write_bytes(payload)
            temporary.replace(target)
            return key, f"downloaded ({len(payload)} bytes)"
        except Exception as exc:
            last_error = exc
    # A missing image does not break packaging: the Academy uses a native
    # Tk-drawn, fully offline diagram for any source image that could not be bundled.
    return key, f"unavailable; using local diagram fallback ({type(last_error).__name__}: {last_error})"


def main() -> None:
    TARGET.mkdir(parents=True, exist_ok=True)
    jobs = list(REMOTE_IMAGES.items())
    ready = 0
    with ThreadPoolExecutor(max_workers=6, thread_name_prefix="academy-assets") as pool:
        futures = [pool.submit(_prepare_one, key, url) for key, url in jobs]
        for future in as_completed(futures):
            key, status = future.result()
            if status.startswith("downloaded") or status == "cached":
                ready += 1
                print(f"[academy asset] {key}: {status}", flush=True)
            else:
                print(f"[academy asset] WARNING {key}: {status}", flush=True)
    print(f"Offline Academy asset library: {ready}/{len(jobs)} images available; native local diagrams cover missing files.", flush=True)


if __name__ == "__main__":
    main()
