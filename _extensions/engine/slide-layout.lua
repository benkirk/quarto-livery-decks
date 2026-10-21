-- pptx only. The theme's per-slide layout controls (.hcenter, .vcenter,
-- .center, scale="S", .fill, .full, .caution, .feature; see the engine's engine-revealjs.lua) mean nothing
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

local CLASSES = { hcenter = true, vcenter = true, center = true, fill = true, full = true,
                  caution = true, feature = true, closing = true }

local function take_layout(blk)
  local words, kept = {}, pandoc.List({})
  local h, v, fill, full, caution, feature, closing = false, false, false, false, false, false, false
  for _, c in ipairs(blk.classes) do
    if CLASSES[c] then
      h = h or c == "hcenter" or c == "center"
      v = v or c == "vcenter" or c == "center"
      fill = fill or c == "fill"
      full = full or c == "full"
      caution = caution or c == "caution"
      feature = feature or c == "feature"
      closing = closing or c == "closing"
    else
      kept:insert(c)
    end
  end
  if h then table.insert(words, "hcenter") end
  if v then table.insert(words, "vcenter") end
  if fill then table.insert(words, "fill") end
  if full then table.insert(words, "full") end
  if caution then table.insert(words, "caution") end
  if feature then table.insert(words, "feature") end
  if closing then table.insert(words, "closing") end
  local scale = blk.attributes["scale"]
  if scale then
    blk.attributes["scale"] = nil
    if tonumber(scale) then table.insert(words, "scale=" .. scale) end
  end
  blk.classes = kept
  return #words > 0 and ("engine-layout: " .. table.concat(words, " ")) or nil
end

local function light_title(meta)
  local to = meta["themeoptions"]
  if not to then return false end
  for _, it in ipairs(pandoc.utils.type(to) == "List" and to or { to }) do
    for kv in pandoc.utils.stringify(it):gmatch("[^,%s]+") do
      if kv == "title=light" then return true end
    end
  end
  return false
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
    if (b.t == "Header" and b.level <= level) or b.t == "HorizontalRule" then flush() end
    if b.t == "Header" and b.level == level then pending = take_layout(b) end
    out:insert(b)
  end
  flush()
  doc.blocks = out
  return doc
end
