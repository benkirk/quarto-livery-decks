--[[
inline-footnotes.lua: a slide's ^[...] notes as slide footnotes, for pptx (engine-pptx).

pandoc's pptx writer gathers every note into a "Notes" slide at the deck's end and leaves a number
in the text. HTML and PDF lift a slide's notes beside its dagger lines (engine-common.lua's
take_footnotes()); here each note on a content slide becomes the same: a superscript mark in the
text and a paragraph led by its marker (lift_footnotes(): † ‡ § ¶, after the slide's own dagger
lines), which pptx_steps/style_footnotes.py then styles in place, muted. Where the paragraph goes:
on a plain two-column slide, at the end of the last column (content after the columns splits the
slide); else at the slide's end, before its notes (after a table or picture, single-body.lua folds
it into the caption). After slide-layout.lua, before grid-pptx.lua, which flattens a grid slide
with the paragraph after its columns.

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

local function is_notes(b) return b.t == "Div" and C.has_class(b, "notes") end

-- one content slide's body (its heading excluded), the notes lifted and placed
local function lift(slide)
  local blocks, lifted = C.lift_footnotes(slide)
  if #lifted == 0 then return blocks end
  local body, notes = pandoc.Blocks({}), pandoc.Blocks({})
  for _, b in ipairs(blocks) do
    if is_notes(b) then notes:insert(b) else body:insert(b) end
  end
  local last = body[#body]
  if last and last.t == "Div" and C.has_class(last, "columns") and not C.is_grid(last, body) then
    local cols = last.content:filter(function(c) return c.t == "Div" and C.has_class(c, "column") end)
    cols[#cols].content:extend(lifted)
  else
    body:extend(lifted)
  end
  body:extend(notes)
  return body
end

function Pandoc(doc)
  local level = (PANDOC_WRITER_OPTIONS and PANDOC_WRITER_OPTIONS.slide_level) or 2
  if level == 0 then level = 2 end
  local out, i, blocks = pandoc.Blocks({}), 1, doc.blocks
  while i <= #blocks do
    local blk = blocks[i]
    out:insert(blk)
    i = i + 1
    if C.content_heading(blk, level) then
      local slide = pandoc.Blocks({})
      while i <= #blocks and not C.is_slide_break(blocks[i], level) do
        slide:insert(blocks[i])
        i = i + 1
      end
      out:extend(lift(slide))
    end
  end
  doc.blocks = out
  return doc
end
