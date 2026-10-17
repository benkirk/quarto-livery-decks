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
      logo, rule or waves; the paragraphs after it are a one-line caption.
      The title stays in the page, hidden, for navigation and tools.

  ## Title {.brand-dark}
      content slide on Space, white text, the white-reversed logo (HTML only;
      pptx and beamer draw an ordinary slide)

  metadata `livery: <dir>` or `themeoptions: [brand=ucar, title=light]`, `titlegraphic:`,
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
(`livery:` in the metadata, else the bundled liveries/<brand>): its build/livery.css,
attached here with the font and logo files and the autofit script as an HTML dependency
(Quarto copies them into <deck>_files/libs/, or inlines everything under
`embed-resources: true`), and build/livery.json for the roles the waves are drawn in.

The waves are inline SVG drawn in slide pixels (the theme fixes the slide at
1600x900) from the same fitted curves as beamerouterthemeEngine.sty (see
tools/fit-waves.py); `themeoptions: [waves=false]` drops them from content
slides.
]]

if not FORMAT:match("revealjs") then
  return {}
end

local VERSION = "3.7.0"
local W, H = 1600, 900

-- The livery (design section 5): `livery:` in the metadata (a directory, relative to the
-- project), else the bundled liveries/<brand> for themeoptions brand= (ncar). Its
-- build/livery.json carries the roles the waves and fields are drawn in; build/livery.css,
-- attached with the font and logo files, the rest.
local EXTDIR = pandoc.path.directory(quarto.utils.resolve_path("engine-revealjs.lua"))

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

local function load_livery(meta, brand)
  local dir = meta["livery"] and pandoc.utils.stringify(meta["livery"])
  if dir and not pandoc.path.is_absolute(dir) then
    dir = pandoc.path.join({ pandoc.system.get_working_directory(), dir })
  end
  dir = dir or pandoc.path.join({ EXTDIR, "liveries", brand })
  local f = io.open(pandoc.path.join({ dir, "build", "livery.json" }))
  if not f then
    error("engine-revealjs: no livery at " .. dir .. " (build/livery.json is missing): set `livery:` "
      .. "to a livery directory, or themeoptions brand=ncar|ucar|ucp|ncarucar for a bundled one")
  end
  local livery = quarto.json.decode(f:read("a")); f:close()
  -- the physical directory: a flavor's inherited files are `../<parent>/...`, and joined onto a
  -- link (a deck's `_livery`) the path is normalized as text, `_livery/..` becoming the deck
  local ok, real = pcall(pandoc.system.with_working_directory, dir, pandoc.system.get_working_directory)
  livery.dir = ok and real or dir
  return livery
end

local slide_level = 2

local function has_class(el, cls)
  for _, c in ipairs(el.classes) do
    if c == cls then return true end
  end
  return false
end

local function html(s) return pandoc.RawBlock("html", s) end

local function is_slide_break(blk)
  return (blk.t == "Header" and blk.level <= slide_level) or blk.t == "HorizontalRule"
end

-- Slide footnotes: a paragraph that starts with † (or ‡) is an aside.  Every
-- one on a content slide, columns included, moves to the slide's foot, in order, under
-- one short rule (scss); its marker hangs in the margin in the accent color.
local MARKERS = { ["†"] = true, ["‡"] = true }

local function footnote_marker(blk)
  if blk.t ~= "Para" then return nil end
  local x = blk.content[1]
  while x and (x.t == "Emph" or x.t == "Strong" or x.t == "Span") do x = x.content[1] end
  if not (x and x.t == "Str") then return nil end
  local m = x.text:sub(1, 3)  -- both markers are 3 bytes of UTF-8
  return MARKERS[m] and m or nil
end

-- the inlines without their leading marker (and its space); *† text* keeps
-- its emphasis on the text
local function strip_marker(inlines)
  local x, out = inlines[1], pandoc.Inlines({})
  if x.t == "Str" then
    local rest = x.text:sub(4)
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

-- the footnote paragraphs of one slide's blocks, removed from where they stood
local function take_footnotes(blocks)
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
  return kept, found
end

local function dagger(p)
  local inl = pandoc.Inlines({ pandoc.RawInline("html",
    '<span class="engine-dagger">' .. footnote_marker(p) .. "</span>") })
  inl:extend(strip_marker(p.content))
  return pandoc.Para(inl)
end

-- Per-slide layout controls.  The body is wrapped in a Div here, before the
-- footnote hoist (which reaches into it), and becomes raw tags afterwards
-- (unwrap_layout), since pandoc turns a Div that starts with a heading into a
-- <section>.  The classes go on the slide; the script and the scss act on them.
local LAYOUT_CLASSES = { hcenter = true, vcenter = true, center = true, fill = true,
                         caution = true }

local function take_layout(blk)
  local h, v, fill, caution, found = false, false, false, false, false
  local kept = pandoc.List({})
  for _, c in ipairs(blk.classes) do
    if LAYOUT_CLASSES[c] then
      found = true
      h = h or c == "hcenter" or c == "center"
      v = v or c == "vcenter" or c == "center"
      fill = fill or c == "fill"
      caution = caution or c == "caution"
    else
      kept:insert(c)
    end
  end
  local scale = blk.attributes["scale"]
  if scale then
    blk.attributes["scale"] = nil
    found = true
    if not tonumber(scale) then
      quarto.log.warning("engine-revealjs: scale=\"" .. scale .. "\" is not a number; ignored")
      scale = nil
    end
  end
  if not found then return nil end
  blk.classes = kept
  return { h = h, v = v, fill = fill, caution = caution, scale = scale }
end

local function wrap_layout(blocks)
  local out, i = pandoc.Blocks({}), 1
  while i <= #blocks do
    local blk = blocks[i]
    out:insert(blk)
    i = i + 1
    local lay = blk.t == "Header" and blk.level == slide_level
      and not has_class(blk, "feature") and not has_class(blk, "closing")
      and not has_class(blk, "full") and take_layout(blk)
    if lay then
      blk.classes:insert("engine-layout")
      if lay.h then blk.classes:insert("engine-hcenter") end
      if lay.v then blk.classes:insert("engine-vcenter") end
      if lay.fill then blk.classes:insert("engine-fill") end
      if lay.caution then blk.classes:insert("engine-caution") end
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
local function add_signoff(blocks)
  local out = pandoc.Blocks({})
  for _, blk in ipairs(blocks) do
    out:insert(blk)
    if blk.t == "Header" and (blk.level == 1 or blk.level == slide_level)
        and not has_class(blk, "feature") and not has_class(blk, "full") then
      out:insert(html('<div class="engine-signoff"></div>'))
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
    if blk.t == "Header" and blk.level == slide_level
        and not has_class(blk, "feature") and not has_class(blk, "closing")
        and not has_class(blk, "full") then
      local slide = pandoc.Blocks({})
      while i <= #blocks and not is_slide_break(blocks[i]) do
        slide:insert(blocks[i])
        i = i + 1
      end
      local kept, notes = take_footnotes(slide)
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

local function split_full(blocks)
  local fig, caption, rest = nil, pandoc.Blocks({}), pandoc.Blocks({})
  for _, b in ipairs(blocks) do
    if b.t == "Div" and (has_class(b, "notes") or has_class(b, "hidden")) then
      rest:insert(b)
    elseif not fig and is_figure(b) then
      fig = b
    elseif fig and (b.t == "Para" or b.t == "Plain") then
      caption:insert(b)
    else
      return nil
    end
  end
  if not fig then return nil end
  return fig, caption, rest
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

-- themeoptions: a list or a comma-separated string of key=value
local function theme_options(meta)
  local opts, to = {}, meta["themeoptions"]
  if not to then return opts end
  local items = pandoc.utils.type(to) == "List" and to or { to }
  for _, it in ipairs(items) do
    for kv in pandoc.utils.stringify(it):gmatch("[^,%s]+") do
      local k, v = kv:match("^([^=]+)=(.*)$")
      if k then opts[k] = v else opts[kv] = "true" end
    end
  end
  return opts
end

---------------------------------------------------------------------------
-- brand waves (y runs down here, up in TikZ)
---------------------------------------------------------------------------
-- The livery's wave lines (art.waves in livery.json; tools/fit-waves.py fits them): each
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
  for _, font in ipairs(livery.typography.fonts or {}) do   -- the base family and a headings family
    if font.family == livery.typography.base or font.family == livery.typography.headings then
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
  for _, kind in ipairs({ "title", "section", "closing", "content", "titlegraphic" }) do   -- static art files
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
  local opts = theme_options(meta)

  local livery = load_livery(meta, opts.brand or "ncar")
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
  local function field_of(comp)
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
  local default_photo = not tg and livery.art and type(livery.art.titlegraphic) == "string"
  local tcomp = comps[band and "title-band" or ((tg or default_photo) and "title-photo" or "title") .. (light and "-light" or "")]
  local bg, fieldclass = field_of(tcomp)
  title_slide_attributes(meta, { ["data-background-color"] = bg })
  meta["engine-title-art"] = pandoc.RawInline("html", comp_art(tcomp, r, (tg or default_photo) and photo_img(tg) or nil))
  meta["engine-title-class"] = fieldclass .. (band and " engine-band" or "") .. (default_photo and " engine-title-photo" or "")
  local ccomp = comps[band and "closing-band" or light and "closing-light" or "closing"]

  local out = pandoc.Blocks({})
  local i, blocks, section = 1, wrap_layout(doc.blocks), 0
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
      local fig, caption, rest = split_full(slide)
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
  doc.blocks = unwrap_layout(hoist_footnotes(add_signoff(out)))
  return doc
end
