// The byte-exact mirror of recordkit's record writer. Every function here has a
// named counterpart in tools/others/python/recordkit/ and must agree with it
// byte for byte — tools/pwa/fixtures.json is the shared contract, checked by
// selftest.html on this side and tests/test_phone_fixtures.py on the other.
//
// Change nothing here without changing the fixture and running both.

const TAG_DROP = /[^a-z0-9-]/g;
const WS = /\s+/g;

// A YAML plain scalar may not open with an indicator, nor hold ': ' or ' #' (a
// space-hash opens a comment mid-scalar and the reader drops everything after it).
const YAML_INDICATORS = "-?:,[]{}#&*!|>'\"%@`";

const pad = (n) => String(n).padStart(2, "0");

// A wall-clock instant plus the offset it is expressed in. Kept explicit rather
// than read from Date so the fixtures pin an offset the test machine may not be in.
export function wallOf(date) {
  return {
    y: date.getFullYear(), mo: date.getMonth() + 1, d: date.getDate(),
    h: date.getHours(), mi: date.getMinutes(), s: date.getSeconds(),
    offsetMinutes: -date.getTimezoneOffset(),
  };
}

// naming.now_stamp — `date +%Y-%m-%d_%H-%M`, local wall-clock, no seconds.
export function fileStamp(w) {
  return `${w.y}-${pad(w.mo)}-${pad(w.d)}_${pad(w.h)}-${pad(w.mi)}`;
}

// naming.now_iso — `date -Iseconds`: local offset, second precision, never Z.
export function isoStamp(w) {
  const off = w.offsetMinutes;
  const sign = off < 0 ? "-" : "+";
  const abs = Math.abs(off);
  return `${w.y}-${pad(w.mo)}-${pad(w.d)}T${pad(w.h)}:${pad(w.mi)}:${pad(w.s)}` +
         `${sign}${pad(Math.floor(abs / 60))}:${pad(abs % 60)}`;
}

// naming.extract_tags_title — leading #tokens are tags; the first non-# token
// ends the run and everything after it is the title, verbatim.
export function extractTagsTitle(argumentString) {
  let rest = (argumentString || "").trimStart();
  const tags = [];
  while (rest.startsWith("#")) {
    const m = /^(\S+)\s*([\s\S]*)$/.exec(rest);
    const tag = m[1].slice(1).toLowerCase().replace(TAG_DROP, "");
    rest = m[2];
    if (tag) tags.push(tag);
  }
  return [tags, rest.trimEnd()];
}

// naming.slugify — lowercase and collapse whitespace runs. Nothing else: no
// punctuation stripping, however much the result looks like it wants some.
export function slugify(title) {
  return title.trim().toLowerCase().replace(WS, "-");
}

export function ensureMd(name) {
  return name.endsWith(".md") ? name : name + ".md";
}

// naming.unique_path — never overwrite; -1, -2 … before the extension.
export function uniqueName(filename, taken) {
  const dot = filename.lastIndexOf(".");
  const stem = dot === -1 ? filename : filename.slice(0, dot);
  const ext = dot === -1 ? "" : filename.slice(dot + 1);
  let candidate = filename;
  let n = 1;
  while (taken(candidate)) {
    candidate = ext ? `${stem}-${n}.${ext}` : `${stem}-${n}`;
    n += 1;
  }
  return candidate;
}

// frontmatter.quote — a YAML scalar: bare when it can be, double-quoted when a
// plain scalar would not parse. Mirrors recordkit/frontmatter.py's quote() exactly.
export function quoteScalar(value) {
  const text = String(value);
  if (!text || YAML_INDICATORS.includes(text[0]) || text.endsWith(":")
      || text.includes(": ") || text.includes(" #") || text.trim() !== text) {
    return '"' + text.replace(/\\/g, "\\\\").replace(/"/g, '\\"') + '"';
  }
  return text;
}

// frontmatter.build — the title is quoted when a bare scalar would not round-trip
// through YAML, draft before tags, the tags line absent entirely when there are
// none. The Python side takes one more argument, `extra`, for the importer's
// source keys; a phone never sets it.
export function buildFrontmatter(title, dateIso, tags, draft) {
  const lines = ["---", `title: ${quoteScalar(title)}`, `date: ${dateIso}`];
  if (draft) lines.push("draft: true");
  if (tags && tags.length) lines.push("tags: [" + tags.join(", ") + "]");
  lines.push("---");
  return lines.join("\n") + "\n";
}

// create.new_record — routes by first tag, names from the title or the stamp.
// `taken` answers "does this path already exist?"; the caller knows, not us.
export function newRecord(options) {
  const { argumentString = "", draft = false, wall, taken = () => false } = options;
  const tags = options.tags == null ? extractTagsTitle(argumentString)[0] : options.tags;
  const parsedTitle = options.title == null ? extractTagsTitle(argumentString)[1] : options.title;
  const title = parsedTitle.trim();

  const dir = tags.length ? tags[0] : "";
  let displayTitle, filename;
  if (title) {
    displayTitle = title;
    filename = ensureMd(slugify(title));
  } else {
    displayTitle = fileStamp(wall);
    filename = `${displayTitle}.md`;
  }

  const name = uniqueName(filename, (c) => taken(dir ? `${dir}/${c}` : c));
  return {
    path: dir ? `${dir}/${name}` : name,
    title: displayTitle,
    tags,
    draft,
    text: buildFrontmatter(displayTitle, isoStamp(wall), tags, draft),
  };
}

// writer.append_block — a leading blank line, the text, a trailing newline.
// Exactly one blank line between blocks, always.
export function appendBlock(existing, text) {
  return existing + "\n" + text + "\n";
}

// writer.append_human — the human side alone. The assistant side and its
// `— model` signature belong to the engine, not to a phone.
export function humanBlock(message, name) {
  return (name ? `## Human (${name})` : "## Human") + "\n\n" + message;
}
