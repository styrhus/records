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
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: system-ui, -apple-system, sans-serif;
      background: var(--vscode-sideBar-background);
      color: var(--vscode-editor-foreground);
      display: flex;
      flex-direction: column;
      height: 100vh;
      padding: 0.5rem;
    }
    #output {
      flex: 1;
      overflow-y: auto;
      overflow-x: hidden;
      border: 1px solid var(--vscode-border-color);
      padding: 0.5rem;
      margin-bottom: 0.5rem;
      background: var(--vscode-textCodeBlock-background);
      border-radius: 4px;
      font-size: 0.9rem;
      font-family: monospace;
    }
    .message { margin-bottom: 0.5rem; white-space: pre-wrap; overflow-wrap: anywhere; }
    .status { color: var(--vscode-descriptionForeground); }
    .user { color: var(--vscode-editor-foreground); }
    .error { color: var(--vscode-errorForeground); }
    .output { color: var(--vscode-terminal-ansiBrightCyan); }
    .response { color: var(--vscode-terminal-ansiBrightGreen); }
    .busy { color: var(--vscode-descriptionForeground); font-style: italic; }
    .dim { color: var(--vscode-descriptionForeground); }
    .setup {
      border: 1px solid var(--vscode-inputValidation-warningBorder);
      border-radius: 4px;
      padding: 0.5rem;
    }
    .setup code {
      display: block;
      margin: 0.3rem 0;
      user-select: all;
    }
    #settings-panel {
      display: none;
      border: 1px solid var(--vscode-focusBorder);
      border-radius: 4px;
      padding: 0.5rem;
      margin-bottom: 0.5rem;
    }
    #settings-panel .sp-title { font-weight: 600; margin-bottom: 0.4rem; }
    #settings-panel label {
      display: block;
      font-size: 0.8rem;
      margin-bottom: 0.4rem;
      color: var(--vscode-descriptionForeground);
    }
    #settings-panel input {
      width: 100%;
      margin-top: 0.15rem;
      padding: 0.3rem;
      background: var(--vscode-input-background);
      color: var(--vscode-input-foreground);
      border: 1px solid var(--vscode-inputBorder-background);
      border-radius: 4px;
      font-family: monospace;
    }
    .sp-buttons { display: flex; gap: 0.5rem; }
    #context-bar, #chips-row {
      display: none;
      flex-wrap: wrap;
      gap: 0.3rem;
      padding-bottom: 0.3rem;
    }
    .chip {
      display: inline-flex;
      align-items: center;
      gap: 0.3rem;
      padding: 0.1rem 0.5rem;
      border-radius: 999px;
      background: var(--vscode-badge-background);
      color: var(--vscode-badge-foreground);
      font-size: 0.8rem;
      cursor: pointer;
      max-width: 100%;
      overflow: hidden;
    }
    .chip.off { opacity: 0.45; text-decoration: line-through; }
    .chip .x { opacity: 0.7; }
    .chip .x:hover { opacity: 1; }
    #hint {
      display: none;
      font-size: 0.8rem;
      color: var(--vscode-descriptionForeground);
      padding: 0 0.2rem 0.3rem;
      font-family: monospace;
    }
    #input-wrap { position: relative; }
    #popup {
      display: none;
      position: absolute;
      bottom: 100%;
      left: 0;
      right: 0;
      margin-bottom: 0.3rem;
      max-height: 12rem;
      overflow-y: auto;
      background: var(--vscode-editorSuggestWidget-background, var(--vscode-input-background));
      border: 1px solid var(--vscode-focusBorder);
      border-radius: 4px;
      z-index: 10;
      font-family: monospace;
      font-size: 0.85rem;
    }
    .popup-item {
      padding: 0.25rem 0.5rem;
      cursor: pointer;
      display: flex;
      gap: 0.5rem;
      justify-content: space-between;
      white-space: nowrap;
      overflow: hidden;
    }
    .popup-item.sel {
      background: var(--vscode-list-activeSelectionBackground);
      color: var(--vscode-list-activeSelectionForeground);
    }
    .pi-name { flex-shrink: 0; }
    .pi-desc { color: var(--vscode-descriptionForeground); overflow: hidden; text-overflow: ellipsis; }
    .popup-item.sel .pi-desc { color: inherit; opacity: 0.8; }
    #input-area {
      display: flex;
      gap: 0.5rem;
    }
    #input {
      flex: 1;
      padding: 0.5rem;
      background: var(--vscode-input-background);
      color: var(--vscode-input-foreground);
      border: 1px solid var(--vscode-inputBorder-background);
      border-radius: 4px;
      font-family: monospace;
    }
    #input:focus { outline: none; border-color: var(--vscode-focusBorder-background); }
    #model-line {
      font-size: 0.75rem;
      color: var(--vscode-descriptionForeground);
      padding: 0.3rem 0.2rem 0;
    }
    button {
      padding: 0.3rem 0.8rem;
      background: var(--vscode-button-background);
      color: var(--vscode-button-foreground);
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-weight: 500;
    }
    button:hover { background: var(--vscode-button-hoverBackground); }
    button.secondary {
      background: var(--vscode-button-secondaryBackground, transparent);
      color: var(--vscode-button-secondaryForeground, inherit);
    }
    #gear {
      background: transparent;
      color: var(--vscode-editor-foreground);
      padding: 0.3rem 0.4rem;
      font-size: 1rem;
    }
    #gear:hover { background: var(--vscode-toolbar-hoverBackground, rgba(128, 128, 128, 0.2)); }
  </style>
</head>
<body>
  <div id="output"></div>
  <div id="settings-panel">
    <div class="sp-title">Ollama settings</div>
    <label>Endpoint
      <input id="sp-endpoint" type="text" placeholder="http://localhost:11434" />
    </label>
    <label>Model
      <input id="sp-model" type="text" placeholder="qwen2.5:14b" />
    </label>
    <div class="sp-buttons">
      <button id="sp-save">Save</button>
      <button id="sp-cancel" class="secondary">Cancel</button>
    </div>
  </div>
  <div id="context-bar"><span id="editor-chip" class="chip"></span></div>
  <div id="chips-row"></div>
  <div id="hint"></div>
  <div id="input-wrap">
    <div id="popup"></div>
    <div id="input-area">
      <input id="input" type="text" placeholder="Message, / for commands, @ to attach files…" />
      <button id="gear" title="Ollama settings">⚙</button>
    </div>
  </div>
  <div id="model-line"></div>
  <script>
    const vscode = acquireVsCodeApi();
    const output = document.getElementById("output");
    const input = document.getElementById("input");
    const popupEl = document.getElementById("popup");
    const hintEl = document.getElementById("hint");
    const chipsRow = document.getElementById("chips-row");
    const contextBar = document.getElementById("context-bar");
    const editorChip = document.getElementById("editor-chip");
    const modelLine = document.getElementById("model-line");
    const settingsPanel = document.getElementById("settings-panel");
    const spEndpoint = document.getElementById("sp-endpoint");
    const spModel = document.getElementById("sp-model");

    const COMMANDS = ${commandsJson};
    let popup = { mode: null, items: [], sel: 0, anchor: 0 };
    let suppress = { slash: false, fileAnchor: -1 };
    let fileCache = null;
    let attachments = [];
    let activeEditor = { path: null, enabled: true };

    window.addEventListener("message", (e) => {
      const msg = e.data;
      if (msg.type === "model-info") {
        renderModelLine(msg);
        return;
      }
      if (msg.type === "file-list") {
        fileCache = msg.files || [];
        if (popup.mode === "file") refreshPopup();
        return;
      }
      if (msg.type === "active-editor") {
        if (msg.path && msg.path !== activeEditor.path) {
          activeEditor = { path: msg.path, enabled: true };
        } else if (!msg.path) {
          activeEditor = { path: null, enabled: true };
        }
        renderEditorChip();
        return;
      }
      if (msg.type === "settings-values") {
        spEndpoint.value = msg.endpoint || "";
        spModel.value = msg.model || "";
        settingsPanel.style.display = "block";
        spEndpoint.focus();
        return;
      }
      if (msg.type === "focus-input") {
        input.focus();
        return;
      }
      if (msg.type === "busy") {
        const div = addLine(msg.content, "busy");
        div.id = "busy";
        input.disabled = true;
        return;
      }
      clearBusy();
      if (msg.type === "update-status") {
        addLine("[" + new Date().toLocaleTimeString() + "] " + msg.content, "status");
      } else if (msg.type === "error") {
        addLine("ERROR: " + msg.error, "error");
      } else if (msg.type === "output") {
        addLine(msg.content, "output");
      } else if (msg.type === "response") {
        addLine(msg.content, "response");
      } else if (msg.type === "setup") {
        addSetup(msg.error);
      }
    });

    function clearBusy() {
      const busy = document.getElementById("busy");
      if (busy) busy.remove();
      if (input.disabled) {
        input.disabled = false;
        input.focus();
      }
    }

    function renderModelLine(msg) {
      if (msg.endpoint && msg.model) modelLine.textContent = msg.model + " @ " + msg.endpoint;
      else if (msg.endpoint) modelLine.textContent = "model unset @ " + msg.endpoint;
      else modelLine.textContent = "no model — user-only recording";
    }

    function renderEditorChip() {
      if (!activeEditor.path) {
        contextBar.style.display = "none";
        return;
      }
      editorChip.textContent = activeEditor.path.split("/").pop();
      editorChip.title = activeEditor.path + (activeEditor.enabled
        ? " — sent as model context (click to disable)"
        : " — context off (click to enable)");
      editorChip.classList.toggle("off", !activeEditor.enabled);
      contextBar.style.display = "flex";
    }

    editorChip.addEventListener("click", () => {
      activeEditor.enabled = !activeEditor.enabled;
      renderEditorChip();
    });

    function renderChips() {
      chipsRow.innerHTML = "";
      attachments.forEach((a, i) => {
        const chip = document.createElement("span");
        chip.className = "chip";
        chip.title = "Sent to the model as context — not recorded";
        const label = document.createElement("span");
        label.textContent = "@" + a.path + (a.kind === "dir" ? "/" : "");
        const x = document.createElement("span");
        x.className = "x";
        x.textContent = "×";
        x.title = "Remove context (the typed @mention stays)";
        x.addEventListener("click", () => {
          attachments.splice(i, 1);
          renderChips();
        });
        chip.append(label, x);
        chipsRow.appendChild(chip);
      });
      chipsRow.style.display = attachments.length ? "flex" : "none";
    }

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
          row.classList.add("dim");
          row.textContent = "Loading files…";
        } else if (popup.mode === "slash") {
          const n = document.createElement("span");
          n.className = "pi-name";
          n.textContent = "/" + item.name + (item.args ? " " + item.args : "");
          const d = document.createElement("span");
          d.className = "pi-desc";
          d.textContent = item.description;
          row.append(n, d);
        } else {
          row.textContent = item.path + (item.type === "dir" ? "/" : "");
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
        hintEl.textContent = "/" + spec.name + (spec.args ? " " + spec.args : "") + " — " + spec.description;
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
        updateHint();
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
        attachments.push({ path: item.path, kind: item.type });
        renderChips();
      }
    }

    input.addEventListener("input", refreshPopup);

    input.addEventListener("keydown", (e) => {
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
      if (e.key === "Enter") submit();
    });

    function submit() {
      const text = input.value.trim();
      if (!text) return;
      addLine("> " + text, "user");
      input.value = "";
      closePopup();
      suppress = { slash: false, fileAnchor: -1 };
      updateHint();

      if (text.startsWith("/")) {
        const parts = text.split(/\\s+/);
        vscode.postMessage({ type: "slash", command: parts[0].slice(1), args: parts.slice(1).join(" ") });
      } else {
        const payload = { type: "message", text: text };
        if (attachments.length) payload.attachments = attachments.slice();
        if (activeEditor.enabled && activeEditor.path) payload.activeEditor = activeEditor.path;
        const note = [];
        if (attachments.length) {
          note.push(attachments.length + " attachment" + (attachments.length > 1 ? "s" : ""));
        }
        if (payload.activeEditor) note.push("editor: " + payload.activeEditor);
        if (note.length) addLine("[context: " + note.join(" + ") + " — model-only, not recorded]", "dim");
        vscode.postMessage(payload);
      }
      attachments = [];
      fileCache = null;
      renderChips();
    }

    document.getElementById("gear").addEventListener("click", () => {
      if (settingsPanel.style.display === "block") {
        settingsPanel.style.display = "none";
        return;
      }
      vscode.postMessage({ type: "get-settings" });
    });

    document.getElementById("sp-save").addEventListener("click", () => {
      vscode.postMessage({ type: "save-settings", endpoint: spEndpoint.value, model: spModel.value });
      settingsPanel.style.display = "none";
      input.focus();
    });

    document.getElementById("sp-cancel").addEventListener("click", () => {
      settingsPanel.style.display = "none";
      input.focus();
    });

    settingsPanel.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        settingsPanel.style.display = "none";
        input.focus();
      } else if (e.key === "Enter") {
        document.getElementById("sp-save").click();
      }
    });

    function addLine(text, cls = "") {
      const div = document.createElement("div");
      div.className = "message " + cls;
      div.textContent = text;
      output.appendChild(div);
      output.scrollTop = output.scrollHeight;
      return div;
    }

    function addSetup(error) {
      const div = document.createElement("div");
      div.className = "message setup";

      const head = document.createElement("div");
      head.className = "error";
      head.textContent = error;
      div.appendChild(head);

      const body = document.createElement("div");
      body.textContent = "Install the recordkit CLI (from the repo root):";
      div.appendChild(body);

      const pip = document.createElement("code");
      pip.textContent = "pip install -e tools/others/python";
      div.appendChild(pip);

      const pipx = document.createElement("code");
      pipx.textContent = "pipx install ./tools/others/python";
      div.appendChild(pipx);

      const hint = document.createElement("div");
      hint.textContent =
        "Already installed elsewhere? Point records.binaryPath at the binary:";
      div.appendChild(hint);

      const btn = document.createElement("button");
      btn.textContent = "Open Settings";
      btn.addEventListener("click", () =>
        vscode.postMessage({ type: "open-settings" })
      );
      div.appendChild(btn);

      output.appendChild(div);
      output.scrollTop = output.scrollHeight;
    }

    vscode.postMessage({ type: "ready" });
  </script>
</body>
</html>`;
}
