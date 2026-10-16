#!/usr/bin/env python3
"""Pictodle maintenance tool.

Run from the root of the site (the folder that holds index.html):

    python tools/pictodle_tool.py add new-maps          # add every map folder inside new-maps/
    python tools/pictodle_tool.py hide JD2/monstermash  # take a map out of the game
    python tools/pictodle_tool.py unhide JD2/monstermash
    python tools/pictodle_tool.py list                  # summary + the next 14 Dailies
    python tools/pictodle_tool.py check                 # sanity-check the data files

Needs Python 3.8+ and Pillow (pip install pillow).
See tools/README.md for the map.json format.
"""
import json, math, os, random, sys, datetime, re
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required: pip install pillow")

ROOT = Path.cwd()
MAPS = ROOT / "data" / "maps.json"
DAILY = ROOT / "data" / "daily.json"
ATLAS_DIR = ROOT / "p"
IMG_EXT = {".png", ".webp", ".jpg", ".jpeg", ".gif"}
DIFF = {"easy": 1, "medium": 2, "hard": 3, "extreme": 4, "hardest": 4}
GENDER = {"f": "F", "female": "F", "m": "M", "male": "M", "nb": "NB", "non-binary": "NB", "nonbinary": "NB",
          "x": "X", "gender-switching": "X", "switching": "X", "o": "O", "other": "O"}
SAFETY_DAYS = 2  # never touch today or tomorrow, so nobody's current puzzle changes


def load():
    if not MAPS.exists() or not DAILY.exists():
        sys.exit("Run this from the site folder (the one with index.html, data/ and p/).")
    return json.loads(MAPS.read_text("utf-8")), json.loads(DAILY.read_text("utf-8"))


def save(db, sched):
    MAPS.write_text(json.dumps(db, separators=(",", ":"), ensure_ascii=False), "utf-8")
    DAILY.write_text(json.dumps(sched, indent=0, ensure_ascii=False), "utf-8")


def today_index(sched):
    """0-based index of today's Daily (UTC, matching the game)."""
    epoch = datetime.date.fromisoformat(sched["epoch"])
    return (datetime.datetime.now(datetime.timezone.utc).date() - epoch).days


def first_editable(sched):
    return max(0, today_index(sched) + SAFETY_DAYS)


def to_cell(path, cell):
    im = Image.open(path).convert("RGBA")
    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)
    gray = im.convert("L")
    la = Image.merge("LA", (gray, im.getchannel("A")))
    w, h = la.size
    sc = cell / max(w, h)
    if sc != 1:
        la = la.resize((max(1, round(w * sc)), max(1, round(h * sc))), Image.LANCZOS)
    return la


def read_map_folder(folder):
    meta_path = folder / "map.json"
    if not meta_path.exists():
        raise ValueError(f"{folder.name}: missing map.json")
    meta = json.loads(meta_path.read_text("utf-8"))
    imgs = sorted(p for p in folder.iterdir() if p.suffix.lower() in IMG_EXT)
    if not imgs:
        raise ValueError(f"{folder.name}: no pictogram images found")
    for k in ("title", "game"):
        if not meta.get(k):
            raise ValueError(f"{folder.name}: map.json needs \"{k}\"")
    d = meta.get("difficulty")
    if isinstance(d, str):
        d = DIFF.get(d.strip().lower(), 0)
    colors = []
    for c in meta.get("colors", []):
        if isinstance(c, str):
            c = [c, ""]
        name, hexv = c[0], (c[1] if len(c) > 1 else "")
        if hexv and not re.fullmatch(r"#[0-9A-Fa-f]{6}", hexv):
            raise ValueError(f"{folder.name}: color \"{hexv}\" must look like #12AB34")
        colors.append([name, hexv.upper() if hexv else ""])
    coaches = [GENDER.get(str(g).strip().lower(), str(g)) for g in meta.get("coaches", [])]
    entry = {
        "id": meta.get("id") or f"{meta['game']}/{folder.name}",
        "t": meta["title"], "a": meta.get("artist", ""), "g": meta["game"],
        "ty": "A" if str(meta.get("type", "Classic")).lower().startswith("alt") else "C",
        "y": str(meta.get("year", "")), "d": int(d or 0), "pc": colors, "dg": coaches,
    }
    if meta.get("gameName"):
        entry["gn"] = meta["gameName"]
    if meta.get("alt"):
        entry["x"] = meta["alt"]
    if meta.get("colorSequence"):
        entry["cs"] = 1
    if meta.get("estimatedColors"):
        entry["pe"] = 1
    return entry, imgs


def cmd_add(src):
    db, sched = load()
    cell, cols, per = db["cell"], db["cols"], db["per"]
    src = Path(src)
    folders = sorted(p for p in src.iterdir() if p.is_dir() and not p.name.startswith(("_", "."))) if src.is_dir() else []
    if not folders:
        sys.exit(f"No map folders found in {src}")
    known = {m["id"] for m in db["maps"]}
    batch = []
    for f in folders:
        try:
            entry, imgs = read_map_folder(f)
        except ValueError as e:
            print(f"skip  {e}")
            continue
        if entry["id"] in known:
            print(f"skip  {entry['id']} (already in the game)")
            continue
        batch.append((entry, imgs))
        known.add(entry["id"])
    if not batch:
        print("Nothing new to add.")
        return
    # New maps start on a fresh atlas so no existing image file is rewritten.
    slot = math.ceil(db["slots"] / per) * per
    atlas, atlas_no = None, None
    rows = per // cols

    def flush():
        nonlocal atlas
        if atlas is not None:
            used = (slot - 1) % per + 1
            h = ((used - 1) // cols + 1) * cell
            atlas.crop((0, 0, cols * cell, h)).save(ATLAS_DIR / f"{atlas_no:03d}.webp", "WEBP", quality=70, method=4)
            atlas = None

    for entry, imgs in batch:
        entry["s"] = slot
        n = 0
        for p in imgs:
            try:
                im = to_cell(p, cell)
            except Exception as e:
                print(f"  ! {p.name}: {e}")
                continue
            if slot % per == 0:
                flush()
                atlas_no = slot // per
                atlas = Image.new("LA", (cols * cell, rows * cell), (0, 0))
            c = slot % per
            x, y = (c % cols) * cell + (cell - im.size[0]) // 2, (c // cols) * cell + (cell - im.size[1]) // 2
            atlas.paste(im, (x, y))
            slot += 1
            n += 1
        entry["n"] = n
        db["maps"].append(entry)
        print(f"add   {entry['id']}  ({n} pictos)")
    flush()
    db["slots"] = slot
    # Slot the new maps into random FUTURE days only; past and current Dailies never change.
    days = sched["days"]
    lo = min(first_editable(sched), len(days))
    rng = random.Random()
    for entry, _ in batch:
        pos = rng.randint(lo, len(days))
        days.insert(pos, entry["id"])
        print(f"      first Daily: #{pos + 1}")
    save(db, sched)
    print(f"Done. {len(db['maps'])} maps, {len(days)} days in the Daily cycle.")


def cmd_hide(mid, hide=True):
    db, sched = load()
    m = next((m for m in db["maps"] if m["id"] == mid), None)
    if not m:
        sys.exit(f"No map with id {mid}. Use 'list --all' to see ids.")
    days = sched["days"]
    lo = min(first_editable(sched), len(days))
    if hide:
        m["h"] = 1
        before = len(days)
        sched["days"] = days[:lo] + [d for d in days[lo:] if d != mid]
        print(f"Hidden {mid}. Removed it from {before - len(sched['days'])} future Daily day(s).")
    else:
        m.pop("h", None)
        if mid not in days[lo:]:
            days.insert(random.Random().randint(lo, len(days)), mid)
        print(f"Unhidden {mid} and scheduled it on a future Daily.")
    save(db, sched)


def cmd_list(show_all=False):
    db, sched = load()
    ix = {m["id"]: m for m in db["maps"]}
    t = today_index(sched)
    live = [m for m in db["maps"] if not m.get("h")]
    print(f"{len(db['maps'])} maps ({len(live)} playable), {db['slots']} picto slots, {len(sched['days'])} days per Daily cycle")
    print(f"Today is Daily #{t + 1}")
    days = sched["days"]
    for k in range(t, t + 14):
        mid = days[k % len(days)]
        m = ix.get(mid, {})
        print(f"  #{k + 1:<5} {mid:<32} {m.get('t', '?')}{' - ' + m['x'] if m.get('x') else ''}")
    if show_all:
        for m in db["maps"]:
            print(("[hidden] " if m.get("h") else "") + m["id"], "-", m["t"], ("- " + m["x"]) if m.get("x") else "")


def cmd_check():
    db, sched = load()
    ids = [m["id"] for m in db["maps"]]
    problems = []
    if len(ids) != len(set(ids)):
        problems.append("duplicate map ids")
    idset = set(ids)
    missing = [d for d in sched["days"] if d not in idset]
    if missing:
        problems.append(f"{len(missing)} scheduled ids not in maps.json, e.g. {missing[:3]}")
    hidden_future = [d for d in sched["days"][first_editable(sched):] if d in idset and db["maps"][ids.index(d)].get("h")]
    if hidden_future:
        problems.append(f"{len(hidden_future)} hidden maps still scheduled in the future")
    unscheduled = [m["id"] for m in db["maps"] if not m.get("h") and m["id"] not in set(sched["days"])]
    if unscheduled:
        problems.append(f"{len(unscheduled)} playable maps never appear in the Daily, e.g. {unscheduled[:3]}")
    need = math.ceil(db["slots"] / db["per"])
    absent = [i for i in range(need) if not (ATLAS_DIR / f"{i:03d}.webp").exists() and any(m["s"] // db["per"] <= i <= (m["s"] + m["n"] - 1) // db["per"] for m in db["maps"])]
    if absent:
        problems.append(f"missing atlas files: {absent[:5]}")
    print("All good." if not problems else "Problems:\n  - " + "\n  - ".join(problems))


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help", "help"):
        print(__doc__)
    elif a[0] == "add" and len(a) == 2:
        cmd_add(a[1])
    elif a[0] in ("hide", "unhide") and len(a) == 2:
        cmd_hide(a[1], a[0] == "hide")
    elif a[0] == "list":
        cmd_list("--all" in a)
    elif a[0] == "check":
        cmd_check()
    else:
        print(__doc__)
