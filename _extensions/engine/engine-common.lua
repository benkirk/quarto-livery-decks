-- engine-common.lua -- what the format filters share (engine-revealjs.lua, engine-beamer.lua, and
-- pptx's slide-layout.lua, single-body.lua, inline-footnotes.lua, grid-pptx.lua, notes-last.lua,
-- linked-images.lua and diagram-dark.lua): loaded with dofile() beside the filter (the directory of
-- PANDOC_SCRIPT_FILE, or quarto.utils.resolve_path), returning a table. A function here reads the
-- same in every format: the slide walk, breaks and kinds, the layout classes, the footnotes and
-- citations, a .full slide's parts, the sections and dividers, the cards, strips, status lists,
-- rails, quotes, galleries and the agenda, the theme options, the livery, the deck's markings. What
-- a format does with the result stays in its filter: the drawers (wrap_layout, hoist_footnotes,
-- size_plots, the cards, strips, rails, galleries, quotes and the agenda's rows).

local function has_class(el, cls)
  for _, c in ipairs(el.classes) do
    if c == cls then return true end
  end
  return false
end

-- A warning, led by its filter's name (who) and the slide's title where one is known: quarto's log,
-- or stderr under plain pandoc (the pptx filters, the tests).
local function warn(s)   -- quarto's log, or stderr under plain pandoc (the pptx filters, the tests)
  if quarto and quarto.log then quarto.log.warning(s) else io.stderr:write("WARNING: " .. s .. "\n") end
end

-- The deck's size step: `type-body: <pt>` (the body in points; every size scales by it over the
-- livery's body, type.roles.body.pt) or `type-scale: <factor>`; type-body wins. 1 without either.
local function deck_type_scale(meta, body_pt, who)
  local function num(k)
    if meta[k] == nil then return nil end
    local v = tonumber(pandoc.utils.stringify(meta[k]))
    if not v or v <= 0 then
      warn(who .. ": " .. k .. " is not a positive number; ignored")
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

-- Whether a block holds a picture or a table anywhere inside it: pandoc's pptx writer draws either
-- as a shape of its own, outside any text, so a card, a rail item or a grid column cannot hold one.
local function holds_shape(blk)
  local found = false
  pandoc.walk_block(blk, { Image = function() found = true end, Table = function() found = true end })
  return found
end

-- Whether a block holds a table anywhere inside it.
local function holds_table(blk)
  local found = false
  pandoc.walk_block(blk, { Table = function() found = true end })
  return found
end

-- A slide boundary: a heading at or above the slide level, or a rule.
local function is_slide_break(blk, level)
  return (blk.t == "Header" and blk.level <= level) or blk.t == "HorizontalRule"
end

-- The slide level pandoc breaks slides at (slide-level:, which the engine formats set to 2).
local function slide_level()
  return (PANDOC_WRITER_OPTIONS and PANDOC_WRITER_OPTIONS.slide_level) or 2
end

-- The slide's blocks from blocks[i] on, up to the next slide break (its heading is blocks[i - 1],
-- which the caller has taken), and the index after them: the one walk every filter takes.
local function slide_from(blocks, i, level)
  local slide = pandoc.Blocks({})
  while i <= #blocks and not is_slide_break(blocks[i], level) do
    slide:insert(blocks[i])
    i = i + 1
  end
  return slide, i
end

-- speaker notes (::: {.notes})
local function is_notes(b)
  return b.t == "Div" and has_class(b, "notes")
end

-- What rides with the notes: the speaker notes, Quarto's vault (`.hidden`), and the
-- `quarto-auto-generated-content` div (its footer and logo) Quarto appends to a revealjs document,
-- which lands in the last slide's blocks and is moved out of the slide afterwards. A walker that
-- validates a slide's body (split_full, agenda_notes, the feature slide) never refuses one of these.
local function is_aside(b)
  return b.t == "Div" and (has_class(b, "notes") or has_class(b, "hidden") or has_class(b, "quarto-auto-generated-content"))
end

-- A slide's body and its speaker notes (the asides with them), each in their order.
local function split_notes(blocks)
  local body, notes = pandoc.Blocks({}), pandoc.Blocks({})
  for _, b in ipairs(blocks) do
    if is_aside(b) then notes:insert(b) else body:insert(b) end
  end
  return body, notes
end

-- A divider's subtitle: the paragraphs alone between the divider at blocks[i] and the next slide.
-- Returns them and the index after them, or nil and i + 1 when there are none (or anything else
-- follows them: they are a slide of their own then).
local function divider_subtitle(blocks, i, level)
  local j, paras = i + 1, pandoc.List({})
  while j <= #blocks and (blocks[j].t == "Para" or blocks[j].t == "Plain") do
    paras:insert(blocks[j])
    j = j + 1
  end
  if #paras > 0 and (j > #blocks or is_slide_break(blocks[j], level)) then return paras, j end
  return nil, i + 1
end

-- The deck's section dividers (`#` headings over `##` slides), in order, as every format counts
-- them: { number (nil for .unnumbered), title (inlines), sub (the subtitle's blocks, or nil),
-- unnumbered, at (the divider's index in blocks) }.
local function sections(blocks, level)
  local out, n = {}, 0
  if level <= 1 then return out end
  for i, b in ipairs(blocks) do
    if b.t == "Header" and b.level == 1 then
      local unnumbered = has_class(b, "unnumbered")
      if not unnumbered then n = n + 1 end
      table.insert(out, { number = (not unnumbered) and n or nil, title = b.content,
                          sub = (divider_subtitle(blocks, i, level)), unnumbered = unnumbered, at = i })
    end
  end
  return out
end

-- The slide kinds a composition draws (their classes on the slide's heading; not content slides), and
-- the per-slide layout classes of a content slide (take_layout()).
local SLIDE_KINDS = { feature = true, closing = true, full = true }
local LAYOUT_CLASSES = { hcenter = true, vcenter = true, center = true, fill = true, caution = true, wide = true,
                         ["brand-dark"] = true }

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
  local h, v, fill, caution, wide, dark, found = false, false, false, false, false, false, false
  local kept = pandoc.List({})
  for _, c in ipairs(blk.classes) do
    if LAYOUT_CLASSES[c] then
      found = true
      h = h or c == "hcenter" or c == "center"
      v = v or c == "vcenter" or c == "center"
      fill = fill or c == "fill"
      caution = caution or c == "caution"
      wide = wide or c == "wide"
      dark = dark or c == "brand-dark"
    else
      kept:insert(c)
    end
  end
  local scale = blk.attributes["scale"]
  if scale then
    blk.attributes["scale"] = nil
    found = true
    if not tonumber(scale) then
      warn(who .. ": scale=\"" .. scale .. "\" is not a number; ignored")
      scale = nil
    end
  end
  if not found then return nil end
  blk.classes = kept
  if dark and (kept:includes("full") or kept:includes("feature")) then   -- the picture fills it: every format alike
    local name = pandoc.utils.stringify(blk.content)   -- a .full frame's title is gone in beamer by now
    warn(who .. ": {.brand-dark} on the {." .. (kept:includes("full") and "full" or "feature") .. "} slide "
      .. (name ~= "" and ("\"" .. name .. "\"") or ("#" .. blk.identifier)) .. " is ignored")
    dark = false
  end
  return { h = h, v = v, fill = fill, caution = caution, wide = wide, dark = dark, scale = scale }
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

-- One slide's ^[...] notes as slide footnotes: every Note outside a .notes div, in order, becomes a
-- superscript mark in the text (a Span .engine-noteref) and a paragraph led by the same marker,
-- the markers after the last one the slide's dagger lines use. Returns the blocks with the marks
-- and the new paragraphs, in order (the slide's foot is the caller's to place). A note holding
-- anything but paragraphs, or one past ¶, warns and stays pandoc's.
local function lift_footnotes(blocks)
  local rank, last = {}, 0
  for k, m in ipairs(MARKERS) do rank[m] = k end
  local function skip_notes(d) if is_notes(d) then return d, false end end
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
    if is_notes(b) then
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

-- Quarto's PDF shape of a captioned image on its own paragraph (`![Caption](path)`, a Figure): its
-- filters turn one into a classless Div holding raw `\begin{figure}[H]`, a paragraph of `{\centering`,
-- the Image (its alt emptied) and `}`, a paragraph of `\caption` `{` the caption's inlines `}` and
-- `\end{figure}` before any engine filter runs (HTML and pptx keep the Figure). The one Image and the
-- caption's inlines, or nil.
local function latex_figure(blk)
  if blk.t ~= "Div" or #blk.classes > 0 or not blk.content[1] then return nil end
  local first = blk.content[1]
  if not (first.t == "RawBlock" and first.text:find("\\begin{figure}", 1, true)) then return nil end
  local imgs, caption = {}, nil
  blk:walk({ Image = function(im) table.insert(imgs, im) end })
  if #imgs ~= 1 then return nil end
  for _, b in ipairs(blk.content) do
    local ils = b.content
    if (b.t == "Para" or b.t == "Plain") and ils[1] and ils[1].t == "RawInline" and ils[1].text:find("^\\caption") then
      local from, to = 1, #ils   -- past `\caption` and `{`, before the closing `}`
      while from <= to and ils[from].t == "RawInline" do from = from + 1 end
      if to >= from and ils[to].t == "RawInline" and ils[to].text == "}" then to = to - 1 end
      caption = pandoc.Inlines({})
      for k = from, to do caption:insert(ils[k]) end
    end
  end
  return imgs[1], caption
end

-- .full: the slide's one figure, the caption paragraphs after it, and its
-- notes; nil when the body is anything else.  A † paragraph is caption too.
local function is_figure(blk)
  if blk.t == "Figure" then return true end
  if blk.t == "Div" then
    return has_class(blk, "cell") or has_class(blk, "cell-output-display")
      or has_class(blk, "quarto-figure") or has_class(blk, "quarto-float") or latex_figure(blk) ~= nil
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
-- centered) in every format
local function is_note(blk)
  return blk.t == "Div" and has_class(blk, "note")
end

-- A .full slide's blocks as (figure, caption paragraphs, the asides), or nil when the body holds
-- anything else; a ::: note after the figure is caption. The figure may be a .gallery div
-- (is_gallery(); its cells fill the slide).
local function split_full(blocks)
  local fig, caption, rest = nil, pandoc.Blocks({}), pandoc.Blocks({})
  for _, b in ipairs(blocks) do
    if is_aside(b) then
      rest:insert(b)
    elseif not fig and (is_figure(b) or (b.t == "Div" and has_class(b, "gallery"))) then   -- a gallery fills the slide too
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

-- The deck's `marking:` (marking_texts reads it, the one reader every format uses): a string (or
-- inlines) sets the livery's first strip, `none` turns every strip off, a map sets strips by name
-- (`none` drops one). {all = Inlines | "none" | nil, by_name = {<name> = Inlines | "none"}}.
local function deck_marking(meta)
  local mk, d = meta["marking"], { by_name = {} }
  if mk == nil then return d end
  local function word(v)
    if pandoc.utils.stringify(v) == "none" then return "none" end
    return pandoc.utils.type(v) == "Inlines" and v or pandoc.Inlines(pandoc.utils.stringify(v))
  end
  if pandoc.utils.type(mk) == "table" then
    for k, v in pairs(mk) do d.by_name[k] = word(v) end
  else
    d.all = word(mk)
  end
  return d
end

-- Each of the livery's marking strips (livery.json marking, in order) with its text: the deck's
-- word on it (deck_marking), else its default; nil, no strip. A name the livery has no strip of is
-- warned and ignored. {{strip = <strip>, text = Inlines | nil}, ...}.
local function marking_texts(meta, strips, who)
  local d, out, known = deck_marking(meta), {}, {}
  for i, s in ipairs(strips or {}) do
    known[s.name] = true
    local w = d.all == "none" and "none" or d.by_name[s.name] or (i == 1 and d.all or nil)
    local text = nil
    if w and w ~= "none" then
      text = w
    elseif not w and type(s.text) == "string" then
      text = pandoc.Inlines(s.text)
    end
    table.insert(out, { strip = s, text = text })
  end
  for k in pairs(d.by_name) do
    if not known[k] then warn(who .. ": marking." .. k .. " is not a marking strip of the livery; ignored") end
  end
  return out
end

-- The watermark's text (the one reader every format uses): the deck's `watermark:` (a string or
-- inlines; `none` drops a default), else the livery's default (livery.json watermark.text); nil, none.
local function watermark_text(meta, livery)
  local w = meta["watermark"]
  if w ~= nil then
    if pandoc.utils.stringify(w) == "none" then return nil end
    return pandoc.utils.type(w) == "Inlines" and w or pandoc.Inlines(pandoc.utils.stringify(w))
  end
  local t = (livery.watermark or {}).text
  return type(t) == "string" and t ~= "" and pandoc.Inlines(t) or nil
end

-- The cover's composition name (livery.json compositions): the band title's, else a photo cover's when
-- the deck's titlegraphic: or the livery's art.titlegraphic gives one (`titlegraphic: none`: the plain
-- cover), its light variant under light (the caller's title=light, false under a band).
local function cover_name(meta, livery, light)
  if livery.title and livery.title.style == "band" then return "title-band" end
  local tg = meta["titlegraphic"] and pandoc.utils.stringify(meta["titlegraphic"])
  local photo = tg and tg ~= "none" or (not tg and livery.art and type(livery.art.titlegraphic) == "string")
  return (photo and "title-photo" or "title") .. (light and "-light" or "")
end

-- The cover's fine print (the one reader every format uses): the deck's `fineprint:` (Blocks as
-- written, inlines as one Plain; `none`, no blocks), else the composition's default paragraphs
-- (livery.json compositions.<cover>.fineprint.paragraphs), each a Para. Returns the Blocks (empty:
-- none) and whether the deck set them (beamer's theme holds the livery's default itself).
local function fineprint_paragraphs(meta, comp)
  local fp = meta["fineprint"]
  if fp ~= nil then
    if pandoc.utils.stringify(fp) == "none" then return pandoc.Blocks({}), true end
    local ty = pandoc.utils.type(fp)
    if ty == "Blocks" then return fp, true end
    return pandoc.Blocks({ pandoc.Plain(ty == "Inlines" and fp or pandoc.Inlines(pandoc.utils.stringify(fp))) }), true
  end
  local paras = pandoc.Blocks({})
  for _, p in ipairs(comp and comp.fineprint and comp.fineprint.paragraphs or {}) do paras:insert(pandoc.Para(pandoc.Inlines(p))) end
  return paras, false
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

-- An agenda slide: a slide-level heading with .agenda (`## Agenda {.agenda}`), the engine its body.
local function is_agenda(blk, level)
  return blk.t == "Header" and blk.level == level and has_class(blk, "agenda")
end

-- An agenda slide's body (its blocks up to the next slide): the speaker notes (and the other asides)
-- kept, anything else warned of and dropped (the engine writes the body). Returns the notes.
local function agenda_notes(body, who, title)
  local notes = pandoc.Blocks({})
  for _, b in ipairs(body) do
    if is_aside(b) then
      notes:insert(b)
    else
      warn(who .. ": the agenda slide \"" .. title .. "\" has a body of its own; the engine writes it, so it is dropped")
      break
    end
  end
  return notes
end

-- The agenda's rows: every numbered section (sections()) in order, { number, title (inlines), sub
-- (the subtitle's inlines, paragraphs joined by a space, or nil), state }: by the section the slide
-- sits in (current: the numbered dividers before it, 0 up front), an earlier one "done", that one
-- "current", a later one "next"; up front all "next".
local function agenda_rows(sections, current)
  local rows = {}
  for _, s in ipairs(sections) do
    if s.number then
      local sub
      if s.sub then
        sub = pandoc.Inlines({})
        for k, p in ipairs(s.sub) do
          if k > 1 then sub:insert(pandoc.Space()) end
          sub:extend(p.content)
        end
      end
      table.insert(rows, { number = s.number, title = s.title, sub = sub,
        state = s.number < current and "done" or (s.number == current and "current" or "next") })
    end
  end
  return rows
end

-- A quote block: `::: {.quote role=..}`, or a bare `>` blockquote (the same box, no role=).
local function is_quote(b)
  return (b.t == "Div" and has_class(b, "quote")) or b.t == "BlockQuote"
end

-- A row of columns (a .columns div) holding a .card and a table anywhere in it: no format draws it as
-- cards (beamer's card boxes cannot hold a longtable; a pptx table is a graphic frame no group of a
-- card's shapes holds), so every format draws the row as plain columns, warned of. The one test.
local function tabled_row(div)
  if div.t ~= "Div" or not has_class(div, "columns") then return false end
  local carded, tabled = false, false
  for _, c in ipairs(column_shares(div)) do
    if has_class(c, "card") then carded = true end
    if holds_table(c) then tabled = true end
  end
  return carded and tabled
end

-- A table pptx draws natively in a grid column: { cols, header (a header row), rows = {{inlines, ...}, ...}
-- (the header row first when there is one), aligns = {"l"|"c"|"r"|"d", ...} (a column's alignment, d
-- its default), caption = inlines or nil }; nil when it is not simple: a
-- cell spanning rows or columns, a cell of more than one block or of a block that is not a
-- paragraph, more than one header row, an intermediate head or a foot.
local function simple_table(tbl)
  if tbl.t ~= "Table" then return nil end
  local cols = #tbl.colspecs
  local rows, header = {}, false
  local function take(row)
    if #row.cells ~= cols then return false end
    local out = {}
    for _, cell in ipairs(row.cells) do
      if cell.row_span ~= 1 or cell.col_span ~= 1 then return false end
      local blocks = cell.contents
      if #blocks > 1 then return false end
      local b = blocks[1]
      if b and b.t ~= "Plain" and b.t ~= "Para" then return false end
      table.insert(out, b and b.content or pandoc.Inlines({}))
    end
    table.insert(rows, out)
    return true
  end
  if #tbl.head.rows > 1 or #tbl.foot.rows > 0 then return nil end
  if #tbl.head.rows == 1 then
    if not take(tbl.head.rows[1]) then return nil end
    header = true
  end
  for _, body in ipairs(tbl.bodies) do
    if #body.head > 0 then return nil end
    for _, row in ipairs(body.body) do
      if not take(row) then return nil end
    end
  end
  local caption = pandoc.utils.blocks_to_inlines(tbl.caption.long or {})
  local aligns = {}
  for k, spec in ipairs(tbl.colspecs) do
    aligns[k] = ({ AlignLeft = "l", AlignCenter = "c", AlignRight = "r" })[spec[1]] or "d"
  end
  return { cols = cols, header = header, rows = rows, aligns = aligns, caption = #caption > 0 and caption or nil }
end

-- A grid slide, the one list (the prose elsewhere says "what is_grid() counts"): the columns div has
-- more than two columns, a .card column (unless the row holds a table: tabled_row(), plain columns in
-- every format), or a column holding a quote (unless a column holds a picture
-- or table, which a grid column cannot: the slide stays pandoc's, the quote its own); or the slide (its
-- blocks) has a .lead, a .strip, a .steps, a .timeline, a .gallery or a quote of its own. pptx draws one
-- from marker paragraphs (grid-pptx.lua, pptx_steps/grid.py and gallery.py); pandoc's two placeholders
-- cannot hold it.
local function is_grid(div, blocks)
  local cols = column_shares(div)
  if #cols > 2 then return true end
  local quoted, pictured = false, false   -- a quote in a column: its box is grid.py's to draw
  local tabled = tabled_row(div)           -- a card row with a table is plain columns
  for _, c in ipairs(cols) do
    if has_class(c, "card") and not tabled then return true end
    c:walk({ Div = function(d) if is_quote(d) then quoted = true end end, BlockQuote = function() quoted = true end })
    if holds_shape(c) then pictured = true end
  end
  if quoted and not pictured then return true end
  for _, b in ipairs(blocks or {}) do
    if b.t == "Div" and (has_class(b, "lead") or has_class(b, "steps") or has_class(b, "timeline") or has_class(b, "gallery")) then return true end
    if is_quote(b) then return true end
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
  warn(who .. ": role=\"" .. role .. "\" is not a role or a blend of the livery; " .. default)
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
-- A quote's parts: { role (role= when it is a role or a blend of the livery, else nil: the box's
-- bar-color, boxes.quote; a name that is neither is warned of), body (its source lines each a
-- paragraph, split_lines()), attribution (the last line's inlines after its leading —, – or --,
-- the dash and the space after it dropped; nil when the last line has none) }. livery nil (the pptx
-- filter, which has none): role= kept as written, for grid.py to check.
local DASHES = { "—", "–", "--" }   -- pandoc's smart quotes make `--` an en dash before a filter sees it
local function quote_parts(b, livery, who)
  local role = b.t == "Div" and b.attributes["role"] or nil
  if role and livery and not (livery.roles[role] or (livery.blends and livery.blends[role])) then
    warn(who .. ": role=\"" .. role .. "\" is not a role or a blend of the livery; the quote bar's color")
    role = nil
  end
  local body = split_lines(b.content)
  local last, attribution = body[#body], nil
  if last and (last.t == "Para" or last.t == "Plain") and last.content[1] and last.content[1].t == "Str" then
    local s = last.content[1].text
    for _, d in ipairs(DASHES) do
      if s:sub(1, #d) == d then
        local il = pandoc.Inlines({})
        if #s > #d then il:insert(pandoc.Str(s:sub(#d + 1))) end
        for k = 2, #last.content do il:insert(last.content[k]) end
        while il[1] and (il[1].t == "Space" or il[1].t == "SoftBreak") do il:remove(1) end
        if #il > 0 then attribution = il; body:remove(#body) end
        break
      end
    end
  end
  return { role = role, body = body, attribution = attribution }
end

-- Every quote block in blocks replaced by draw(quote_parts()), the blocks a format draws it with: at
-- any depth (a column, a card, a wrapper div), but not in the speaker notes, nor inside another quote;
-- inside a .lead or a .strip (a box of lines already) a quote is warned of and left as its lines.
-- One rule for every format.
local function quote_blocks(blocks, livery, who, draw)
  local function as_lines(d)   -- the quotes inside a lead or a strip: their lines, warned of
    local function lines(q)
      warn(who .. ": a quote inside a .lead or a .strip is not drawn; left as its lines")
      return split_lines(q.content)
    end
    return d:walk({ Div = function(x) if is_quote(x) then return lines(x) end end, BlockQuote = lines })
  end
  return blocks:walk({ traverse = "topdown",
    Div = function(d)
      if is_notes(d) then return d, false end
      if has_class(d, "lead") or has_class(d, "strip") then return as_lines(d), false end
      if is_quote(d) then return draw(quote_parts(d, livery, who)), false end
      return nil
    end,
    BlockQuote = function(b) return draw(quote_parts(b, livery, who)), false end })
end

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
-- { role, start, items = { { title = inlines|nil, body = blocks, done = bool|nil }, ... } }, as every
-- format draws it (start: the ordered list's first number, a step's badges count from it, so a
-- process split over two slides goes on at `7.`; nil for a timeline): an item's first bold run (a
-- Strong first in its first paragraph) is its title (a step's)
-- or its date (a milestone's), the Space after it dropped, the rest of that paragraph its first body
-- line and its other blocks the rest, the source lines lines (split_lines()); a milestone's `- [x]`
-- (status_item(), marked) is done, a plain item (or `- [ ]`) pending, `[!]` and `[-]` warned of and
-- drawn as pending. role= is taken off (HTML's ARIA attribute) and checked by box_role() when a
-- livery is given (pptx's grid.py checks its own), default primary-contrast: a mark is a small
-- shape on the slide, so it takes the primary that reads on the background (a dark livery's
-- primary does not), and a badge's number is knocked out in the background color, so a mark
-- that shows has a number that reads. nil, warned of, for anything
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
  local default = livery and livery.boxes and livery.boxes.rail.role or "primary-contrast"   -- boxes.rail.role
  role = livery and box_role(livery, role, default, who) or role or default
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
  if holds_shape(list) then
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
  return { role = role, start = kind == "steps" and (list.start or 1) or nil, items = items }
end

-- The slide's elements of one kind drawn at its top level: each top-level block whose kind(b) names
-- it (".steps", ".gallery"...) and read(b, kind) accepts becomes draw(x, kind) (blocks); one inside
-- another div (a column, a card) is not drawn, in any format (beamer's save boxes are a card's; pptx
-- flattens a column), and is warned of and left as it is (left: "list", "pictures"), its role=
-- dropped (an invalid ARIA role in HTML otherwise).
local function top_level(blocks, kind_of, read, draw, who, left)
  local out = pandoc.Blocks({})
  for _, b in ipairs(blocks) do
    local kind = kind_of(b)
    local x = kind and read(b, kind)
    if x then
      out:extend(draw(x, kind))
    else
      if b.t == "Div" and not kind then
        b.content = b.content:walk({ Div = function(d)
          local inner = kind_of(d)
          if inner then
            warn(who .. ": a ." .. inner .. " inside a column or another div is not drawn; left as its " .. left)
            d.attributes["role"] = nil
            return d
          end
        end })
      end
      out:insert(b)
    end
  end
  return out
end

-- The slide's rails drawn (top_level): each .steps or .timeline div rail_items() reads becomes
-- draw(kind, rail).
local function top_rails(blocks, livery, who, draw)
  return top_level(blocks, rail_kind, function(b, kind) return rail_items(b, kind, livery, who) end,
                   function(r, kind) return draw(kind, r) end, who, "list")
end

-- Image galleries (::: {.gallery cols= rows= fit= height=}): a div of image files, each its own paragraph
-- (`![Caption](path)` a Figure, `![](path)` a Para of one Image), drawn as a grid of equal cells in every
-- format. gallery_items() reads one: { cols, rows, fit, height = number|nil, items = { { src, caption =
-- inlines|nil }, ... }, captioned } or nil, warned of: anything but an image paragraph (a plot or a
-- diagram cell among them), an image under a figure-*/ or *_files/ directory (an executed cell's plot or
-- a baked diagram: pptx reads the files from disk after the render, where those are not), a link round
-- an image, a gallery inside it, more than GALLERY_MAX images or more than cols*rows, a cols or rows
-- that is not a positive integer, a height outside (0, 1]. cols defaults to ceil(sqrt(n)), rows to
-- ceil(n/cols) (rows alone given: cols = ceil(n/rows)); fit is contain or cover (anything else warned
-- of: contain). A per-image width= or height= is dropped: the cell sizes the picture.
local GALLERY_MAX = 12   -- every format holds to it (beamer stores the items one macro each)

local function is_gallery(b)
  return b.t == "Div" and has_class(b, "gallery")
end

-- a Para or Plain of images alone (spaces and line breaks between them): the images, else nil; linked
-- true when an image inside a link is the reason
local function para_images(b)
  if b.t ~= "Para" and b.t ~= "Plain" then return nil end
  local imgs = {}
  for _, il in ipairs(b.content) do
    if il.t == "Image" then table.insert(imgs, il)
    elseif il.t == "Link" and #il.content == 1 and il.content[1].t == "Image" then return nil, true
    elseif il.t ~= "Space" and il.t ~= "SoftBreak" and il.t ~= "LineBreak" then return nil end
  end
  return #imgs > 0 and imgs or nil
end

-- A picture in a grid column or a card, as every format draws it: { src, caption = inlines or nil,
-- image = the Image, sized = its width= when the author gave one (it keeps that size) } for a Figure
-- of one image (its caption the Figure's, else the alt text), a Para or Plain of one image (the alt
-- text), Quarto's PDF figure (latex_figure()), or an executed cell's or a Quarto figure's Div whose
-- one block of substance, wrappers unwrapped, is one of those. nil otherwise; nil, true for an image
-- inside a link (para_images()'s linked), which the caller warns of.
local FIGURE_DIVS = { "cell", "cell-output-display", "quarto-figure", "quarto-float" }

local function cell_figure(b)
  local img, caption, linked
  if b.t == "Figure" and #b.content == 1 then
    local imgs
    imgs, linked = para_images(b.content[1])
    img = imgs and #imgs == 1 and imgs[1] or nil
    caption = pandoc.utils.blocks_to_inlines(b.caption.long or {})
  elseif b.t == "Para" or b.t == "Plain" then
    local imgs
    imgs, linked = para_images(b)
    img = imgs and #imgs == 1 and imgs[1] or nil
  elseif b.t == "Div" then
    img, caption = latex_figure(b)
    if not img then
      local wrapper = false
      for _, c in ipairs(FIGURE_DIVS) do if has_class(b, c) then wrapper = true end end
      if not wrapper then return nil end
      local inner = {}
      local function gather(blocks)
        for _, x in ipairs(blocks) do
          if x.t == "Div" and not latex_figure(x) then gather(x.content) else table.insert(inner, x) end
        end
      end
      gather(b.content)
      if #inner ~= 1 then return nil end
      return cell_figure(inner[1])
    end
  end
  if linked then return nil, true end
  if not img then return nil end
  if not caption or #caption == 0 then caption = #img.caption > 0 and img.caption or nil end
  return { src = img.src, caption = caption, image = img, sized = img.attributes["width"] }
end

-- data as base64 (RFC 4648, padded): pandoc's Lua has no encoder (quarto.base64 is Quarto's, and the
-- tests run plain pandoc); grid-pptx.lua carries an executed plot's bytes in its picture marker.
local B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

local function base64(data)
  local out = {}
  for i = 1, #data, 3 do
    local a, b, c = data:byte(i, i + 2)
    local n = (a << 16) | ((b or 0) << 8) | (c or 0)
    local q = { (n >> 18) & 63, (n >> 12) & 63, (n >> 6) & 63, n & 63 }
    for k = 1, 4 do q[k] = B64:sub(q[k] + 1, q[k] + 1) end
    if not b then q[3] = "=" end
    if not c then q[4] = "=" end
    out[#out + 1] = table.concat(q)
  end
  return table.concat(out)
end

local function gallery_items(div, who)
  local function refuse(why)
    warn(who .. ": a .gallery " .. why .. "; left as it is")
    return nil
  end
  local items = {}
  for _, b in ipairs(div.content) do
    local imgs, linked, long
    if b.t == "Figure" and #b.content == 1 then   -- ![Caption](path): its caption the Figure's
      imgs, linked = para_images(b.content[1])
      long = pandoc.utils.blocks_to_inlines(b.caption.long or {})
    elseif is_gallery(b) then
      return refuse("inside a .gallery is not drawn")
    else
      local img, cap = latex_figure(b)   -- the PDF's shape of ![Caption](path) (Quarto rewrites the Figure first)
      if img then imgs, long = { img }, cap else imgs, linked = para_images(b) end
    end
    if linked then return refuse("image inside a link is not drawn (links round gallery images are deferred)") end
    if not imgs then return refuse("holds image files, each its own paragraph; a plot or diagram is not drawn") end
    for _, img in ipairs(imgs) do
      if img.src:match("figure%-[%w%-]+/") or img.src:match("_files/") then
        return refuse("holds image files; " .. img.src .. " is an executed cell's plot or a baked diagram, not drawn")
      end
      img.attributes["width"], img.attributes["height"] = nil, nil   -- the cell sizes the picture
      local caption = (#imgs == 1 and long and #long > 0) and long or (#img.caption > 0 and img.caption or nil)
      table.insert(items, { src = img.src, caption = caption, image = img })
    end
  end
  local n = #items
  if n == 0 then return refuse("holds no image") end
  if n > GALLERY_MAX then return refuse("has " .. n .. " images, more than " .. GALLERY_MAX) end
  local function count(key)
    local v = div.attributes[key]
    if v == nil then return true, nil end
    local k = tonumber(v)
    if not k or k < 1 or k ~= math.floor(k) then return false end
    return true, math.floor(k)
  end
  local okc, cols = count("cols")
  local okr, rows = count("rows")
  if not okc then return refuse("cols=" .. div.attributes["cols"] .. " is not a positive whole number") end
  if not okr then return refuse("rows=" .. div.attributes["rows"] .. " is not a positive whole number") end
  if not cols then cols = rows and math.ceil(n / rows) or math.ceil(math.sqrt(n)) end
  if not rows then rows = math.ceil(n / cols) end
  if n > cols * rows then return refuse("of " .. n .. " images does not fit cols=" .. cols .. " rows=" .. rows) end
  local height = div.attributes["height"]
  if height ~= nil then
    local h = tonumber(height)
    if not h or h <= 0 or h > 1 then return refuse("height=" .. height .. " is not a share of the body in (0, 1]") end
    height = h
  end
  local fit = div.attributes["fit"] or "contain"
  if fit ~= "contain" and fit ~= "cover" then
    warn(who .. ": a .gallery's fit=" .. fit .. " is contain or cover; contain")
    fit = "contain"
  end
  local captioned = false
  for _, it in ipairs(items) do if it.caption then captioned = true end end
  return { cols = cols, rows = rows, fit = fit, height = height, items = items, captioned = captioned }
end

-- The file a raw \includegraphics names for an image src: percent-decoded (pandoc writes a space as
-- %20), and a media-bag item written to disk first. Quarto's pdfImages filter converts an .svg to a
-- PDF with rsvg-convert, puts it in pandoc's media bag and names it in the src (vec.svg -> vec.pdf);
-- pandoc writes a bag item out only where an Image references it, and a gallery's images are raw
-- LaTeX (engine-beamer.lua's \engineimage), so this writes it where pandoc would,
-- <output>_files/mediabag/<src> (out: the output file, PANDOC_STATE.output_file), and names that.
-- Beamer's alone; here so tests/test_gallery.py reaches it.
local function latex_file(src, out)
  local file = src:gsub("%%(%x%x)", function(h) return string.char(tonumber(h, 16)) end)
  local _, bytes = pandoc.mediabag.lookup(src)
  if not bytes then return file end
  local stem = (out or "index.tex"):gsub("%.[^.%/]*$", "")
  local path = pandoc.path.join({ stem .. "_files", "mediabag", file })
  pandoc.system.make_directory(pandoc.path.directory(path), true)
  local f = assert(io.open(path, "wb"), "engine-common: cannot write " .. path)
  f:write(bytes); f:close()
  return path
end

-- The slide's galleries drawn (top_level): each .gallery div gallery_items() reads becomes draw(g).
local function top_galleries(blocks, who, draw)
  return top_level(blocks, function(b) return is_gallery(b) and "gallery" end,
                   function(b) return gallery_items(b, who) end, draw, who, "pictures")
end

-- The slide a heading opens, when it is not a content slide: "feature" or "closing" (the composed
-- slides, whose bodies are the composition's), "divider" (a heading above the slide level),
-- "untitled" (no heading: the blocks before the first, or after a rule); nil for a content slide
-- (a .full one included: its figure is the format's .full branch's).
local function composed_kind(blk, level)
  if blk.t ~= "Header" then return "untitled" end
  if blk.level < level then return "divider" end
  for _, c in ipairs(blk.classes) do
    if c == "feature" or c == "closing" then return c end
  end
  return nil
end

-- A gallery outside a content slide (composed_kind(): where) is not drawn in any format: each
-- top-level .gallery div of the slide is warned of and unwrapped into its paragraphs (pandoc's pptx
-- writer draws no picture held in a Div), so the pictures stay.
local function unwrap_galleries(blocks, who, where)
  local out = pandoc.Blocks({})
  for _, b in ipairs(blocks) do
    if is_gallery(b) then
      warn(who .. ": a .gallery on a " .. where .. " slide is not drawn; left as its pictures")
      out:extend(b.content)
    else
      out:insert(b)
    end
  end
  return out
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
  has_class = has_class, warn = warn, column_shares = column_shares, status_lists = status_lists, is_grid = is_grid, split_lines = split_lines,
  lone_span = lone_span, card_attrs = card_attrs, box_role = box_role, deck_type_scale = deck_type_scale,
  footnote_marker = footnote_marker, strip_marker = strip_marker, take_footnotes = take_footnotes, lift_footnotes = lift_footnotes, is_figure = is_figure,
  is_note = is_note, split_full = split_full, holds_shape = holds_shape, holds_table = holds_table, is_slide_break = is_slide_break, SLIDE_KINDS = SLIDE_KINDS,
  slide_level = slide_level, slide_from = slide_from, is_notes = is_notes, is_aside = is_aside, split_notes = split_notes,
  divider_subtitle = divider_subtitle, sections = sections, is_quote = is_quote,
  is_agenda = is_agenda, agenda_notes = agenda_notes, agenda_rows = agenda_rows,
  quote_blocks = quote_blocks,
  content_heading = content_heading, take_layout = take_layout,
  theme_options = theme_options, load_livery = load_livery, marking_texts = marking_texts,
  watermark_text = watermark_text, cover_name = cover_name, fineprint_paragraphs = fineprint_paragraphs,
  refs_div = refs_div, refs_heading = refs_heading, ensure_refs = ensure_refs,
  rail_kind = rail_kind, rail_items = rail_items, top_level = top_level, top_rails = top_rails,
  is_gallery = is_gallery, gallery_items = gallery_items, para_images = para_images, top_galleries = top_galleries,
  cell_figure = cell_figure, latex_figure = latex_figure, base64 = base64, simple_table = simple_table, tabled_row = tabled_row,
  composed_kind = composed_kind, unwrap_galleries = unwrap_galleries,
  latex_file = latex_file,
}
