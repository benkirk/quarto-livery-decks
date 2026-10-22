--[[
engine-beamer.lua -- Markdown sugar for the engine beamer theme (beamer output only)

  ## Title {.feature background="photo.jpg"}
      full-bleed photo frame (-> \begin{frame}[enginebg=photo.jpg])

  ## Title {.full}
      one figure (a diagram cell or an image) fills the frame, with no title,
      logo, rule or waves (-> \begin{frame}[enginefull=image]); the paragraphs
      after it (or a ::: note) become one caption line (\enginefullcaption)

  ::: note
  A remark under a figure or table.
  :::
      drawn as its caption: the caption size, muted, centred (\enginenote)

  ## Thank you! {.closing}
      closing frame on the brand field; the heading becomes the large
      headline and the slide's content sits beneath it

  # Section
  One paragraph right after the divider heading.
      the paragraph becomes the divider's subtitle instead of a slide of
      its own (declared in the preamble as \enginesectionsubtitle{n}{...},
      so no stray block before the section can open an empty frame)

  A paragraph that starts with † (or ‡)
      a slide footnote: every one on the frame, columns included, moves to
      the frame's foot under a short rule (\enginefootnotes; see
      beamerinnerthemeEngine.sty)

  ## Title {.center scale="1.4"}
      per-slide layout of the body (everything but the title, notes and
      footnotes), as in HTML: scale="S" sizes its text, tables and code by S
      (enginescale: no autofit here, so check the PDF), .vcenter is
      frame option c, .hcenter centers prose and lists as a block (tables
      and captioned figures center on their own; with one of those or
      columns it does nothing), .center is both, and .fill does nothing;
      .caution boxes the body on a soft yellow field (enginecaution), .wide
      widens it to the paper less geometry.wide-margin a side (enginewide)

  :::: {.columns} / ::: {.column width="55%"}
      columns each its share of the text width less the livery's gaps
      (boxes.columns.gap), as HTML and pptx lay them out (onlytextwidth: no
      overhang into the margins; \enginecolshare)

  ::: {.lead}, ::: {.column .card}, ::: {.strip role=}, status items
      the lead box (enginelead), cards (enginecards, enginecard), strips
      (enginestrip) and ✓ ⚠ ✗ items as HTML and pptx draw them, from
      livery.sty's boxes; the theme's own environments, written as a hand
      author writes them (latex/authoring.md)

  metadata `fineprint: "..."`
      small print under the title block, e.g. an NSF funding statement

  metadata `marking: "CUI"`
      the marking strip on every frame (\enginemarking; the livery places it)

  metadata `themeoptions: [title=light, footer=full, ...]`
      options for \usetheme{Engine} (see beamerthemeEngine.sty)

The filter also loads the theme: it puts this extension's directory on
LaTeX's \input@path and passes livery=<dir>, so the .sty files, logos
and bundled fonts are used in place -- nothing is copied next to the
document.
]]

if not FORMAT:match("beamer") then
  return {}
end

local slide_level = 2

-- Shared with the other format's filter (engine-common.lua): has_class, the deck's type step, the
-- livery, the slide breaks and kinds, the layout classes, the footnotes, a .full slide's parts,
-- the theme options, the cards' and strips' reading.
local C = dofile(quarto.utils.resolve_path("engine-common.lua"))
local has_class, deck_type_scale = C.has_class, C.deck_type_scale
local footnote_marker, strip_marker, is_note = C.footnote_marker, C.strip_marker, C.is_note
-- a content frame here: not a feature or closing frame; a .full frame keeps its layout classes and
-- footnotes in the PDF (HTML leaves them out; the unplanned-city ledger has the divergence)
local CONTENT_KINDS = { feature = true, closing = true }

local function add_frameoption(el, opt)
  local cur = el.attributes["frameoptions"]
  el.attributes["frameoptions"] = (cur and cur ~= "") and (cur .. "," .. opt) or opt
end

local function latex(s) return pandoc.RawBlock("latex", s) end
local function latex_inline(s) return pandoc.RawInline("latex", s) end

local function inlines_to_latex(inlines)
  local doc = pandoc.Pandoc({ pandoc.Plain(inlines) })
  return (pandoc.write(doc, "latex"):gsub("%s+$", ""))
end

local function is_slide_break(blk) return C.is_slide_break(blk, slide_level) end

-- slide footnotes: † ‡ § ¶ paragraphs and ^[...] notes (C.take_footnotes()), lifted to the frame's foot

-- A footnote as \enginefootnote{<marker>}{<text>} with its text left as pandoc's inlines, so a
-- citation in it reaches citeproc (which runs after this filter) and a Code inline in it makes
-- the frame [fragile] as pandoc decides.
local function footnote_block(p)
  local inl = pandoc.Inlines({ latex_inline("\\enginefootnote{" .. footnote_marker(p) .. "}{") })
  inl:extend(strip_marker(p.content))
  inl:insert(latex_inline("}"))
  return pandoc.Plain(inl)
end

-- a lifted note's mark in the text: superscript, in the theme's footnote mark color
local function noteref(s)
  if has_class(s, "engine-noteref") then
    return latex_inline("\\textsuperscript{\\usebeamercolor[fg]{footnote mark}" .. pandoc.utils.stringify(s) .. "}")
  end
end

local function hoist_footnotes(blocks)
  local out, i = pandoc.Blocks({}), 1
  while i <= #blocks do
    local blk = blocks[i]
    out:insert(blk)
    i = i + 1
    if C.content_heading(blk, slide_level, CONTENT_KINDS) then
      local slide = pandoc.Blocks({})
      while i <= #blocks and not is_slide_break(blocks[i]) do
        slide:insert(blocks[i])
        i = i + 1
      end
      local kept, notes = C.take_footnotes(slide)
      local body, tail = pandoc.Blocks({}), pandoc.Blocks({})
      for _, b in ipairs(kept:walk({ Span = noteref })) do
        if b.t == "Div" and has_class(b, "notes") then tail:insert(b) else body:insert(b) end
      end
      if #notes > 0 then
        out:insert(latex("\\enginefootnotespring"))
        out:extend(body)
        out:insert(latex("\\enginefootnotespring\n\\begin{enginefootnotes}"))
        for _, p in ipairs(notes) do out:insert(footnote_block(p)) end
        out:insert(latex("\\end{enginefootnotes}"))
      else
        out:extend(body)
      end
      out:extend(tail)
    end
  end
  return out
end

-- Per-slide layout controls (C.take_layout; .fill means nothing here): the body goes in a Div
-- before the footnote hoist (which reaches into it) and becomes raw LaTeX afterwards (unwrap_layout).
local used = { hcenter = false }

local function wrap_layout(blocks)
  local out, i = pandoc.Blocks({}), 1
  while i <= #blocks do
    local blk = blocks[i]
    out:insert(blk)
    i = i + 1
    local lay = C.content_heading(blk, slide_level, CONTENT_KINDS) and C.take_layout(blk, "engine-beamer")
    if lay then
      if lay.v then add_frameoption(blk, "c") end
      local body, notes = pandoc.Blocks({}), pandoc.Blocks({})
      while i <= #blocks and not is_slide_break(blocks[i]) do
        local b = blocks[i]
        if b.t == "Div" and has_class(b, "notes") then notes:insert(b) else body:insert(b) end
        i = i + 1
      end
      local attr = {}
      if lay.scale then attr["scale"] = lay.scale end
      if lay.h then attr["hcenter"] = "1" end
      if lay.caution then attr["caution"] = "1" end
      if lay.wide then attr["wide"] = "1" end
      out:insert(pandoc.Div(body, pandoc.Attr("", { "engine-body" }, attr)))
      out:extend(notes)
    end
  end
  return out
end

-- longtable cannot go in a box, nor can beamer's columns (verbatim can: varwidth
-- is an environment, not a macro argument); a captioned figure fits but keeps
-- its full width, which strands its caption at the left edge (Quarto has
-- already rendered the float to raw LaTeX by the time this filter runs)
local function boxable(blocks)
  local ok = true
  pandoc.walk_block(pandoc.Div(blocks), {
    Table = function() ok = false end,
    Figure = function() ok = false end,
    RawBlock = function(r)
      if r.format:match("latex") and r.text:find("\\begin{figure}", 1, true) then ok = false end
    end,
    Div = function(d) if has_class(d, "columns") then ok = false end end,   -- cards included (enginecards)
  })
  return ok
end

local function unwrap_layout(blocks)
  local out = pandoc.Blocks({})
  for _, b in ipairs(blocks) do
    if b.t == "Div" and has_class(b, "engine-body") then
      local open, close = "", ""
      local scale = b.attributes["scale"]
      if scale then
        open, close = "\\begin{enginescale}{" .. scale .. "}", "\\end{enginescale}"
      end
      if b.attributes["wide"] then
        open = open .. "\\begin{enginewide}"
        close = "\\end{enginewide}" .. close
      end
      if b.attributes["caution"] then
        open = open .. "\\begin{enginecaution}"
        close = "\\end{enginecaution}" .. close
      end
      if b.attributes["hcenter"] and boxable(b.content) then
        used.hcenter = true
        open = open .. "\\begin{center}\\begin{varwidth}{\\linewidth}"
        close = "\\end{varwidth}\\end{center}" .. close
      end
      if open ~= "" then out:insert(latex(open)) end
      out:extend(b.content)
      if close ~= "" then out:insert(latex(close)) end
    else
      out:insert(b)
    end
  end
  return out
end

-- A .columns div at the text width (onlytextwidth: pandoc's spread the columns into the margins),
-- each column its share (C.column_shares()) of the width less the gaps, a factor pandoc's writer
-- puts before \linewidth (\enginecolshare), so beamer's \hfill between them is the livery's gap,
-- with \enginecolrule (boxes.columns.rule) between the columns. The Div stays a Div: pandoc's
-- writer scopes a heading's block to its column. Last, after the footnote hoist and the layout
-- boxes, which read the Div.
local function beamer_columns(blocks)
  return blocks:walk({ Div = function(d)
    if not has_class(d, "columns") then return nil end
    local cols, shares = C.column_shares(d)
    if not has_class(d, "onlytextwidth") then d.classes:insert("onlytextwidth") end
    local content, k = pandoc.Blocks({}), 0
    for _, b in ipairs(d.content) do
      if b.t == "Div" and has_class(b, "column") then
        k = k + 1
        if k > 1 then content:insert(latex("\\enginecolrule")) end
        b.attributes["width"] = string.format("\\enginecolshare{%.4f}{%d}", shares[k], #cols)
      end
      content:insert(b)
    end
    d.content = content
    return d
  end })
end

-- A row with a card (C.card_attrs()): \begin{enginecards}{<the columns' shares>}, then per column
-- \begin{enginecard}[role=<role>,pick,solid]{<title>}{<sub>} round its body (a plain column beside
-- cards is [plain]{}{}), [..]{.label} and [..]{.big} lines as \enginelabel and \enginebig;
-- beamerinnerthemeEngine.sty sets the bodies first, so the row's cards take one height. A table
-- cannot sit in a box (longtable): the row stays plain columns, warned of. A column's role= is
-- checked here (C.box_role(): all three formats warn alike on an unknown name) and reaches the
-- theme as the role's name; a column without one writes no key, the theme's default by place.

local function card_body(blocks)
  local out = pandoc.Blocks({})
  for _, b in ipairs(blocks) do
    local label, big = C.lone_span(b, "label"), C.lone_span(b, "big")
    if label or big then
      local il = pandoc.Inlines({ pandoc.RawInline("latex", label and "\\enginelabel{" or "\\enginebig{") })
      il:extend(label or big)
      il:insert(pandoc.RawInline("latex", "}"))
      out:insert(pandoc.Para(il))
    else
      out:insert(b)
    end
  end
  return out
end

local function card_rows(blocks, livery)
  local roles = livery.boxes.card.roles
  local title = ""
  local function row(d)
    if not has_class(d, "columns") then return nil end
    local cols, shares = C.column_shares(d)
    local any, tabled = false, false
    for _, col in ipairs(cols) do
      if has_class(col, "card") then any = true end
      col:walk({ Table = function() tabled = true end })
    end
    if not any then return nil end
    if tabled then
      quarto.log.warning("engine-beamer: slide \"" .. title .. "\": a table in a card is drawn as a plain column")
      return nil
    end
    local spec = {}
    for k = 1, #cols do spec[k] = string.format("%.4f", shares[k]) end
    local out = pandoc.Blocks({ latex("\\begin{enginecards}{" .. table.concat(spec, ",") .. "}") })
    for k, col in ipairs(cols) do
      local default = roles[(k - 1) % #roles + 1]   -- by its place in the row
      local given = col.attributes["role"]           -- (card_attrs takes it off)
      local c = C.card_attrs(col, default)
      local keys, head, sub, body = { "plain" }, "", "", col.content
      if c then
        keys = {}
        if given then table.insert(keys, "role=" .. C.box_role(livery, c.role, default, "engine-beamer")) end
        if c.pick then table.insert(keys, "pick") end
        if c.solid then table.insert(keys, "solid") end
        body = c.body
        head = c.title and inlines_to_latex(c.title) or ""
        sub = c.sub and inlines_to_latex(c.sub) or ""
      end
      out:insert(latex(string.format("\\begin{enginecard}[%s]{%s}{%s}", table.concat(keys, ","), head, sub)))
      out:extend(card_body(body))
      out:insert(latex("\\end{enginecard}"))
    end
    out:insert(latex("\\end{enginecards}"))
    return out
  end
  local out = pandoc.Blocks({})
  for _, b in ipairs(blocks) do
    if b.t == "Header" then title = pandoc.utils.stringify(b.content) end
    if b.t == "Div" and has_class(b, "columns") then
      local r = row(b)
      if r then out:extend(r) else out:insert(b) end
    else
      out:insert(b:walk({ Div = row }))
    end
  end
  return out
end

-- Status items (C.status_lists()): a list holding one becomes the theme's enginestatus (beamer's
-- itemize whose \done, \warn and \fail items carry the glyph as the label, where the bullet is,
-- as HTML's and the pptx's, bold in its status color, a failed item's text muted); the other
-- items keep the bullet (\item). The glyph and its space come off the item's inlines.
local STATUS_TEX = { done = "\\done ", warn = "\\warn ", fail = "\\fail " }

local function status_items(blocks)
  return C.status_lists(blocks, function(l, kinds)
    local out = pandoc.Blocks({ latex("\\begin{enginestatus}") })
    for k, item in ipairs(l.content) do
      local kind, blocks2 = kinds[k], pandoc.Blocks(item)
      local first = blocks2[1]
      if kind then
        local il = pandoc.Inlines({ pandoc.RawInline("latex", STATUS_TEX[kind]) })
        for j = 3, #first.content do il:insert(first.content[j]) end
        blocks2[1] = pandoc.Plain(il)
      elseif first and (first.t == "Plain" or first.t == "Para") then
        local il = pandoc.Inlines({ pandoc.RawInline("latex", "\\item ") })
        il:extend(first.content)
        blocks2[1] = pandoc.Plain(il)
      else
        blocks2:insert(1, latex("\\item"))
      end
      out:extend(blocks2)
    end
    out:insert(latex("\\end{enginestatus}"))
    return out
  end)
end

-- A .strip: \begin{enginestrip}[role=<role>] round its blocks, its source lines each a paragraph
local function strips(blocks, livery)
  return blocks:walk({ Div = function(d)
    if not has_class(d, "strip") then return nil end
    local role = C.box_role(livery, d.attributes["role"], "accent", "engine-beamer")
    local out = pandoc.Blocks({ latex("\\begin{enginestrip}[role=" .. role .. "]") })
    out:extend(C.split_lines(d.content))
    out:insert(latex("\\end{enginestrip}"))
    return out
  end })
end

-- Quote blocks (C.quote_blocks(): ::: {.quote}, or a bare `>`), at any depth:
-- \begin{enginequote}[role=<role>]{<attribution>} round its lines (no role=: the box's bar-color)
local function quote_boxes(blocks, livery)
  return C.quote_blocks(blocks, livery, "engine-beamer", function(q)
    local who = q.attribution and inlines_to_latex(q.attribution) or ""
    local out = pandoc.Blocks({ latex("\\begin{enginequote}" .. (q.role and ("[role=" .. q.role .. "]") or "") .. "{" .. who .. "}") })
    out:extend(q.body)
    out:insert(latex("\\end{enginequote}"))
    return out
  end)
end

-- Steps and timelines (C.rail_items()): \begin{enginesteps}[role=<role>]{<n>} with a
-- \begin{enginestep}{<title>} round each step's text (as a card's body: \enginelabel and \enginebig
-- lines), or \begin{enginetimeline}[role=<role>]{<n>} with \enginemilestone[done]{<date>}{<label>}
-- per milestone; beamerinnerthemeEngine.sty sets the texts first and draws the row. At the slide's
-- top level only (C.top_rails(): a card's save boxes are the rail's too). Before the
-- status items, so a literal ✓ first in a milestone is its status, as in the other formats.
local function rails(blocks, livery)
  return C.top_rails(blocks, livery, "engine-beamer", function(kind, r)
    local keys = "role=" .. r.role .. (r.start and r.start ~= 1 and (",start=" .. r.start) or "")   -- the list's first number
    local out = pandoc.Blocks({ latex(string.format("\\begin{engine%s}[%s]{%d}", kind, keys, #r.items)) })
    for _, it in ipairs(r.items) do
      local title = it.title and inlines_to_latex(it.title) or ""
      if kind == "steps" then
        out:insert(latex("\\begin{enginestep}{" .. title .. "}"))
        out:extend(card_body(it.body))
        out:insert(latex("\\end{enginestep}"))
      else
        out:insert(latex("\\enginemilestone" .. (it.done and "[done]" or "") .. "{" .. title .. "}{"))
        out:extend(it.body)
        out:insert(latex("}"))
      end
    end
    out:insert(latex("\\end{engine" .. kind .. "}"))
    return out
  end)
end

-- An image gallery (C.gallery_items()): \begin{enginegallery}[cols=,rows=,fit=,height=] with an
-- \engineimage[<caption>]{<file>} per image (C.latex_file(): the src a URL in pandoc's form, a space
-- as %20, decoded to the file's name; an .svg's PDF, which Quarto left in the media bag, written out
-- first), one raw block; beamerinnerthemeEngine.sty draws the cells, or on a bare [enginefull] frame
-- stores them for the background.
local function gallery_latex(g)
  local keys = string.format("cols=%d,rows=%d,fit=%s", g.cols, g.rows, g.fit) .. (g.height and (",height=" .. g.height) or "")
  local lines = { "\\begin{enginegallery}[" .. keys .. "]" }
  for _, it in ipairs(g.items) do
    local file = C.latex_file(it.src, PANDOC_STATE and PANDOC_STATE.output_file)
    table.insert(lines, "\\engineimage" .. (it.caption and ("[{" .. inlines_to_latex(it.caption) .. "}]") or "") .. "{" .. file .. "}")
  end
  table.insert(lines, "\\end{enginegallery}")
  return pandoc.Blocks({ latex(table.concat(lines, "\n")) })
end

-- The slide's top-level galleries (C.top_galleries(); one in a column is warned of and stays its
-- pictures), as raw LaTeX before bound_sized_images, which would turn an image with a width= into
-- raw LaTeX first (the reader drops the attribute: the cell sizes the picture). A {.full} slide's
-- is full_frames()'.
local function galleries(blocks)
  return C.top_galleries(blocks, "engine-beamer", gallery_latex)
end

-- A .lead box: \begin{enginelead} round its blocks, its source lines each a paragraph
-- (C.split_lines()); beamerinnerthemeEngine.sty draws it from livery.sty's boxes
local function lead_boxes(blocks)
  return blocks:walk({ Div = function(d)
    if not has_class(d, "lead") then return nil end
    local out = pandoc.Blocks({ latex("\\begin{enginelead}") })
    out:extend(C.split_lines(d.content))
    out:insert(latex("\\end{enginelead}"))
    return out
  end })
end

-- A frame whose body opens with a paragraph: \vskip-\parskip before it, so it starts at the body's
-- top as HTML's and the pptx's do (TeX puts \parskip, the parskip package's half line, before every
-- paragraph; a list opens at its own \topsep, which already matches). Frames are top-aligned
-- (beamerthemeEngine.sty), so the space showed. A caution, lead, quote or gallery box opens a paragraph too; the
-- footnote spring and a scale group are looked past; a wide body cancels its own.
local function opens_paragraph(b)   -- true, false, or nil: look at the next block
  if b.t == "Para" or b.t == "Plain" then return true end
  if b.t ~= "RawBlock" then return false end
  local t = b.text
  if t == "\\enginefootnotespring" or t:match("^\\begin{enginescale}{[^}]*}$") then return nil end
  if t:find("\\begin{enginewide}", 1, true) or t:find("\\begin{varwidth}", 1, true) then return false end
  return t:find("\\begin{enginecaution}", 1, true) ~= nil or t:find("\\begin{enginelead}", 1, true) ~= nil
    or t:find("\\begin{enginequote}", 1, true) ~= nil or t:find("\\begin{enginegallery}", 1, true) ~= nil
end

local function first_paragraph(blocks)
  local out, fresh = pandoc.Blocks({}), false
  for _, b in ipairs(blocks) do
    if b.t == "Header" and b.level == slide_level then
      fresh = true
    elseif fresh then
      local opens = opens_paragraph(b)
      if opens ~= nil then
        if opens then out:insert(latex("\\vskip-\\parskip")) end
        fresh = false
      end
    end
    out:insert(b)
  end
  return out
end

local function header_includes(doc)
  local hi = doc.meta["header-includes"]
  if hi == nil then
    hi = pandoc.List({})
  elseif pandoc.utils.type(hi) ~= "List" then
    hi = pandoc.List({ hi })
  end
  return hi
end

local LIVERY   -- build/livery.json, read by load_theme

-- Plots at the canvas scale (engine-plots.lua): a figure's width is its natural inches over the
-- canvas width, as a share of the paper (beamer's paper is not the pptx canvas), and
-- \pandocbounded still keeps an oversized one inside its column and the frame.
local function size_plots(doc)
  local plots = dofile(quarto.utils.resolve_path("engine-plots.lua"))
  local canvas_in = LIVERY.type.canvas.w / 72
  return doc:walk({
    Image = function(img)
      local path = plots.figure_path(img, "beamer")
      local w = path and plots.natural_inches(path)
      if not w then return nil end
      return pandoc.RawInline("latex", string.format(
        "\\pandocbounded{\\includegraphics[width=%.4f\\paperwidth]{%s}}", w / canvas_in, img.src))
    end,
  })
end

local function load_theme(doc)
  local extdir = pandoc.path.directory(quarto.utils.resolve_path("engine_livery.sty"))
  if not pandoc.path.is_absolute(extdir) then
    extdir = pandoc.path.join({ pandoc.system.get_working_directory(), extdir })
  end
  if extdir:find("[%s%%#]") then
    quarto.log.warning("engine-beamer: extension path contains spaces or special "
      .. "characters, which LaTeX's \\input@path cannot handle: " .. extdir)
  end
  local _, opts = C.theme_options(doc.meta)   -- the items as written, for \usetheme
  doc.meta["themeoptions"] = nil -- consumed here; the template would ignore it
  -- Quarto's own `mathfont:` key (\setmathfont in the template, before the
  -- theme loads) wins over the theme's default math font
  if doc.meta["mathfont"] then
    local set = false
    for _, o in ipairs(opts) do
      if o:match("^%s*mathfont%s*=") then set = true end
    end
    if not set then table.insert(opts, "mathfont=keep") end
  end
  -- the livery (C.load_livery): `livery:` in the metadata, else the bundled liveries/ncar
  LIVERY = C.load_livery(doc.meta, extdir, "engine-beamer")
  if not doc.meta["livery"] then doc.meta["livery"] = LIVERY.dir end   -- for the filters after this one (linked-images, diagram-dark)
  table.insert(opts, "livery=" .. LIVERY.dir)
  -- the deck's size step as typescale= (a deck's own typescale= in themeoptions wins)
  local has_scale = false
  for _, o in ipairs(opts) do if o:match("^%s*typescale%s*=") then has_scale = true end end
  if not has_scale then
    local f = deck_type_scale(doc.meta, LIVERY.type.roles.body.pt, "engine-beamer")
    if f ~= 1 then table.insert(opts, "typescale=" .. string.format("%.4f", f)) end
  end
  local tex = table.concat({
    "\\makeatletter",
    "\\providecommand\\input@path{}",
    "\\edef\\input@path{\\input@path{" .. extdir .. "/}}",
    "\\makeatother",
    "\\usetheme[" .. table.concat(opts, ",") .. "]{Engine}",
    -- Quarto callouts (tcolorbox) in the livery's roles; Quarto defines its own
    -- after header-includes, hence \AtBeginDocument
    "\\AtBeginDocument{%",
    "  \\colorlet{quarto-callout-color}{BrandText}%",
    "  \\colorlet{quarto-callout-note-color}{BrandPrimaryContrast}%",
    "  \\colorlet{quarto-callout-note-color-frame}{BrandPrimaryContrast}%",
    "  \\colorlet{quarto-callout-tip-color}{BrandHighlight}%",
    "  \\colorlet{quarto-callout-tip-color-frame}{BrandHighlight}%",
    "  \\colorlet{quarto-callout-important-color}{BrandText}%",
    "  \\colorlet{quarto-callout-important-color-frame}{BrandText}%",
    "  \\colorlet{quarto-callout-warning-color}{BrandAccent}%",
    "  \\colorlet{quarto-callout-warning-color-frame}{BrandAccent}%",
    "  \\colorlet{quarto-callout-caution-color}{BrandAccent}%",
    "  \\colorlet{quarto-callout-caution-color-frame}{BrandAccent}}",
  }, "\n")
  local hi = header_includes(doc)
  hi:insert(1, pandoc.Blocks({ latex(tex) }))
  doc.meta["header-includes"] = hi
end

-- Raw HTML blocks (e.g. an editor modeline comment above the YAML) are
-- dropped by the LaTeX writer, but only after pandoc has already opened an
-- empty frame for them.  Drop them up front.  (Only HTML: quarto uses
-- internal raw formats such as `latex-merge' that must survive.)
function RawBlock(el)
  if el.format:match("^html") then
    return {}
  end
end

-- [text]{.alert} -> \alert{text}
function Span(el)
  if has_class(el, "alert") then
    local out = pandoc.Inlines({ pandoc.RawInline("latex", "\\alert{") })
    out:extend(el.content)
    out:insert(pandoc.RawInline("latex", "}"))
    return out
  end
end

-- Tables in the theme's style (beamerinnerthemeEngine.sty, "tables"): each
-- header cell in \engineth, and every second body row starting with \rowcolor,
-- which colortbl requires to be the first thing in the row
local function raw(s) return pandoc.RawInline("latex", s) end

function Table(tbl)
  for _, row in ipairs(tbl.head.rows) do
    for _, cell in ipairs(row.cells) do
      for _, blk in ipairs(cell.contents) do
        if blk.t == "Plain" or blk.t == "Para" then
          blk.content:insert(1, raw("\\engineth{"))
          blk.content:insert(raw("}"))
        end
      end
    end
  end
  for _, body in ipairs(tbl.bodies) do
    for k, row in ipairs(body.body) do
      local first = row.cells[1]
      if k % 2 == 0 and first then
        local blk = first.contents[1]
        if blk and (blk.t == "Plain" or blk.t == "Para") then
          blk.content:insert(1, raw("\\rowcolor{enginetableband}"))
        else
          first.contents:insert(1, pandoc.Plain({ raw("\\rowcolor{enginetableband}") }))
        end
      end
    end
  end
  return tbl
end

-- .full: the one figure's image path (C.split_full), its caption paragraphs and its notes.
-- Runs before bound_sized_images, which turns the image into raw LaTeX.
local function split_full(blocks)
  local fig, caption, rest = C.split_full(blocks)
  if not fig then return nil end
  local src
  pandoc.walk_block(fig, { Image = function(im) src = src or im.src end })
  if not src then return nil end
  return src, caption, rest
end

local function full_frames(blocks)
  local out, i = pandoc.Blocks({}), 1
  while i <= #blocks do
    local blk = blocks[i]
    i = i + 1
    if blk.t == "Header" and blk.level == slide_level and has_class(blk, "full") then
      local slide = pandoc.Blocks({})
      while i <= #blocks and not is_slide_break(blocks[i]) do
        slide:insert(blocks[i])
        i = i + 1
      end
      local src, caption, rest = split_full(slide)
      local fig = C.split_full(slide)
      local gallery = fig and C.is_gallery(fig) and C.gallery_items(fig, "engine-beamer")
      if fig and C.is_gallery(fig) and not gallery then   -- refused, warned of: an ordinary frame of its pictures
        src = nil
        fig.classes = fig.classes:filter(function(c) return c ~= "gallery" end)   -- read once: galleries() passes it
      end
      if gallery or src then
        -- a gallery's frame takes the bare key (the background draws its cells), a figure's its image
        add_frameoption(blk, gallery and "enginefull" or ("enginefull=" .. src))
        blk.content = pandoc.Inlines({})
        out:insert(blk)
        if gallery then out:extend(gallery_latex(gallery)) end
        if #caption > 0 then
          local text = pandoc.List({})
          for k, p in ipairs(caption) do
            if k > 1 then text:insert(pandoc.RawInline("latex", "\\par ")) end
            text:extend(p.content)
          end
          out:insert(latex("\\enginefullcaption{" .. inlines_to_latex(text) .. "}"))
        end
        out:extend(rest)
      else
        quarto.log.warning("engine-beamer: {.full} slide \"" .. pandoc.utils.stringify(blk.content)
          .. "\" needs one figure or a gallery, then only paragraphs; drawn as an ordinary slide")
        blk.classes = blk.classes:filter(function(c) return c ~= "full" end)
        out:insert(blk)
        out:extend(slide)
      end
    else
      out:insert(blk)
    end
  end
  return out
end

-- ::: note: \enginenote{...} (beamerinnerthemeEngine.sty: the caption's look, under the
-- figure), after the footnote hoist has lifted any † line out of it; a note left empty goes.
-- Under a table it first takes back the skip longtable leaves (\LTpost, which a penalty
-- follows, so \lastskip cannot see it).
local function note_frames(blocks)
  return blocks:walk({
    Blocks = function(bs)
      local out = pandoc.Blocks({})
      for k, d in ipairs(bs) do
        if not is_note(d) then
          out:insert(d)
        elseif #d.content > 0 then
          local tex = pandoc.write(pandoc.Pandoc(d.content), "latex"):gsub("%s+$", "")
          local back = (k > 1 and bs[k - 1].t == "Table") and "\\vskip-\\LTpost" or ""
          out:insert(latex(back .. "\\enginenote{" .. tex .. "}"))
        end
      end
      return out
    end,
  })
end

-- Images with an absolute size (e.g. mermaid diagrams, which Quarto includes
-- at their natural size and so ignore fig-width) can run off the slide or
-- into the neighboring column.  Wrap them in pandoc's \pandocbounded, which
-- scales the image down to the current \linewidth / \textheight if needed.
-- (\pandocbounded exists since pandoc 3.2.1, i.e. Quarto >= 1.6; see _extension.yml.)
local function bound_sized_images(doc)
  return doc:walk({
    Image = function(img)
      local w, h = img.attributes["width"], img.attributes["height"]
      if not (w or h) then return nil end -- unsized: pandoc bounds these itself
      if (w and w:match("%%$")) or (h and h:match("%%$")) then return nil end -- relative
      local tex = pandoc.write(pandoc.Pandoc({ pandoc.Plain({ img }) }), "latex")
      return pandoc.RawInline("latex", "\\pandocbounded{" .. tex:gsub("%s+$", "") .. "}")
    end,
  })
end

function Pandoc(doc)
  if PANDOC_WRITER_OPTIONS and PANDOC_WRITER_OPTIONS.slide_level then
    slide_level = PANDOC_WRITER_OPTIONS.slide_level
  end

  doc.blocks = galleries(full_frames(doc.blocks))
  doc = bound_sized_images(doc)
  load_theme(doc)
  doc = size_plots(doc)

  -- `titlegraphic: none`: the plain cover, not the livery's default photo (pandoc's template
  -- would otherwise \includegraphics{none})
  if doc.meta["titlegraphic"] and pandoc.utils.stringify(doc.meta["titlegraphic"]) == "none" then
    doc.meta["titlegraphic"] = nil
    local hi = header_includes(doc)
    hi:insert(pandoc.Blocks({ latex("\\enginenotitlegraphic") }))
    doc.meta["header-includes"] = hi
  end

  -- title fine print from metadata
  local fp = doc.meta["fineprint"]
  if fp then
    local ty, text = pandoc.utils.type(fp), nil
    if ty == "Inlines" then
      text = inlines_to_latex(fp)
    elseif ty == "Blocks" then
      text = (pandoc.write(pandoc.Pandoc(fp), "latex"):gsub("%s+$", ""))
    else
      text = pandoc.utils.stringify(fp)
    end
    local hi = header_includes(doc)
    hi:insert(pandoc.Blocks({ latex("\\titlefineprint{" .. text .. "}") }))
    doc.meta["header-includes"] = hi
  end

  -- the marking strip's text (marking:; `none` turns the livery's default off): the theme draws it
  local mk = doc.meta["marking"]
  if mk then
    local text = pandoc.utils.stringify(mk) == "none" and "" or
      (pandoc.utils.type(mk) == "Inlines" and inlines_to_latex(mk) or pandoc.utils.stringify(mk))
    local hi = header_includes(doc)
    hi:insert(pandoc.Blocks({ latex("\\enginemarking{" .. text .. "}") }))
    doc.meta["header-includes"] = hi
  end

  -- the references slide (a deck that cites without one gets it last): its frame breaks across
  -- pages as the list needs
  local cited = C.ensure_refs(doc.blocks, doc.meta, slide_level)
  local refs = C.refs_heading(cited, slide_level)
  if refs then add_frameoption(cited[refs], "allowframebreaks") end
  doc.blocks = cited

  local out = pandoc.Blocks({})
  local i, blocks = 1, wrap_layout(doc.blocks)
  local section, subtitles = 0, pandoc.List({})
  while i <= #blocks do
    local blk = blocks[i]
    if blk.t == "Header" and blk.level == slide_level then
      if C.is_agenda(blk, slide_level) then
        -- the agenda: the theme's \engineagenda (beamer's table of contents in the agenda's rows, by
        -- the section the frame sits in); the slide's own body dropped (warned), its notes kept
        blk.classes = blk.classes:filter(function(c) return c ~= "agenda" end)
        out:insert(blk)
        i = i + 1
        local body = pandoc.Blocks({})
        while i <= #blocks and not is_slide_break(blocks[i]) do body:insert(blocks[i]); i = i + 1 end
        local notes = C.agenda_notes(body, "engine-beamer", pandoc.utils.stringify(blk.content))
        out:insert(latex("\\engineagenda"))
        out:extend(notes)
      elseif has_class(blk, "feature") then
        local bg = blk.attributes["background"] or blk.attributes["background-image"]
        if bg then
          add_frameoption(blk, "enginebg=" .. bg)
          blk.attributes["background"] = nil
          blk.attributes["background-image"] = nil
        end
        out:insert(blk)
        i = i + 1
        -- the body on the composition's panel (enginefeaturepanel), the notes outside it
        local body, notes = pandoc.Blocks({}), pandoc.Blocks({})
        while i <= #blocks and not is_slide_break(blocks[i]) do
          local b = blocks[i]
          if b.t == "Div" and has_class(b, "notes") then notes:insert(b) else body:insert(b) end
          i = i + 1
        end
        if #body > 0 then
          -- a heading below the slide's becomes a block here, so it closes inside the panel
          -- (pandoc's own block would run on past the panel's end)
          out:insert(latex("\\begin{enginefeaturepanel}"))
          local open = false
          for _, b in ipairs(body) do
            if b.t == "Header" and b.level > slide_level then
              if open then out:insert(latex("\\end{block}")) end
              out:insert(latex("\\begin{block}{" .. inlines_to_latex(b.content) .. "}"))
              open = true
            else
              out:insert(b)
            end
          end
          if open then out:insert(latex("\\end{block}")) end
          out:insert(latex("\\end{enginefeaturepanel}"))
        end
        out:extend(notes)
      elseif has_class(blk, "closing") then
        -- move the heading into the frame body as the closing headline
        local headline = inlines_to_latex(blk.content)
        add_frameoption(blk, "engineclosing,plain,noframenumbering")
        blk.content = pandoc.Inlines({})
        out:insert(blk)
        out:insert(latex("\\engineclosingcontent{" .. headline .. "}{%"))
        i = i + 1
        while i <= #blocks and not is_slide_break(blocks[i]) do
          out:insert(blocks[i])
          i = i + 1
        end
        out:insert(latex("}"))
      else
        out:insert(blk)
        i = i + 1
      end
    elseif blk.t == "Header" and blk.level == 1 and slide_level > 1 then
      -- paragraphs alone between a divider and the next slide: the subtitle (C.divider_subtitle)
      local paras, j = C.divider_subtitle(blocks, i, slide_level)
      local text = pandoc.List({})
      for k, p in ipairs(paras or {}) do
        if k > 1 then text:insert(pandoc.RawInline("latex", "\\par ")) end
        text:extend(p.content)
      end
      if has_class(blk, "unnumbered") then
        -- outside the count: no \section (pandoc's \section* steps the counter as \section does),
        -- the divider drawn by the theme in a plain frame of its own (an empty-titled slide heading;
        -- a raw block between slides would land in the slide before)
        local frame = pandoc.Header(slide_level, {}, pandoc.Attr(blk.identifier))
        add_frameoption(frame, "plain,noframenumbering")
        out:insert(frame)
        out:insert(latex("\\enginesectionunnumbered{" .. inlines_to_latex(blk.content) .. "}{"
          .. (paras and inlines_to_latex(text) or "") .. "}"))
      else
        section = section + 1
        if paras then
          subtitles:insert(latex("\\enginesectionsubtitle{" .. section .. "}{" .. inlines_to_latex(text) .. "}"))
        end
        out:insert(blk)
      end
      i = j
    else
      out:insert(blk)
      i = i + 1
    end
  end
  doc.blocks = first_paragraph(lead_boxes(strips(quote_boxes(beamer_columns(card_rows(status_items(rails(note_frames(unwrap_layout(hoist_footnotes(out))), LIVERY)), LIVERY)), LIVERY), LIVERY)))
  if used.hcenter then
    local hi = header_includes(doc)
    hi:insert(pandoc.Blocks({ latex("\\usepackage{varwidth}") }))
    doc.meta["header-includes"] = hi
  end
  if #subtitles > 0 then
    local hi = header_includes(doc)
    hi:insert(pandoc.Blocks(subtitles))
    doc.meta["header-includes"] = hi
  end
  if section > 0 then   -- the numbered sections' total, for a livery's section.progress ("SECTION 3 of 5")
    local hi = header_includes(doc)
    hi:insert(pandoc.Blocks({ latex("\\enginesectiontotal{" .. section .. "}") }))
    doc.meta["header-includes"] = hi
  end
  return doc
end
