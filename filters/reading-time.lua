-- Approximate reading time for dated article pages (200 words/min, same as Quarto listings).
local words = 0
local skip = false

local function count_text(text)
  if skip or text == nil then
    return
  end
  for _ in text:gmatch("%S+") do
    words = words + 1
  end
end

function Pandoc(doc)
  local input = ""
  if quarto and quarto.doc and quarto.doc.input_file then
    input = quarto.doc.input_file
  end
  if not input:match("articles[/\\]20%d%d%-") then
    return doc
  end

  words = 0
  skip = false
  doc.blocks:walk({
    Header = function(el)
      local title = pandoc.utils.stringify(el.content):lower()
      if el.identifier == "refs" or title == "references" then
        skip = true
      end
    end,
    Str = function(el)
      count_text(el.text)
    end,
    Code = function(el)
      count_text(el.text)
    end,
    CodeBlock = function(el)
      count_text(el.text)
    end,
  })

  local minutes = math.max(1, math.ceil(words / 200))
  doc.meta["reading-time"] = pandoc.MetaString(tostring(minutes) .. " min")
  return doc
end
