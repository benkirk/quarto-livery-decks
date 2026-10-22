-- engine-common.lua -- what the format filters share (engine-revealjs.lua, engine-beamer.lua, and
-- pptx's slide-layout.lua, single-body.lua and grid-pptx.lua): loaded with
-- dofile(quarto.utils.resolve_path("engine-common.lua")), or under plain pandoc beside
-- PANDOC_SCRIPT_FILE, returning a table. A function here reads the same in every format (the slide
-- breaks and kinds, the layout classes, the footnotes, a .full slide's parts, the theme options,
-- the livery); what a format does with the result stays in its filter (wrap_layout,
-- hoist_footnotes, size_plots, the cards and strips).

local function has_class(el, cls)
  for _, c in ipairs(el.classes) do
    if c == cls then return true end
  end
  return false
end

-- The deck's size step: `type-body: <pt>` (the body in points; every size scales by it over the
-- livery's body, type.roles.body.pt) or `type-scale: <factor>`; type-body wins. 1 without either.
local function deck_type_scale(meta, body_pt, who)
  local function num(k)
    if meta[k] == nil then return nil end
    local v = tonumber(pandoc.utils.stringify(meta[k]))
    if not v or v <= 0 then
      quarto.log.warning(who .. ": " .. k .. " is not a positive number; ignored")
      return nil
    end
    return v
  end
  local tb, ts = num("type-body"), num("type-scale")
  if tb then return tb / body_pt end
  return ts or 1
end

-- The default livery: liveries/ncar beside the _extensions/ that holds this extension
-- (liveries/ at the top of this repo). A deck reaches the extension through a linked
-- _extensions/, and Lua does not resolve links, so the extension's own directory is found
-- first: changing into a directory does resolve them.
local function default_livery(extdir)
  local ok, real = pcall(pandoc.system.with_working_directory, extdir, pandoc.system.get_working_directory)
  local root = pandoc.path.directory(pandoc.path.directory(ok and real or extdir))
  return pandoc.path.join({ root, "liveries", "ncar" })
end

-- A slide boundary: a heading at or above the slide level, or a rule.
local function is_slide_break(blk, level)
  return (blk.t == "Header" and blk.level <= level) or blk.t == "HorizontalRule"
end

-- The slide kinds a composition draws (their classes on the slide's heading; not content slides), and
-- the per-slide layout classes of a content slide (take_layout()).
local SLIDE_KINDS = { feature = true, closing = true, full = true }
local LAYOUT_CLASSES = { hcenter = true, vcenter = true, center = true, fill = true, caution = true, wide = true }

-- A content slide's heading: at the slide level, with none of the kinds' classes (SLIDE_KINDS by
-- default; a format that treats a kind as content passes its own set).
local function content_heading(blk, level, kinds)
  if not (blk.t == "Header" and blk.level == level) then return false end
  for _, c in ipairs(blk.classes) do
    if (kinds or SLIDE_KINDS)[c] then return false end
  end
  return true
end

-- The per-slide layout controls on a heading (.hcenter, .vcenter, .center, .fill, .caution, .wide,
-- scale="S"), taken off it: { h, v, fill, caution, wide, scale } (scale the string, or nil), or nil
-- when it has none. A scale that is not a number is dropped with a warning (who: the filter).
local function take_layout(blk, who)
  local h, v, fill, caution, wide, found = false, false, false, false, false, false
  local kept = pandoc.List({})
  for _, c in ipairs(blk.classes) do
    if LAYOUT_CLASSES[c] then
      found = true
      h = h or c == "hcenter" or c == "center"
      v = v or c == "vcenter" or c == "center"
      fill = fill or c == "fill"
      caution = caution or c == "caution"
      wide = wide or c == "wide"
    else
      kept:insert(c)
    end
  end
  local scale = blk.attributes["scale"]
  if scale then
    blk.attributes["scale"] = nil
    found = true
    if not tonumber(scale) then
      quarto.log.warning(who .. ": scale=\"" .. scale .. "\" is not a number; ignored")
      scale = nil
    end
  end
  if not found then return nil end
  blk.classes = kept
  return { h = h, v = v, fill = fill, caution = caution, wide = wide, scale = scale }
end

-- themeoptions: a list or a comma-separated string of key=value (a bare key is "true"). Returns
-- the options as a table and the items as written (beamer's \usetheme takes them as they are).
local function theme_options(meta)
  local opts, items, to = {}, {}, meta["themeoptions"]
  if not to then return opts, items end
  for _, it in ipairs(pandoc.utils.type(to) == "List" and to or { to }) do
    local s = pandoc.utils.stringify(it)
    table.insert(items, s)
    for kv in s:gmatch("[^,%s]+") do
      local k, v = kv:match("^([^=]+)=(.*)$")
      if k then opts[k] = v else opts[kv] = "true" end
    end
  end
  return opts, items
end

-- The slide footnotes' markers, in the printer's order: a slide's dagger lines take them as the
-- author writes them, its ^[...] notes the ones after (lift_footnotes()).
local MARKERS = { "†", "‡", "§", "¶" }

local function leading_marker(text)   -- the marker text starts with, matched by its own byte length
  for _, m in ipairs(MARKERS) do
    if text:sub(1, #m) == m then return m end
  end
  return nil
end

local function footnote_marker(blk)
  if blk.t ~= "Para" then return nil end
  local x = blk.content[1]
  while x and (x.t == "Emph" or x.t == "Strong" or x.t == "Span") do x = x.content[1] end
  if not (x and x.t == "Str") then return nil end
  return leading_marker(x.text)
end

-- the inlines without their leading marker (and its space); *† text* keeps
-- its emphasis on the text
local function strip_marker(inlines)
  local x, out = inlines[1], pandoc.Inlines({})
  if x.t == "Str" then
    local rest = x.text:sub(#leading_marker(x.text) + 1)
    if rest ~= "" then out:insert(pandoc.Str(rest)) end
    for k = 2, #inlines do
      if not (k == 2 and rest == "" and inlines[k].t == "Space") then out:insert(inlines[k]) end
    end
  else
    local c = x:clone()
    c.content = strip_marker(x.content)
    out:insert(c)
    for k = 2, #inlines do out:insert(inlines[k]) end
  end
  return out
end

local function warn(s)   -- quarto's log, or stderr under plain pandoc (the pptx filters, the tests)
  if quarto and quarto.log then quarto.log.warning(s) else io.stderr:write("WARNING: " .. s .. "\n") end
end

-- One slide's ^[...] notes as slide footnotes: every Note outside a .notes div, in order, becomes a
-- superscript mark in the text (a Span .engine-noteref) and a paragraph led by the same marker,
-- the markers after the last one the slide's dagger lines use. Returns the blocks with the marks
-- and the new paragraphs, in order (the slide's foot is the caller's to place). A note holding
-- anything but paragraphs, or one past ¶, warns and stays pandoc's.
local function lift_footnotes(blocks)
  local rank, last = {}, 0
  for k, m in ipairs(MARKERS) do rank[m] = k end
  local function skip_notes(d) if has_class(d, "notes") then return d, false end end
  local used = { traverse = "topdown", Div = skip_notes, Para = function(p)
    local m = footnote_marker(p)
    if m and rank[m] > last then last = rank[m] end
  end }
  pandoc.Blocks(blocks):walk(used)
  local lifted, full = pandoc.Blocks({}), false
  local lift = { traverse = "topdown", Div = skip_notes, Note = function(n)
    for _, b in ipairs(n.content) do
      if b.t ~= "Para" and b.t ~= "Plain" then
        warn("engine: a ^[...] footnote holding more than paragraphs stays pandoc's")
        return n, false
      end
    end
    if last >= #MARKERS then
      if not full then warn("engine: more ^[...] footnotes on a slide than markers († ‡ § ¶); the rest stay pandoc's") end
      full = true
      return n, false
    end
    last = last + 1
    local m = MARKERS[last]
    local text = pandoc.Inlines({ pandoc.Str(m), pandoc.Space() })
    for k, b in ipairs(n.content) do
      if k > 1 then text:insert(pandoc.LineBreak()) end
      text:extend(b.content)
    end
    lifted:insert(pandoc.Para(text))
    return pandoc.Span({ pandoc.Superscript({ pandoc.Str(m) }) }, pandoc.Attr("", { "engine-noteref" })), false
  end }
  return pandoc.Blocks(blocks):walk(lift), lifted
end

-- The slide footnotes of one slide's blocks (a † ‡ § ¶ paragraph, in a column or a div too, and
-- its ^[...] notes, lift_footnotes()), removed from where they stood: the blocks kept (notes divs
-- untouched), the footnotes found, the lifted notes last.
local function take_footnotes(blocks)
  local lifted
  blocks, lifted = lift_footnotes(blocks)
  local found = pandoc.List({})
  local kept = pandoc.Blocks({})
  local filter = { Para = function(p) if footnote_marker(p) then found:insert(p); return {} end end }
  for _, b in ipairs(blocks) do
    if b.t == "Div" and has_class(b, "notes") then
      kept:insert(b)
    elseif footnote_marker(b) then
      found:insert(b)
    else
      kept:insert(pandoc.walk_block(b, filter))
    end
  end
  found:extend(lifted)
  return kept, found
end

-- Citations ([@key] with a bibliography:): citeproc runs after the engine's filters and fills the
-- deck's ::: {#refs} div, so every filter sees the Cite inlines and the author's empty div. The
-- slide holding the div is the references slide in every format.

-- Quarto's cross-reference prefixes: a [@fig-x] is a cross-reference, not a citation
local CROSSREF = { fig = true, tbl = true, lst = true, sec = true, eq = true, thm = true, lem = true,
  cor = true, prp = true, cnj = true, def = true, exm = true, exr = true, sol = true, rem = true,
  tip = true, nte = true, wrn = true, imp = true, cau = true }

-- Whether the document cites: a bibliography (or inline references) and a Cite of a key that is
-- not a cross-reference, or a nocite:.
local function has_cites(doc)
  local meta = doc.meta
  if not (meta["bibliography"] or meta["references"]) then return false end
  if meta["nocite"] then return true end
  local found = false
  doc.blocks:walk({ Cite = function(c)
    for _, cit in ipairs(c.citations) do
      local prefix = cit.id:match("^(%a+)%-")
      if not (prefix and CROSSREF[prefix]) then found = true end
    end
  end })
  return found
end

-- The ::: {#refs} div among the blocks (at any depth), or nil.
local function refs_div(blocks)
  local div
  pandoc.Blocks(blocks):walk({ Div = function(d) if d.identifier == "refs" then div = div or d end end })
  return div
end

-- The index among the blocks of the heading (at the slide level) whose slide holds the #refs div,
-- or nil.
local function refs_heading(blocks, level)
  local heading
  for k, b in ipairs(blocks) do
    if is_slide_break(b, level) then
      heading = (b.t == "Header" and b.level == level) and k or nil
    elseif heading and refs_div({ b }) then
      return heading
    end
  end
  return nil
end

-- The blocks with a references slide last when the deck cites but has no #refs div (a warning
-- says so): a heading at the slide level (reference-section-title:, else "References") and the
-- empty div citeproc fills. Untouched under suppress-bibliography:.
local function ensure_refs(blocks, meta, level)
  blocks = pandoc.Blocks(blocks)
  if refs_div(blocks) or not has_cites(pandoc.Pandoc(blocks, meta)) then return blocks end
  if meta["suppress-bibliography"] and pandoc.utils.stringify(meta["suppress-bibliography"]) == "true" then
    return blocks
  end
  local title = meta["reference-section-title"] and pandoc.utils.stringify(meta["reference-section-title"]) or "References"
  warn("engine: [@..] cited but no ::: {#refs}; a References slide was added last")
  blocks:insert(pandoc.Header(level, pandoc.Inlines(title)))
  blocks:insert(pandoc.Div({}, pandoc.Attr("refs")))
  return blocks
end

-- .full: the slide's one figure, the caption paragraphs after it, and its
-- notes; nil when the body is anything else.  A † paragraph is caption too.
local function is_figure(blk)
  if blk.t == "Figure" then return true end
  if blk.t == "Div" then
    return has_class(blk, "cell") or has_class(blk, "cell-output-display")
      or has_class(blk, "quarto-figure") or has_class(blk, "quarto-float")
  end
  if blk.t ~= "Para" and blk.t ~= "Plain" then return false end
  local n = 0
  for _, il in ipairs(blk.content) do
    if il.t == "Image" or (il.t == "Link" and #il.content == 1 and il.content[1].t == "Image") then
      n = n + 1
    elseif il.t ~= "Space" and il.t ~= "SoftBreak" then
      return false
    end
  end
  return n == 1
end

-- ::: note: a remark under a figure or table, drawn as its caption (the caption role, muted,
-- centred) in every format
local function is_note(blk)
  return blk.t == "Div" and has_class(blk, "note")
end

-- A .full slide's blocks as (figure, caption paragraphs, the notes and hidden divs), or nil when the
-- body holds anything else; a ::: note after the figure is caption.
local function split_full(blocks)
  local fig, caption, rest = nil, pandoc.Blocks({}), pandoc.Blocks({})
  for _, b in ipairs(blocks) do
    if b.t == "Div" and (has_class(b, "notes") or has_class(b, "hidden")) then
      rest:insert(b)
    elseif not fig and is_figure(b) then
      fig = b
    elseif fig and (b.t == "Para" or b.t == "Plain") then
      caption:insert(b)
    elseif fig and is_note(b) then
      caption:extend(b.content)
    else
      return nil
    end
  end
  if not fig then return nil end
  return fig, caption, rest
end

-- The livery (design section 5): `livery:` in the metadata (a directory, relative to the project),
-- else the bundled liveries/ncar beside the _extensions/ that holds the extension (extdir: the
-- filter's own directory). Its build/livery.json, with `dir` the physical directory: a flavor's
-- inherited files are `../<parent>/...`, and joined onto a link (a deck's `_livery`) the path is
-- normalized as text, `_livery/..` becoming the deck. A missing build/ is an error naming the fix.
local function load_livery(meta, extdir, who)
  local dir = meta["livery"] and pandoc.utils.stringify(meta["livery"])
  if dir and not pandoc.path.is_absolute(dir) then
    dir = pandoc.path.join({ pandoc.system.get_working_directory(), dir })
  end
  dir = dir or default_livery(extdir)
  local f = io.open(pandoc.path.join({ dir, "build", "livery.json" }))
  if not f then
    error(who .. ": no livery at " .. dir .. " (build/livery.json is missing): set `livery:` "
      .. "to a livery directory (a bundled one is liveries/<name>)")
  end
  local livery = quarto.json.decode(f:read("a")); f:close()
  local ok, real = pcall(pandoc.system.with_working_directory, dir, pandoc.system.get_working_directory)
  livery.dir = ok and real or dir
  return livery
end

-- A .columns div's columns and their shares of the row, the gaps taken out first, as every format
-- lays them out: a column's width= ("55%" or "0.55") is its share, the columns without one share
-- what is left equally, and shares that add to more than 1 are scaled down to 1 (less than 1
-- leaves the rest of the row empty, at the right).
local function column_shares(div)
  local cols, shares, given, missing = {}, {}, 0, 0
  for _, c in ipairs(div.content) do
    if c.t == "Div" and has_class(c, "column") then
      table.insert(cols, c)
      local w = c.attributes["width"]
      local v = w and tonumber((w:gsub("%%$", "")))
      if v and w:find("%%$") then v = v / 100 end
      if v and v <= 0 then v = nil end
      shares[#cols] = v or false
      if v then given = given + v else missing = missing + 1 end
    end
  end
  local rest = missing > 0 and (given < 1 and (1 - given) / missing or 1 / #cols) or 0
  local total = 0
  for i = 1, #cols do
    shares[i] = shares[i] or rest
    total = total + shares[i]
  end
  if total > 1 then
    for i = 1, #cols do shares[i] = shares[i] / total end
  end
  return cols, shares
end

-- A grid slide: the columns div has a .card column or more than two columns, or the slide (its
-- blocks) has a .lead, a .steps or a .timeline. pptx draws one from marker paragraphs
-- (grid-pptx.lua, pptx_steps/grid.py); pandoc's two placeholders cannot hold it.
local function is_grid(div, blocks)
  local cols = column_shares(div)
  if #cols > 2 then return true end
  for _, c in ipairs(cols) do
    if has_class(c, "card") then return true end
  end
  for _, b in ipairs(blocks or {}) do
    if b.t == "Div" and (has_class(b, "lead") or has_class(b, "steps") or has_class(b, "timeline")) then return true end
  end
  return false
end

-- In a .lead or a .card a source line is a line: each Para cut at its soft and hard line breaks
-- into Paras of their own, so a bold headline over a plain line needs no blank line between them.
-- Lists and other blocks are left alone.
local function split_lines(blocks)
  local out = pandoc.Blocks({})
  for _, b in ipairs(blocks) do
    if b.t == "Para" then
      local cur = pandoc.Inlines({})
      for _, il in ipairs(b.content) do
        if il.t == "SoftBreak" or il.t == "LineBreak" then
          if #cur > 0 then out:insert(pandoc.Para(cur)) end
          cur = pandoc.Inlines({})
        else
          cur:insert(il)
        end
      end
      if #cur > 0 then out:insert(pandoc.Para(cur)) end
    else
      out:insert(b)
    end
  end
  return out
end

-- A paragraph that is one span of the class (`[$20M]{.big}`): its inlines, else nil.
local function lone_span(b, cls)
  if (b.t == "Para" or b.t == "Plain") and #b.content == 1 and b.content[1].t == "Span"
      and has_class(b.content[1], cls) then
    return b.content[1].content
  end
  return nil
end

-- A card column (`::: {.column .card .pick .solid role="primary"}`), as every format draws it:
-- { role, pick, solid, title (inlines or nil), sub (inlines or nil), body (blocks) }. role names the
-- head band's fill (with .solid, the card's), else default (the livery's boxes.card.roles by the
-- card's place in its row, which the caller picks), else primary; .pick draws the outline; a first
-- heading is the band's title, and a paragraph that is one [...]{.sub} right after it the band's
-- second line; the body's source lines are lines (split_lines()). The column's role= is taken off
-- (HTML's ARIA attribute). nil for a column that is not a card.
local function card_attrs(col, default)
  if not has_class(col, "card") then return nil end
  local c = { role = col.attributes["role"] or default or "primary", pick = has_class(col, "pick"),
              solid = has_class(col, "solid") }
  col.attributes["role"] = nil
  local blocks, i = col.content, 1
  if blocks[1] and blocks[1].t == "Header" then
    c.title, i = blocks[1].content, 2
    local sub = blocks[2] and lone_span(blocks[2], "sub")
    if sub then c.sub, i = sub, 3 end
  end
  local rest = pandoc.Blocks({})
  for k = i, #blocks do rest:insert(blocks[k]) end
  c.body = split_lines(rest)
  return c
end

-- A card's or strip's role= as every format draws it: a role or a blend of livery.json, else default
-- (the card's place in its row, a strip's accent); a name that is neither warns and takes the
-- default, as pptx_steps/grid.py does for the pptx.
local function box_role(livery, role, default, who)
  if role == nil or role == default then return default end
  if livery.roles[role] or (livery.blends and livery.blends[role]) then return role end
  quarto.log.warning(who .. ": role=\"" .. role .. "\" is not a role or a blend of the livery; " .. default)
  return default
end

-- Status items: in a .card or a ::: {.status} list, `- [x]` (pandoc's ☒), `- [!]` and `- [-]` are
-- done, warn and fail; a literal ✓ ⚠ ✗ first in an item is one anywhere. `- [ ]` (☐) stays a task
-- list's unchecked box: an unchecked task is not a failure.
local MARKED = { ["☒"] = "done", ["[!]"] = "warn", ["[-]"] = "fail" }
local LITERAL = { ["✓"] = "done", ["⚠"] = "warn", ["✗"] = "fail" }
local GLYPHS = { done = "✓", warn = "⚠", fail = "✗" }

-- status_item(item, marked): an item's (a list of blocks) status, "done" | "warn" | "fail", and the
-- item with its leading glyph normalized to the glyph's Str (✓ ⚠ ✗, no variation selector) and a
-- Space; nil when it is not one. marked: inside a card or a .status list, where [x] [!] [-] count.
local function status_item(item, marked)
  local first = item[1]
  if not first or (first.t ~= "Plain" and first.t ~= "Para") then return nil end
  local x = first.content[1]
  if not x or x.t ~= "Str" then return nil end
  local t = x.text:gsub("\u{FE0E}", ""):gsub("\u{FE0F}", "")
  local kind = LITERAL[t] or (marked and MARKED[t])
  if not kind then return nil end
  local il = first.content:clone()
  il[1] = pandoc.Str(GLYPHS[kind])
  if il[2] and il[2].t ~= "Space" then il:insert(2, pandoc.Space()) end
  local out = pandoc.List(item):clone()
  out[1] = first.t == "Para" and pandoc.Para(il) or pandoc.Plain(il)
  return kind, out
end

-- Steps and timelines, the rail: a ::: {.steps role=} div holding one ordered list, a ::: {.timeline}
-- one bullet list. rail_kind(div): "steps", "timeline" or nil. rail_items(div, kind, livery, who):
-- { role, items = { { title = inlines|nil, body = blocks, done = bool|nil }, ... } }, as every format
-- draws it: an item's first bold run (a Strong first in its first paragraph) is its title (a step's)
-- or its date (a milestone's), the Space after it dropped, the rest of that paragraph its first body
-- line and its other blocks the rest, the source lines lines (split_lines()); a milestone's `- [x]`
-- (status_item(), marked) is done, a plain item (or `- [ ]`) pending, `[!]` and `[-]` warned of and
-- drawn as pending. role= is taken off (HTML's ARIA attribute) and checked by box_role() when a
-- livery is given (pptx's grid.py checks its own), default primary. nil, warned of, for anything
-- else: the wrong list or more than one block, more than RAIL_MAX items, a picture or table inside.
local RAIL_MAX = 6   -- beamer's six save boxes (the cards'); every format holds to it
local RAIL_LIST = { steps = "OrderedList", timeline = "BulletList" }

local function rail_kind(div)
  if div.t ~= "Div" then return nil end
  if has_class(div, "steps") then return "steps" end
  if has_class(div, "timeline") then return "timeline" end
  return nil
end

local function rail_items(div, kind, livery, who)
  local role = div.attributes["role"]
  div.attributes["role"] = nil
  role = livery and box_role(livery, role, "primary", who) or role or "primary"
  local list = #div.content == 1 and div.content[1] or nil
  local what = kind == "steps" and "ordered list (1. 2. 3.)" or "bullet list (- [x] done, - pending)"
  if not list or list.t ~= RAIL_LIST[kind] then
    warn(who .. ": a ." .. kind .. " div holds one " .. what .. " and nothing else; left as it is")
    return nil
  end
  if #list.content > RAIL_MAX then
    warn(who .. ": a ." .. kind .. " div has " .. #list.content .. " items, more than " .. RAIL_MAX .. "; left as it is")
    return nil
  end
  local shape = false
  pandoc.Blocks({ list }):walk({ Image = function() shape = true end, Table = function() shape = true end,
                                 Figure = function() shape = true end })
  if shape then
    warn(who .. ": a ." .. kind .. " item holds a picture or table, which a rail does not draw; left as it is")
    return nil
  end
  local items = {}
  for _, item in ipairs(list.content) do
    local done, glyph = nil, false
    if kind == "timeline" then
      local status, norm = status_item(item, true)
      if status then
        item, glyph = norm, true
        if status ~= "done" then
          warn(who .. ": a milestone is done (- [x]) or pending (a plain item); " .. GLYPHS[status] .. " drawn as pending")
        end
      end
      done = status == "done"
    end
    local first = item[1]
    local il = (first and (first.t == "Plain" or first.t == "Para")) and first.content:clone() or nil
    if il and il[1] and (glyph or (kind == "timeline" and il[1].t == "Str" and il[1].text == "☐")) then
      il:remove(1)   -- the glyph, or an unchecked box (- [ ]: pending)
      if il[1] and il[1].t == "Space" then il:remove(1) end
    end
    local title
    if il and il[1] and il[1].t == "Strong" then
      title = il[1].content
      il:remove(1)
      if il[1] and il[1].t == "Space" then il:remove(1) end
    end
    local body = pandoc.Blocks({})
    if il and #il > 0 then body:insert(pandoc.Para(il)) end
    for k = il and 2 or 1, #item do body:insert(item[k]) end
    table.insert(items, { title = title, body = split_lines(body), done = done })
  end
  return { role = role, items = items }
end

-- Every bullet list's status items normalized (status_item()), marked ones inside a card column or
-- a .status div; fn(list, kinds) then returns the list as a format draws it (kinds: the items'
-- statuses, nil for a plain item), or nil to keep it.
local function status_lists(blocks, fn)
  local function lists(bs, marked)
    return bs:walk({ BulletList = function(l)
      local kinds, any = {}, false
      for k, item in ipairs(l.content) do
        local kind, norm = status_item(item, marked)
        if kind then l.content[k], kinds[k], any = norm, kind, true end
      end
      if any then return fn(l, kinds) end
      return nil
    end })
  end
  return blocks:walk({ Div = function(d)
    if has_class(d, "status") or (has_class(d, "column") and has_class(d, "card")) then
      d.content = lists(d.content, true)
      return d
    end
    return nil
  end }):walk({ BulletList = function(l)   -- literal glyphs anywhere
    local kinds, any = {}, false
    for k, item in ipairs(l.content) do
      local kind, norm = status_item(item, false)
      if kind then l.content[k], kinds[k], any = norm, kind, true end
    end
    if any then return fn(l, kinds) end
    return nil
  end })
end

return {
  has_class = has_class, column_shares = column_shares, status_item = status_item, status_lists = status_lists, is_grid = is_grid, split_lines = split_lines,
  lone_span = lone_span, card_attrs = card_attrs, box_role = box_role, deck_type_scale = deck_type_scale, default_livery = default_livery,
  footnote_marker = footnote_marker, strip_marker = strip_marker, take_footnotes = take_footnotes, lift_footnotes = lift_footnotes, is_figure = is_figure,
  is_note = is_note, split_full = split_full, is_slide_break = is_slide_break, SLIDE_KINDS = SLIDE_KINDS,
  LAYOUT_CLASSES = LAYOUT_CLASSES, content_heading = content_heading, take_layout = take_layout,
  theme_options = theme_options, load_livery = load_livery,
  has_cites = has_cites, refs_div = refs_div, refs_heading = refs_heading, ensure_refs = ensure_refs,
  rail_kind = rail_kind, rail_items = rail_items, RAIL_MAX = RAIL_MAX,
}
