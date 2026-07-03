# comfyui-random-image

`LoadRandomImage` — a LoadImage-alike node: picks a file from an **arbitrary** directory on disk (not just the managed `ComfyUI/input`), manually / randomly / sequentially in alphabetical order.

## Install (manual / from archive)

1. Copy/extract the `comfyui-random-image` folder into `<ComfyUI>/custom_nodes/`
2. Restart ComfyUI
3. The node shows up as **Load Random Image 🎲** (category `image`)

Dependencies — `torch`, `Pillow`, `aiohttp`, `numpy` — already ship with ComfyUI, no separate install needed.

## Install via git

```bash
cd <ComfyUI>/custom_nodes
git clone <your_repo_URL> comfyui-random-image
```

Update:

```bash
cd <ComfyUI>/custom_nodes/comfyui-random-image
git pull
```

Restart ComfyUI after installing/updating.

## Usage

- **`directory`** — absolute path to a folder of images (recursive, `.png/.jpg/.jpeg/.webp/.bmp/.gif`)
- **Filename dropdown** — manually pick a specific file from the list
- **🎲 Randomize** — button that instantly picks a random file and updates the preview (no graph execution needed)
- **Drag & drop** an image straight onto the node — uploads it through ComfyUI's own `/upload/image`, switches `directory` to the managed input dir, and selects the uploaded file (mirrors core LoadImage's behavior)
- **`randomize_on_queue`** — random pick on **every** Queue Prompt (server-side, not just via the button)
- **`sequential_on_queue`** — next file in alphabetical order on every Queue Prompt, wrapping back to the start after the last file

The two checkboxes are mutually exclusive in the UI, and the server also rejects the queue if both end up enabled at once (guards against a hand-edited workflow.json).

**Sequential semantics:** a given run outputs the file **currently** selected (the one already shown in the preview), and the advance to the next one happens **after** — preparing the starting point for the next run. The advance is tracked in server memory per node `unique_id` + `directory`, which also protects against a batch-queue race (several runs queued before the first one finishes don't end up loading the same file repeatedly).

The node's preview shows what **actually** got loaded on the last run (survives saving/reopening the workflow), not what's queued up next.

## ⚠️ Security

The `/random_image/list`, `/random_image/pick` and `/random_image/view` routes accept a `dir` parameter with **no restriction whatsoever** — anyone who can reach ComfyUI's HTTP port (not necessarily through the graph/UI at all — a bare GET request is enough) can list and read the contents of arbitrary files on disk that the ComfyUI process has access to. This is a deliberate tradeoff for the node's core feature (loading from any folder), not a bug that an allowlist should close.

**If ComfyUI is exposed on a LAN or the internet** (not just `127.0.0.1`), keep this in mind and restrict access at the network level (VPN, an authenticating reverse proxy, firewall) rather than assuming ComfyUI or this node restrict anything on their own. This isn't unique to this node either — ComfyUI itself ships with no authentication on any of its endpoints by default.

## Tests

`selection.py` (the pure file-selection logic, no torch/numpy/PIL) is covered by unit tests:

```bash
python3 -m unittest discover -s tests -v
```

## Files

- `selection.py` — pure logic: `list_images()`, `resolve_filenames()` (lightweight, no ComfyUI dependencies, tested independently)
- `nodes.py` — the backend node (`LoadRandomImage`): tensors/masks/EXIF handling
- `routes.py` — aiohttp API: `/random_image/pick`, `/random_image/list`, `/random_image/view`, `/random_image/input_dir`
- `js/random_image.js` — frontend: file dropdown, randomize button, drag & drop, live preview, `last_loaded` persistence
- `__init__.py` — node registration (`NODE_CLASS_MAPPINGS`) and `WEB_DIRECTORY`
- `tests/` — unit tests for `selection.py`

## Known limitation

Sequential-mode advancement is kept in the ComfyUI process's memory (resets on restart, then simply continues from the last value persisted in the workflow) and isn't synchronized across multiple parallel ComfyUI workers/processes, if you happen to run that (uncommon) setup.
