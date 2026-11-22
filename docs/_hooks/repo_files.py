"""Docs hook: publish the repository's own data files with the site, and link them from the included text.

The pages include the repository markdown unchanged (pymdownx.snippets). Backticked file names in that text
(IGES files, the method deck, the paper inputs and results) become download links to the copies placed under
files/ in the site, so the repository files are the single source.
"""
import os
import re
from pathlib import PurePosixPath

from properdocs.structure.files import File

ROOT = os.path.abspath(os.getcwd())
SOURCES = [
    ("geometry/1st-generation", (".igs",)),
    ("method", (".pdf",)),
    ("publications/2027-ja-smi-l2/inputs", (".toml",)),
    ("publications/2027-ja-smi-l2/results", (".csv",)),
]
_BY_NAME = {}


def on_files(files, config):
    _BY_NAME.clear()
    for folder, exts in SOURCES:
        base = os.path.join(ROOT, *folder.split("/"))
        for name in sorted(os.listdir(base)):
            if name.lower().endswith(exts):
                uri = "files/%s/%s" % (folder, name)
                files.append(File.generated(config, uri, abs_src_path=os.path.join(base, name)))
                _BY_NAME[name] = uri
    return files


def on_page_content(html, page, config, files):
    here = str(PurePosixPath(page.file.src_uri).parent)

    def link(match):
        name = match.group(1)
        uri = _BY_NAME.get(name)
        if uri is None:
            return match.group(0)
        rel = os.path.relpath(uri, here).replace("\\", "/")
        return '<a href="%s"><code>%s</code></a>' % (rel, name)

    return re.sub(r"<code>([A-Za-z0-9_.+-]+\.(?:igs|pdf|toml|csv))</code>", link, html)
