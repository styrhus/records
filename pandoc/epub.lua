-- EPUB chapters are XHTML: re-read raw HTML (unsafe: true record content) as
-- native pandoc elements so void tags like <br>/<img> stay well-formed.
local function readHtml(txt)
  local ok, doc = pcall(pandoc.read, txt, "html")
  if ok then return doc.blocks end
  return pandoc.Blocks({})
end

function RawInline(r)
  if r.format ~= "html" then return nil end
  return pandoc.utils.blocks_to_inlines(readHtml(r.text))
end

function RawBlock(r)
  if r.format ~= "html" then return nil end
  return readHtml(r.text)
end
