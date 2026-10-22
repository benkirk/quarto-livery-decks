-- pptx only. The theme's per-slide layout controls (.hcenter, .vcenter,
-- .center, scale="S", .fill, .full, .caution, .feature, .wide; see the engine's engine-revealjs.lua) mean nothing
-- to pandoc's pptx writer, which drops slide classes. Carry them to
-- the engine's pptx_steps/slide_layout.py as one speaker-notes line,
--   engine-layout: hcenter vcenter scale=1.4
-- which that script applies, and removes, after rendering. Pandoc merges
-- every notes Div on a slide, so the line joins any notes the author wrote.
-- .closing becomes `closing` (the template's Closing layout); themeoptions title=light becomes
-- the string `engine-title: light` in the metadata (pandoc records lists in the pptx as empty).

if not quarto.doc.is_format("pptx") then
  return {}
end

local function here(f)   -- this file's directory: Quarto's resolver, else plain pandoc's script path
  if quarto and quarto.utils then return quarto.utils.resolve_path(f) end
  return pandoc.path.join({ pandoc.path.directory(PANDOC_SCRIPT_FILE), f })
end
local C = dofile(here("engine-common.lua"))

-- the layout controls (C.take_layout, as the other formats read them) and the slide kinds
-- (C.SLIDE_KINDS), as the words of the notes line, in one order
local WORDS = { "hcenter", "vcenter", "fill", "full", "caution", "feature", "closing", "wide" }

local function take_layout(blk)
  local lay = C.take_layout(blk, "slide-layout")
  local have, kept = {}, pandoc.List({})
  for _, c in ipairs(blk.classes) do
    if C.SLIDE_KINDS[c] then have[c] = true else kept:insert(c) end
  end
  blk.classes = kept
  if lay then
    have.hcenter, have.vcenter, have.fill, have.caution, have.wide = lay.h, lay.v, lay.fill, lay.caution, lay.wide
  end
  local words = {}
  for _, w in ipairs(WORDS) do
    if have[w] then table.insert(words, w) end
  end
  if lay and lay.scale then table.insert(words, "scale=" .. lay.scale) end
  return #words > 0 and ("engine-layout: " .. table.concat(words, " ")) or nil
end

local function light_title(meta)
  return C.theme_options(meta).title == "light"
end

-- the cover's author and institute lines as strings (one per line): pandoc's pptx writer joins the
-- authors into the subtitle placeholder and drops the institute, and records lists in
-- docProps/custom.xml as empty strings; slide_layout.py's cover_byline() reads these
local function lines_of(v)
  local out = {}
  if not v then return out end
  for _, it in ipairs(pandoc.utils.type(v) == "List" and v or { v }) do
    local s = pandoc.utils.stringify(type(it) == "table" and (it.name and (it.name.literal or it.name)) or it)
    if s ~= "" then table.insert(out, s) end
  end
  return out
end

local function byline_meta(meta)
  local authors, institutes = lines_of(meta["by-author"] or meta["author"]), {}
  for _, it in ipairs(meta["by-author"] and meta["by-author"] or {}) do
    for _, s in ipairs(lines_of(it.affiliations)) do table.insert(institutes, s) end
  end
  if #institutes == 0 then institutes = lines_of(meta["institute"]) end
  if #authors > 0 then meta["engine-author"] = pandoc.MetaString(table.concat(authors, "\n")) end
  if #institutes > 0 then meta["engine-institute"] = pandoc.MetaString(table.concat(institutes, "\n")) end
end

function Pandoc(doc)
  if light_title(doc.meta) then doc.meta["engine-title"] = pandoc.MetaString("light") end
  byline_meta(doc.meta)
  local level = (PANDOC_WRITER_OPTIONS and PANDOC_WRITER_OPTIONS.slide_level) or 2
  local out, pending = pandoc.Blocks({}), nil
  local function flush()
    if pending then
      out:insert(pandoc.Div({ pandoc.Para({ pandoc.Str(pending) }) }, pandoc.Attr("", { "notes" })))
      pending = nil
    end
  end
  for _, b in ipairs(doc.blocks) do
    if C.is_slide_break(b, level) then flush() end
    if b.t == "Header" and b.level == level then pending = take_layout(b) end
    out:insert(b)
  end
  flush()
  doc.blocks = out
  return doc
end
