-- On a dark livery (build/livery.json "mode": "dark"), swap each diagram Quarto baked to PNG
-- (mermaid and graphviz cells, for pptx and PDF) for a copy turned to the dark by
-- diagram_dark.py (beside this filter): lightness flipped, hues kept, white to the slide's background, black to
-- its foreground. Quarto renders diagram cells before any Lua filter runs, so the picture is
-- recolored, not the diagram source. HTML draws mermaid live in the livery's roles and inlines
-- graphviz as SVG (the engine's livery.css turns that one); a light livery is left alone.

local livery

local function load_livery()
  if livery ~= nil then return livery end
  livery = false
  local f = io.open("_livery/build/livery.json", "r")
  if f then
    local ok, data = pcall(pandoc.json.decode, f:read("a"))
    f:close()
    if ok and type(data) == "table" and data.mode == "dark" then livery = data end
  end
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

function Image(el)
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
RawInline, RawBlock = raw, raw

function Header(el)
  local opts = el.attributes["frameoptions"]
  if html() or not opts then return nil end
  local text = paths(opts)
  if text then el.attributes["frameoptions"] = text; return el end
end
