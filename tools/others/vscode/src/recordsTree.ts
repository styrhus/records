// SPDX-FileCopyrightText: 2026 tb4
// SPDX-License-Identifier: AGPL-3.0-or-later

import * as vscode from "vscode";
import * as fs from "fs/promises";
import * as path from "path";

interface RecordEntry {
  file: string;
  title: string;
  date: Date | undefined;
  section: string;
  draft: boolean;
  featured: boolean;
}

const MAX_DEPTH = 3;
const HEAD_BYTES = 4096;

// The activity-bar list of earlier records, newest first — the counterpart of the chat's current one.
export class RecordsTreeProvider implements vscode.TreeDataProvider<RecordEntry>, vscode.Disposable {
  static readonly viewType = "recordsList";

  private readonly changed = new vscode.EventEmitter<void>();
  readonly onDidChangeTreeData = this.changed.event;
  private watcher: vscode.FileSystemWatcher | undefined;
  private watchedDir: string | undefined;

  constructor(private readonly resolveDir: () => Promise<string | undefined>) {}

  refresh() {
    this.changed.fire();
  }

  dispose() {
    this.watcher?.dispose();
    this.changed.dispose();
  }

  getTreeItem(r: RecordEntry): vscode.TreeItem {
    const item = new vscode.TreeItem(r.title, vscode.TreeItemCollapsibleState.None);
    const when = r.date ? formatDate(r.date) : "";
    item.description = [when, r.section, r.draft ? "draft" : ""].filter(Boolean).join(" · ");
    item.tooltip = new vscode.MarkdownString(
      `**${r.title.replace(/[*_`[\]]/g, "\\$&")}**\n\n${r.file}`
    );
    item.iconPath = new vscode.ThemeIcon(
      r.featured ? "star-full" : r.draft ? "lock" : "comment-discussion"
    );
    item.resourceUri = vscode.Uri.file(r.file);
    item.command = { command: "vscode.open", title: "Open record", arguments: [vscode.Uri.file(r.file)] };
    return item;
  }

  async getChildren(parent?: RecordEntry): Promise<RecordEntry[]> {
    if (parent) return [];
    const dir = await this.resolveDir();
    if (!dir) return [];
    this.watch(dir);
    const files: string[] = [];
    await collect(dir, 0, files);
    const entries = await Promise.all(files.map((f) => readEntry(dir, f)));
    return entries.sort((a, b) => (b.date?.getTime() || 0) - (a.date?.getTime() || 0));
  }

  private watch(dir: string) {
    if (this.watchedDir === dir) return;
    this.watcher?.dispose();
    this.watchedDir = dir;
    this.watcher = vscode.workspace.createFileSystemWatcher(
      new vscode.RelativePattern(vscode.Uri.file(dir), "**/*.md")
    );
    const fire = () => this.refresh();
    this.watcher.onDidCreate(fire);
    this.watcher.onDidDelete(fire);
    this.watcher.onDidChange(fire);
  }
}

async function collect(dir: string, depth: number, out: string[]) {
  let entries;
  try {
    entries = await fs.readdir(dir, { withFileTypes: true });
  } catch {
    return;
  }
  for (const e of entries) {
    if (e.name.startsWith(".")) continue;
    const full = path.join(dir, e.name);
    if (e.isDirectory() && depth < MAX_DEPTH) await collect(full, depth + 1, out);
    else if (e.isFile() && e.name.endsWith(".md") && e.name !== "_index.md") out.push(full);
  }
}

async function readEntry(root: string, file: string): Promise<RecordEntry> {
  let head = "";
  try {
    const fh = await fs.open(file, "r");
    const { buffer, bytesRead } = await fh.read(Buffer.alloc(HEAD_BYTES), 0, HEAD_BYTES, 0);
    await fh.close();
    head = buffer.toString("utf-8", 0, bytesRead);
  } catch {
    // unreadable: listed by filename only
  }
  const fm = head.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  const field = (k: string) => {
    const m = fm?.[1].match(new RegExp("^" + k + ":\\s*(.*)$", "m"));
    return m ? m[1].trim().replace(/^(["'])(.*)\1$/, "$2") : "";
  };
  // leaf bundle: the record is the folder, index.md is its body
  const base = path.basename(file) === "index.md" ? path.dirname(file) : file;
  const rel = path.relative(root, base);
  const stem = path.basename(rel).replace(/\.md$/, "");
  const section = path.dirname(rel) === "." ? "" : path.dirname(rel);
  const parsed = field("date") ? new Date(field("date")) : fromFilename(stem);
  return {
    file,
    title: field("title") || stem,
    date: parsed && !isNaN(parsed.getTime()) ? parsed : undefined,
    section,
    draft: field("draft") === "true",
    featured: field("featured") === "true",
  };
}

function fromFilename(stem: string): Date | undefined {
  const m = stem.match(/^(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})/);
  return m ? new Date(+m[1], +m[2] - 1, +m[3], +m[4], +m[5]) : undefined;
}

function formatDate(d: Date): string {
  const mins = Math.max(0, Math.floor((Date.now() - d.getTime()) / 60000));
  if (mins < 60) return mins + "m";
  if (mins < 1440) return Math.floor(mins / 60) + "h";
  if (mins < 43200) return Math.floor(mins / 1440) + "d";
  return d.toISOString().slice(0, 10);
}
