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
  drawn as part of it; it stays in the flow, where pandoc splits the slide, and this warns. So a
  two-column slide holding a quote beside a picture or table stays pandoc's (is_grid() false), its
  quote pandoc's own blockquote, warned of.
- Steps and a timeline (engine-common.lua's rail_items()) are `⟦engine:rail kind=steps role=r⟧`
  (kind=timeline; `start=4` when the ordered list begins past 1: the badges count from it), per
  item `⟦engine:item⟧` (`⟦engine:item done⟧`, a done milestone), its title
  or date a paragraph led by `⟦engine:title⟧`, its text, `⟦engine:end⟧`, and a last `⟦engine:end⟧`;
  a slide with one is a grid slide. A div rail_items() refuses (warned of) stays as it is.

- An image gallery (engine-common.lua's gallery_items(), a top-level `::: {.gallery}`) is
  `⟦engine:gallery cols=3 rows=2 fit=contain|cover⟧` (` height=0.6` with height=, ` full` on a
  `{.full}` slide, from slide-layout.lua's notes line), per image `⟦engine:item src=<path>⟧` (the
  path percent-encoded where it holds white space, `=`, `⟦` or `⟧`, as pandoc's URL form already
  writes a space), its caption a paragraph,
  `⟦engine:end⟧`, and a last `⟦engine:end⟧`: text, so pandoc embeds no picture and keeps Title and
  Content; pptx_steps/gallery.py reads the files from the deck's directory. A gallery the reader
  refuses (warned of, naming the slide), or one in a column (warned of), is unwrapped into its
  pictures (pandoc's pptx writer draws no picture held in a Div): on the slide itself pandoc draws
  them and splits the slide over them, which `make qa`'s count catches; in a column it keeps the
  first and drops the rest silently, so the warning is the one signal.

An agenda slide (`## Agenda {.agenda}`, an empty body) is `⟦engine:agenda current=n⟧`, per numbered
section `⟦engine:item n=k state=done|current|next⟧` with its title and subtitle led by
`⟦engine:title⟧` and `⟦engine:sub⟧`, `⟦engine:end⟧`, and a last `⟦engine:end⟧`.

It also writes the deck's `.unnumbered` dividers, which the pptx writer drops, into the metadata
(`engine-unnumbered: 2 4`, their places among the dividers), for pptx_steps/section_subtitle.py.

Plain pandoc, no Quarto API, so a test can run it.
]]

if FORMAT ~= "pptx" then
  return {}
end

local C = dofile(pandoc.path.join({ pandoc.path.directory(PANDOC_SCRIPT_FILE), "engine-common.lua" }))   -- beside this filter
local MARK = "engine-columns:"

local function warn(title, msg)   -- this filter's warnings name the slide (C.warn)
  C.warn(string.format("grid-pptx.lua: slide %q: %s", title, msg))
end

-- the words of slide-layout.lua's notes line on this slide (`wide`, `full`, ...), as a set
local function layout_words(blocks)
  local set = {}
  for _, b in ipairs(blocks) do
    if C.is_notes(b) then
      local words = pandoc.utils.stringify(b):match("engine%-layout:([^\n]*)")
      for w in (words or ""):gmatch("%S+") do set[w] = true end
    end
  end
  return set
end

-- a gallery item's path in its marker, percent-encoded where it would break the marker's grammar
-- (white space, `=`, `⟦`, `⟧`); pandoc has already written a space in it as %20 (a src is a URL), and
-- gallery.py decodes the lot once, so a file's own name comes back
local function encode(src)
  return (src:gsub("[%s=]", function(c) return string.format("%%%02X", c:byte()) end)
    :gsub("⟦", "%%E2%%9F%%A6"):gsub("⟧", "%%E2%%9F%%A7"))
end

local function share(v)
  return (string.format("%.4f", v):gsub("0+$", ""):gsub("%.$", ""))
end

local function marker(s)
  return pandoc.Para({ pandoc.Str("⟦engine:" .. s .. "⟧") })
end

-- a picture or table: pandoc draws it as a shape of its own, outside any column's text
local function is_shape(b)
  return b.t == "Table" or C.is_figure(b) or (b.t == "Div" and C.holds_shape(b))
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
    elseif C.is_gallery(b) then   -- unwrapped: pandoc's pptx writer draws no picture inside a Div
      warn(title, "a .gallery inside a column or another div is not drawn; left as its pictures")
      out:extend(b.content)
    elseif is_shape(b) then
      warn(title, "a picture/table in a card or a 3+ column slide is not drawn in pptx; left in the flow")
      out:insert(b)
    elseif b.t == "Div" and not C.is_notes(b) then
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

-- an agenda slide (C.is_agenda()): its heading (the class off), then `⟦engine:agenda current=n⟧`, per
-- numbered section `⟦engine:item n=k state=done|current|next⟧`, its title led by `⟦engine:title⟧`,
-- the divider's subtitle by `⟦engine:sub⟧`, `⟦engine:end⟧`, and a last `⟦engine:end⟧` (one body
-- placeholder: Title and Content, for grid.py); the slide's own body dropped (warned), its notes kept
local function agenda_marks(blocks, title, secs, current)
  local h = blocks[1]
  h.classes = h.classes:filter(function(c) return c ~= "agenda" end)
  local body = pandoc.Blocks({})
  for k = 2, #blocks do body:insert(blocks[k]) end
  local out = pandoc.Blocks({ h, marker("agenda current=" .. current) })
  for _, row in ipairs(C.agenda_rows(secs, current)) do
    out:insert(marker("item n=" .. row.number .. " state=" .. row.state))
    out:insert(prefixed("title", row.title))
    if row.sub then out:insert(prefixed("sub", row.sub)) end
    out:insert(marker("end"))
  end
  out:insert(marker("end"))
  out:extend(C.agenda_notes(body, "grid-pptx.lua", title))
  return out
end

-- one slide's blocks: a plain columns slide marked on a notes line, a grid slide flattened
local function mark(blocks, title)
  local words = layout_words(blocks)
  local out, wide = pandoc.Blocks({}), words.wide
  local grid, kept = {}, {}   -- which columns divs are a grid slide's, read before the quotes become markers;
  for k, b in ipairs(blocks) do   -- a plain one's quotes (beside a picture or table) stay pandoc's, warned of
    if b.t == "Div" and C.has_class(b, "columns") then
      grid[k] = C.is_grid(b, blocks)
      if not grid[k] then
        b = b:walk({ Div = function(d)   -- a plain columns slide stays pandoc's: a gallery in a column its pictures,
          if C.is_gallery(d) then        -- unwrapped (pandoc draws no picture held in a Div)
            warn(title, "a .gallery inside a column or another div is not drawn; left as its pictures")
            return d.content
          end
        end })
        blocks[k] = b
        local quoted = false
        b:walk({ Div = function(d) if C.is_quote(d) then quoted = true end end, BlockQuote = function() quoted = true end })
        if quoted then
          warn(title, "a quote beside a picture or table in a two-column slide is not drawn in pptx; pandoc's own")
          kept[k] = b
        end
      end
    end
  end
  blocks = C.quote_blocks(blocks, nil, "grid-pptx.lua", quote_marks)   -- one block for one: k still names it
  for k, b in pairs(kept) do blocks[k] = b end
  for k, b in ipairs(blocks) do
    local kind = C.rail_kind(b)
    local who = string.format("grid-pptx.lua: slide %q", title)
    local rail = kind and C.rail_items(b, kind, nil, who)
    local gallery = C.is_gallery(b) and C.gallery_items(b, who)
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
    elseif gallery then
      out:insert(marker(string.format("gallery cols=%d rows=%d fit=%s", gallery.cols, gallery.rows, gallery.fit)
        .. (gallery.height and (" height=" .. gallery.height) or "") .. (words.full and " full" or "")))
      for _, it in ipairs(gallery.items) do
        out:insert(marker("item src=" .. encode(it.src)))
        if it.caption then out:insert(pandoc.Para(it.caption)) end
        out:insert(marker("end"))
      end
      out:insert(marker("end"))
    elseif C.is_gallery(b) then   -- refused (warned of): its pictures, unwrapped, which pandoc draws (a Div's it drops)
      out:extend(b.content)
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
  local level = C.slide_level()
  -- pandoc's pptx writer drops .unnumbered: the dividers outside the count, by their place among
  -- the deck's dividers (1-based), as `engine-unnumbered: 2 4` for pptx_steps/section_subtitle.py
  local unnumbered = {}
  for k, s in ipairs(C.sections(doc.blocks, level)) do
    if s.unnumbered then table.insert(unnumbered, tostring(k)) end
  end
  if #unnumbered > 0 then doc.meta["engine-unnumbered"] = pandoc.MetaString(table.concat(unnumbered, " ")) end
  local secs, current = C.sections(doc.blocks, level), 0   -- current: the numbered dividers so far
  local function one(slide, title)
    if slide[1] and C.is_agenda(slide[1], level) then return agenda_marks(slide, title, secs, current) end
    return mark(slide, title)
  end
  local out, slide, title = pandoc.Blocks({}), pandoc.Blocks({}), "(before the first slide)"
  for _, blk in ipairs(doc.blocks) do
    if C.is_slide_break(blk, level) then
      out:extend(one(slide, title))
      slide = pandoc.Blocks({})
      if blk.t == "Header" then title = pandoc.utils.stringify(blk.content) end
      if blk.t == "Header" and blk.level == 1 and level > 1 and not C.has_class(blk, "unnumbered") then current = current + 1 end
    end
    slide:insert(blk)
  end
  out:extend(one(slide, title))
  doc.blocks = out
  return doc
end
