// SPDX-FileCopyrightText: 2026 tb4
// SPDX-License-Identifier: AGPL-3.0-or-later

// Self-contained on purpose: the webview inlines renderMarkdown.toString(), so no module-scope references.
export function renderMarkdown(src: string): string {
  const esc = (s: string) =>
    s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

  const inline = (s: string): string => {
    const stash: string[] = [];
    const keep = (html: string) => "\u0001" + (stash.push(html) - 1) + "\u0001";
    let t = s.replace(/`([^`]+)`/g, (_m, code: string) => keep("<code>" + esc(code) + "</code>"));
    t = esc(t);
    t = t.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, (m, label: string, url: string) =>
      /^(https?:|mailto:)/i.test(url) ? keep('<a href="' + url + '">' + label + "</a>") : m
    );
    t = t.replace(/(^|[\s(])(https?:\/\/[^\s<]+[^\s<.,;:!?)])/g, (_m, pre: string, url: string) =>
      pre + keep('<a href="' + url + '">' + url + "</a>")
    );
    t = t
      .replace(/\*\*(?=\S)([\s\S]*?\S)\*\*/g, "<strong>$1</strong>")
      .replace(/__(?=\S)([\s\S]*?\S)__/g, "<strong>$1</strong>")
      .replace(/~~(?=\S)([\s\S]*?\S)~~/g, "<del>$1</del>")
      .replace(/(^|[^*\w])\*(?=\S)([^*]*?\S)\*(?!\*)/g, "$1<em>$2</em>")
      .replace(/(^|[^_\w])_(?=\S)([^_]*?\S)_(?!\w)/g, "$1<em>$2</em>");
    return t.replace(/\u0001(\d+)\u0001/g, (_m, n: string) => stash[Number(n)]);
  };

  const LIST = /^(\s*)([-*+]|\d+[.)])\s+(.*)$/;
  const FENCE = /^\s*(`{3,}|~{3,})\s*([\w+#.-]*)/;
  const HEADING = /^(#{1,6})\s+(.*?)\s*#*\s*$/;
  const HR = /^\s*([-*_])(\s*\1){2,}\s*$/;
  const QUOTE = /^\s*>/;
  const TABLE_SEP = /^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*$/;
  const isTable = (ls: string[], i: number) =>
    ls[i].includes("|") && i + 1 < ls.length && TABLE_SEP.test(ls[i + 1]);
  const cells = (row: string) =>
    row.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((c) => c.trim());

  const lines = src.replace(/\r\n?/g, "\n").split("\n");
  const out: string[] = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];

    const fence = line.match(FENCE);
    if (fence) {
      const body: string[] = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith(fence[1])) body.push(lines[i++]);
      i++;
      const lang = fence[2] ? ' data-lang="' + esc(fence[2]) + '"' : "";
      out.push("<pre" + lang + "><code>" + esc(body.join("\n")) + "</code></pre>");
      continue;
    }
    if (!line.trim()) {
      i++;
      continue;
    }
    const h = line.match(HEADING);
    if (h) {
      out.push("<h" + h[1].length + ">" + inline(h[2]) + "</h" + h[1].length + ">");
      i++;
      continue;
    }
    if (HR.test(line)) {
      out.push("<hr>");
      i++;
      continue;
    }
    if (QUOTE.test(line)) {
      const body: string[] = [];
      while (i < lines.length && QUOTE.test(lines[i])) body.push(lines[i++].replace(/^\s*> ?/, ""));
      out.push("<blockquote>" + renderMarkdown(body.join("\n")) + "</blockquote>");
      continue;
    }
    if (isTable(lines, i)) {
      const head = cells(lines[i]);
      const align = cells(lines[i + 1]).map((c) =>
        /^:-+:$/.test(c) ? "center" : /-:$/.test(c) ? "right" : /^:/.test(c) ? "left" : ""
      );
      const td = (tag: string, c: string, k: number) =>
        "<" + tag + (align[k] ? ' style="text-align:' + align[k] + '"' : "") + ">" + inline(c) + "</" + tag + ">";
      let html = "<table><thead><tr>" + head.map((c, k) => td("th", c, k)).join("") + "</tr></thead><tbody>";
      i += 2;
      while (i < lines.length && lines[i].includes("|") && lines[i].trim()) {
        html += "<tr>" + cells(lines[i++]).map((c, k) => td("td", c, k)).join("") + "</tr>";
      }
      out.push('<div class="md-table">' + html + "</tbody></table></div>");
      continue;
    }
    if (LIST.test(line)) {
      const items: { indent: number; ordered: boolean; start: number; text: string }[] = [];
      while (i < lines.length) {
        const m = lines[i].match(LIST);
        // a top-level switch between - and 1. starts a new list
        if (m && items.length && m[1].length <= items[0].indent && /\d/.test(m[2]) !== items[0].ordered) break;
        if (m) {
          items.push({
            indent: m[1].replace(/\t/g, "    ").length,
            ordered: /\d/.test(m[2]),
            start: parseInt(m[2], 10),
            text: m[3],
          });
        } else if (lines[i].trim() && /^\s+/.test(lines[i]) && !FENCE.test(lines[i])) {
          items[items.length - 1].text += "\n" + lines[i].trim();
        } else if (!lines[i].trim() && i + 1 < lines.length && LIST.test(lines[i + 1])) {
          // blank line inside a loose list
        } else {
          break;
        }
        i++;
      }
      const stack: { indent: number; tag: string }[] = [];
      let html = "";
      for (const it of items) {
        const tag = it.ordered ? "ol" : "ul";
        if (!stack.length || it.indent > stack[stack.length - 1].indent) {
          html += "<" + tag + (it.ordered && it.start !== 1 ? ' start="' + it.start + '"' : "") + ">";
          stack.push({ indent: it.indent, tag });
        } else {
          while (stack.length > 1 && it.indent < stack[stack.length - 1].indent) {
            html += "</li></" + stack.pop()!.tag + ">";
          }
          html += "</li>";
        }
        const task = it.text.match(/^\[([ xX])\]\s+([\s\S]*)$/);
        html += task
          ? '<li class="task">' + (task[1] === " " ? "☐ " : "☑ ") + inline(task[2])
          : "<li>" + inline(it.text);
      }
      while (stack.length) html += "</li></" + stack.pop()!.tag + ">";
      out.push(html);
      continue;
    }

    const para: string[] = [];
    while (
      i < lines.length &&
      lines[i].trim() &&
      !FENCE.test(lines[i]) &&
      !HEADING.test(lines[i]) &&
      !QUOTE.test(lines[i]) &&
      !LIST.test(lines[i]) &&
      !isTable(lines, i) &&
      !(para.length && HR.test(lines[i]))
    ) {
      para.push(lines[i++]);
    }
    if (!para.length) para.push(lines[i++]);
    out.push("<p>" + inline(para.join("\n")).replace(/\n/g, "<br>") + "</p>");
  }
  return out.join("\n");
}
