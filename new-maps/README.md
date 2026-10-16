# Adding new maps

1. Make one folder per map inside `new-maps/`. Name it with the map's codename (for example `newsong`). The folder name becomes part of the map's id (`JD2027/newsong`), so keep it short, lowercase, with no spaces.
2. Put the map's pictogram images in that folder (`.png`, `.webp` or `.jpg`). Color images are fine; the tool turns them black and white.
3. Copy `_example/map.json` into the folder and fill it in (see the table below).
4. From the site folder, run:

       python tools/pictodle_tool.py add new-maps

5. Run `python tools/pictodle_tool.py check`. It should say `All good.`
6. Delete or move the map folders out of `new-maps/` (keep `_example`), then commit and push.

Folders whose id is already in the game are skipped, so running `add` twice is safe.

## map.json fields

| Field | Required | What to put |
|---|---|---|
| `title` | yes | Song title as players should guess it |
| `artist` | no | Artist credit shown in the guess list |
| `game` | yes | Game code: `JD1` `JD2` `JD3` `JD4` `JD2014` … `JD2026` `JDU` `JDDH` `JDP`, or a new code such as `JD2027` |
| `gameName` | for new codes | How the Game hint should read, e.g. `Just Dance 2027` |
| `type` | no | `Classic` (default) or `Alternate` |
| `alt` | for alternates | The routine name, e.g. `Extreme Version` (players see "Title - Extreme Version") |
| `year` | no | Song release year |
| `difficulty` | no | `Easy`, `Medium`, `Hard` or `Extreme` (leave out if unknown) |
| `colors` | no | One `["Name", "#HEX"]` pair per coach, in P1, P2… order |
| `coaches` | no | One per coach: `Female`, `Male`, `Non-binary`, `Gender-switching` or `Other` |
| `colorSequence` | no | `true` for a solo whose single coach changes color (colors are then listed in order) |
| `estimatedColors` | no | `true` if the colors aren't from the wiki; the game shows them with an asterisk |

The `_example` folder has no images, so the tool ignores it.
