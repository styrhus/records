# Carry it — records on a USB stick

Publishing is about reach. This page is about the other direction: your
records on a stick, usable on a machine that has nothing installed and no
network. Two files do the work.

| | What it is | Needs |
|---|---|---|
| `records.pyz` | the whole engine as one file | any Python 3.9+ |
| `pack/index.html` | the whole site as one file | a browser |

## Making the stick

```bash
tools/others/python/build-pyz.sh          # -> tools/others/python/dist/records.pyz
bin/build.sh                              # the normal build, into public/
records pack                              # -> pack/index.html
```

Then copy three things to the stick: your records checkout, `records.pyz`,
and `pack/`.

`records pack` never builds a site — it post-processes the one `bin/build.sh`
already made. Build first, pack second.

## What each machine can do

**A machine with nothing but a browser.** Open `pack/index.html`. Every
stylesheet, script, image and font is inside that one file, so it renders
from `file://` with no server and no network. Links between records became
in-page anchors.

**A machine with Python but no network.** Add the engine:

```bash
./records.pyz new "#travel a note from the train"
./records.pyz append --file records/travel/a-note-from-the-train.md --text "..."
./records.pyz version
```

Nothing is installed and nothing is left behind — the zipapp is one file
that runs and exits. This works because the engine takes no dependencies at
all; that border is what makes a stdlib `zipapp` enough.

**A machine that is not yours.** Both of the above, without touching it.
Write your records to the checkout on the stick, and commit them later from
your own machine.

## What does not travel

- **Publishing.** `records publish` needs a network and a destination.
- **Ollama.** The two-sided `/record` needs a model server; without one the
  recording skills still work, user-only.
- **git push.** A remote is a remote.
- **Rebuilding the site.** That needs Hugo. The pack is the site as it was
  when you packed it; to refresh it, build and pack again on a machine that
  has Hugo.

## Size, and the text-only pack

Images are embedded as data URIs, which run about a third larger than the
bytes they carry. A corpus with photographs makes a file no browser enjoys.
`records pack` reports the size and warns past 8 MiB. For the common case:

```bash
records pack --no-images
```

The font and the tab icon still travel — they are small and the page looks
wrong without them; photographs are dropped and their alt text stays.

## Books on the stick

The PDF and EPUB are already single files, so they are the most portable
thing here:

```bash
records pack --with-books
```

That fills `pack/` with the packed page, whichever of the PDF, EPUB and
booklet you have configured and built, and a `manifest.json` listing each
file with its SHA-256. The site's own footer links (*Get PDF*, *Get EPUB*)
are rewritten to point at the copies beside it, so the directory is its own
index. Book params you have not built are skipped with a note, the same way
`bin/build.sh` skips them when pandoc is missing.

Verify a stick that has been sitting in a drawer:

```bash
cd pack && sha256sum -c <(python3 -c "
import json;[print(f\"{f['sha256']}  {f['name']}\") for f in json.load(open('manifest.json'))['files']]")
```

## If it fetches anything, it is broken

The point of a pack is that it works on a train. Anything that would load
from the network — an embedded player, a CDN stylesheet, a remote image — is
removed while packing and listed in the report under `removed`. Ordinary
links to the web are left alone: a link you click is not a fetch.

Test it the honest way, with the network actually gone rather than merely
unused:

```bash
unshare -rn chromium --headless --dump-dom file://$PWD/pack/index.html | head
```
