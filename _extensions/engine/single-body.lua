-- pptx only. Pandoc's pptx writer moves anything that follows a table or an
-- image (a rendered diagram arrives as a Para holding one Image) onto an
-- untitled continuation slide; a code block is text and does not split. The
-- paragraphs after one table or image (a footnote, a remark) move into its
-- caption, which pandoc draws at the slide's foot. A bullet or numbered list
-- there moves in too, as marker paragraphs (`⟦engine:list⟧`, its items, a
-- nested list a span of its own, `⟦engine:end⟧`), which grid.py draws as the
-- body's list under the table or picture. Anything else after it (code, a
-- second table, a list item holding more than a line and its sublists) is left
-- to split: an extra slide is visible, where text in a 100% column wrapper was
-- silently dropped. A slide that already holds a columns div is left alone.
-- Runs after notes-last.lua.
-- A `::: note` div of paragraphs folds the same way, and marks its slide with
-- an `engine-layout: note` notes line: slide_layout.py then draws the caption
-- box as the note (the caption role, muted, centered, under the picture or
-- table). A figure or table with a caption of its own marks its slide the same
-- way, note or not, so its caption looks as in HTML and PDF; a figure's caption
-- that is only folded paragraphs (a lone footnote) stays at the foot.

if not quarto.doc.is_format("pptx") then
  return {}
end

local C = dofile(quarto.utils.resolve_path("engine-common.lua"))
local is_note = C.is_note

local is_aside = C.is_aside   -- speaker notes and Quarto's own divs stay outside the wrapper

local function is_image_para(blk)   -- a paragraph of images alone (C.para_images)
  return C.para_images(blk) ~= nil
end

local function is_nontext(blk)
  if blk.t == "Table" or blk.t == "Figure" or is_image_para(blk) then
    return true
  end
  if blk.t == "Div" then
    for _, inner in ipairs(blk.content) do
      if is_nontext(inner) then return true end
    end
  end
  return false
end

local function is_text(blk)
  return (blk.t == "Para" or blk.t == "Plain") and not is_image_para(blk)
end

local function is_list(blk)
  return blk.t == "BulletList" or blk.t == "OrderedList"
end

local function marker(s)   -- a marker paragraph, as grid-pptx.lua writes them
  return pandoc.Para({ pandoc.Str("⟦engine:" .. s .. "⟧") })
end

-- A list as the paragraphs a caption can carry: `⟦engine:list⟧` (`⟦engine:list ordered
-- start=n⟧`), each item's line, a nested list a span of its own, `⟦engine:end⟧`. nil when an item
-- holds more than one line of text or anything but text and lists: the slide then splits.
local function list_paras(blk)
  local out = pandoc.Blocks({ marker(blk.t == "OrderedList"
    and "list ordered start=" .. blk.listAttributes.start or "list") })
  for _, item in ipairs(blk.content) do
    local lines = 0
    for _, b in ipairs(item) do
      if is_text(b) and lines == 0 then
        out:insert(pandoc.Para(b.content))
        lines = 1
      elseif is_list(b) then
        local inner = list_paras(b)
        if not inner then return nil end
        out:extend(inner)
      else
        return nil
      end
    end
  end
  out:insert(marker("end"))
  return out
end

-- a note of paragraphs only (anything else in it is left to split, as after a figure)
local function is_text_note(blk)
  if not is_note(blk) then return false end
  for _, b in ipairs(blk.content) do
    if not is_text(b) then return false end
  end
  return true
end

-- pandoc's pptx writer captions a figure from its image's text, so paragraphs
-- go there too, one line each: the image's text and the paragraphs' inlines,
-- joined by line breaks
local function caption_lines(text, paras)
  local out = pandoc.Inlines({})
  out:extend(text)
  for _, para in ipairs(paras) do
    if #out > 0 then out:insert(pandoc.LineBreak()) end
    out:extend(para.content)
  end
  return out
end

-- The caption of a table or figure, or nil when blk has neither.
local function caption_of(blk)
  if blk.t == "Table" or blk.t == "Figure" then
    return blk.caption.long
  end
  return nil
end

-- true when blk is a figure or table (or a div holding one) with a caption of its own
local function own_caption(blk)
  if blk.t == "Figure" or blk.t == "Table" then
    return pandoc.utils.stringify(blk.caption.long) ~= ""
  end
  if blk.t == "Div" then
    local inner = nil
    for _, b in ipairs(blk.content) do
      if is_nontext(b) then
        if inner then return false end
        inner = b
      end
    end
    return inner ~= nil and own_caption(inner)
  end
  return false
end

-- blk with paras appended to its caption; an image paragraph becomes a figure.
-- A div holding exactly one table or figure is folded into that block.
local function fold(blk, paras)
  local cap = caption_of(blk)
  if cap then
    cap:extend(paras)
    if blk.t == "Figure" then   -- a captioned figure: its image's text too, or they vanish
      blk.content = blk.content:walk({
        Image = function(il) il.caption = caption_lines(il.caption, paras); return il end,
      })
    end
    return blk
  end
  if is_image_para(blk) then
    local content = blk.content:map(function(il)
      if il.t == "Image" then il.caption = caption_lines(pandoc.Inlines({}), paras) end
      return il
    end)
    return pandoc.Figure({ pandoc.Plain(content) }, { long = paras })
  end
  if blk.t == "Div" then
    local inner = nil
    for i, b in ipairs(blk.content) do
      if is_nontext(b) then
        if inner then return nil end
        inner = i
      end
    end
    if inner then
      local folded = fold(blk.content[inner], paras)
      if folded then
        blk.content[inner] = folded
        return blk
      end
    end
  end
  return nil
end

-- The body with trailing paragraphs folded into the one table or image they
-- follow, or the body unchanged when that is not its shape; true when a note
-- was folded or the block has a caption of its own (slide_layout.py then draws
-- the caption box in the caption's look, as HTML and PDF set a caption).
local function fold_trailing(body)
  local at = nil
  for i, blk in ipairs(body) do
    if blk.t == "Div" and blk.classes:includes("columns") then
      return body
    end
    if is_nontext(blk) then
      if at then return body end
      at = i
    end
  end
  if not at then
    return body
  end
  local captioned = own_caption(body[at])   -- before the fold extends the caption
  if at == #body then
    return body, captioned
  end
  local paras, noted = pandoc.Blocks({}), captioned
  for i = at + 1, #body do
    if is_text(body[i]) then
      paras:insert(body[i])
    elseif is_text_note(body[i]) then
      paras:extend(body[i].content)
      noted = true
    elseif is_list(body[i]) then
      local list = list_paras(body[i])
      if not list then return body end
      paras:extend(list)
    else
      return body
    end
  end
  local folded = fold(body[at], paras)
  if not folded then return body end
  local out = pandoc.Blocks({})
  for i = 1, at - 1 do out:insert(body[i]) end
  out:insert(folded)
  return out, noted
end

function Pandoc(doc)
  local level = C.slide_level()
  local out = pandoc.Blocks({})
  local body, notes, in_slide = pandoc.Blocks({}), pandoc.Blocks({}), false
  local function flush()
    local blocks, noted = body, false
    if in_slide then blocks, noted = fold_trailing(body) end
    out:extend(blocks)
    out:extend(notes)
    if noted then   -- slide_layout.py reads it (slide-layout.lua writes the other words)
      out:insert(pandoc.Div({ pandoc.Para({ pandoc.Str("engine-layout: note") }) },
        pandoc.Attr("", { "notes" })))
    end
    body, notes = pandoc.Blocks({}), pandoc.Blocks({})
  end
  for _, blk in ipairs(doc.blocks) do
    if C.is_slide_break(blk, level) then
      flush()
      out:insert(blk)
      in_slide = blk.t == "Header" and blk.level == level
    elseif is_aside(blk) then
      notes:insert(blk)
    else
      body:insert(blk)
    end
  end
  flush()
  doc.blocks = out
  return doc
end
