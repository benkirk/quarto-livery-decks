-- On a dark livery (build/livery.json "mode": "dark"), swap each diagram Quarto baked to PNG
-- (mermaid and graphviz cells, for pptx and PDF) for a copy turned to the dark by
-- diagram_dark.py (beside this filter): lightness flipped, hues kept, white to the slide's background, black to
-- its foreground. Quarto renders diagram cells before any Lua filter runs, so the picture is
-- recolored, not the diagram source. HTML draws mermaid live in the livery's roles and inlines
-- graphviz as SVG (the engine's livery.css turns that one); a light livery is left alone.

local C = dofile(pandoc.path.join({ pandoc.path.directory(PANDOC_SCRIPT_FILE), "engine-common.lua" }))   -- beside this filter
local EXTDIR = pandoc.path.directory(PANDOC_SCRIPT_FILE)

local livery
local META   -- the document's metadata: `livery:` (an engine format's filter sets the one it resolved)

-- the livery (C.load_livery), or false: a light one, or none (a deck outside the engine's formats)
local function load_livery()
  if livery ~= nil then return livery end
  local ok, data = pcall(C.load_livery, META or {}, EXTDIR, "diagram-dark.lua")
  livery = ok and type(data) == "table" and data.mode == "dark" and data or false
  return livery
end

local function script()
  return quarto.utils.resolve_path("diagram_dark.py")   -- beside this filter
end

local done = {}   -- in.png -> out.png, so a picture used twice is recolored once

local function turn(src)
  if not (src:match("/mermaid%-figure%-%d+%.png$") or src:match("/dot%-figure%-%d+%.png$")) then return nil end
  if done[src] then return done[src] end
  local lv = load_livery()
  if not lv then return nil end
  local out = src:gsub("%.png$", "-dark.png")
  local ok = pcall(pandoc.pipe, "python3", { script(), src, out, lv.roles.background, lv.roles.foreground }, "")
  if not ok then
    io.stderr:write("diagram-dark.lua: could not turn " .. src .. " to the dark\n")
    return nil
  end
  done[src] = out
  return out
end

local function html() return FORMAT:match("html") or FORMAT:match("revealjs") end

local function Image(el)
  if html() then return nil end
  local out = turn(el.src)
  if out then el.src = out; return el end
end

-- beamer: the engine's filter has already written its pictures as raw LaTeX, and a {.full}
-- slide's as the heading's frame option (enginefull=<path>)
local function paths(text)
  local changed = false
  text = text:gsub("[^{}%s,=%[%]]+/[%w]+%-figure%-%d+%.png", function(src)
    local out = turn(src)
    if out then changed = true; return out end
  end)
  return changed and text or nil
end

local function raw(el)
  if html() or not (el.format == "latex" or el.format == "beamer") then return nil end
  local text = paths(el.text)
  if text then el.text = text; return el end
end
local function Header(el)
  local opts = el.attributes["frameoptions"]
  if html() or not opts then return nil end
  local text = paths(opts)
  if text then el.attributes["frameoptions"] = text; return el end
end

return {
  { Meta = function(meta) META = meta end },
  { Image = Image, RawInline = raw, RawBlock = raw, Header = Header },
}
