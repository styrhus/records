-- Assemble every record into one Pandoc document (JSON on stdout), mirroring the
-- site: intro (_index.md), loose records, then chapters ascending (arabic before
-- roman), records ordered by date per params.singleOrder. Run via `pandoc lua`.
-- Usage: pandoc lua book.lua <records-dir> <repo-root> <site-config>

local system = pandoc.system
local path = pandoc.path
local utils = pandoc.utils

local recordsDir = assert(arg[1], "usage: pandoc lua book.lua <records-dir> <repo-root> <site-config>")
local repoRoot = assert(arg[2], "missing repo root")
local siteConfig = assert(arg[3], "missing site config")

local function slurp(p)
  local f = io.open(p, "rb")
  if not f then return nil end
  local s = f:read("a")
  f:close()
  return s
end

local function exists(p)
  local f = io.open(p, "rb")
  if f then f:close() return true end
  return false
end

---------------------------------------------------------------- site config

-- hugo.yaml parsed as pandoc YAML metadata (smart off — values stay literal);
-- theme defaults where unset.
local siteConfigText = slurp(siteConfig) or ""
local cfg = pandoc.read("---\n" .. siteConfigText .. "\n---\n", "markdown-smart").meta
local params = cfg.params or {}

local function str(v)
  if v == nil then return nil end
  local s = utils.stringify(v)
  if s == "" then return nil end
  return s
end

local function boolOr(v, dflt)
  if type(v) == "boolean" then return v end
  return dflt
end

local siteTitle = str(cfg.title) or ""
local themeName = str(cfg.theme) or "Fuglekasse"
local greeting = str(params.greeting)
local dateTitleFormat = str(params.dateTitleFormat)
local datePostFormat = str(params.datePostFormat)
local singleOrder = str(params.singleOrder) or "asc"
if singleOrder ~= "asc" and singleOrder ~= "desc" then singleOrder = "asc" end
-- single-flowing: bare turn stream — no titles/tags/dates/chapters, dinkus between records.
local flowing = str(params.pageMode) == "single-flowing"
-- bookLook (flowing only): forside/side-1/bakside at the records root become
-- front cover, page 1 and back cover; forside replaces the intro and the cover page.
local bookLook = boolOr(params.bookLook, false)
local showTags = boolOr(params.showTags, true)
local repoURL = os.getenv("HUGO_PARAMS_REPOURL") or str(params.repoURL) or ""
-- Raw-link URL shape per forge; auto/unknown = detect from the repoURL host (mirrors repo-link.html).
local repoLinkStyle = str(params.repoLinkStyle) or "auto"
local repoBranch = str(params.repoBranch) or "main"
local rawShapes = { forgejo = "raw/branch", github = "raw", gitlab = "-/raw" }
if rawShapes[repoLinkStyle] == nil then
  local host = repoURL:match("^https?://([^/]+)") or ""
  repoLinkStyle = host == "github.com" and "github" or host == "gitlab.com" and "gitlab" or "forgejo"
end
local rawPrefix = repoURL .. "/" .. rawShapes[repoLinkStyle] .. "/" .. repoBranch

local styleParams = params.style or {}
local lightParams = styleParams.light or {}
local light = {}
for k, dflt in pairs({ bg = "#d5d6db", fg = "#343b58", dim = "#9699a3", accent = "#34548a", surface = "#e5e6ea" }) do
  light[k] = str(lightParams[k]) or dflt
end
local fontName = str(styleParams.font) or "Architects Daughter"
local fontFile = str(styleParams.fontfile) or "fonts/architects-daughter.woff2"

-- ignoreFiles regexes read raw from the config text (a markdown-metadata pass
-- would mangle them); block-list form only.
local function yamlListItems(txt, key)
  local items, active = {}, false
  for line in (txt .. "\n"):gmatch("(.-)\r?\n") do
    if active then
      local item = line:match("^%s*%-%s*(.+)$")
      if item then
        local dq, sq = item:match('^"(.-)"'), item:match("^'(.-)'")
        if dq then
          item = dq:gsub("\\(.)", "%1")
        elseif sq then
          item = sq:gsub("''", "'")
        else
          item = (item:gsub("%s+#.*$", ""):gsub("%s+$", ""))
        end
        if item ~= "" then items[#items + 1] = item end
      elseif not line:match("^%s*#") and not line:match("^%s*$") then
        active = false
      end
    end
    if not active and line:match("^%s*" .. key .. ":%s*$") then active = true end
  end
  return items
end

-- Supported regex subset: literals, \-escapes, ^, $ (what the instances use).
local ignorePatterns = {}
local function regexToLua(re)
  local out, i = {}, 1
  while i <= #re do
    local c = re:sub(i, i)
    if c == "\\" then
      out[#out + 1] = "%" .. re:sub(i + 1, i + 1)
      i = i + 2
    elseif c == "^" or c == "$" or c:match("[%w/ ]") then
      out[#out + 1] = c
      i = i + 1
    else
      out[#out + 1] = "%" .. c
      i = i + 1
    end
  end
  return table.concat(out)
end
for _, re in ipairs(yamlListItems(siteConfigText, "ignoreFiles")) do
  ignorePatterns[#ignorePatterns + 1] = regexToLua(re)
end
local function ignored(rel)
  for _, p in ipairs(ignorePatterns) do
    if rel:find(p) then return true end
  end
  return false
end

---------------------------------------------------------------- dates

-- "2026-07-07T11:38:59+02:00" / "2026-07-06_23-22" / "2026-07-05" → parts + sort key.
local function parseDate(s)
  if not s then return nil end
  local y, mo, d = s:match("^(%d%d%d%d)%-(%d%d)%-(%d%d)")
  if not y then return nil end
  local h, mi = s:match("^%d+%-%d+%-%d+[T_ ](%d%d)[:%-](%d%d)")
  local se = s:match("^%d+%-%d+%-%d+[T_ ]%d%d[:%-]%d%d[:%-](%d%d)")
  local t = {
    year = tonumber(y), month = tonumber(mo), day = tonumber(d),
    hour = tonumber(h) or 0, min = tonumber(mi) or 0, sec = tonumber(se) or 0,
  }
  t.key = string.format("%04d%02d%02d%02d%02d%02d", t.year, t.month, t.day, t.hour, t.min, t.sec)
  return t
end

local MONTHS = { "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December" }
local DAYS = { "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday" }

-- Sakamoto's algorithm; 1 = Sunday (locale-independent English day names).
local function weekday(y, m, d)
  local tt = { 0, 3, 2, 5, 0, 3, 5, 1, 4, 6, 2, 4 }
  if m < 3 then y = y - 1 end
  return (y + y // 4 - y // 100 + y // 400 + tt[m] + d) % 7 + 1
end

-- Go reference-date layout → formatted string (the tokens the site docs use).
local function goFormat(layout, t)
  local h12 = t.hour % 12
  if h12 == 0 then h12 = 12 end
  local tokens = {
    { "2006", string.format("%04d", t.year) },
    { "January", MONTHS[t.month] },
    { "Monday", DAYS[weekday(t.year, t.month, t.day)] },
    { "Jan", MONTHS[t.month]:sub(1, 3) },
    { "Mon", DAYS[weekday(t.year, t.month, t.day)]:sub(1, 3) },
    { "15", string.format("%02d", t.hour) },
    { "06", string.format("%02d", t.year % 100) },
    { "05", string.format("%02d", t.sec) },
    { "04", string.format("%02d", t.min) },
    { "03", string.format("%02d", h12) },
    { "02", string.format("%02d", t.day) },
    { "01", string.format("%02d", t.month) },
    { "PM", t.hour < 12 and "AM" or "PM" },
    { "pm", t.hour < 12 and "am" or "pm" },
    { "5", tostring(t.sec) },
    { "4", tostring(t.min) },
    { "3", tostring(h12) },
    { "2", tostring(t.day) },
    { "1", tostring(t.month) },
  }
  local out, i = {}, 1
  while i <= #layout do
    local matched = false
    for _, tk in ipairs(tokens) do
      if layout:sub(i, i + #tk[1] - 1) == tk[1] then
        out[#out + 1] = tk[2]
        i = i + #tk[1]
        matched = true
        break
      end
    end
    if not matched then
      out[#out + 1] = layout:sub(i, i)
      i = i + 1
    end
  end
  return table.concat(out)
end

---------------------------------------------------------------- chapters

local ROMAN = { { 1000, "m" }, { 900, "cm" }, { 500, "d" }, { 400, "cd" }, { 100, "c" },
  { 90, "xc" }, { 50, "l" }, { 40, "xl" }, { 10, "x" }, { 9, "ix" }, { 5, "v" }, { 4, "iv" }, { 1, "i" } }
local RVAL = { i = 1, v = 5, x = 10, l = 50, c = 100, d = 500, m = 1000 }

local function intToRoman(n)
  local out = {}
  for _, p in ipairs(ROMAN) do
    while n >= p[1] do
      out[#out + 1] = p[2]
      n = n - p[1]
    end
  end
  return table.concat(out)
end

local function romanToInt(s)
  local n = 0
  for i = 1, #s do
    local v = RVAL[s:sub(i, i)]
    if not v then return nil end
    local nx = RVAL[s:sub(i + 1, i + 1)]
    if nx and v < nx then n = n - v else n = n + v end
  end
  return n
end

-- Chapter folders: arabic integers, or strict roman numerals (canonical form only).
local function chapterNumber(name)
  if name:match("^%-?%d+$") then return tonumber(name), "arabic" end
  local l = name:lower()
  local n = romanToInt(l)
  if n and n > 0 and n < 4000 and intToRoman(n) == l then return n, "roman" end
  return nil
end

---------------------------------------------------------------- collect files

local function listDir(p)
  local ok, entries = pcall(system.list_directory, p)
  if ok then return entries end
  return nil
end

local files = {}
local function collect(dir, rel)
  local entries = listDir(dir) or {}
  table.sort(entries)
  for _, e in ipairs(entries) do
    local p = path.join({ dir, e })
    local r = rel == "" and e or (rel .. "/" .. e)
    if listDir(p) then
      collect(p, r)
    elseif e:match("%.md$") then
      files[#files + 1] = { file = p, rel = r }
    end
  end
end
collect(recordsDir, "")

---------------------------------------------------------------- parse records

local function splitFrontmatter(s)
  s = s:gsub("^\239\187\191", "")
  local fm, body = s:match("^%-%-%-[ \t]*\r?\n(.-)\r?\n%-%-%-[ \t]*\r?\n?(.*)$")
  if fm then return fm, body end
  return nil, s
end

local function readMeta(fm)
  if not fm then return {} end
  local ok, doc = pcall(pandoc.read, "---\n" .. fm .. "\n---\n", "markdown-smart")
  if ok then return doc.meta end
  return {}
end

local function isTrue(v) return v == true or str(v) == "true" end
local function isFalse(v) return v == false or str(v) == "false" end

local introFile = nil
local chapterIndex = {}
local records = {}

for _, f in ipairs(files) do
  local base = f.rel:match("([^/]+)%.md$")
  local seg1 = f.rel:match("^([^/]+)/")
  if not ignored(f.rel) then
    if base == "_index" then
      if f.rel == "_index.md" then
        introFile = f.file
      elseif seg1 and f.rel == seg1 .. "/_index.md" then
        chapterIndex[seg1] = f.file
      end
    elseif base ~= "LICENSE" and base ~= "404" then
      local fm, body = splitFrontmatter(slurp(f.file) or "")
      local meta = readMeta(fm)
      if not isTrue(meta.draft) then
        local dateT = parseDate(str(meta.date))
        if not dateT then dateT = parseDate(base) end
        records[#records + 1] = {
          file = f.file, rel = f.rel, base = base, section = seg1,
          meta = meta, body = body, dateT = dateT,
          key = (dateT and dateT.key or "00000000000000"),
        }
      end
    end
  end
end

---------------------------------------------------------------- order

local function byDate(a, b)
  if a.key ~= b.key then
    if singleOrder == "desc" then return a.key > b.key end
    return a.key < b.key
  end
  return a.rel < b.rel
end

local SPECIAL = { forside = true, ["side-1"] = true, bakside = true }
local special = {}

local loose, chapterMap = {}, {}
for _, r in ipairs(records) do
  if flowing and bookLook and not r.section and SPECIAL[r.base] then
    special[r.base] = r
  else
    local num, kind = nil, nil
    -- flowing flattens: chapter folders are ignored, every record is loose
    if r.section and not flowing then num, kind = chapterNumber(r.section) end
    if num then
      if not chapterMap[r.section] then
        chapterMap[r.section] = { name = r.section, num = num, kind = kind, records = {} }
      end
      table.insert(chapterMap[r.section].records, r)
    else
      loose[#loose + 1] = r
    end
  end
end
table.sort(loose, byDate)

local arabic, roman = {}, {}
for _, ch in pairs(chapterMap) do
  table.sort(ch.records, byDate)
  if ch.kind == "arabic" then arabic[#arabic + 1] = ch else roman[#roman + 1] = ch end
end
local function byNum(a, b)
  if a.num ~= b.num then return a.num < b.num end
  return a.name < b.name
end
table.sort(arabic, byNum)
table.sort(roman, byNum)
local chapters = {}
for _, ch in ipairs(arabic) do chapters[#chapters + 1] = ch end
for _, ch in ipairs(roman) do chapters[#chapters + 1] = ch end

---------------------------------------------------------------- transforms

local staticDirs = {
  path.join({ repoRoot, "hugo", "static" }),
  path.join({ repoRoot, "hugo", "themes", themeName, "static" }),
}

local function resolveLocal(src, recDir)
  for _, d in ipairs({ recDir, recordsDir, staticDirs[1], staticDirs[2] }) do
    local p = path.join({ d, src })
    if exists(p) then return p end
  end
  return nil
end

local function hasScheme(s) return s:match("^%a[%w+.-]*:") ~= nil end

-- Raw HTML images (unsafe: true content): point relative srcs at local files.
local function rewriteRawHtml(txt, recDir)
  return (txt:gsub('src="([^"]+)"', function(src)
    if hasScheme(src) then return nil end
    local p = resolveLocal(src, recDir)
    if p then return 'src="' .. p .. '"' end
    return nil
  end))
end

-- Shared content rewrites: demote headings under record titles, embed local
-- images, send records/ links to the forge raw URL (as record.html does).
local function contentFilter(recDir)
  return {
    Header = function(h)
      if h.classes:includes("speaker") then return h end
      h.level = math.min(h.level + 2, 6)
      h.identifier = ""
      return h
    end,
    Image = function(img)
      if not hasScheme(img.src) then
        local p = resolveLocal(img.src, recDir)
        if p then
          img.src = p
          return img
        end
      end
      return nil
    end,
    Link = function(l)
      if not hasScheme(l.target) and not l.target:match("^#") then
        local rest = l.target:match("records/(.+)$")
        if rest and repoURL ~= "" then
          l.target = rawPrefix .. "/records/" .. rest
          return l
        end
      end
      return nil
    end,
    RawInline = function(r)
      if r.format == "html" then return pandoc.RawInline("html", rewriteRawHtml(r.text, recDir)) end
      return nil
    end,
    RawBlock = function(r)
      if r.format == "html" then return pandoc.RawBlock("html", rewriteRawHtml(r.text, recDir)) end
      return nil
    end,
  }
end

-- Signature lines: <p>— model-name</p>, stripped like record.html.
local function isSignature(b)
  if b.t ~= "Para" or #b.content ~= 3 then return false end
  local dash, sp, name = b.content[1], b.content[2], b.content[3]
  return dash.t == "Str" and dash.text == "—" and sp.t == "Space"
    and name.t == "Str" and name.text:match("^[%w_%.%-]+$") ~= nil
end

local function speakerOf(b)
  if b.t ~= "Header" or b.level ~= 2 then return nil end
  local s = utils.stringify(b.content):lower()
  if s == "human" or s == "user" then return "user" end
  if s == "assistant" then return "assistant" end
  return nil
end

-- Mic icon on Human headings of voiceRecorded records; same SVG as record.html.
local micSvg = '<span class="voice-icon" title="voice recorded"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 11a7 7 0 0 0 14 0"/><path d="M12 18v4"/></svg></span>'

-- Mirror record.html: drop signatures, wrap speaker turns in user/assistant divs.
local function turnDivs(blocks, voice)
  local divs, cur, curClass = pandoc.Blocks({}), pandoc.Blocks({}), nil
  local function flush()
    if #cur > 0 then
      local attr = curClass and pandoc.Attr("", { curClass }) or pandoc.Attr()
      divs:insert(pandoc.Div(cur, attr))
    end
    cur = pandoc.Blocks({})
  end
  for _, b in ipairs(blocks) do
    local who = speakerOf(b)
    if who then
      flush()
      curClass = who
      local label = pandoc.Inlines(b.content)
      if voice and who == "user" then label:insert(pandoc.RawInline("html", micSvg)) end
      cur:insert(pandoc.Header(6, label, pandoc.Attr("", { "speaker" })))
    elseif not isSignature(b) then
      cur:insert(b)
    end
  end
  flush()
  return divs
end

local function readBody(body)
  local ok, doc = pcall(pandoc.read, body, "gfm+smart")
  if not ok then doc = pandoc.read(body, "gfm") end
  return doc.blocks
end

---------------------------------------------------------------- assemble

-- Display title: hand-written title:, else the date via dateTitleFormat.
local function titleInlines(r)
  local title = r.meta.title and utils.stringify(r.meta.title) or nil
  local isStamp = r.base:match("^%d%d%d%d%-%d%d%-%d%d_%d%d%-%d%d$") ~= nil
  if title and not (isStamp and title == r.base) then
    return pandoc.Inlines(r.meta.title)
  end
  local disp = r.base
  if r.dateT then
    if dateTitleFormat then
      disp = goFormat(dateTitleFormat, r.dateT)
    else
      disp = string.format("%04d-%02d-%02d %02d:%02d", r.dateT.year, r.dateT.month, r.dateT.day, r.dateT.hour, r.dateT.min)
    end
  end
  return pandoc.Inlines({ pandoc.Str(disp) })
end

local body = pandoc.Blocks({})
local firstRecord = true

local function addRecord(r)
  local recDir = path.directory(r.file)
  if flowing then
    if not firstRecord then
      body:insert(pandoc.Div({ pandoc.Plain({ pandoc.Str("· · ·") }) }, pandoc.Attr("", { "record-sep" })))
    end
    firstRecord = false
    body:insert(pandoc.Div(turnDivs(readBody(r.body), isTrue(r.meta.voiceRecorded)):walk(contentFilter(recDir)), pandoc.Attr("", { "record" })))
    return
  end
  body:insert(pandoc.Header(2, titleInlines(r), pandoc.Attr(r.base, { "record-head" })))
  body:insert(pandoc.Div(turnDivs(readBody(r.body), isTrue(r.meta.voiceRecorded)):walk(contentFilter(recDir)), pandoc.Attr("", { "record" })))
  if showTags and not isFalse(r.meta.showTags) and r.meta.tags then
    local inls = pandoc.Inlines({})
    for i, tag in ipairs(r.meta.tags) do
      if i > 1 then inls:insert(pandoc.Space()) end
      inls:insert(pandoc.Str("#" .. utils.stringify(tag)))
    end
    body:insert(pandoc.Div({ pandoc.Plain(inls) }, pandoc.Attr("", { "post-tags" })))
  end
  if datePostFormat and not isFalse(r.meta.showDate) and r.dateT then
    body:insert(pandoc.Div({ pandoc.Plain({ pandoc.Str(goFormat(datePostFormat, r.dateT)) }) }, pandoc.Attr("", { "post-date" })))
  end
end

-- bookLook specials: no title/tags/date/separator; class drives the page-break CSS.
local function addSpecial(r)
  body:insert(pandoc.Div(turnDivs(readBody(r.body), isTrue(r.meta.voiceRecorded)):walk(contentFilter(path.directory(r.file))), pandoc.Attr("", { "record", "book-" .. r.base })))
end

if introFile and not special.forside then
  local _, introBody = splitFrontmatter(slurp(introFile) or "")
  local introBlocks = readBody(introBody):walk(contentFilter(path.directory(introFile)))
  body:insert(pandoc.Div(introBlocks, pandoc.Attr("", { "intro" })))
end

if special.forside then addSpecial(special.forside) end
if special["side-1"] then addSpecial(special["side-1"]) end

for _, r in ipairs(loose) do addRecord(r) end

for _, ch in ipairs(chapters) do
  local inls = pandoc.Inlines({ pandoc.Str(ch.name) })
  local idx = chapterIndex[ch.name]
  if idx then
    local fm = splitFrontmatter(slurp(idx) or "")
    local title = str(readMeta(fm).title)
    if title and title:lower() ~= ch.name:lower() then
      inls:extend({ pandoc.Space(), pandoc.Str("—"), pandoc.Space(), pandoc.Str(title) })
    end
  end
  body:insert(pandoc.Header(1, inls, pandoc.Attr("chapter-" .. ch.name, { "chapter" })))
  for _, r in ipairs(ch.records) do addRecord(r) end
end

if special.bakside then addSpecial(special.bakside) end

---------------------------------------------------------------- metadata

local doc = pandoc.Pandoc(body)
doc.meta.pagetitle = siteTitle
doc.meta["document-css"] = false

-- With a forside, the forside is the cover — skip the generated cover page.
if not special.forside then
  local cover = pandoc.Blocks({})
  if greeting then
    cover:insert(pandoc.Div({ pandoc.Plain({ pandoc.Str(greeting) }) }, pandoc.Attr("", { "greeting" })))
  end
  cover:insert(pandoc.Div({ pandoc.Plain({ pandoc.Str(siteTitle) }) }, pandoc.Attr("", { "cover-title" })))
  cover:insert(pandoc.Div({ pandoc.Plain({ pandoc.Str(os.date("%Y-%m-%d")) }) }, pandoc.Attr("", { "cover-date" })))
  doc.meta["include-before"] = pandoc.MetaBlocks({ pandoc.Div(cover, pandoc.Attr("", { "cover" })) })
end

-- Palette + greeting font from site params, injected after pdf.css so they win.
local css = string.format(":root{--bg:%s;--fg:%s;--dim:%s;--accent:%s;--surface:%s}@page{background:%s}",
  light.bg, light.fg, light.dim, light.accent, light.surface, light.bg)
local fontPath = path.join({ repoRoot, "hugo", "themes", themeName, "static", fontFile })
if not exists(fontPath) then fontPath = path.join({ repoRoot, "hugo", "static", fontFile }) end
if exists(fontPath) then
  css = css .. string.format('@font-face{font-family:"%s";src:url("%s") format("woff2")}.greeting{font-family:"%s",cursive}',
    fontName, fontPath, fontName)
end
doc.meta["header-includes"] = pandoc.MetaBlocks({ pandoc.RawBlock("html", "<style>" .. css .. "</style>") })

io.write(pandoc.write(doc, "json"))
