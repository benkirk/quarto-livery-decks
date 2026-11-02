-- pptx only. A movie (C.movie: an image whose source is a movie, docs/authoring.md "Movies") means
-- nothing to pandoc's pptx writer, which knows pictures alone (it embeds the .mp4 as a broken
-- picture). So pandoc gets the movie's poster, and lays it out as any picture (a column, a .full
-- slide, a caption folded under it by single-body.lua), and the slide gets one speaker-notes line per
-- movie,
--   engine-movie: <poster> <movie> autoplay loop muted
-- the two paths percent-encoded where they hold white space or `%`, the flags those that are on.
-- pptx_steps/movie.py finds the picture by its path (pandoc writes the src as the picture's descr),
-- puts the movie in its frame over the poster, and removes the line. Before grid-pptx.lua: a movie in a
-- grid cell or a gallery is drawn by the steps from a marker, not by pandoc, and stays its poster (the
-- step warns). A movie with no poster (C.ensure_poster warns) is its path, as text.

if not quarto.doc.is_format("pptx") then
  return {}
end

local C = dofile(pandoc.path.join({ pandoc.path.directory(PANDOC_SCRIPT_FILE), "engine-common.lua" }))   -- beside this filter

local function encode(path)
  return (path:gsub("[%s%%]", function(c) return string.format("%%%02X", c:byte()) end))
end

function Pandoc(doc)
  local level = C.slide_level()
  local out, lines = pandoc.Blocks({}), {}
  local function flush()
    if #lines > 0 then
      local paras = pandoc.Blocks({})
      for _, l in ipairs(lines) do paras:insert(pandoc.Para({ pandoc.Str(l) })) end
      out:insert(pandoc.Div(paras, pandoc.Attr("", { "notes" })))
      lines = {}
    end
  end
  for _, b in ipairs(doc.blocks) do
    if C.is_slide_break(b, level) then flush() end
    if C.is_notes(b) then
      out:insert(b)
    else
      out:insert(b:walk({
        Image = function(img)
          if not C.is_movie(img) then return nil end
          local m = C.movie(img)
          if not C.ensure_poster(m, "movie-pptx") then return C.movie_stand_in(m) end
          if m.mime == "video/webm" then
            C.warn("movie-pptx: " .. m.src .. " is WebM, which PowerPoint does not play: its poster stands in"
              .. " (an H.264 mp4 plays everywhere; frames2movie.py --reencode makes one)")
          else
            local flags = {}
            for _, k in ipairs({ "autoplay", "loop", "muted" }) do
              if m[k] then table.insert(flags, k) end
            end
            table.insert(lines, table.concat({ "engine-movie:", encode(m.poster), encode(m.src), table.unpack(flags) }, " "))
          end
          img.src = m.poster
          return C.strip_movie_attrs(img)
        end,
      }))
    end
  end
  flush()
  doc.blocks = out
  return doc
end
