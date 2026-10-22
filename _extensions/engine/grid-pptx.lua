--[[
grid-pptx.lua: a slide's columns, carried to the engine's pptx steps (engine-pptx).

pandoc's pptx writer lays a `.columns` div out on the Two Content layout, two placeholders of the
template's half width each, keeps the first two `.column`s (dropping the rest, silently: pandoc
3.8.3) and drops their `width=`. Two tiers:

- A plain columns slide (two columns, no card, lead or quote; engine-common.lua's is_grid() false)
  stays pandoc's: this leaves a notes line, `engine-columns: 0.55 0.45` (the shares,
  column_shares(), as HTML and PDF lay them out; `wide` added on a `{.wide}` slide, which
  slide-layout.lua has written on its own notes line), after the columns div, so the body still
  starts with it and pandoc still picks Two Content; notes-last.lua moves it to the slide's end,
  and pptx_steps/columns.py frames the columns and deletes the line. Never a marker paragraph
  here: beside a picture or a table it demotes the slide to a Comparison-style layout.
- A grid slide (more than two columns, a card, a lead) is flattened on purpose into one text flow
  with marker paragraphs, a Para of one Str in ⟦ ⟧ (which never occur in prose), for
  pptx_steps/grid.py to redraw and delete: `⟦engine:columns widths=0.3333,0.3333,0.3333⟧`, a
  `⟦engine:column⟧` opening each column and a `⟦engine:end⟧` closing it, a last `⟦engine:end⟧`
  closing the columns (a slide with a lead before its columns already gets one flat
  placeholder from pandoc); a `.lead` (with columns or alone) is `⟦engine:lead⟧` ... `⟦engine:end⟧`,
  its source lines each a paragraph (engine-common.lua's split_lines()). A card column's marker is
  `⟦engine:column card role=primary pick solid⟧` (card_attrs()), its band's title and sub and its
  label and big lines paragraphs led by `⟦engine:title⟧`, `⟦engine:sub⟧`, `⟦engine:label⟧`,
  `⟦engine:big⟧`; a `.strip` (in a card or on its own) is `⟦engine:strip role=accent⟧` ...
  `⟦engine:end⟧`; a quote (`::: {.quote}` or a bare `>`, on its own, in a column or in a card) is
  `⟦engine:quote role=r⟧` (role= only when it names one), its lines, an attribution paragraph led by
  `⟦engine:attribution⟧`, `⟦engine:end⟧`. First-cut limit: a picture or table in a flattened column is not
  drawn as part of it; it stays in the flow, where pandoc splits the slide, and this warns.
- Steps and a timeline (engine-common.lua's rail_items()) are `⟦engine:rail kind=steps role=r⟧`
  (kind=timeline; `start=4` when the ordered list begins past 1: the badges count from it), per
  item `⟦engine:item⟧` (`⟦engine:item done⟧`, a done milestone), its title
  or date a paragraph led by `⟦engine:title⟧`, its text, `⟦engine:end⟧`, and a last `⟦engine:end⟧`;
  a slide with one is a grid slide. A div rail_items() refuses (warned of) stays as it is.

It also writes the deck's `.unnumbered` dividers, which the pptx writer drops, into the metadata
(`engine-unnumbered: 2 4`, their places among the dividers), for pptx_steps/section_subtitle.py.

Plain pandoc, no Quarto API, so a test can run it.
]]

if FORMAT ~= "pptx" then
  return {}
end

local function here(f)   -- this file's directory: Quarto's resolver, else plain pandoc's script path
  if quarto and quarto.utils then return quarto.utils.resolve_path(f) end
  return pandoc.path.join({ pandoc.path.directory(PANDOC_SCRIPT_FILE), f })
end
local C = dofile(here("engine-common.lua"))
local MARK = "engine-columns:"

local function warn(title, msg)
  io.stderr:write(string.format("grid-pptx.lua: WARNING: slide %q: %s\n", title, msg))
end

-- slide-layout.lua's notes line on this slide says `wide`
local function is_wide(blocks)
  for _, b in ipairs(blocks) do
    if b.t == "Div" and C.has_class(b, "notes") then
      local words = pandoc.utils.stringify(b):match("engine%-layout:([^\n]*)")
      if words and (" " .. words .. " "):find("%swide%s") then return true end
    end
  end
  return false
end

local function share(v)
  return (string.format("%.4f", v):gsub("0+$", ""):gsub("%.$", ""))
end

local function marker(s)
  return pandoc.Para({ pandoc.Str("⟦engine:" .. s .. "⟧") })
end

-- a picture or table: pandoc draws it as a shape of its own, outside any column's text
local function is_shape(b)
  if b.t == "Table" or C.is_figure(b) then return true end
  local found = false
  if b.t == "Div" then
    b:walk({ Image = function() found = true end, Table = function() found = true end })
  end
  return found
end

local function prefixed(word, inlines)   -- a paragraph led by a prefix marker, for grid.py
  local il = pandoc.Inlines({ pandoc.Str("⟦engine:" .. word .. "⟧") })
  il:extend(inlines)
  return pandoc.Para(il)
end

-- a quote (C.quote_blocks()): `⟦engine:quote⟧` (`role=r` when it names one; grid.py checks it, the
-- box's bar-color by default), its lines, the attribution a paragraph led by `⟦engine:attribution⟧`,
-- `⟦engine:end⟧`; in a Div of its own (.engine-quote-marks), which flow() and pandoc unwrap
local function quote_marks(q)
  local out = pandoc.Blocks({ marker("quote" .. (q.role and (" role=" .. q.role) or "")) })
  out:extend(q.body)
  if q.attribution then out:insert(prefixed("attribution", q.attribution)) end
  out:insert(marker("end"))
  return pandoc.Div(out, pandoc.Attr("", { "engine-quote-marks" }))
end

-- a column's blocks, its divs unwrapped (the flow has no divs), a [..]{.label} or [..]{.big} line
-- led by its prefix marker, its pictures and tables warned of
local function flow(blocks, title, out)
  for _, b in ipairs(blocks) do
    local label, big = C.lone_span(b, "label"), C.lone_span(b, "big")
    if label or big then
      out:insert(prefixed(label and "label" or "big", label or big))
    elseif b.t == "Div" and C.has_class(b, "strip") then   -- a strip keeps its box: grid.py draws it
      out:insert(marker("strip role=" .. (b.attributes["role"] or "accent")))
      flow(C.split_lines(b.content), title, out)
      out:insert(marker("end"))
    elseif C.rail_kind(b) then
      warn(title, "a ." .. C.rail_kind(b) .. " inside a column or another div is not drawn; left as its list")
      flow(b.content, title, out)
    elseif is_shape(b) then
      warn(title, "a picture/table in a card or a 3+ column slide is not drawn in pptx; left in the flow")
      out:insert(b)
    elseif b.t == "Div" and not C.has_class(b, "notes") then
      flow(b.content, title, out)
    else
      out:insert(b)
    end
  end
  return out
end

local function flatten(d, title)
  local cols, shares = C.column_shares(d)
  local widths = {}
  for k = 1, #cols do widths[k] = share(shares[k]) end
  local out = pandoc.Blocks({ marker("columns widths=" .. table.concat(widths, ",")) })
  for _, col in ipairs(cols) do
    local card = C.card_attrs(col, "")   -- "": no role= (grid.py takes the livery's by place)
    if card then   -- its band's title and sub led by their prefix markers (no heading: no spcBef)
      local role = card.role ~= "" and (" role=" .. card.role) or ""   -- none: grid.py's, by place
      out:insert(marker("column card" .. role .. (card.pick and " pick" or "") .. (card.solid and " solid" or "")))
      if card.title then out:insert(prefixed("title", card.title)) end
      if card.sub then out:insert(prefixed("sub", card.sub)) end
      flow(card.body, title, out)
    else
      out:insert(marker("column"))
      flow(col.content, title, out)
    end
    out:insert(marker("end"))
  end
  out:insert(marker("end"))
  return out
end

-- one slide's blocks: a plain columns slide marked on a notes line, a grid slide flattened
local function mark(blocks, title)
  local out, wide = pandoc.Blocks({}), is_wide(blocks)
  local grid = {}   -- which columns divs are a grid slide's, read before the quotes become markers
  for k, b in ipairs(blocks) do
    if b.t == "Div" and C.has_class(b, "columns") then grid[k] = C.is_grid(b, blocks) end
  end
  blocks = C.quote_blocks(blocks, nil, "grid-pptx.lua", quote_marks)   -- one block for one: k still names it
  for k, b in ipairs(blocks) do
    local kind = C.rail_kind(b)
    local rail = kind and C.rail_items(b, kind, nil, "grid-pptx.lua")
    if b.t == "Div" and C.has_class(b, "strip") then   -- a strip on its own, as wide as the body
      flow({ b }, title, out)
    elseif b.t == "Div" and C.has_class(b, "lead") then
      out:insert(marker("lead"))
      flow(C.split_lines(b.content), title, out)
      out:insert(marker("end"))
    elseif rail then
      out:insert(marker("rail kind=" .. kind .. " role=" .. rail.role
        .. (rail.start and rail.start ~= 1 and (" start=" .. rail.start) or "")))
      for _, item in ipairs(rail.items) do
        out:insert(marker(item.done and "item done" or "item"))
        if item.title then out:insert(prefixed("title", item.title)) end
        flow(item.body, title, out)
        out:insert(marker("end"))
      end
      out:insert(marker("end"))
    elseif b.t == "Div" and C.has_class(b, "engine-quote-marks") then   -- a quote on its own
      out:extend(b.content)
    elseif b.t == "Div" and C.has_class(b, "columns") and grid[k] then
      out:extend(flatten(b, title))
    else
      out:insert(b)
      if b.t == "Div" and C.has_class(b, "columns") then
        local _, shares = C.column_shares(b)
        local words = { MARK, share(shares[1]), share(shares[2]) }
        if wide then table.insert(words, "wide") end
        out:insert(pandoc.Div({ pandoc.Para({ pandoc.Str(table.concat(words, " ")) }) }, pandoc.Attr("", { "notes" })))
      end
    end
  end
  return out
end

function Pandoc(doc)
  -- status items (C.status_lists()): the glyph a Str of its own, first in its item, for
  -- pptx_steps/status_glyphs.py to color; before the cards are flattened (it reads the card divs)
  doc.blocks = C.status_lists(doc.blocks, function(l) return l end)
  local level = (PANDOC_WRITER_OPTIONS and PANDOC_WRITER_OPTIONS.slide_level) or 2
  if level == 0 then level = 2 end
  -- pandoc's pptx writer drops .unnumbered: the dividers outside the count, by their place among
  -- the deck's dividers (1-based), as `engine-unnumbered: 2 4` for pptx_steps/section_subtitle.py
  local unnumbered = {}
  for k, s in ipairs(C.sections(doc.blocks, level)) do
    if s.unnumbered then table.insert(unnumbered, tostring(k)) end
  end
  if #unnumbered > 0 then doc.meta["engine-unnumbered"] = pandoc.MetaString(table.concat(unnumbered, " ")) end
  local out, slide, title = pandoc.Blocks({}), pandoc.Blocks({}), "(before the first slide)"
  for _, blk in ipairs(doc.blocks) do
    if C.is_slide_break(blk, level) then
      out:extend(mark(slide, title))
      slide = pandoc.Blocks({})
      if blk.t == "Header" then title = pandoc.utils.stringify(blk.content) end
    end
    slide:insert(blk)
  end
  out:extend(mark(slide, title))
  doc.blocks = out
  return doc
end
