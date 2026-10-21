#!/usr/bin/env bash
# Open built decks in Keynote and PowerPoint, as a release check (macOS, both apps installed).
#
#   tests/app-open.sh [-a keynote|powerpoint|both] [deck.pptx ...]
#
# Without files: every decks/*/*.pptx (build them first: `make all` in each deck directory).
# Each file is opened by the app's own AppleScript `open` (Apple Events: no keystrokes, nothing
# to click) and closed unsaved; a file the app refuses is a FAIL. Keynote's "can't be imported"
# alert and PowerPoint's "Repair?" prompt are modal and hold the Apple Event, so a 60 s timeout
# with no document showing 90 s later is the FAIL, and the app is then quit by its process
# before the next file (a slow open, the first after the app starts, counts once this file's
# document shows). An app left with a window after the document closes (Keynote's import
# warnings, which AppleScript cannot close and the next open waits behind) is quit first. Each
# file is opened as a copy in a temporary directory: a sandboxed app asks before reading
# ~/Documents, modally too. It stops rather than quit an app that holds a document of its own.
# Controls come first and show the verdicts are real: the ncar template (opens in both) and,
# for Keynote, a one-slide pandoc deck with a speaker note as pandoc writes it (refused: its
# notes slide lacks p:clrMapOvr, which notes_clrmap.py adds; needs pandoc). The first run asks,
# once, to let the terminal control each app. Exit 1 if a file or a control goes the wrong way.
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
apps=both
while getopts "a:" o; do
  case $o in a) apps=$OPTARG ;; *) sed -n '2,19p' "$0"; exit 2 ;; esac
done
shift $((OPTIND - 1))
case $apps in keynote|powerpoint|both) ;; *) echo "app-open: -a keynote|powerpoint|both" >&2; exit 2 ;; esac
files=("$@")
if [ ${#files[@]} -eq 0 ]; then
  for f in "$ROOT"/decks/*/*.pptx; do [ -e "$f" ] && files+=("$f"); done
  [ ${#files[@]} -gt 0 ] || { echo "app-open: no decks/*/*.pptx; build the decks first" >&2; exit 2; }
fi
for i in "${!files[@]}"; do   # AppleScript's POSIX file needs an absolute path
  [ -f "${files[$i]}" ] || { echo "app-open: ${files[$i]}: no such file" >&2; exit 2; }
  files[$i]=$(cd "$(dirname "${files[$i]}")" && pwd)/$(basename "${files[$i]}")
done

# the copies' directory: "app-open." in every path, so a run closes its own documents (and an
# interrupted run's), never the user's
tmp=$(mktemp -d "${TMPDIR:-/tmp}/app-open.XXXXXX")
bad=0

# app <name>: the application's name, its process, its document class and the timeout
app_name()  { [ "$1" = keynote ] && echo "Keynote" || echo "Microsoft PowerPoint"; }
app_proc()  { [ "$1" = keynote ] && echo "Keynote" || echo "Microsoft PowerPoint"; }
app_docs()  { [ "$1" = keynote ] && echo "documents" || echo "presentations"; }
app_wait()  { echo 60; }

docs_open() {   # <app>: how many documents it holds, or nothing when it does not answer
  osascript -e 'with timeout of 5 seconds' -e "tell application \"$(app_name "$1")\" to count $(app_docs "$1")" \
    -e 'end timeout' 2>/dev/null
}

quit_app() {   # <app>: quit by its process (a modal alert ignores a polite quit)
  pkill -x "$(app_proc "$1")"
  while pgrep -x "$(app_proc "$1")" >/dev/null; do sleep 1; done
}

ready_app() {   # <app>: launch it and wait until it answers (after a quit_app, the next open ran
  # before Keynote was ready: "every slide ... doesn't understand count")
  osascript -e "tell application \"$(app_name "$1")\" to activate" >/dev/null 2>&1
  for _ in $(seq 1 60); do [ -n "$(docs_open "$1")" ] && return 0; sleep 1; done
  return 1
}

close_ours() {   # <app>: close, saving nothing, every document opened from an app-open copy (this
  # run's or an interrupted one's: its file was deleted, and the next run's guard then hung on it)
  pgrep -x "$(app_proc "$1")" >/dev/null || return 0
  if [ "$1" = keynote ]; then
    osascript -e 'with timeout of 10 seconds' -e 'tell application "Keynote"' \
      -e 'repeat with d in (get every document)' \
      -e 'try' -e 'if (POSIX path of (file of d)) contains "app-open." then close d saving no' -e 'end try' \
      -e 'end repeat' -e 'end tell' -e 'end timeout' >/dev/null 2>&1   # (a file reference: no alias, the file may be gone)
  else
    osascript -e 'with timeout of 10 seconds' -e 'tell application "Microsoft PowerPoint"' \
      -e 'repeat with d in (get every presentation)' \
      -e 'try' -e 'if (full name of d) contains "app-open." then close d saving no' -e 'end try' \
      -e 'end repeat' -e 'end tell' -e 'end timeout' >/dev/null 2>&1
  fi
}

cleanup() {   # on exit, an interrupted run's included: our documents closed, then the copies gone
  for a in keynote powerpoint; do close_ours "$a"; done
  rm -rf "$tmp"
}
trap cleanup EXIT

settle() {   # <app>, after an OK: quit it if a window outlived the document (Keynote's "may look
  # different" warnings stay open, AppleScript cannot close them, and the next open then waits
  # behind them); politely, since it holds no document of ours or anyone's by now
  local w; w=$(osascript -e 'with timeout of 5 seconds' -e "tell application \"$(app_name "$1")\" to count windows" \
    -e 'end timeout' 2>/dev/null)
  [ -n "$w" ] && [ "$w" != 0 ] || return 0
  osascript -e 'with timeout of 20 seconds' -e "tell application \"$(app_name "$1")\" to quit" -e 'end timeout' >/dev/null 2>&1
  for _ in $(seq 1 20); do pgrep -x "$(app_proc "$1")" >/dev/null || return 0; sleep 1; done
  quit_app "$1"
}

try() {   # <app> <file>: prints OK (n slides) or FAIL (why)
  local app=$1 r n f names stem
  # a copy in a temporary directory: the apps are sandboxed, and a file under ~/Documents (or
  # ~/Downloads) raises macOS's folder-access prompt, modal like a refusal
  f=$(mktemp -d "$tmp/open.XXXX")/$(basename "$2"); cp "$2" "$f"
  pgrep -x "$(app_proc "$app")" >/dev/null || ready_app "$app"   # launched and answering first
  if pgrep -x "$(app_proc "$app")" >/dev/null; then
    n=$(docs_open "$app")
    if [ -n "$n" ] && [ "$n" != 0 ]; then
      echo "STOP $(app_name "$app") holds $n document(s) of its own; close them first"
      return
    fi
  fi
  if [ "$app" = keynote ]; then
    r=$(osascript - "$f" "$(app_wait "$app")" 2>&1 <<'AS'
on run argv
  set p to POSIX file (item 1 of argv)
  set t to (item 2 of argv) as integer
  tell application "Keynote"
    with timeout of t seconds
      try
        set d to open p
        if d is missing value then return "FAIL (import refused)"
        set n to count of slides of d
        close d saving no
        return "OK " & n & " slides"
      on error m number e
        if e is -1712 then return "TIMEOUT"
        return "FAIL (" & m & ")"
      end try
    end timeout
  end tell
end run
AS
)
  else
    r=$(osascript - "$f" "$(app_wait "$app")" 2>&1 <<'AS'
on run argv
  set p to POSIX file (item 1 of argv)
  set t to (item 2 of argv) as integer
  tell application "Microsoft PowerPoint"
    with timeout of t seconds
      try
        open p
        set d to active presentation
        set n to count of slides of d
        close d saving no
        return "OK " & n & " slides"
      on error m number e
        if e is -1712 then return "TIMEOUT"
        return "FAIL (" & m & ")"
      end try
    end timeout
  end tell
end run
AS
)
  fi
  if [ "$r" = TIMEOUT ]; then   # slow, or held by a modal alert? A slow open shows its document
    r="FAIL (a modal alert: import refused or Repair?)"   # within 90 s more; an app may answer
    for _ in $(seq 1 45); do                              # "0" while it is still loading
      n=$(docs_open "$app")
      if [ -n "$n" ] && [ "$n" != 0 ]; then   # this file's document, not one left over
        names=$(osascript -e 'with timeout of 5 seconds' \
          -e "tell application \"$(app_name "$app")\" to get name of every $(app_docs "$app" | sed 's/s$//')" \
          -e 'end timeout' 2>/dev/null)
        stem=$(basename "$f" .pptx)
        case ", $names," in
          *", $stem,"*|*", $stem.pptx,"*) r="OK (slow)" ;;
          *) r="FAIL (another document showed: $names)" ;;
        esac
        osascript -e "tell application \"$(app_name "$app")\" to close every $(app_docs "$app" | sed 's/s$//') saving no" >/dev/null 2>&1
        break
      fi
      sleep 2
    done
  fi
  case $r in OK*) settle "$app" ;; *) quit_app "$app" ;; esac
  echo "$r"
}

check() {   # <app> <file> <expect: OK|FAIL> [label]
  local r; r=$(try "$1" "$2")
  case $r in STOP*) echo "app-open: ${r#STOP }" >&2; exit 1 ;; esac
  printf '  %-44s %s\n' "${4:-$(basename "$2")}" "$r"
  case $r in "$3"*) ;; *) bad=1; [ "$3" = FAIL ] && echo "  ^ the control opened: these verdicts cannot be trusted" ;; esac
}

for app in keynote powerpoint; do
  [ "$apps" = both ] || [ "$apps" = "$app" ] || continue
  if ! osascript -e "id of application \"$(app_name "$app")\"" >/dev/null 2>&1; then
    echo "app-open: $(app_name "$app") is not installed" >&2; bad=1; continue
  fi
  echo "== $(app_name "$app")"
  # pre-flight: an instance that does not answer (wedged on a document whose file is gone) is
  # quit, else the guard reads "no answer" as "nothing open" and the first open hangs; then our
  # leftover documents are closed
  if pgrep -x "$(app_proc "$app")" >/dev/null && [ -z "$(docs_open "$app")" ]; then
    echo "  ($(app_name "$app") does not answer: quitting it)"; quit_app "$app"
  fi
  close_ours "$app"
  check "$app" "$ROOT/liveries/ncar/template.pptx" OK "control: the ncar template (opens)"
  if [ "$app" = keynote ]; then
    pandoc=${QUARTO_PANDOC:-$(command -v pandoc || true)}
    if [ -n "$pandoc" ]; then
      printf '## A slide\n\nText.\n\n::: notes\nA note.\n:::\n' | "$pandoc" -o "$tmp/refused.pptx"
      check "$app" "$tmp/refused.pptx" FAIL "control: pandoc's raw notes (refused)"
    else
      echo "  (no pandoc: the refused control is skipped)"
    fi
  fi
  for f in "${files[@]}"; do check "$app" "$f" OK; done
done
exit $bad
