// SPDX-FileCopyrightText: 2026 tb4
// SPDX-License-Identifier: AGPL-3.0-or-later

// UI wiring. All the byte-level decisions live in record.js and all the network
// in forge.js; this file only moves text between them and the screen.

import { newRecord, appendBlock, humanBlock, wallOf } from "./record.js";
import { forgejo, ForgeError } from "./forge.js";

const SETTINGS = "records.settings";
const CURRENT = "records.current";
const QUEUE = "records.queue";

const $ = (id) => document.getElementById(id);
const load = (key, fallback) => {
  try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; }
};
const save = (key, value) => localStorage.setItem(key, JSON.stringify(value));

let settings = load(SETTINGS, { url: "", owner: "", repo: "", branch: "main", dir: "records", name: "", token: "" });
let current = load(CURRENT, null);
let queue = load(QUEUE, {});

function say(message, kind) {
  const li = document.createElement("li");
  li.textContent = message;
  if (kind) li.className = kind;
  $("log").prepend(li);
  while ($("log").children.length > 8) $("log").lastChild.remove();
}

function client() {
  if (!settings.url || !settings.owner || !settings.repo || !settings.token) return null;
  return forgejo(settings);
}

// Where a record lives in the repo: the configured records dir plus whatever
// newRecord() decided (a tag folder, a slug or a timestamp).
const fullPath = (recordPath) => `${(settings.dir || "records").replace(/^\/+|\/+$/g, "")}/${recordPath}`;

function paint() {
  for (const key of ["url", "owner", "repo", "branch", "dir", "name", "token"]) $(key).value = settings[key] || "";
  $("send").textContent = current ? "Send" : "Start record";
  $("args").parentElement.hidden = false;
  $("args").disabled = !!current;
  $("finish").hidden = !current;
  $("where").innerHTML = current
    ? `Writing to <b>${current.path}</b> — ${current.count} message${current.count === 1 ? "" : "s"}.`
    : "No record open. Writing starts a new one.";
  const waiting = Object.keys(queue).length;
  $("pending").hidden = !waiting;
  $("pending").textContent = `${waiting} queued`;
  $("pending").style.color = "var(--bad)";
  if (!settings.token) $("settings").open = true;
}

// One pending write per path — each commit sends the whole file, so the newest
// text supersedes anything still waiting for it.
async function push(path, text, message) {
  const forge = client();
  if (!forge) { say("Set the forge and token first.", "bad"); return false; }
  try {
    const sha = current?.path === path ? current.sha : (await forge.read(path))?.sha;
    const next = await forge.write(path, text, message, sha);
    if (current?.path === path) { current.sha = next; save(CURRENT, current); }
    delete queue[path];
    save(QUEUE, queue);
    return true;
  } catch (e) {
    if (e instanceof ForgeError && !e.blocked && !e.status) {
      queue[path] = { text, message };
      save(QUEUE, queue);
      say(e.message, "bad");
    } else {
      say(e.message, "bad");
    }
    return false;
  }
}

async function flush() {
  for (const [path, held] of Object.entries({ ...queue })) {
    say(`Retrying ${path}…`);
    if (await push(path, held.text, held.message)) say(`Committed ${path}`, "good");
  }
  paint();
}

$("save").onclick = () => {
  settings = Object.fromEntries(["url", "owner", "repo", "branch", "dir", "name", "token"]
    .map((key) => [key, $(key).value.trim()]));
  settings.branch = settings.branch || "main";
  settings.dir = settings.dir || "records";
  save(SETTINGS, settings);
  $("settings").open = false;
  say("Saved to this browser.", "good");
  paint();
};

$("test").onclick = async () => {
  const forge = client();
  if (!forge) return say("Fill in the forge, owner, repo and token first.", "bad");
  try {
    say(`Connected to ${await forge.check()} — the token can write.`, "good");
  } catch (e) {
    say(e.message, "bad");
  }
};

$("send").onclick = async () => {
  const message = $("body").value;
  if (!message.trim()) return;
  const block = $("headings").checked ? humanBlock(message, settings.name || null) : message;

  if (!current) {
    const built = newRecord({ argumentString: $("args").value, wall: wallOf(new Date()) });
    current = { path: fullPath(built.path), text: appendBlock(built.text, block), sha: null, count: 1 };
  } else {
    current = { ...current, text: appendBlock(current.text, block), count: current.count + 1 };
  }
  save(CURRENT, current);

  $("body").value = "";
  paint();

  if (await push(current.path, current.text, `record: ${current.path.split("/").pop()}`)) {
    say(`Committed ${current.path}`, "good");
  }
  paint();
};

$("finish").onclick = () => {
  say(`Closed ${current.path}.`);
  current = null;
  localStorage.removeItem(CURRENT);
  $("args").value = "";
  paint();
};

addEventListener("online", flush);
paint();
if (Object.keys(queue).length && navigator.onLine) flush();

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("sw.js").catch(() => { /* the app works without it */ });
}
