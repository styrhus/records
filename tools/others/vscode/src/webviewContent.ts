// SPDX-FileCopyrightText: 2026 tb4
// SPDX-License-Identifier: AGPL-3.0-or-later

import { renderMarkdown } from "./markdown";

const ICON = {
  plus: '<svg viewBox="0 0 16 16"><path d="M8 3v10M3 8h10"/></svg>',
  slash: '<svg viewBox="0 0 16 16"><rect x="2.5" y="2.5" width="11" height="11" rx="2"/><path d="M9.5 5 6.5 11"/></svg>',
  send: '<svg viewBox="0 0 16 16"><path d="M8 13V3M3.5 7.5 8 3l4.5 4.5"/></svg>',
  stop: '<svg viewBox="0 0 16 16"><rect x="4" y="4" width="8" height="8" rx="1.5" class="fill"/></svg>',
  gear: '<svg viewBox="0 0 16 16"><circle cx="8" cy="8" r="2.2"/><path d="M8 1.8v1.7M8 12.5v1.7M1.8 8h1.7M12.5 8h1.7M3.6 3.6l1.2 1.2M11.2 11.2l1.2 1.2M3.6 12.4l1.2-1.2M11.2 4.8l1.2-1.2"/></svg>',
  file: '<svg viewBox="0 0 16 16"><path d="M4 1.5h5l3 3v10H4z"/><path d="M9 1.5v3h3"/></svg>',
  folder: '<svg viewBox="0 0 16 16"><path d="M1.5 3.5h4.5l1.5 1.5h7v8.5h-13z"/></svg>',
  house:
    '<svg viewBox="0 0 32 32"><path class="fill" fill-rule="evenodd" d="M16 6 L25 14 V25 H7 V14 Z M16 13.8 a3.2 3.2 0 1 0 0 6.4 3.2 3.2 0 0 0 0 -6.4 Z M15 20.2 h2 v4.8 h-2 Z"/></svg>',
};

// Inline webview page: HTML + CSS + JS in one template literal (CSP: inline only, no external resources).
export function getWebviewContent(commandsJson: string): string {
  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <meta http-equiv="Content-Security-Policy"
        content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Records Chat</title>
  <style>
    :root {
      --rc-border: var(--vscode-widget-border, var(--vscode-panel-border, rgba(128, 128, 128, 0.35)));
      --rc-subtle: rgba(128, 128, 128, 0.12);
      --rc-hover: var(--vscode-toolbar-hoverBackground, rgba(128, 128, 128, 0.2));
      --rc-dim: var(--vscode-descriptionForeground);
      --rc-radius: 8px;
      --rc-rec: var(--vscode-charts-red, var(--vscode-errorForeground));
    }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    html, body { height: 100%; }
    body {
      font-family: var(--vscode-font-family);
      font-size: var(--vscode-font-size);
      line-height: 1.5;
      color: var(--vscode-foreground);
      background: var(--vscode-sideBar-background);
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    svg { width: 16px; height: 16px; fill: none; stroke: currentColor; stroke-width: 1.4;
          stroke-linecap: round; stroke-linejoin: round; flex-shrink: 0; }
    svg .fill { fill: currentColor; stroke: none; }
    button { font: inherit; color: inherit; background: none; border: none; cursor: pointer; }
    button:focus-visible { outline: 1px solid var(--vscode-focusBorder); outline-offset: 1px; }
    .icon-btn {
      display: inline-flex; align-items: center; justify-content: center;
      width: 24px; height: 24px; border-radius: 5px; color: var(--rc-dim);
    }
    .icon-btn:hover { background: var(--rc-hover); color: var(--vscode-foreground); }

    /* header: recording state */
    #header {
      display: flex; align-items: center; gap: 8px;
      padding: 6px 12px; min-height: 34px;
      border-bottom: 1px solid var(--rc-border);
      font-size: 0.92em;
    }
    #rec-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--rc-dim); opacity: 0.5; flex-shrink: 0; }
    #header.recording #rec-dot { background: var(--rc-rec); opacity: 1; animation: pulse 2s ease-in-out infinite; }
    #header.ephemeral #rec-dot { background: var(--vscode-charts-blue, var(--vscode-textLink-foreground)); opacity: 1; }
    #rec-label { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    #rec-label .sub { color: var(--rc-dim); }
    #btn-stop { display: none; }
    #header.recording #btn-stop { display: inline-flex; }
    @keyframes pulse { 50% { opacity: 0.35; } }

    /* transcript */
    #output { flex: 1; overflow-y: auto; overflow-x: hidden; padding: 12px 14px 8px; }
    .msg { margin: 0 0 12px; overflow-wrap: anywhere; }
    .msg.user {
      white-space: pre-wrap;
      background: var(--vscode-input-background);
      border: 1px solid var(--rc-border);
      border-radius: var(--rc-radius);
      padding: 6px 10px;
    }
    .msg.context { margin-top: -8px; font-size: 0.85em; color: var(--rc-dim); padding: 0 2px; }
    .msg.status { font-size: 0.85em; color: var(--rc-dim); display: flex; gap: 6px; margin-bottom: 6px; }
    .msg.status .t { opacity: 0.7; font-variant-numeric: tabular-nums; flex-shrink: 0; }
    .msg.output, .msg.error {
      white-space: pre-wrap;
      border-left: 2px solid var(--vscode-textLink-foreground);
      padding: 2px 0 2px 10px;
    }
    .msg.error { border-left-color: var(--vscode-errorForeground); color: var(--vscode-errorForeground); }
    .msg.busy { color: var(--rc-dim); display: flex; align-items: center; gap: 8px; }
    .dots span { display: inline-block; width: 4px; height: 4px; margin-right: 3px; border-radius: 50%;
                 background: currentColor; animation: blink 1.2s infinite both; }
    .dots span:nth-child(2) { animation-delay: 0.2s; }
    .dots span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes blink { 0%, 80%, 100% { opacity: 0.2; } 40% { opacity: 1; } }

    /* assistant markdown */
    .msg.assistant > :first-child { margin-top: 0; }
    .msg.assistant > :last-child { margin-bottom: 0; }
    .msg.assistant p, .msg.assistant ul, .msg.assistant ol, .msg.assistant pre,
    .msg.assistant blockquote, .msg.assistant .md-table { margin: 0 0 0.7em; }
    .msg.assistant h1, .msg.assistant h2, .msg.assistant h3,
    .msg.assistant h4, .msg.assistant h5, .msg.assistant h6 { margin: 1em 0 0.4em; line-height: 1.3; font-weight: 600; }
    .msg.assistant h1 { font-size: 1.3em; }
    .msg.assistant h2 { font-size: 1.18em; }
    .msg.assistant h3 { font-size: 1.06em; }
    .msg.assistant h4, .msg.assistant h5, .msg.assistant h6 { font-size: 1em; }
    .msg.assistant ul, .msg.assistant ol { padding-left: 1.4em; }
    .msg.assistant li { margin: 0.15em 0; }
    .msg.assistant li > ul, .msg.assistant li > ol { margin: 0.15em 0 0; }
    .msg.assistant li.task { list-style: none; margin-left: -1.1em; }
    .msg.assistant a { color: var(--vscode-textLink-foreground); text-decoration: none; }
    .msg.assistant a:hover { text-decoration: underline; }
    .msg.assistant hr { border: none; border-top: 1px solid var(--rc-border); margin: 1em 0; }
    .msg.assistant blockquote {
      border-left: 3px solid var(--vscode-textBlockQuote-border, var(--rc-border));
      padding: 0 0 0 10px; color: var(--rc-dim);
    }
    code, pre { font-family: var(--vscode-editor-font-family, monospace); font-size: 0.92em; }
    .msg.assistant :not(pre) > code {
      background: var(--vscode-textCodeBlock-background, var(--rc-subtle));
      border-radius: 4px; padding: 0.1em 0.35em;
    }
    .msg.assistant pre {
      position: relative;
      background: var(--vscode-textCodeBlock-background, var(--rc-subtle));
      border: 1px solid var(--rc-border);
      border-radius: 6px;
      padding: 8px 10px;
      overflow-x: auto;
      white-space: pre;
    }
    .msg.assistant pre code { font-size: 1em; }
    .msg.assistant pre .copy {
      position: absolute; top: 4px; right: 4px;
      font-family: var(--vscode-font-family); font-size: 0.8em; padding: 1px 6px; border-radius: 4px;
      color: var(--rc-dim); background: var(--vscode-sideBar-background);
      border: 1px solid var(--rc-border);
      opacity: 0; transition: opacity 0.12s;
    }
    .msg.assistant pre:hover .copy { opacity: 1; }
    .md-table { overflow-x: auto; }
    .md-table table { border-collapse: collapse; font-size: 0.95em; }
    .md-table th, .md-table td { border: 1px solid var(--rc-border); padding: 3px 8px; text-align: left; }
    .md-table th { background: var(--rc-subtle); font-weight: 600; }

    /* welcome */
    #welcome {
      display: flex; flex-direction: column; align-items: center; text-align: center;
      gap: 6px; padding: 32px 12px 24px; color: var(--rc-dim);
    }
    #welcome svg { width: 40px; height: 40px; color: var(--vscode-foreground); opacity: 0.8; }
    #welcome .title { color: var(--vscode-foreground); font-size: 1.1em; font-weight: 600; }
    #welcome .keys { font-size: 0.9em; }
    kbd {
      font-family: var(--vscode-editor-font-family, monospace); font-size: 0.9em;
      border: 1px solid var(--rc-border); border-radius: 4px; padding: 0 4px;
    }

    /* setup card */
    .msg.setup {
      border: 1px solid var(--vscode-inputValidation-warningBorder, var(--rc-border));
      border-radius: var(--rc-radius); padding: 10px 12px;
      display: flex; flex-direction: column; gap: 6px;
    }
    .setup .head { color: var(--vscode-errorForeground); font-weight: 600; }
    .setup code {
      display: block; user-select: all; padding: 4px 8px; border-radius: 4px;
      background: var(--vscode-textCodeBlock-background, var(--rc-subtle));
    }

    /* bottom area */
    #bottom { padding: 6px 12px 10px; position: relative; }
    #hint { display: none; font-size: 0.85em; color: var(--rc-dim); padding: 0 4px 4px; }
    #hint b { font-family: var(--vscode-editor-font-family, monospace); font-weight: 500; color: var(--vscode-foreground); }
    #settings-panel {
      display: none;
      border: 1px solid var(--rc-border); border-radius: var(--rc-radius);
      background: var(--vscode-editorWidget-background, var(--vscode-input-background));
      padding: 10px 12px; margin-bottom: 8px;
    }
    #settings-panel .sp-title { font-weight: 600; margin-bottom: 8px; }
    #settings-panel label { display: block; font-size: 0.85em; color: var(--rc-dim); margin-bottom: 8px; }
    #settings-panel input {
      display: block; width: 100%; margin-top: 3px; padding: 4px 8px;
      font-family: var(--vscode-editor-font-family, monospace); font-size: 0.95em;
      color: var(--vscode-input-foreground); background: var(--vscode-input-background);
      border: 1px solid var(--vscode-input-border, var(--rc-border)); border-radius: 4px;
    }
    #settings-panel input:focus { outline: none; border-color: var(--vscode-focusBorder); }
    .sp-buttons { display: flex; gap: 6px; justify-content: flex-end; }
    .btn {
      padding: 3px 12px; border-radius: 4px;
      background: var(--vscode-button-background); color: var(--vscode-button-foreground);
    }
    .btn:hover { background: var(--vscode-button-hoverBackground); }
    .btn.secondary {
      background: var(--vscode-button-secondaryBackground, var(--rc-subtle));
      color: var(--vscode-button-secondaryForeground, inherit);
    }
    .btn.secondary:hover { background: var(--vscode-button-secondaryHoverBackground, var(--rc-hover)); }

    #popup {
      display: none;
      position: absolute; left: 12px; right: 12px; bottom: 100%;
      max-height: 14rem; overflow-y: auto;
      background: var(--vscode-editorSuggestWidget-background, var(--vscode-editorWidget-background));
      border: 1px solid var(--vscode-editorSuggestWidget-border, var(--rc-border));
      border-radius: var(--rc-radius);
      box-shadow: 0 4px 16px var(--vscode-widget-shadow, rgba(0, 0, 0, 0.2));
      padding: 4px; z-index: 10;
    }
    .popup-item {
      display: flex; align-items: center; gap: 8px;
      padding: 3px 8px; border-radius: 5px; cursor: pointer;
      white-space: nowrap; overflow: hidden;
    }
    .popup-item.sel {
      background: var(--vscode-editorSuggestWidget-selectedBackground, var(--vscode-list-activeSelectionBackground));
      color: var(--vscode-editorSuggestWidget-selectedForeground, var(--vscode-list-activeSelectionForeground));
    }
    .popup-item svg { color: var(--rc-dim); }
    .pi-name, .pi-args { flex-shrink: 0; font-family: var(--vscode-editor-font-family, monospace); font-size: 0.92em; }
    .pi-args { color: var(--rc-dim); }
    .pi-desc { color: var(--rc-dim); overflow: hidden; text-overflow: ellipsis; margin-left: auto; padding-left: 8px; }
    .popup-item.sel .pi-desc, .popup-item.sel .pi-args, .popup-item.sel svg { color: inherit; opacity: 0.85; }
    .popup-item.loading { color: var(--rc-dim); cursor: default; }

    #composer {
      border: 1px solid var(--vscode-input-border, var(--rc-border));
      border-radius: var(--rc-radius);
      background: var(--vscode-input-background);
      transition: border-color 0.12s;
    }
    #composer:focus-within { border-color: var(--vscode-focusBorder); }
    #composer.disabled { opacity: 0.7; }
    #chips { display: none; flex-wrap: wrap; gap: 4px; padding: 8px 8px 0; }
    .chip {
      display: inline-flex; align-items: center; gap: 4px; max-width: 100%;
      padding: 1px 6px; border-radius: 4px;
      border: 1px solid var(--rc-border); background: var(--rc-subtle);
      font-size: 0.85em; cursor: pointer; overflow: hidden;
    }
    .chip svg { width: 13px; height: 13px; color: var(--rc-dim); }
    .chip .label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .chip .x { color: var(--rc-dim); padding: 0 2px; }
    .chip .x:hover { color: var(--vscode-foreground); }
    .chip.off { opacity: 0.5; }
    .chip.off .label { text-decoration: line-through; }
    #input {
      display: block; width: 100%; resize: none; border: none; outline: none;
      background: transparent; color: var(--vscode-input-foreground);
      font: inherit; line-height: 1.45;
      padding: 8px 10px 4px; min-height: 2.4em; max-height: 14em; overflow-y: auto;
    }
    #input::placeholder { color: var(--vscode-input-placeholderForeground); }
    #toolbar { display: flex; align-items: center; gap: 2px; padding: 2px 6px 6px; }
    #model-pill {
      display: inline-flex; align-items: center; gap: 4px; min-width: 0;
      margin-left: 4px; padding: 1px 8px; border-radius: 999px; max-width: 60%;
      font-size: 0.85em; color: var(--rc-dim); background: var(--rc-subtle);
    }
    #model-pill:hover { background: var(--rc-hover); color: var(--vscode-foreground); }
    #model-pill svg { width: 13px; height: 13px; }
    #model-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .spacer { flex: 1; }
    #send {
      display: inline-flex; align-items: center; justify-content: center;
      width: 26px; height: 26px; border-radius: 6px; flex-shrink: 0;
      background: var(--vscode-button-background); color: var(--vscode-button-foreground);
    }
    #send:hover { background: var(--vscode-button-hoverBackground); }
    #send:disabled { opacity: 0.4; cursor: default; }
    #watch-line { font-size: 0.8em; color: var(--rc-dim); padding: 4px 4px 0; }
    #watch-line:empty { display: none; }
  </style>
</head>
<body>
  <div id="header">
    <span id="rec-dot"></span>
    <span id="rec-label">Not recording</span>
    <button id="btn-stop" class="icon-btn" title="Stop recording (/esc)">${ICON.stop}</button>
  </div>
  <div id="output">
    <div id="welcome">
      ${ICON.house}
      <div class="title">Records Chat</div>
      <div><kbd>/record</kbd> starts a recording — or just chat once a model is set.</div>
      <div class="keys"><kbd>/</kbd> commands · <kbd>@</kbd> attach files · <kbd>Shift</kbd>+<kbd>Enter</kbd> new line</div>
    </div>
  </div>
  <div id="bottom">
    <div id="popup"></div>
    <div id="settings-panel">
      <div class="sp-title">Ollama</div>
      <label>Endpoint
        <input id="sp-endpoint" type="text" placeholder="http://localhost:11434" />
      </label>
      <label>Model
        <input id="sp-model" type="text" placeholder="qwen2.5:14b" />
      </label>
      <div class="sp-buttons">
        <button id="sp-cancel" class="btn secondary">Cancel</button>
        <button id="sp-save" class="btn">Save</button>
      </div>
    </div>
    <div id="hint"></div>
    <div id="composer">
      <div id="chips"></div>
      <textarea id="input" rows="1" placeholder="Message… (/ for commands, @ to attach)"></textarea>
      <div id="toolbar">
        <button id="btn-attach" class="icon-btn" title="Attach a file or folder (@)">${ICON.plus}</button>
        <button id="btn-slash" class="icon-btn" title="Commands (/)">${ICON.slash}</button>
        <button id="model-pill" title="Ollama settings">${ICON.gear}<span id="model-name">no model</span></button>
        <span class="spacer"></span>
        <button id="send" title="Send (Enter)" disabled>${ICON.send}</button>
      </div>
    </div>
    <div id="watch-line"></div>
  </div>
  <script>
    const vscode = acquireVsCodeApi();
    const $ = (id) => document.getElementById(id);
    const output = $("output");
    const input = $("input");
    const sendBtn = $("send");
    const composer = $("composer");
    const popupEl = $("popup");
    const hintEl = $("hint");
    const chipsEl = $("chips");
    const header = $("header");
    const recLabel = $("rec-label");
    const modelName = $("model-name");
    const modelPill = $("model-pill");
    const watchLine = $("watch-line");
    const settingsPanel = $("settings-panel");
    const spEndpoint = $("sp-endpoint");
    const spModel = $("sp-model");

    const COMMANDS = ${commandsJson};
    const ICON = ${JSON.stringify(ICON)};
    ${renderMarkdown.toString()}

    let popup = { mode: null, items: [], sel: 0, anchor: 0 };
    let suppress = { slash: false, fileAnchor: -1 };
    let fileCache = null;
    let attachments = [];
    let activeEditor = { path: null, abs: null, enabled: true };
    let model = { model: null, endpoint: null };
    let recording = null;
    let busy = false;
    let streamEl = null; // the in-progress streamed response, while one is arriving
    let streamText = "";

    window.addEventListener("message", (e) => {
      const msg = e.data;
      switch (msg.type) {
        case "model-info":
          model = { model: msg.model || null, endpoint: msg.endpoint || null };
          renderModel();
          renderHeader();
          return;
        case "recording-state":
          recording = msg.path ? { path: msg.path, mode: msg.mode, model: msg.model } : null;
          renderHeader();
          return;
        case "file-list":
          fileCache = msg.files || [];
          if (popup.mode === "file") refreshPopup();
          return;
        case "active-editor":
          if (msg.path && msg.path !== activeEditor.path) {
            activeEditor = { path: msg.path, abs: msg.abs || null, enabled: true };
          } else if (!msg.path) {
            activeEditor = { path: null, abs: null, enabled: true };
          }
          renderChips();
          return;
        case "settings-values":
          spEndpoint.value = msg.endpoint || "";
          spModel.value = msg.model || "";
          settingsPanel.style.display = "block";
          spEndpoint.focus();
          return;
        case "focus-input":
          input.focus();
          return;
        case "busy":
          clearBusy();
          addBusy(msg.content);
          setBusy(true);
          streamEl = null;
          streamText = "";
          return;
        case "watch-status":
          watchLine.textContent = msg.content;
          return;
        case "stream-token":
          clearBusy();
          if (!streamEl) {
            streamEl = addEl("assistant");
            streamText = "";
          }
          streamText += msg.content;
          streamEl.innerHTML = renderMarkdown(streamText);
          scrollDown();
          return;
      }
      clearBusy();
      setBusy(false);
      if (msg.type === "update-status") addStatus(msg.content);
      else if (msg.type === "error") addText(msg.error, "error");
      else if (msg.type === "output") addText(msg.content, "output");
      else if (msg.type === "response") {
        // a streamed reply is already on screen; re-render once from the final text
        const el = streamEl || addEl("assistant");
        el.innerHTML = renderMarkdown(msg.content || "");
        decorateCode(el);
        streamEl = null;
        streamText = "";
        scrollDown();
      } else if (msg.type === "setup") addSetup(msg.error);
    });

    // ---- rendering ----

    function scrollDown() {
      output.scrollTop = output.scrollHeight;
    }

    function addEl(cls) {
      const div = document.createElement("div");
      div.className = "msg " + cls;
      output.appendChild(div);
      scrollDown();
      return div;
    }

    function addText(text, cls) {
      const div = addEl(cls);
      div.textContent = text;
      return div;
    }

    function addStatus(text) {
      const div = addEl("status");
      const t = document.createElement("span");
      t.className = "t";
      t.textContent = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
      const body = document.createElement("span");
      body.textContent = text;
      div.append(t, body);
    }

    function addBusy(text) {
      const div = addEl("busy");
      div.id = "busy";
      const dots = document.createElement("span");
      dots.className = "dots";
      dots.innerHTML = "<span></span><span></span><span></span>";
      const label = document.createElement("span");
      label.textContent = text;
      div.append(dots, label);
    }

    function clearBusy() {
      const b = $("busy");
      if (b) b.remove();
    }

    function setBusy(on) {
      if (busy === on) return;
      busy = on;
      input.disabled = on;
      composer.classList.toggle("disabled", on);
      updateSend();
      if (!on) input.focus();
    }

    function decorateCode(el) {
      el.querySelectorAll("pre").forEach((pre) => {
        const btn = document.createElement("button");
        btn.className = "copy";
        btn.textContent = "Copy";
        btn.addEventListener("click", () => {
          navigator.clipboard.writeText(pre.querySelector("code").textContent).then(() => {
            btn.textContent = "Copied";
            setTimeout(() => (btn.textContent = "Copy"), 1200);
          });
        });
        pre.appendChild(btn);
      });
    }

    function addSetup(error) {
      const div = addEl("setup");
      const head = document.createElement("div");
      head.className = "head";
      head.textContent = error;
      const body = document.createElement("div");
      body.textContent = "Install the recordkit CLI:";
      const pipx = document.createElement("code");
      pipx.textContent = "pipx install styrhus-records";
      const hint = document.createElement("div");
      hint.textContent = "Already installed elsewhere? Point records.binaryPath at the binary.";
      const btn = document.createElement("button");
      btn.className = "btn";
      btn.style.alignSelf = "flex-start";
      btn.textContent = "Open Settings";
      btn.addEventListener("click", () => vscode.postMessage({ type: "open-settings" }));
      div.append(head, body, pipx, hint, btn);
    }

    function renderModel() {
      modelName.textContent = model.model || (model.endpoint ? "model unset" : "no model");
      modelPill.title = model.endpoint
        ? (model.model || "model unset") + " @ " + model.endpoint + " — Ollama settings"
        : "No model — recordings are user-only. Click to set up Ollama.";
    }

    function renderHeader() {
      header.classList.toggle("recording", !!recording);
      header.classList.toggle("ephemeral", !recording && !!model.model);
      recLabel.textContent = "";
      const sub = document.createElement("span");
      sub.className = "sub";
      if (recording) {
        recLabel.append(recording.mode === "me" ? "Draft " : "Recording ");
        sub.textContent = recording.path.split("/").pop() + (recording.model ? " · " + recording.model : "");
        recLabel.title = recording.path;
      } else if (model.model) {
        recLabel.append("Chat ");
        sub.textContent = "· not recorded";
        recLabel.title = "Messages go to " + model.model + " and are kept in memory only";
      } else {
        recLabel.append("Not recording ");
        sub.textContent = "· /record to start";
        recLabel.title = "";
      }
      recLabel.appendChild(sub);
    }

    function chip(iconSvg, text, title) {
      const c = document.createElement("span");
      c.className = "chip";
      c.title = title;
      c.innerHTML = iconSvg;
      const label = document.createElement("span");
      label.className = "label";
      label.textContent = text;
      c.appendChild(label);
      return c;
    }

    function renderChips() {
      chipsEl.innerHTML = "";
      if (activeEditor.path) {
        const c = chip(ICON.file, activeEditor.path.split("/").pop(), activeEditor.path + (activeEditor.enabled
          ? " — sent as model context (click to disable)"
          : " — context off (click to enable)"));
        c.classList.toggle("off", !activeEditor.enabled);
        c.addEventListener("click", () => {
          activeEditor.enabled = !activeEditor.enabled;
          renderChips();
        });
        chipsEl.appendChild(c);
      }
      attachments.forEach((a, i) => {
        const c = chip(a.kind === "dir" ? ICON.folder : ICON.file,
          a.path + (a.kind === "dir" ? "/" : ""), "Sent to the model as context — not recorded");
        const x = document.createElement("span");
        x.className = "x";
        x.textContent = "×";
        x.title = "Remove context (the typed @mention stays)";
        x.addEventListener("click", () => {
          attachments.splice(i, 1);
          renderChips();
        });
        c.appendChild(x);
        chipsEl.appendChild(c);
      });
      chipsEl.style.display = chipsEl.children.length ? "flex" : "none";
    }

    // ---- popup (slash commands, @ files) ----

    function openPopup(mode, items, anchor) {
      popup = { mode: mode, items: items, sel: 0, anchor: anchor };
      renderPopup();
    }

    function closePopup() {
      if (!popup.mode) return;
      popup = { mode: null, items: [], sel: 0, anchor: 0 };
      popupEl.style.display = "none";
    }

    function renderPopup() {
      popupEl.innerHTML = "";
      popup.items.forEach((item, i) => {
        const row = document.createElement("div");
        row.className = "popup-item" + (i === popup.sel ? " sel" : "");
        if (item.loading) {
          row.classList.add("loading");
          row.textContent = "Loading files…";
        } else if (popup.mode === "slash") {
          const n = document.createElement("span");
          n.className = "pi-name";
          n.textContent = "/" + item.name;
          const a = document.createElement("span");
          a.className = "pi-args";
          a.textContent = item.args;
          const d = document.createElement("span");
          d.className = "pi-desc";
          d.textContent = item.description;
          row.append(n, a, d);
        } else {
          row.innerHTML = item.type === "dir" ? ICON.folder : ICON.file;
          const n = document.createElement("span");
          n.className = "pi-name";
          n.textContent = item.path + (item.type === "dir" ? "/" : "");
          row.appendChild(n);
        }
        row.addEventListener("mousedown", (ev) => {
          ev.preventDefault();
          accept(i);
        });
        popupEl.appendChild(row);
      });
      popupEl.style.display = popup.items.length ? "block" : "none";
      const sel = popupEl.children[popup.sel];
      if (sel) sel.scrollIntoView({ block: "nearest" });
    }

    function moveSel(delta) {
      if (!popup.items.length) return;
      popup.sel = (popup.sel + delta + popup.items.length) % popup.items.length;
      renderPopup();
    }

    function fileTokenAt() {
      const caret = input.selectionStart == null ? input.value.length : input.selectionStart;
      const before = input.value.slice(0, caret);
      const at = before.lastIndexOf("@");
      if (at < 0) return null;
      if (at > 0 && !/\\s/.test(before[at - 1])) return null;
      const token = before.slice(at + 1);
      if (/\\s/.test(token)) return null;
      return { anchor: at, token: token, caret: caret };
    }

    function refreshPopup() {
      const v = input.value;
      const slash = v.match(/^\\/([a-zA-Z]*)$/);
      if (slash) {
        const items = suppress.slash
          ? []
          : COMMANDS.filter((c) => c.name.startsWith(slash[1].toLowerCase()));
        if (items.length) openPopup("slash", items, 0);
        else closePopup();
        updateHint();
        return;
      }
      suppress.slash = false;
      const ft = fileTokenAt();
      if (ft) {
        if (ft.anchor === suppress.fileAnchor) {
          closePopup();
        } else if (fileCache === null) {
          suppress.fileAnchor = -1;
          openPopup("file", [{ loading: true }], ft.anchor);
          vscode.postMessage({ type: "list-files" });
        } else {
          suppress.fileAnchor = -1;
          const token = ft.token.toLowerCase();
          const items = fileCache
            .filter((f) => f.path.toLowerCase().includes(token))
            .slice(0, 50);
          if (items.length) openPopup("file", items, ft.anchor);
          else closePopup();
        }
        updateHint();
        return;
      }
      suppress.fileAnchor = -1;
      closePopup();
      updateHint();
    }

    function updateHint() {
      const m = input.value.match(/^\\/([a-zA-Z]+)(\\s|$)/);
      const spec = m && COMMANDS.find((c) => c.name === m[1].toLowerCase());
      if (spec && !popup.mode) {
        hintEl.innerHTML = "";
        const b = document.createElement("b");
        b.textContent = "/" + spec.name + (spec.args ? " " + spec.args : "");
        hintEl.append(b, " — " + spec.description);
        hintEl.style.display = "block";
      } else {
        hintEl.style.display = "none";
      }
    }

    function accept(i) {
      const item = popup.items[i];
      if (!item || item.loading) return;
      if (popup.mode === "slash") {
        input.value = "/" + item.name + " ";
        closePopup();
        input.focus();
        input.setSelectionRange(input.value.length, input.value.length);
        onInputChanged();
        return;
      }
      const ft = fileTokenAt();
      const caret = ft ? ft.caret : input.value.length;
      const anchor = popup.anchor;
      const insert = "@" + item.path + (item.type === "dir" ? "/" : "") + " ";
      input.value = input.value.slice(0, anchor) + insert + input.value.slice(caret);
      const pos = anchor + insert.length;
      closePopup();
      input.focus();
      input.setSelectionRange(pos, pos);
      if (!attachments.some((a) => a.path === item.path && a.kind === item.type)) {
        attachments.push({ path: item.path, abs: item.abs, kind: item.type });
        renderChips();
      }
      onInputChanged();
    }

    // ---- composer ----

    function autosize() {
      input.style.height = "auto";
      input.style.height = input.scrollHeight + "px";
    }

    function updateSend() {
      sendBtn.disabled = busy || !input.value.trim();
    }

    function onInputChanged() {
      autosize();
      updateSend();
      updateHint();
    }

    input.addEventListener("input", () => {
      refreshPopup();
      autosize();
      updateSend();
    });

    input.addEventListener("keydown", (e) => {
      if (e.isComposing) return;
      if (popup.mode) {
        if (e.key === "ArrowDown") { e.preventDefault(); moveSel(1); return; }
        if (e.key === "ArrowUp") { e.preventDefault(); moveSel(-1); return; }
        if (e.key === "Tab" || e.key === "Enter") { e.preventDefault(); accept(popup.sel); return; }
        if (e.key === "Escape") {
          e.preventDefault();
          if (popup.mode === "slash") suppress.slash = true;
          else suppress.fileAnchor = popup.anchor;
          closePopup();
          return;
        }
      }
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        submit();
      }
    });

    // insert a trigger character at the caret and let the popup logic take over
    function insertTrigger(ch, replaceAll) {
      input.focus();
      if (replaceAll) {
        input.value = ch;
      } else {
        const pos = input.selectionStart == null ? input.value.length : input.selectionStart;
        const before = input.value.slice(0, pos);
        const pad = before && !/\\s$/.test(before) ? " " : "";
        input.value = before + pad + ch + input.value.slice(pos);
        const caret = pos + pad.length + ch.length;
        input.setSelectionRange(caret, caret);
      }
      suppress = { slash: false, fileAnchor: -1 };
      refreshPopup();
      autosize();
      updateSend();
    }

    $("btn-attach").addEventListener("click", () => insertTrigger("@", false));
    $("btn-slash").addEventListener("click", () => insertTrigger("/", !input.value.trim()));
    sendBtn.addEventListener("click", submit);
    $("btn-stop").addEventListener("click", () => {
      addText("/esc", "user");
      vscode.postMessage({ type: "slash", command: "esc", args: "" });
    });

    function submit() {
      const text = input.value.trim();
      if (!text || busy) return;
      const welcome = $("welcome");
      if (welcome) welcome.remove();
      addText(text, "user");
      input.value = "";
      closePopup();
      suppress = { slash: false, fileAnchor: -1 };
      onInputChanged();

      if (text.startsWith("/")) {
        const parts = text.split(/\\s+/);
        vscode.postMessage({ type: "slash", command: parts[0].slice(1), args: parts.slice(1).join(" ") });
      } else {
        const payload = { type: "message", text: text };
        if (attachments.length) payload.attachments = attachments.slice();
        if (activeEditor.enabled && activeEditor.path) payload.activeEditor = activeEditor.abs || activeEditor.path;
        const note = [];
        if (payload.activeEditor) note.push(activeEditor.path.split("/").pop());
        attachments.forEach((a) => note.push(a.path.split("/").pop() + (a.kind === "dir" ? "/" : "")));
        if (note.length) addText("Context: " + note.join(", ") + " — model-only, not recorded", "context");
        vscode.postMessage(payload);
      }
      attachments = [];
      fileCache = null;
      renderChips();
    }

    // ---- settings panel ----

    function closeSettings() {
      settingsPanel.style.display = "none";
      input.focus();
    }

    modelPill.addEventListener("click", () => {
      if (settingsPanel.style.display === "block") return closeSettings();
      vscode.postMessage({ type: "get-settings" });
    });

    $("sp-save").addEventListener("click", () => {
      vscode.postMessage({ type: "save-settings", endpoint: spEndpoint.value, model: spModel.value });
      closeSettings();
    });

    $("sp-cancel").addEventListener("click", closeSettings);

    settingsPanel.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeSettings();
      else if (e.key === "Enter") $("sp-save").click();
    });

    renderModel();
    renderHeader();
    autosize();
    vscode.postMessage({ type: "ready" });
  </script>
</body>
</html>`;
}
