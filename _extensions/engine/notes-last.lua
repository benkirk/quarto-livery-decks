-- Move each slide's speaker notes (::: {.notes}) to the end of the slide
-- when writing pptx.  Pandoc's pptx writer only picks the Two Content
-- layout when a slide's body *starts* with a columns div, so notes written
-- before the columns split the slide into a title-only slide plus an
-- untitled continuation.  Notes after any content (images and tables
-- included) are harmless, so last is always safe.  Other formats: untouched.

if FORMAT ~= "pptx" then
  return {}
end

local C = dofile(pandoc.path.join({ pandoc.path.directory(PANDOC_SCRIPT_FILE), "engine-common.lua" }))   -- beside this filter

function Pandoc(doc)
  local level = C.slide_level()
  local out, notes = pandoc.Blocks({}), pandoc.Blocks({})
  local function flush()
    out:extend(notes)
    notes = pandoc.Blocks({})
  end
  for _, blk in ipairs(doc.blocks) do
    if C.is_slide_break(blk, level) then
      flush()
      out:insert(blk)
    elseif C.is_notes(blk) then
      notes:insert(blk)
    else
      out:insert(blk)
    end
  end
  flush()
  doc.blocks = out
  return doc
end
