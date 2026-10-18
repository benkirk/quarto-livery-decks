-- engine-plots.lua: plots at the livery's canvas scale, for both engine filters (dofile'd).
--
-- A Jupyter figure is drawn in canvas inches (Make.common passes charts.figsize as fig-width and
-- fig-height, livery.mplstyle sets its type in points on the pptx canvas), so its text is the
-- slide's size when the picture is shown at width / canvas width of the slide. pptx does that by
-- itself (pandoc places a picture at its natural size); HTML and beamer need the width written:
-- reveal would stretch a lone picture to the slide's free height, and beamer's paper is not the
-- canvas. A figure is a Jupyter cell's picture in Quarto's figure-<format>/ directory with no size
-- of its own.

local M = {}

-- (width, height) in inches of a figure file: an SVG's pt size, a PDF's MediaBox, a PNG's pixels
-- over its pHYs density (matplotlib writes the dpi there); nil when unreadable
function M.natural_inches(path)
  local f = io.open(path, "rb")
  if not f then return nil end
  local data = f:read("a"); f:close()
  local ext = path:match("%.(%w+)$"):lower()
  if ext == "svg" then
    local head = data:sub(1, 2000)
    local w = tonumber(head:match('<svg[^>]-%swidth="([%d.]+)pt"'))
    local h = tonumber(head:match('<svg[^>]-%sheight="([%d.]+)pt"'))
    if w and h then return w / 72, h / 72 end
  elseif ext == "pdf" then
    local x0, y0, x1, y1 = data:match("/MediaBox%s*%[%s*([%d.%-]+)%s+([%d.%-]+)%s+([%d.%-]+)%s+([%d.%-]+)")
    if x0 then return (tonumber(x1) - tonumber(x0)) / 72, (tonumber(y1) - tonumber(y0)) / 72 end
  elseif ext == "png" and data:sub(2, 4) == "PNG" then
    local w, h = string.unpack(">I4I4", data, 17)
    local at = data:find("pHYs", 1, true)
    if at then
      local px, _, unit = string.unpack(">I4I4B", data, at + 4)
      if unit == 1 and px > 0 then return w / (px * 0.0254), h / (px * 0.0254) end
    end
  end
  return nil
end

-- the figure's file when img is a plot a Jupyter cell made for this format, else nil: Quarto
-- names those <cell or label>-output-<n>.<ext>, beside the mermaid and Graphviz pictures in the
-- same figure-<format>/ directory, which keep their own sizes
function M.figure_path(img, format)
  if img.attributes.width or img.attributes.height then return nil end   -- the author sized it
  local src = img.src
  if not src:match("figure%-" .. format:gsub("%-", "%%-") .. "/[^/]*%-output%-%d+%.%w+$") then return nil end
  if src:match("^/") then return src end
  return pandoc.path.join({ pandoc.system.get_working_directory(), src })
end

return M
