# Pictodle

A fan-made Wordle-style game: guess the Just Dance map from a single black-and-white pictogram. Daily and Unlimited modes, 18 cover themes, Hard Mode, stats, an Archive of past Dailies, and data import/export.

> Fan project, not affiliated with or endorsed by Ubisoft. Just Dance and its pictograms belong to Ubisoft; song titles belong to their owners. Map data comes from the [Just Dance Wiki](https://justdance.fandom.com).

## What's in this folder

| Path | What it is |
|---|---|
| `index.html` | The whole game (HTML, CSS and JavaScript in one file) |
| `data/maps.json` | Every map: title, artist, game, hints, and where its pictos sit in the image files |
| `data/daily.json` | The Daily schedule: one map id per day, starting 2026-10-15 |
| `p/000.webp …` | Pictogram sheets (128 pictos each) |
| `tools/pictodle_tool.py` | Adds, hides and checks maps without changing past Dailies |
| `new-maps/` | Drop new map folders here (see `new-maps/README.md`) |
| `fonts/` | Montserrat and Nunito Sans (SIL Open Font License, licenses included) |
| `.nojekyll` | Tells GitHub Pages to serve the files as they are |

It's a static site: no server, database or build step.

## Put it on GitHub Pages

1. Create a new repository on GitHub (public, unless you have a paid plan).
2. Upload everything in this folder to the repository's main branch. With Git:

       git init
       git add .
       git commit -m "Pictodle"
       git branch -M main
       git remote add origin https://github.com/YOUR-NAME/YOUR-REPO.git
       git push -u origin main

   Or use **GitHub Desktop**, or drag the files into the repository page in your browser (the web uploader takes up to 100 files at a time, so upload `p/` in a few batches).
3. In the repository, open **Settings → Pages**, set **Source** to **Deploy from a branch**, pick **main** and **/ (root)**, and save.
4. After a minute or two the game is live at `https://YOUR-NAME.github.io/YOUR-REPO/`.

To use your own domain, add it under **Settings → Pages → Custom domain**.

## Adding, removing and checking maps

You need Python 3 and Pillow (`pip install pillow`). Run these from this folder:

    python tools/pictodle_tool.py add new-maps          # add new maps (see new-maps/README.md)
    python tools/pictodle_tool.py hide JD2/monstermash  # take a map out of the game
    python tools/pictodle_tool.py unhide JD2/monstermash
    python tools/pictodle_tool.py list                  # today's Daily and the next 13
    python tools/pictodle_tool.py list --all            # also every map id
    python tools/pictodle_tool.py check                 # make sure everything lines up

Then commit and push; GitHub Pages updates on its own.

How it keeps the Daily fair:

- **Past Dailies never change.** New maps are slotted into random future days (never today or tomorrow), so the Archive and everyone's saved results stay correct.
- **Nothing is renumbered.** New maps and their pictos are added at the end, so existing image files are never rewritten.
- **Hide, don't delete.** `hide` removes a map from guesses, Unlimited and future Dailies but keeps it in the files so saved data still lines up. Don't delete entries from `maps.json` or reorder `daily.json` by hand.
- After the last day in `daily.json`, the Daily starts the list over.

## Notes

- The title font is Just Dance Bold, used only if it's installed on the player's device (it isn't included because of its license). Everyone else sees Montserrat, which is bundled in `fonts/`.
- Players' stats live in their browser and are tied to the site's address. If you move the game to a new address, players can carry their data over with **Settings → Your data**.

## Security notes

- The site is static: no server, logins, passwords, cookies or database, and it never collects player data. Stats stay in each player's own browser.
- A Content-Security-Policy in `index.html` only lets the page load its own files, which blocks injected scripts and data being sent elsewhere.
- Imported data files and codes are size-limited, only known keys are accepted, and every saved value is checked and reshaped before use, so a tampered file or code can't run code on the page.
- In **Settings → Pages**, keep **Enforce HTTPS** turned on.
- Everything in a static site is public, including `data/daily.json`, so a determined player could look up future answers. That's normal for games like this and can't be prevented without a server.
- The Contact button shows your email address in the page, so expect some spam.
- Never commit passwords, API keys or personal files to this repository.
