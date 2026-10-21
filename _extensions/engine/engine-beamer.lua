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
      (a \fontsize group: no autofit here, so check the PDF), .vcenter is
      frame option c, .hcenter centers prose and lists as a block (tables
      and captioned figures center on their own; with one of those or
      columns it does nothing), .center is both, and .fill does nothing;
      .caution boxes the body on a soft yellow field (enginecaution), .wide
      widens it to the paper less geometry.wide-margin a side (enginewide)

  :::: {.columns} / ::: {.column width="55%"}
      columns each its share of the text width less the livery's gaps
      (boxes.columns.gap), as HTML and pptx lay them out (onlytextwidth: no
      overhang into the margins; \enginecolshare)

  metadata `fineprint: "..."`
      small print under the title block, e.g. an NSF funding statement

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

-- Shared with the other format's filter (engine-common.lua): has_class, the deck's type step,
-- the default livery, the slide-footnote markers, the one-figure test and the note test.
local C = dofile(quarto.utils.resolve_path("engine-common.lua"))
local has_class, deck_type_scale, default_livery = C.has_class, C.deck_type_scale, C.default_livery
local footnote_marker, strip_marker, is_figure = C.footnote_marker, C.strip_marker, C.is_figure
local is_note = C.is_note

local function add_frameoption(el, opt)
  local cur = el.attributes["frameoptions"]
  el.attributes["frameoptions"] = (cur and cur ~= "") and (cur .. "," .. opt) or opt
end

local function latex(s) return pandoc.RawBlock("latex", s) end

local function inlines_to_latex(inlines)
  local doc = pandoc.Pandoc({ pandoc.Plain(inlines) })
  return (pandoc.write(doc, "latex"):gsub("%s+$", ""))
end

local function is_slide_break(blk)
  return (blk.t == "Header" and blk.level <= slide_level) or blk.t == "HorizontalRule"
end

-- slide footnotes: † / ‡ paragraphs, lifted to the frame's foot

-- The footnote is a raw block, so pandoc cannot see a Code inline in it when it
-- decides on [fragile]; fine with \texttt, NOT with `listings: true` (\lstinline).
local function footnote_latex(p)
  return "\\enginefootnote{" .. footnote_marker(p) .. "}{"
    .. inlines_to_latex(strip_marker(p.content)) .. "}"
end

local function hoist_footnotes(blocks)
  local out, i = pandoc.Blocks({}), 1
  while i <= #blocks do
    local blk = blocks[i]
    out:insert(blk)
    i = i + 1
    if blk.t == "Header" and blk.level == slide_level
        and not has_class(blk, "feature") and not has_class(blk, "closing") then
      local body, notes, tail = pandoc.Blocks({}), pandoc.List({}), pandoc.Blocks({})
      local filter = { Para = function(p) if footnote_marker(p) then notes:insert(p); return {} end end }
      while i <= #blocks and not is_slide_break(blocks[i]) do
        local b = blocks[i]
        if b.t == "Div" and has_class(b, "notes") then
          tail:insert(b)
        elseif footnote_marker(b) then
          notes:insert(b)
        else
          body:insert(pandoc.walk_block(b, filter))
        end
        i = i + 1
      end
      if #notes > 0 then
        out:insert(latex("\\enginefootnotespring"))
        out:extend(body)
        local tex = pandoc.List({ "\\enginefootnotespring", "\\begin{enginefootnotes}" })
        for _, p in ipairs(notes) do tex:insert(footnote_latex(p)) end
        tex:insert("\\end{enginefootnotes}")
        out:insert(latex(table.concat(tex, "\n")))
      else
        out:extend(body)
      end
      out:extend(tail)
    end
  end
  return out
end

-- Per-slide layout controls: the body goes in a Div before the footnote hoist
-- (which reaches into it) and becomes raw LaTeX afterwards (unwrap_layout).
local LAYOUT_CLASSES = { hcenter = true, vcenter = true, center = true, fill = true,
                         caution = true, wide = true }
local used = { scale = false, hcenter = false }

local function take_layout(blk)
  local h, v, caution, wide, found = false, false, false, false, false
  local kept = pandoc.List({})
  for _, c in ipairs(blk.classes) do
    if LAYOUT_CLASSES[c] then
      found = true
      h = h or c == "hcenter" or c == "center"
      v = v or c == "vcenter" or c == "center"
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
      quarto.log.warning("engine-beamer: scale=\"" .. scale .. "\" is not a number; ignored")
      scale = nil
    end
  end
  if not found then return nil end
  blk.classes = kept
  return { h = h, v = v, caution = caution, wide = wide, scale = scale }
end

local function wrap_layout(blocks)
  local out, i = pandoc.Blocks({}), 1
  while i <= #blocks do
    local blk = blocks[i]
    out:insert(blk)
    i = i + 1
    local lay = blk.t == "Header" and blk.level == slide_level
      and not has_class(blk, "feature") and not has_class(blk, "closing") and take_layout(blk)
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
    Div = function(d) if has_class(d, "columns") then ok = false end end,
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
        used.scale = true
        open, close = "\\enginescalebegin{" .. scale .. "}", "\\enginescaleend"
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

-- \enginescalebegin{S}: the body at S times the current size. Under the engine's font theme
-- every role (tables, code, captions, the sub-item levels, list spacing) is a share of
-- \engine@typebody, read when it is used, so scaling that scales them all; without it, the
-- sub-item sizes (absolute \small, \footnotesize) are scaled by hand, expanded when the group
-- opens (inside it, \f@size is already scaled)
local SCALE_TEX = table.concat({
  "\\makeatletter",
  "\\newcommand\\engine@size[2]{\\noexpand\\fontsize{\\fpeval{#1*#2*\\f@size}pt}"
    .. "{\\fpeval{#1*#2*\\strip@pt\\dimexpr\\f@baselineskip\\relax}pt}}",
  "\\newcommand\\enginescalebegin[1]{\\begingroup",
  "  \\ifdefined\\engine@typebody \\engine@typebody=#1\\engine@typebody \\else",
  "  \\edef\\engine@sub{\\engine@size{#1}{0.9}}\\edef\\engine@subsub{\\engine@size{#1}{0.8}}%",
  "  \\setbeamerfont{itemize/enumerate subbody}{size=\\engine@sub}%",
  "  \\setbeamerfont{itemize/enumerate subsubbody}{size=\\engine@subsub}\\fi",
  "  \\edef\\engine@body{\\engine@size{#1}{1}}\\engine@body\\selectfont}",
  "\\newcommand\\enginescaleend{\\endgroup}",
  "\\makeatother",
}, "\n")

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
  if not (LIVERY and LIVERY.type and LIVERY.type.canvas) then return doc end
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
  local opts = {}
  local to = doc.meta["themeoptions"]
  if to then
    if pandoc.utils.type(to) == "List" then
      for _, o in ipairs(to) do table.insert(opts, pandoc.utils.stringify(o)) end
    else
      table.insert(opts, pandoc.utils.stringify(to))
    end
    doc.meta["themeoptions"] = nil -- consumed here; the template would ignore it
  end
  -- Quarto's own `mathfont:` key (\setmathfont in the template, before the
  -- theme loads) wins over the theme's default math font
  if doc.meta["mathfont"] then
    local set = false
    for _, o in ipairs(opts) do
      if o:match("^%s*mathfont%s*=") then set = true end
    end
    if not set then table.insert(opts, "mathfont=keep") end
  end
  -- the livery: `livery:` in the metadata (a directory, relative to the project), else
  -- the bundled liveries/ncar beside _extensions/
  local livery = doc.meta["livery"] and pandoc.utils.stringify(doc.meta["livery"])
  if livery then
    if not pandoc.path.is_absolute(livery) then
      livery = pandoc.path.join({ pandoc.system.get_working_directory(), livery })
    end
  else
    livery = default_livery(extdir)
    doc.meta["livery"] = livery   -- for the filters after this one (linked-images, diagram-dark)
  end
  table.insert(opts, "livery=" .. livery)
  -- the deck's size step as typescale= (a deck's own typescale= in themeoptions wins)
  local has_scale = false
  for _, o in ipairs(opts) do if o:match("^%s*typescale%s*=") then has_scale = true end end
  local jf = io.open(pandoc.path.join({ livery, "build", "livery.json" }))
  if jf then
    LIVERY = quarto.json.decode(jf:read("a")); jf:close()
    if not has_scale then
      local f = deck_type_scale(doc.meta, LIVERY.type.roles.body.pt, "engine-beamer")
      if f ~= 1 then table.insert(opts, "typescale=" .. string.format("%.4f", f)) end
    end
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

-- .full: the one figure (is_figure, engine-common.lua), its caption paragraphs and its notes.
-- Runs before bound_sized_images, which turns the image into raw LaTeX.
local function split_full(blocks)
  local fig, caption, rest = nil, pandoc.List({}), pandoc.Blocks({})
  for _, b in ipairs(blocks) do
    if b.t == "Div" and (has_class(b, "notes") or has_class(b, "hidden")) then
      rest:insert(b)
    elseif not fig and is_figure(b) then
      fig = b
    elseif fig and (b.t == "Para" or b.t == "Plain") then
      caption:insert(b)
    elseif fig and is_note(b) then   -- a note is the caption here
      caption:extend(b.content)
    else
      return nil
    end
  end
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
      if src then
        add_frameoption(blk, "enginefull=" .. src)
        blk.content = pandoc.Inlines({})
        out:insert(blk)
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
          .. "\" needs one figure, then only paragraphs; drawn as an ordinary slide")
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

  doc.blocks = full_frames(doc.blocks)
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
    hi:insert(pandoc.Blocks({ latex("\\gdef\\enginemarkingtext{" .. text .. "}") }))
    doc.meta["header-includes"] = hi
  end

  local out = pandoc.Blocks({})
  local i, blocks = 1, wrap_layout(doc.blocks)
  local section, subtitles = 0, pandoc.List({})
  while i <= #blocks do
    local blk = blocks[i]
    if blk.t == "Header" and blk.level == slide_level then
      if has_class(blk, "feature") then
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
      -- paragraphs alone between a divider and the next slide: the subtitle
      if not has_class(blk, "unnumbered") then section = section + 1 end
      local j, paras = i + 1, pandoc.List({})
      while j <= #blocks and (blocks[j].t == "Para" or blocks[j].t == "Plain") do
        paras:insert(blocks[j])
        j = j + 1
      end
      if #paras > 0 and (j > #blocks or is_slide_break(blocks[j]))
          and not has_class(blk, "unnumbered") then
        local text = pandoc.List({})
        for k, p in ipairs(paras) do
          if k > 1 then text:insert(pandoc.RawInline("latex", "\\par ")) end
          text:extend(p.content)
        end
        subtitles:insert(latex("\\enginesectionsubtitle{" .. section .. "}{"
          .. inlines_to_latex(text) .. "}"))
        out:insert(blk)
        i = j
      else
        out:insert(blk)
        i = i + 1
      end
    else
      out:insert(blk)
      i = i + 1
    end
  end
  doc.blocks = beamer_columns(note_frames(unwrap_layout(hoist_footnotes(out))))
  if used.scale or used.hcenter then
    local hi = header_includes(doc)
    if used.hcenter then hi:insert(pandoc.Blocks({ latex("\\usepackage{varwidth}") })) end
    if used.scale then hi:insert(pandoc.Blocks({ latex(SCALE_TEX) })) end
    doc.meta["header-includes"] = hi
  end
  if #subtitles > 0 then
    local hi = header_includes(doc)
    hi:insert(pandoc.Blocks(subtitles))
    doc.meta["header-includes"] = hi
  end
  return doc
end
