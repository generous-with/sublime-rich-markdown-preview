"""Fetch pinned build inputs; verify integrity before reading archive members."""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import tarfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
NPM_FILES = {
    "dompurify": {"package/dist/purify.min.js": "web/vendor/purify.min.js", "package/LICENSE": "licenses/DOMPurify-LICENSE.txt"},
    "mermaid": {"package/dist/mermaid.min.js": "web/vendor/mermaid.min.js", "package/LICENSE": "licenses/Mermaid-LICENSE.txt"},
    "markdown-it": {"package/dist/browser/markdown-it.umd.min.js": "web/vendor/markdown-it.min.js", "package/LICENSE": "licenses/markdown-it-LICENSE.txt"},
    "@highlightjs/cdn-assets": {"package/highlight.min.js": "web/vendor/highlight.min.js", "package/styles/github-dark.min.css": "web/vendor/highlight.css", "package/LICENSE": "licenses/highlightjs-LICENSE.txt"},
}


def download(url, path, algorithm, digest):
    if path.exists():
        data = path.read_bytes()
    else:
        request = urllib.request.Request(url, headers={"User-Agent": "RichMarkdownPreview-build/0.2"})
        with urllib.request.urlopen(request, timeout=120) as response:
            data = response.read()
    if hashlib.new(algorithm, data).digest() != digest:
        raise ValueError("Dependency integrity mismatch: " + path.name)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(data)
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=ROOT / "build/downloads")
    args = parser.parse_args()
    lock = json.loads((ROOT / "dependencies.lock.json").read_text(encoding="utf-8"))
    output = []

    def write(name, data, package, version):
        destination = ROOT / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        output.append({"path": name, "package": package, "version": version, "sha256": hashlib.sha256(data).hexdigest()})

    for package in lock["npm"]:
        algorithm, digest = package["integrity"].split("-", 1)
        filename = package["name"].replace("/", "-").lstrip("@") + "-" + package["version"] + ".tgz"
        data = download(package["url"], args.cache_dir / filename, algorithm, base64.b64decode(digest))
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
            for member, destination in NPM_FILES[package["name"]].items():
                file = archive.extractfile(member)
                if file is None:
                    raise ValueError("Required archive member missing: " + member)
                write(destination, file.read(), package["name"], package["version"])
        print(package["name"] + " " + package["version"] + " verified")
    package = lock["webview2"]
    data = download(package["url"], args.cache_dir / ("webview2-" + package["version"] + ".nupkg"), "sha256", bytes.fromhex(package["sha256"]))
    files = {
        "lib/net462/Microsoft.Web.WebView2.Core.dll": "bin/Microsoft.Web.WebView2.Core.dll",
        "runtimes/win-x64/native/WebView2Loader.dll": "bin/WebView2Loader.dll",
        "LICENSE.txt": "licenses/WebView2-LICENSE.txt",
        "NOTICE.txt": "licenses/WebView2-NOTICE.txt",
    }
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for member, destination in files.items():
            write(destination, archive.read(member), "Microsoft.Web.WebView2", package["version"])
    (ROOT / "build").mkdir(exist_ok=True)
    (ROOT / "build/dependency-manifest.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
