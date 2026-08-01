# naming
<!-- werden: 0.12.1 badstu-flue -->

How werden-cycle names are formed, and the name pools they draw from.

## Scheme

A **werden cycle** — the project's development cycle, advanced with `/werden` — is named
`<structure>-<animal>`:

- `<structure>` — a human-chosen build-structure name, from [strukturer.json](strukturer.json).
- `<animal>` — an animal name, from [dyr.json](dyr.json).

The semantic number `<epoch>.<major>.<minor>` is *derived* from the name, never stored on its own:

- **epoch** — the leading digit, human-owned; edited by hand in `CURRENT`, preserved verbatim.
- **major** — 1-based index of the structure in [strukturer.json](strukturer.json) (`fuglekasse` = 1).
- **minor** — 1-based index of the animal in [dyr.json](dyr.json) (`flue` = 1, `spider` = 18).

```
cycle   <epoch>.<major>.<minor> <structure>-<animal>   e.g.  0.1.18 fuglekasse-spider
```

The current cycle lives in `CURRENT` at the repo root (one line); living docs carry the greppable
marker `<!-- werden: <number> <name> -->`. Names are the version; the digits are just their indices.

## The pools

### [dyr.json](dyr.json) — animals, a size mountain

An ordered list of ~500 animals shaped like a mountain. List starts to climb **smallest → largest**
(first `flue` = fly, up to `pferd` = horse) — the original well-known ladder. From
`pferd` onward the ordering **reverses**: the remaining entries descend **largest → smallest**,
so the animal grows as the project matures, crests at the horse, then shrinks back down the far
side toward fly-size. Version progression is legible at a glance, and the crest marks the turn.

Rules the list follows:

- **Ascending arm (indices 0–[pferd]): well-known animals only** — recognizable names, no obscure
  species. Unchanged from the original ladder.
- **Descending arm (indices [pferd]+): obscure animals welcome** — the far side draws on not-well-known
  species (`kiang`, `gerenuk`, `axolotl`, `hoatzin`, …) so it can descend without re-using any name
  from the climb.
- **`pferd` stays the largest, `flue` stays the smallest** — nothing tops the horse at the crest,
  and the descending tail bottoms out around fly-size (ending at `gadfly`) without going below the
  fly that anchors index 0.
- **Perceptible steps** — each entry reads as a clear size change from its neighbour. On the
  obscure far side exact ordering is sometimes hard to know, so the descent follows rough size tiers. Humpete terreng.
- **Short, ASCII, single-token** — the shortest clear form across English, German, or Norwegian
  (hence `flue` and `pferd`); no spaces, hyphens, or non-ASCII (`ø/æ/å/ä/ö/ß`). Hyphens would
  break the `<structure>-<animal>` split, so single-token is load-bearing, not just style.
- **No duplicates** — each animal appears once across the whole mountain.

### [strukturer.json](strukturer.json) — build structures, ordered by size

An ordered list of ~200 human-built structures, **smallest → largest** (first `fuglekasse` =
birdhouse, last `tokyo`) — a size ladder that climbs alongside the animals, following the same
naming rules: well-known (at least to some), short, ASCII, single-token across English/German/Norwegian, and no
duplicates.

> we have >100k werden cycles available. If more are wanted, change your desire. Borders are a good thing.
