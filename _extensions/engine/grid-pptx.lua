--[[
grid-pptx.lua: a slide's columns, carried to the engine's pptx steps (engine-pptx).

pandoc's pptx writer lays a `.columns` div out on the Two Content layout, two placeholders of the
template's half width each, and drops the columns' `width=`. On a two-column slide this leaves a
notes line, `engine-columns: 0.55 0.45` (the shares, engine-common.lua's column_shares(), as HTML
and PDF lay them out; `wide` added on a `{.wide}` slide, which slide-layout.lua has written on its
own notes line), after the columns div, so the body still starts with it and pandoc still picks
Two Content; notes-last.lua then moves it to the slide's end, and pptx_steps/columns.py frames the
columns and deletes the line. Never a marker paragraph in the body: beside a picture or a table
it demotes the slide to a Comparison-style layout.

pandoc keeps the first two `.column`s and drops the rest, with no message (pandoc 3.8.3), while
HTML and PDF lay out any number; a slide of more than two warns, naming it, once per columns div.
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

local function warn_many(d, title)
  if not C.has_class(d, "columns") then return end
  local cols = C.column_shares(d)
  if #cols > 2 then
    io.stderr:write(string.format("grid-pptx.lua: WARNING: slide %q has %d columns; "
      .. "the pptx keeps the first 2 (pandoc drops the rest; HTML and PDF show all)\n", title, #cols))
  end
end

-- slide-layout.lua's notes line on this slide says `wide`
local function is_wide(blocks)
  for _, b in ipairs(blocks) do
    if b.t == "Div" and C.has_class(b, "notes") then
      local text = pandoc.utils.stringify(b)
      local words = text:match("engine%-layout:([^\n]*)")
      if words and (" " .. words .. " "):find("%swide%s") then return true end
    end
  end
  return false
end

local function share(v)
  return (string.format("%.4f", v):gsub("0+$", ""):gsub("%.$", ""))
end

-- one slide's blocks, its columns slide marked
local function mark(blocks, title)
  local out, wide = pandoc.Blocks({}), is_wide(blocks)
  for _, b in ipairs(blocks) do
    out:insert(b)
    if b.t == "Div" and C.has_class(b, "columns") then
      local cols, shares = C.column_shares(b)
      if #cols == 2 then
        local words = { MARK, share(shares[1]), share(shares[2]) }
        if wide then table.insert(words, "wide") end
        out:insert(pandoc.Div({ pandoc.Para({ pandoc.Str(table.concat(words, " ")) }) }, pandoc.Attr("", { "notes" })))
      end
    end
  end
  return out
end

function Pandoc(doc)
  local level = (PANDOC_WRITER_OPTIONS and PANDOC_WRITER_OPTIONS.slide_level) or 2
  if level == 0 then level = 2 end
  local out, slide, title = pandoc.Blocks({}), pandoc.Blocks({}), "(before the first slide)"
  for _, blk in ipairs(doc.blocks) do
    if (blk.t == "Header" and blk.level <= level) or blk.t == "HorizontalRule" then
      out:extend(mark(slide, title))
      slide = pandoc.Blocks({})
      if blk.t == "Header" then title = pandoc.utils.stringify(blk.content) end
    end
    if blk.t == "Div" then warn_many(blk, title) end   -- walk() visits a block's children, not the block
    blk:walk({ Div = function(d) warn_many(d, title) end })
    slide:insert(blk)
  end
  out:extend(mark(slide, title))
  doc.blocks = out
  return doc
end
