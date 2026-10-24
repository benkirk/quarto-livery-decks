-- A linked image, [![](shot.png)](https://...), gets a visible link line on
-- its slide in every format, so a viewer knows the picture opens the live page:
--   revealjs  the slide's footer, muted (.engine-link-line, the scss)
--   beamer    a tiny muted line, bottom center (a TikZ overlay); a linked
--             image taller than 68% is capped there to keep the line clear
--   pptx      nothing here: anything after an image splits the slide, so
--             the engine's pptx_steps/link_captions.py adds a caption box after rendering
-- The picture itself is the link in all three. One line per slide: the first
-- linked image's URL.

local C = dofile(pandoc.path.join({ pandoc.path.directory(PANDOC_SCRIPT_FILE), "engine-common.lua" }))   -- beside this filter

local PDF_MAX = 68      -- % height that leaves the PDF foot line clear of a 16:9 shot

-- PDF: a linked 16:9 screenshot at {height="72%"} reaches the page foot, under
-- the link line; cap it so authors keep one recipe for every format.
function Link(link)
  if not quarto.doc.is_format("beamer") then return nil end
  for _, il in ipairs(link.content) do
    local pct = il.t == "Image" and tonumber((il.attributes.height or ""):match("^([%d.]+)%%$"))
    if pct and pct > PDF_MAX then il.attributes.height = PDF_MAX .. "%" end
  end
  return link
end

local function image_link(blk)
  local url
  pandoc.walk_block(blk, {
    Link = function(link)
      if url then return end
      for _, il in ipairs(link.content) do
        if il.t == "Image" then url = link.target; return end
      end
    end,
  })
  return url
end

local function link_line(url)
  local label = url:gsub("^https?://", "")
  if quarto.doc.is_format("revealjs") then
    local link = pandoc.Link(label, url, "", pandoc.Attr("", { "engine-link-line" }))
    return pandoc.Div({ pandoc.Plain({ link }) }, pandoc.Attr("", { "footer" }))
  elseif quarto.doc.is_format("beamer") then
    local tex = label:gsub("([_%%#&~^$])", "\\%1")
    return pandoc.RawBlock("latex", string.format(
      "\\begin{tikzpicture}[remember picture, overlay]"
        .. "\\node[anchor=south] at ([yshift=1mm]current page.south)"
        .. " {\\tiny\\href{%s}{\\textcolor{BrandMuted}{%s}}};\\end{tikzpicture}",
      (url:gsub("[%%#]", "\\%0")), tex))
  end
end

function Pandoc(doc)
  if not (quarto.doc.is_format("revealjs") or quarto.doc.is_format("beamer")) then
    return nil
  end
  local level = C.slide_level()
  local out, url = pandoc.Blocks({}), nil
  local function close_slide()
    if url then out:insert(link_line(url)) end
    url = nil
  end
  for _, blk in ipairs(doc.blocks) do
    if C.is_slide_break(blk, level) then
      close_slide()
    else
      url = url or image_link(blk)
    end
    out:insert(blk)
  end
  close_slide()
  doc.blocks = out
  return doc
end
