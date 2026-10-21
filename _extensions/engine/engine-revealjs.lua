--[[
engine-revealjs.lua -- the engine theme's slide furniture for revealjs (HTML) output

The same Markdown as the beamer theme (engine-beamer.lua):

  # Section
  One paragraph right after the divider heading.
      brand-field divider with the brand waves, a "SECTION n" eyebrow, and the
      paragraph as its subtitle

  ## Thank you! {.closing}
      closing slide on the brand field, the heading as a large headline

  ## Title {.feature background-image="photo.jpg"}
      full-bleed photo (pandoc makes it the slide background; the CSS adds
      the translucent title band and drops the logo)

  ## Title {.full}
      one figure (a diagram cell or an image) fills the slide: no title,
      logo, rule or waves; the paragraphs after it (or a ::: note) are a
      one-line caption. The title stays in the page, hidden, for navigation
      and tools.

  ::: note
  A remark under a figure or table.
  :::
      drawn as its caption: the caption size, muted, centred (.engine-note)

  ## Title {.brand-dark}
      content slide on Space, white text, the white-reversed logo (HTML only;
      pptx and beamer draw an ordinary slide)

  metadata `livery: <dir>`, `themeoptions: [title=light]`, `titlegraphic:`,
  `fineprint:`, `institute:` -- as for beamer; HTML also reads `autofit=false`

Overflowing content slides shrink their body text to fit (engine-revealjs.js);
{.no-autofit} or {.scrollable} on a slide opts out.

  ## Title {.center scale="1.4"}
      per-slide layout of the body (everything but the title, notes and
      footnotes), each control independent: .hcenter centers the body block
      across (its text stays left-aligned), .vcenter centers it between the
      title rule and the floor, .center does both (NOT Quarto's .center,
      which moves the title too), scale="S" sizes its text, tables and code
      by S, and .fill grows it until it just fits (HTML only)
      .caution sets the body on a soft yellow field with a brand-yellow bar
      at its left: the warning slides (footnotes stay below it)

Layout lives in engine-revealjs.scss; colors, fonts and logos come from the livery
(`livery:` in the metadata, else the bundled liveries/ncar): its build/livery.css,
attached here with the font and logo files and the autofit script as an HTML dependency
(Quarto copies them into <deck>_files/libs/, or inlines everything under
`embed-resources: true`), and build/livery.json for the roles the waves are drawn in.

The waves are inline SVG drawn in slide pixels (the theme fixes the slide at
1600x900) from the same fitted curves as beamerouterthemeEngine.sty (see
common/utils/fit-waves.py); `themeoptions: [waves=false]` drops them from content
slides.
]]

if not FORMAT:match("revealjs") then
  return {}
end

local W, H = 1600, 900

-- Shared with the other format's filter (engine-common.lua): has_class, the deck's type step, the
-- livery, the slide breaks and kinds, the layout classes, the footnotes, a .full slide's parts,
-- the theme options, the cards' and strips' reading.
local C = dofile(quarto.utils.resolve_path("engine-common.lua"))
local has_class, deck_type_scale = C.has_class, C.deck_type_scale
local footnote_marker, strip_marker, is_note = C.footnote_marker, C.strip_marker, C.is_note

-- The livery (C.load_livery): its build/livery.json carries the roles the waves and fields are drawn
-- in; build/livery.css, attached with the font and logo files, the rest.
local EXTDIR = pandoc.path.directory(quarto.utils.resolve_path("engine-revealjs.lua"))

-- The engine's version, read from _extension.yml beside this file (its one home; a release bumps
-- it there): it names the HTML dependency, engine-revealjs-<version>, so every deck's paths
-- change with it.
local VERSION = (function()
  local f = assert(io.open(pandoc.path.join({ EXTDIR, "_extension.yml" })), "engine-revealjs.lua: no _extension.yml beside the filter")
  local v = f:read("a"):match("\nversion:%s*([%w%.]+)")
  f:close()
  return assert(v, "engine-revealjs.lua: no version: in _extension.yml")
end)()

local PLOTS = dofile(pandoc.path.join({ EXTDIR, "engine-plots.lua" }))

-- Plots at the canvas scale (engine-plots.lua): a figure shown at its natural inches times the
-- slide pixels per canvas inch (and the autofit's factor, as the text), kept out of reveal's
-- stretch, which would size it to the slide's free height; the scss's max-width keeps an
-- oversized one inside its column.
local function size_plots(doc, livery)
  local per_in = 1600 / (livery.type.canvas.w / 72)
  return doc:walk({
    Image = function(img)
      local path = PLOTS.figure_path(img, "revealjs")
      local w = path and PLOTS.natural_inches(path)
      if not w then return nil end
      local style = img.attributes.style or ""
      if style ~= "" and not style:match(";%s*$") then style = style .. "; " end
      img.attributes.style = style .. string.format("width: calc(%.0fpx * var(--engine-fit, 1));", w * per_in)
      img.classes = img.classes:filter(function(c) return c ~= "r-stretch" end)
      for _, c in ipairs({ "nostretch", "engine-plot" }) do
        if not img.classes:includes(c) then img.classes:insert(c) end
      end
      return img
    end,
  })
end

local slide_level = 2

local function html(s) return pandoc.RawBlock("html", s) end

local function is_slide_break(blk) return C.is_slide_break(blk, slide_level) end

-- Slide footnotes: a paragraph that starts with † (or ‡) is an aside.  Every
-- one on a content slide, columns included, moves to the slide's foot, in order, under
-- one short rule (scss); its marker hangs in the margin in the accent color.

local function dagger(p)
  local inl = pandoc.Inlines({ pandoc.RawInline("html",
    '<span class="engine-dagger">' .. footnote_marker(p) .. "</span>") })
  inl:extend(strip_marker(p.content))
  return pandoc.Para(inl)
end

-- Per-slide layout controls (C.take_layout, C.LAYOUT_CLASSES).  The body is wrapped in a Div here,
-- before the footnote hoist (which reaches into it), and becomes raw tags afterwards
-- (unwrap_layout), since pandoc turns a Div that starts with a heading into a
-- <section>.  The classes go on the slide; the script and the scss act on them.
local function wrap_layout(blocks)
  local out, i = pandoc.Blocks({}), 1
  while i <= #blocks do
    local blk = blocks[i]
    out:insert(blk)
    i = i + 1
    local lay = C.content_heading(blk, slide_level) and C.take_layout(blk, "engine-revealjs")
    if lay then
      blk.classes:insert("engine-layout")
      if lay.h then blk.classes:insert("engine-hcenter") end
      if lay.v then blk.classes:insert("engine-vcenter") end
      if lay.fill then blk.classes:insert("engine-fill") end
      if lay.caution then blk.classes:insert("engine-caution") end
      if lay.wide then blk.classes:insert("engine-wide") end
      if lay.scale then blk.attributes["data-engine-scale"] = lay.scale end
      local body, notes = pandoc.Blocks({}), pandoc.Blocks({})
      while i <= #blocks and not is_slide_break(blocks[i]) do
        local b = blocks[i]
        if b.t == "Div" and has_class(b, "notes") then notes:insert(b) else body:insert(b) end
        i = i + 1
      end
      out:insert(pandoc.Div(body, pandoc.Attr("", { "engine-body" })))
      out:extend(notes)
    end
  end
  return out
end

-- A .columns div's columns at their shares of the row less its gaps (C.column_shares(), as the pptx
-- and PDF lay them out): flex-grow by the share from a zero basis, Quarto's width= dropped (the
-- scss gives the row its gap)
local function flex_columns(blocks)
  return blocks:walk({ Div = function(d)
    if not has_class(d, "columns") then return nil end
    local cols, shares = C.column_shares(d)
    for k, col in ipairs(cols) do
      col.attributes["width"] = nil
      col.attributes["style"] = string.format("flex: %.4f 1 0%%;", shares[k]) .. (col.attributes["style"] or "")
    end
    return d
  end })
end

-- A .strip (in a card or on its own): raw tags round its blocks, its role a custom property
-- (role= is ARIA's attribute), its source lines each a paragraph; the scss tints it
local function strips(blocks, livery)
  return blocks:walk({ Div = function(d)
    if not has_class(d, "strip") then return nil end
    local out = pandoc.Blocks({ html(string.format('<div class="engine-strip" style="--engine-strip-role: var(--engine-%s)">',
      C.box_role(livery, d.attributes["role"], "accent", "engine-revealjs"))) })
    out:extend(C.split_lines(d.content))
    out:insert(html("</div>"))
    return out
  end })
end

-- Status items (C.status_lists()): the glyph a span of its status (⚠ with U+FE0E: no emoji), which
-- the scss sets where the bullet was (the bullet dropped), a failed item's text a span it mutes
local function status_items(blocks)
  return C.status_lists(blocks, function(l, kinds)
    for k, item in ipairs(l.content) do
      local kind = kinds[k]
      if kind then
        local first = item[1]
        local glyph = first.content[1].text .. (kind == "warn" and "\u{FE0E}" or "")
        local il = pandoc.Inlines({ pandoc.Span({ pandoc.Str(glyph) }, pandoc.Attr("", { "engine-glyph-" .. kind })) })
        local rest = pandoc.Inlines({})
        for j = 3, #first.content do rest:insert(first.content[j]) end
        if kind == "fail" then il:insert(pandoc.Span(rest, pandoc.Attr("", { "engine-glyph-text" }))) else il:extend(rest) end
        first.content = il
      end
    end
    return l
  end)
end

-- A .lead box: raw tags round its blocks (a Div whose first block is a heading becomes a <section>),
-- its source lines each a paragraph (C.split_lines()); the scss draws it from livery.css's boxes
local function lead_boxes(blocks)
  return blocks:walk({ Div = function(d)
    if not has_class(d, "lead") then return nil end
    local out = pandoc.Blocks({ html('<div class="engine-lead">') })
    out:extend(C.split_lines(d.content))
    out:insert(html("</div>"))
    return out
  end })
end

-- A card column (C.card_attrs()): the Div kept (its flex share), its content raw tags round a head
-- band (the title and sub) and a body, the role a custom property (role= is ARIA's attribute in
-- HTML); [..]{.label} and [..]{.big} spans as engine- classes (a .sub is the band's, read by
-- card_attrs; one in a body is left alone, as the other formats leave it). The scss draws it.
local function inline_html(inlines)
  return (pandoc.write(pandoc.Pandoc({ pandoc.Plain(inlines) }), "html"):gsub("%s+$", ""))
end

local SPANS = { label = "engine-label", big = "engine-big" }

local function card_columns(blocks, livery)
  local roles = livery.boxes.card.roles
  local function card(d, k)
    local default = roles[(k - 1) % #roles + 1]
    local c = C.card_attrs(d, default)
    if not c then return nil end
    c.role = C.box_role(livery, c.role, default, "engine-revealjs")
    local cls = "engine-card" .. (c.pick and " engine-pick" or "") .. (c.solid and " engine-solid" or "")
    local out = pandoc.Blocks({ html(string.format('<div class="%s" style="--engine-card-role: var(--engine-%s)">', cls, c.role)) })
    if c.title or c.sub then
      local head = '<div class="engine-card-head">'
      if c.title then head = head .. '<div class="engine-card-title">' .. inline_html(c.title) .. "</div>" end
      if c.sub then head = head .. '<div class="engine-card-sub">' .. inline_html(c.sub) .. "</div>" end
      out:insert(html(head .. "</div>"))
    end
    out:insert(html('<div class="engine-card-body">'))
    out:extend(c.body:walk({ Span = function(sp)
      for k, v in pairs(SPANS) do
        if has_class(sp, k) then sp.classes = sp.classes:filter(function(x) return x ~= k end); sp.classes:insert(v) end
      end
      return sp
    end }))
    out:insert(html("</div></div>"))
    d.content = out
    return d
  end
  return blocks:walk({ Div = function(d)   -- a card's default role is by its place in the row
    if not has_class(d, "columns") then return nil end
    for k, col in ipairs(C.column_shares(d)) do card(col, k) end
    return d
  end })
end

local function unwrap_layout(blocks)
  local out = pandoc.Blocks({})
  for _, b in ipairs(blocks) do
    if b.t == "Div" and has_class(b, "engine-body") then
      out:insert(html('<div class="engine-body">'))
      out:extend(b.content)
      out:insert(html("</div>"))
    else
      out:insert(b)
    end
  end
  return out
end

-- raw tags, not a Div (see the feature body); before the notes, after the body.
-- Content slides only, as in engine-beamer.lua: a feature slide's text sits on
-- its panel, and the floor of a closing slide is the brand field.
-- the sign-off lockup's box on every content, section and closing slide (the title slide's is
-- in title-slide.html); livery.css shows and places it when the livery has one. Raw tags, not
-- a Div (the <section> trap).
local SIGNOFF_SKIP = { feature = true, full = true }   -- a closing slide wears it

local function add_signoff(blocks)
  local out = pandoc.Blocks({})
  for _, blk in ipairs(blocks) do
    out:insert(blk)
    if (blk.t == "Header" and blk.level == 1) or C.content_heading(blk, slide_level, SIGNOFF_SKIP) then
      out:insert(html('<div class="engine-signoff"></div>'))
    end
  end
  return out
end

-- the marking strip (livery.json marking; its text the deck's marking:, else the livery's default)
-- on every slide, feature and full ones too: a raw div livery.css places and colors
local function add_marking(blocks, text)
  if not text then return blocks end
  local out = pandoc.Blocks({})
  for _, blk in ipairs(blocks) do
    out:insert(blk)
    if blk.t == "Header" and (blk.level == 1 or blk.level == slide_level) then
      out:insert(html('<div class="engine-marking">' .. text .. '</div>'))
    end
  end
  return out
end

local function hoist_footnotes(blocks)
  local out, i = pandoc.Blocks({}), 1
  while i <= #blocks do
    local blk = blocks[i]
    out:insert(blk)
    i = i + 1
    if C.content_heading(blk, slide_level) then
      local slide = pandoc.Blocks({})
      while i <= #blocks and not is_slide_break(blocks[i]) do
        slide:insert(blocks[i])
        i = i + 1
      end
      local kept, notes = C.take_footnotes(slide)
      if #notes > 0 then
        local body, tail = pandoc.Blocks({}), pandoc.Blocks({})
        for _, b in ipairs(kept) do
          if b.t == "Div" and has_class(b, "notes") then tail:insert(b) else body:insert(b) end
        end
        out:extend(body)
        out:insert(html('<div class="engine-footnotes">'))
        for _, p in ipairs(notes) do out:insert(dagger(p)) end
        out:insert(html("</div>"))
        out:extend(tail)
      else
        out:extend(kept)
      end
    end
  end
  return out
end

-- ::: note: the div as .engine-note (the scss: the caption's look, under the figure), after the
-- footnote hoist has lifted any † line out of it; a note left empty goes
local function mark_notes(blocks)
  return blocks:walk({
    Div = function(d)
      if not is_note(d) then return nil end
      if #d.content == 0 then return {} end
      d.classes = d.classes:filter(function(c) return c ~= "note" end)
      d.classes:insert("engine-note")
      return d
    end,
  })
end

-- A percentage height resolves against the whole 900-px slide here, so the
-- beamer recipe for a full-width screenshot, {height="72%"}, runs past the
-- bottom.  Map it onto the content height instead: 72% is the 600-px cap the
-- diagrams get, a smaller percentage is proportionally smaller, and nothing
-- exceeds the cap.  Any style the author set is kept.
local CAP, FULL = 600, 72
function Image(el)
  local pct = tonumber((el.attributes.height or ""):match("^([%d.]+)%%$"))
  if not pct then return nil end
  local px = math.min(CAP, CAP * pct / FULL)
  local style = el.attributes.style or ""
  if style ~= "" and not style:match(";%s*$") then style = style .. ";" end
  el.attributes.height = nil
  el.attributes.style = string.format(
    "%s max-height: calc(%.0fpx * var(--engine-fit, 1)); width: auto;", style, px):gsub("^ ", "")
  return el
end

---------------------------------------------------------------------------
-- brand waves (y runs down here, up in TikZ)
---------------------------------------------------------------------------
-- The livery's wave lines (art.waves in livery.json; common/utils/fit-waves.py fits them): each
-- two cubics from the top edge to the bottom edge, as {x, y} fractions of the slide (y
-- down): start, ctrl, ctrl, peak, ctrl, ctrl, end; and the shift of the cover art per
-- slide kind. Set from the livery in Pandoc(); nil when the livery has no waves.
local WAVES, SHIFT = nil, {}

local function n(v) return string.format("%.1f", v) end
local function P(k, i, dx)
  local p = WAVES[k][i]
  return (p[1] + dx) * W, p[2] * H
end
local function pt(x, y) return n(x) .. " " .. n(y) end
local function seg(k, dx, a, b, c)  -- cubic to point c through controls a, b
  return string.format("C %s %s %s", pt(P(k, a, dx)), pt(P(k, b, dx)), pt(P(k, c, dx)))
end

-- Every shape continues past the slide and the field to the left, so
-- letterboxed screens show no cut edge.  Past each end a line follows its
-- tangent for L px, then eases to vertical over M more (the tangents differ,
-- so a longer run would let the lines cross, which the brand forbids) and
-- runs straight on to E.
local E, L, M = 1200, 100, 160
-- past endpoint i (tangent towards control point j), in direction dir:
-- the end of the straight run, the easing control point, and the far end
local function ext(k, i, j, dx, dir)
  local xe, ye = P(k, i, dx)
  local xc, yc = P(k, j, dx)
  local slope = (xc - xe) / (yc - ye)
  local near = pt(xe + slope * dir * L, ye + dir * L)
  local xfar = xe + slope * dir * (L + M)
  return near, pt(xfar, ye + dir * (L + M)), pt(xfar, ye + dir * E)
end
local function top(k, dx) local _, _, far = ext(k, 1, 2, dx, -1) return far end
local function bottom(k, dx) local _, _, far = ext(k, 7, 6, dx, 1) return far end
-- line k from above the slide to below it, and back up
local function down(k, dx)
  local tnear, tc, tfar = ext(k, 1, 2, dx, -1)
  local bnear, bc, bfar = ext(k, 7, 6, dx, 1)
  return string.format("L %s C %s %s %s L %s %s %s L %s C %s %s %s", tfar, tc, tc, tnear,
    pt(P(k, 1, dx)), seg(k, dx, 2, 3, 4), seg(k, dx, 5, 6, 7), bnear, bc, bc, bfar)
end
local function up(k, dx)
  local tnear, tc, tfar = ext(k, 1, 2, dx, -1)
  local bnear, bc, bfar = ext(k, 7, 6, dx, 1)
  return string.format("L %s C %s %s %s L %s %s %s L %s C %s %s %s", bfar, bc, bc, bnear,
    pt(P(k, 7, dx)), seg(k, dx, 6, 5, 4), seg(k, dx, 3, 2, 1), tnear, tc, tc, tfar)
end

-- the slide left of line k
local function field(k, dx, fill)
  return string.format('<path d="M %d %d L %d %d %s Z" fill="%s"/>',
    -E, H + E, -E, -E, down(k, dx), fill)
end
-- between lines k and m
local function band(k, m, dx, fill, opacity)
  return string.format('<path d="M %s %s %s Z" fill="%s" fill-opacity="%s"/>',
    top(k, dx), down(k, dx), up(m, dx), fill, opacity)
end
local function lines(dx, stroke, width)
  local out = {}
  for k = 1, 3 do
    out[k] = string.format('<path d="M %s %s" fill="none" stroke="%s" stroke-width="%s"/>',
      top(k, dx), down(k, dx), stroke, width or 2.4)
  end
  return table.concat(out)
end

local function svg(body)
  return string.format('<svg class="engine-waves" viewBox="0 0 %d %d" '
    .. 'preserveAspectRatio="none" aria-hidden="true" focusable="false">%s</svg>', W, H, body)
end

-- the title photo as a plain <img>, not an svg <image>: pandoc's embed-resources inlines the
-- former only. Its box is the composition's, from livery.css.
local function photo_img(src)
  if src then return string.format('<img class="engine-title-photo-img" src="%s" alt="">', src) end
  -- the livery's art.titlegraphic: a box livery.css paints (its url() is beside the css)
  return '<div class="engine-title-photo-img engine-title-photo-default"></div>'
end

-- A composition's drawing (livery.json compositions): its band, then the waves by style --
-- bands: the lines with the brand's translucent bands between them (Brand Guide p24); lines:
-- the lines alone; cover: the field to line 2, a translucent band to line 3, the lines -- or,
-- without waves, a field narrower than the slide as a straight-edged rect. `img` (the title
-- photo) goes under the waves, over the band.
local function comp_art(comp, r, img)
  local body, w = {}, comp.waves
  if comp.band then
    local b = comp.band.box
    table.insert(body, string.format('<rect x="%g" y="%g" width="%g" height="%g" fill="%s"/>',
      b[1] * W, b[2] * H, b[3] * W, b[4] * H, r[comp.band.role]))
  end
  if w and WAVES then
    local c, sw = r[w.role], w.line * W
    if w.style == "bands" then
      table.insert(body, band(1, 2, w.shift, c, w.opacity[1]) .. band(2, 3, w.shift, c, w.opacity[2]))
    elseif w.style == "cover" then
      local f = r[comp.field.role]
      table.insert(body, field(2, w.shift, f) .. band(2, 3, w.shift, f, w.opacity[1]))
    end
    table.insert(body, lines(w.shift, c, sw))
  elseif comp.field and comp.field.box[3] < 1 then
    local b = comp.field.box
    table.insert(body, string.format('<path d="M %g %g H %g V %g H %g Z" fill="%s"/>',
      b[1] * W, b[2] * H, (b[1] + b[3]) * W, (b[2] + b[4]) * H, b[1] * W, r[comp.field.role]))
  end
  local art = #body > 0 and svg(table.concat(body)) or ""
  img = img or ""
  return comp.band and art .. img or img .. art
end

-- content slides: the faint lines of the brand's content slides (p26), in the surface color
local function content_waves(c)
  if not WAVES then return "" end
  return svg(lines(SHIFT.content, c.surface))
end

---------------------------------------------------------------------------
-- document setup
---------------------------------------------------------------------------
-- livery.css with the font and logo files beside it (its url()s are bare names), and the
-- autofit script; paths relative to this filter's directory, as the dependency wants
local function add_dependency(livery)
  local function rel(p)
    if not pandoc.path.is_absolute(p) then p = pandoc.path.join({ livery.dir, p }) end
    return pandoc.path.make_relative(p, EXTDIR)
  end
  local res, seen = {}, {}
  local function add(p)
    local name = pandoc.path.filename(p)
    if not seen[name] then seen[name] = true; table.insert(res, { name = name, path = rel(p) }) end
  end
  local mono = livery.typography.monospace   -- a family name, or {family = ...}
  if type(mono) == "table" then mono = mono.family end
  for _, font in ipairs(livery.typography.fonts or {}) do   -- the base family, a headings family, the code face
    if font.family == livery.typography.base or font.family == livery.typography.headings or font.family == mono then
      for _, f in ipairs(font.files or {}) do add(f.path) end
    end
  end
  local roles = {}   -- every field's mark and sign-off (marks): background, primary, the rest sorted
  for role in pairs(livery.marks) do
    if role ~= "background" and role ~= "primary" then table.insert(roles, role) end
  end
  table.sort(roles)
  table.insert(roles, 1, "primary"); table.insert(roles, 1, "background")
  for _, role in ipairs(roles) do
    add(livery.marks[role].logo)
    if livery.marks[role].signoff then add(livery.marks[role].signoff) end
  end
  local comps = {}   -- every composition's own mark and sign-off files (an image: of its own)
  for k in pairs(livery.compositions or {}) do table.insert(comps, k) end
  table.sort(comps)
  for _, k in ipairs(comps) do
    for _, part in ipairs({ "mark", "signoff" }) do
      local p = livery.compositions[k][part]
      if type(p) == "table" and type(p.img) == "string" then add(p.img) end
    end
  end
  for _, kind in ipairs({ "title", "title-light", "section", "closing", "content", "titlegraphic" }) do   -- static art files
    if livery.art and type(livery.art[kind]) == "string" then add(livery.art[kind]) end
  end
  quarto.doc.add_html_dependency({
    name = "engine-revealjs",
    version = VERSION,
    stylesheets = { rel("build/livery.css") },
    scripts = { "engine-revealjs.js" },
    resources = res,
  })
end

-- merge key/values into the title-slide-attributes map, keeping the user's
local function title_slide_attributes(meta, kv)
  local tsa = meta["title-slide-attributes"] or {}
  for k, v in pairs(kv) do
    if tsa[k] == nil then tsa[k] = v end
  end
  meta["title-slide-attributes"] = tsa
end

function Pandoc(doc)
  if PANDOC_WRITER_OPTIONS and PANDOC_WRITER_OPTIONS.slide_level then
    slide_level = PANDOC_WRITER_OPTIONS.slide_level
  end
  local meta = doc.meta
  local opts = C.theme_options(meta)

  local livery = C.load_livery(meta, EXTDIR, "engine-revealjs")
  -- the filters after this one (linked-images, diagram-dark) read the livery it resolved
  if not meta["livery"] then meta["livery"] = livery.dir end
  doc = size_plots(doc, livery); meta = doc.meta
  if livery.art and livery.art.waves then
    WAVES, SHIFT = livery.art.waves.lines, livery.art.waves.shift
  end
  local r = livery.roles
  local c = { primary = r.primary, primary_text = r["primary-text"], secondary = r.secondary,
              surface = r.surface, dark = r.dark }
  local comps = livery.compositions
  local band = livery.title and livery.title.style == "band"
  local light = (opts.title == "light")
  if band and light then
    quarto.log.warning("engine-revealjs: themeoptions title=light is ignored under the livery's band title")
    light = false
  end
  -- a composition's field: the slide's background color, and .engine-field unless it is the page
  -- (field: null, a photo cover's with no field over the photo, is the page)
  local function field_of(comp)
    if not comp.field then return r.background, "" end
    return r[comp.field.role], comp.field.role ~= "background" and " engine-field" or ""
  end
  local content_art = opts.waves ~= "false" and content_waves(c) or nil
  if content_art == "" then content_art = nil end

  add_dependency(livery)
  local tscale = deck_type_scale(meta, livery.type.roles.body.pt, "engine-revealjs")
  if tscale ~= 1 then   -- livery.css multiplies its base sizes by it (every other size is em-relative)
    quarto.doc.include_text("in-header", string.format("<style>:root { --engine-type-scale: %.4f; }</style>", tscale))
  end
  quarto.doc.include_text("in-header", string.format(
    "<script>document.documentElement.classList.add('engine-title-%s'%s)</script>",
    light and "light" or "dark",
    opts.autofit == "false" and ",'engine-no-autofit'" or ""))

  -- title slide: the composition by the band, a photo (the deck's or the livery's) and light
  local tg = meta["titlegraphic"] and pandoc.utils.stringify(meta["titlegraphic"])
  local nophoto = tg == "none"   -- `titlegraphic: none`: the plain cover, not the livery's default
  if nophoto then tg = nil; meta["titlegraphic"] = nil end
  local default_photo = not tg and not nophoto and livery.art and type(livery.art.titlegraphic) == "string"
  local tcomp = comps[band and "title-band" or ((tg or default_photo) and "title-photo" or "title") .. (light and "-light" or "")]
  local bg, fieldclass = field_of(tcomp)
  title_slide_attributes(meta, { ["data-background-color"] = bg })
  meta["engine-title-art"] = pandoc.RawInline("html", comp_art(tcomp, r, (tg or default_photo) and photo_img(tg) or nil))
  meta["engine-title-class"] = fieldclass .. (band and " engine-band" or "") .. (default_photo and " engine-title-photo" or "")
  -- a cover's byline with a box of its own (livery.json compositions): title-slide.html's second stack
  if tcomp.byline and tcomp.byline.box then meta["engine-byline"] = true end
  -- the marking strip's text, as HTML: the deck's marking: (none: off), else the livery's default
  local mk, marking = meta["marking"], nil
  if mk then
    if pandoc.utils.stringify(mk) ~= "none" then
      marking = pandoc.write(pandoc.Pandoc({ pandoc.Plain(pandoc.utils.type(mk) == "Inlines" and mk
        or pandoc.Inlines(pandoc.utils.stringify(mk))) }), "html"):gsub("%s+$", "")
    end
  elseif livery.marking and type(livery.marking.text) == "string" then
    marking = pandoc.write(pandoc.Pandoc({ pandoc.Plain(pandoc.Inlines(livery.marking.text)) }), "html"):gsub("%s+$", "")
  end
  if marking then meta["engine-marking"] = pandoc.RawInline("html", marking) end
  local ccomp = comps[band and "closing-band" or light and "closing-light" or "closing"]

  local out = pandoc.Blocks({})
  local i, blocks, section = 1, wrap_layout(lead_boxes(card_columns(strips(flex_columns(status_items(doc.blocks)), livery), livery))), 0
  while i <= #blocks do
    local blk = blocks[i]
    if blk.t == "Header" and blk.level == 1 and slide_level > 1 then
      local sbg, sclass = field_of(comps.section)
      blk.classes:insert("engine-section")
      if sclass ~= "" then blk.classes:insert("engine-field") end
      blk.attributes["data-background-color"] = sbg
      if not has_class(blk, "unnumbered") then
        section = section + 1
        blk.attributes["data-engine-section"] = tostring(section)
      end
      out:insert(blk)
      out:insert(html(comp_art(comps.section, r)))
      i = i + 1
      -- paragraphs alone between the divider and the next slide: the subtitle
      local j, paras = i, pandoc.List({})
      while j <= #blocks and (blocks[j].t == "Para" or blocks[j].t == "Plain") do
        paras:insert(blocks[j])
        j = j + 1
      end
      if #paras > 0 and (j > #blocks or is_slide_break(blocks[j])) then
        out:insert(pandoc.Div(paras, pandoc.Attr("", { "engine-subtitle" })))
        i = j
      end
    elseif blk.t == "Header" and blk.level == slide_level and has_class(blk, "closing") then
      local cbg, cclass = field_of(ccomp)
      blk.attributes["data-background-color"] = cbg
      if cclass ~= "" then blk.classes:insert("engine-field") end
      if band then blk.classes:insert("engine-band") end
      out:insert(blk)
      local art = comp_art(ccomp, r)
      if art ~= "" then out:insert(html(art)) end
      i = i + 1
    elseif blk.t == "Header" and blk.level == slide_level and has_class(blk, "feature") then
      -- the body goes on a translucent panel over the photo; Space under the
      -- photo so reveal flags the slide dark (white slide number), and a
      -- missing photo is not white-on-white
      if not blk.attributes["data-background-color"] and not blk.attributes["background-color"] then
        blk.attributes["data-background-color"] = c.dark
      end
      -- feature.style: the bar (and the body on its panel), or the cover (the field and waves over
      -- the photo, the title and body in the column)
      local fimg
      if not comps.feature.panel then   -- the cover: the photo into its box, not reveal's full-bleed background
        blk.classes:insert("engine-feature-cover")
        for _, k in ipairs({ "background-image", "background", "data-background-image" }) do
          if blk.attributes[k] then fimg = fimg or blk.attributes[k]; blk.attributes[k] = nil end
        end
      end
      out:insert(blk)
      if comps.feature.bar then out:insert(html('<div class="engine-feature-bar"></div>')) end
      local fart = comp_art(comps.feature, r, fimg and photo_img(fimg))
      if fart ~= "" then out:insert(html(fart)) end
      i = i + 1
      local body, notes = pandoc.Blocks({}), pandoc.Blocks({})
      while i <= #blocks and not is_slide_break(blocks[i]) do
        local b = blocks[i]
        if b.t == "Div" and has_class(b, "notes") then notes:insert(b) else body:insert(b) end
        i = i + 1
      end
      -- raw tags, not a Div: pandoc turns a Div that starts with a heading
      -- into a <section>, which reveal would count as a slide of its own
      if #body > 0 then
        out:insert(html('<div class="engine-feature-body">'))
        out:extend(body)
        out:insert(html('</div>'))
      end
      out:extend(notes)
    elseif blk.t == "Header" and blk.level == slide_level and has_class(blk, "full") then
      i = i + 1
      local slide = pandoc.Blocks({})
      while i <= #blocks and not is_slide_break(blocks[i]) do
        slide:insert(blocks[i])
        i = i + 1
      end
      local fig, caption, rest = C.split_full(slide)
      if fig then
        if #caption > 0 then blk.classes:insert("engine-captioned") end
        out:insert(blk)
        -- raw tags, not a Div (the <section> trap; see the feature body)
        out:insert(html('<div class="engine-full-figure">'))
        out:insert(fig)
        out:insert(html("</div>"))
        if #caption > 0 then
          out:insert(html('<div class="engine-full-caption">'))
          out:extend(caption)
          out:insert(html("</div>"))
        end
        out:extend(rest)
      else
        quarto.log.warning("engine-revealjs: {.full} slide \"" .. pandoc.utils.stringify(blk.content)
          .. "\" needs one figure, then only paragraphs; drawn as an ordinary slide")
        blk.classes = blk.classes:filter(function(c) return c ~= "full" end)
        out:insert(blk)
        if content_art then out:insert(html(content_art)) end
        out:extend(slide)
      end
    elseif blk.t == "Header" and blk.level == slide_level and has_class(blk, "brand-dark") then
      blk.attributes["data-background-color"] = c.dark
      blk.classes:insert("engine-field")
      out:insert(blk)
      i = i + 1
    else
      out:insert(blk)
      i = i + 1
      -- (not over a slide's own background image: the waves sit above
      -- reveal's background layer)
      if content_art and blk.t == "Header" and blk.level == slide_level
          and not blk.attributes["background"] and not blk.attributes["background-image"]
          and not blk.attributes["data-background-image"] then
        out:insert(html(content_art))
      end
    end
  end
  doc.blocks = mark_notes(unwrap_layout(hoist_footnotes(add_marking(add_signoff(out), marking))))
  return doc
end
