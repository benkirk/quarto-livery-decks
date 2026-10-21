--[[
columns-pptx.lua: a warning for a slide of more than two columns (engine-pptx).

pandoc's pptx writer lays a `.columns` div out on the Two Content layout: it keeps the first two
`.column`s and drops the rest, with no message (pandoc 3.8.3). HTML and PDF lay out any number,
so the third column silently goes missing from the pptx only, and `make qa` cannot see it (the
slide count does not change). This says which slide, once per columns div; the deck is left as
it is. Plain pandoc, no Quarto API, so a test can run it.
]]

local function is_column(b, cls)
  return b.t == "Div" and b.classes:includes(cls)
end

function Pandoc(doc)
  local title = "(before the first slide)"
  local function count(d)
    if not d.classes:includes("columns") then return end
    local n = 0
    for _, c in ipairs(d.content) do
      if is_column(c, "column") then n = n + 1 end
    end
    if n > 2 then
      io.stderr:write(string.format("columns-pptx.lua: WARNING: slide %q has %d columns; "
        .. "the pptx keeps the first 2 (pandoc drops the rest; HTML and PDF show all)\n", title, n))
    end
  end
  for _, blk in ipairs(doc.blocks) do
    if blk.t == "Header" then title = pandoc.utils.stringify(blk.content) end
    if blk.t == "Div" then count(blk) end   -- walk() visits a block's children, not the block
    blk:walk({ Div = count })
  end
  return nil
end
