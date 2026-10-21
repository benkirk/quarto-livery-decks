-- engine-common.lua -- what the format filters share (engine-revealjs.lua, engine-beamer.lua, and
-- pptx's single-body.lua and grid-pptx.lua): loaded with dofile(quarto.utils.resolve_path("engine-common.lua")),
-- returning a table. A function here reads the same in every format; what a format does with the
-- result stays in its filter (take_layout, hoist_footnotes and split_full differ by format and are
-- not here).

local function has_class(el, cls)
  for _, c in ipairs(el.classes) do
    if c == cls then return true end
  end
  return false
end

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

-- The default livery: liveries/ncar beside the _extensions/ that holds this extension
-- (liveries/ at the top of this repo). A deck reaches the extension through a linked
-- _extensions/, and Lua does not resolve links, so the extension's own directory is found
-- first: changing into a directory does resolve them.
local function default_livery(extdir)
  local ok, real = pcall(pandoc.system.with_working_directory, extdir, pandoc.system.get_working_directory)
  local root = pandoc.path.directory(pandoc.path.directory(ok and real or extdir))
  return pandoc.path.join({ root, "liveries", "ncar" })
end

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

-- ::: note: a remark under a figure or table, drawn as its caption (the caption role, muted,
-- centred) in every format
local function is_note(blk)
  return blk.t == "Div" and has_class(blk, "note")
end

-- A .columns div's columns and their shares of the row, the gaps taken out first, as every format
-- lays them out: a column's width= ("55%" or "0.55") is its share, the columns without one share
-- what is left equally, and shares that add to more than 1 are scaled down to 1 (less than 1
-- leaves the rest of the row empty, at the right).
local function column_shares(div)
  local cols, shares, given, missing = {}, {}, 0, 0
  for _, c in ipairs(div.content) do
    if c.t == "Div" and has_class(c, "column") then
      table.insert(cols, c)
      local w = c.attributes["width"]
      local v = w and tonumber((w:gsub("%%$", "")))
      if v and w:find("%%$") then v = v / 100 end
      if v and v <= 0 then v = nil end
      shares[#cols] = v or false
      if v then given = given + v else missing = missing + 1 end
    end
  end
  local rest = missing > 0 and (given < 1 and (1 - given) / missing or 1 / #cols) or 0
  local total = 0
  for i = 1, #cols do
    shares[i] = shares[i] or rest
    total = total + shares[i]
  end
  if total > 1 then
    for i = 1, #cols do shares[i] = shares[i] / total end
  end
  return cols, shares
end

-- A grid slide: the columns div has a .card column or more than two columns, or the slide (its
-- blocks) has a .lead. pptx draws one from marker paragraphs (grid-pptx.lua, pptx_steps/grid.py);
-- pandoc's two placeholders cannot hold it.
local function is_grid(div, blocks)
  local cols = column_shares(div)
  if #cols > 2 then return true end
  for _, c in ipairs(cols) do
    if has_class(c, "card") then return true end
  end
  for _, b in ipairs(blocks or {}) do
    if b.t == "Div" and has_class(b, "lead") then return true end
  end
  return false
end

-- In a .lead or a .card a source line is a line: each Para cut at its soft and hard line breaks
-- into Paras of their own, so a bold headline over a plain line needs no blank line between them.
-- Lists and other blocks are left alone.
local function split_lines(blocks)
  local out = pandoc.Blocks({})
  for _, b in ipairs(blocks) do
    if b.t == "Para" then
      local cur = pandoc.Inlines({})
      for _, il in ipairs(b.content) do
        if il.t == "SoftBreak" or il.t == "LineBreak" then
          if #cur > 0 then out:insert(pandoc.Para(cur)) end
          cur = pandoc.Inlines({})
        else
          cur:insert(il)
        end
      end
      if #cur > 0 then out:insert(pandoc.Para(cur)) end
    else
      out:insert(b)
    end
  end
  return out
end

-- A paragraph that is one span of the class (`[$20M]{.big}`): its inlines, else nil.
local function lone_span(b, cls)
  if (b.t == "Para" or b.t == "Plain") and #b.content == 1 and b.content[1].t == "Span"
      and has_class(b.content[1], cls) then
    return b.content[1].content
  end
  return nil
end

-- A card column (`::: {.column .card .pick .solid role="primary"}`), as every format draws it:
-- { role, pick, solid, title (inlines or nil), sub (inlines or nil), body (blocks) }. role names the
-- head band's fill (with .solid, the card's), else default (the livery's boxes.card.roles by the
-- card's place in its row, which the caller picks), else primary; .pick draws the outline; a first
-- heading is the band's title, and a paragraph that is one [...]{.sub} right after it the band's
-- second line; the body's source lines are lines (split_lines()). The column's role= is taken off
-- (HTML's ARIA attribute). nil for a column that is not a card.
local function card_attrs(col, default)
  if not has_class(col, "card") then return nil end
  local c = { role = col.attributes["role"] or default or "primary", pick = has_class(col, "pick"),
              solid = has_class(col, "solid") }
  col.attributes["role"] = nil
  local blocks, i = col.content, 1
  if blocks[1] and blocks[1].t == "Header" then
    c.title, i = blocks[1].content, 2
    local sub = blocks[2] and lone_span(blocks[2], "sub")
    if sub then c.sub, i = sub, 3 end
  end
  local rest = pandoc.Blocks({})
  for k = i, #blocks do rest:insert(blocks[k]) end
  c.body = split_lines(rest)
  return c
end

-- A card's or strip's role= as every format draws it: a role or a blend of livery.json, else default
-- (the card's place in its row, a strip's accent); a name that is neither warns and takes the
-- default, as pptx_steps/grid.py does for the pptx.
local function box_role(livery, role, default, who)
  if role == nil or role == default then return default end
  if livery.roles[role] or (livery.blends and livery.blends[role]) then return role end
  quarto.log.warning(who .. ": role=\"" .. role .. "\" is not a role or a blend of the livery; " .. default)
  return default
end

-- Status items: in a .card or a ::: {.status} list, `- [x]` (pandoc's ☒), `- [!]` and `- [-]` are
-- done, warn and fail; a literal ✓ ⚠ ✗ first in an item is one anywhere. `- [ ]` (☐) stays a task
-- list's unchecked box: an unchecked task is not a failure.
local MARKED = { ["☒"] = "done", ["[!]"] = "warn", ["[-]"] = "fail" }
local LITERAL = { ["✓"] = "done", ["⚠"] = "warn", ["✗"] = "fail" }
local GLYPHS = { done = "✓", warn = "⚠", fail = "✗" }

-- status_item(item, marked): an item's (a list of blocks) status, "done" | "warn" | "fail", and the
-- item with its leading glyph normalized to the glyph's Str (✓ ⚠ ✗, no variation selector) and a
-- Space; nil when it is not one. marked: inside a card or a .status list, where [x] [!] [-] count.
local function status_item(item, marked)
  local first = item[1]
  if not first or (first.t ~= "Plain" and first.t ~= "Para") then return nil end
  local x = first.content[1]
  if not x or x.t ~= "Str" then return nil end
  local t = x.text:gsub("\u{FE0E}", ""):gsub("\u{FE0F}", "")
  local kind = LITERAL[t] or (marked and MARKED[t])
  if not kind then return nil end
  local il = first.content:clone()
  il[1] = pandoc.Str(GLYPHS[kind])
  if il[2] and il[2].t ~= "Space" then il:insert(2, pandoc.Space()) end
  local out = pandoc.List(item):clone()
  out[1] = first.t == "Para" and pandoc.Para(il) or pandoc.Plain(il)
  return kind, out
end

-- Every bullet list's status items normalized (status_item()), marked ones inside a card column or
-- a .status div; fn(list, kinds) then returns the list as a format draws it (kinds: the items'
-- statuses, nil for a plain item), or nil to keep it.
local function status_lists(blocks, fn)
  local function lists(bs, marked)
    return bs:walk({ BulletList = function(l)
      local kinds, any = {}, false
      for k, item in ipairs(l.content) do
        local kind, norm = status_item(item, marked)
        if kind then l.content[k], kinds[k], any = norm, kind, true end
      end
      if any then return fn(l, kinds) end
      return nil
    end })
  end
  return blocks:walk({ Div = function(d)
    if has_class(d, "status") or (has_class(d, "column") and has_class(d, "card")) then
      d.content = lists(d.content, true)
      return d
    end
    return nil
  end }):walk({ BulletList = function(l)   -- literal glyphs anywhere
    local kinds, any = {}, false
    for k, item in ipairs(l.content) do
      local kind, norm = status_item(item, false)
      if kind then l.content[k], kinds[k], any = norm, kind, true end
    end
    if any then return fn(l, kinds) end
    return nil
  end })
end

return {
  has_class = has_class, column_shares = column_shares, status_item = status_item, status_lists = status_lists, is_grid = is_grid, split_lines = split_lines,
  lone_span = lone_span, card_attrs = card_attrs, box_role = box_role, deck_type_scale = deck_type_scale, default_livery = default_livery,
  footnote_marker = footnote_marker, strip_marker = strip_marker, is_figure = is_figure,
  is_note = is_note,
}
