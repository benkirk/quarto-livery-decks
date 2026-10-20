# Unplanned-city ledger

The record of the `unplanned-city-sweep` skill (`.claude/skills/unplanned-city-sweep/SKILL.md`):
each sweep over a window of merged PRs or an area of the tree adds an entry, newest first, and
the findings nobody picked wait in **Untriaged** until a later sweep takes them up or drops them.
Window mode starts from the newest entry's end commit.

## Entry format

```
## <date>: <window #a–#b | area <name>>

- Mode: window | area
- Range: <end of the previous entry>..<end commit> (window), or the area name
- End commit: <sha> (the `origin/main` commit the sweep read up to, or branched from)
- Done: <finding> (#PR), ...
- Tried and dropped: <finding>: <the numbers that said no>, ...
- Open: <finding>, ...
```

## Entries

None yet.

## Untriaged

None yet.
