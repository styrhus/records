import * as vscode from "vscode";
import * as child_process from "child_process";

interface OllamaConfig {
  endpoint: string;
  model: string;
}

interface RecordingSession {
  file: string;
  draft: boolean;
  ollama?: OllamaConfig;
}

type MessageToView = {
  type: "update-status" | "response" | "error" | "output" | "setup" | "busy";
  content?: string;
  json?: Record<string, unknown>;
  error?: string;
};

type MessageFromView = {
  type: "slash" | "message" | "stop-recording" | "open-settings";
  command?: string;
  args?: string;
  text?: string;
};

export class ChatViewProvider implements vscode.WebviewViewProvider {
  static readonly viewType = "recordsChat";

  private view?: vscode.WebviewView;
  private recording: RecordingSession | undefined;

  constructor(private readonly extensionUri: vscode.Uri) {}

  resolveWebviewView(webviewView: vscode.WebviewView): void {
    this.view = webviewView;
    webviewView.webview.options = { enableScripts: true };
    webviewView.webview.html = this.getWebviewContent();

    webviewView.webview.onDidReceiveMessage((message: MessageFromView) =>
      this.handleMessage(message)
    );

    const configListener = vscode.workspace.onDidChangeConfiguration((e) => {
      if (
        e.affectsConfiguration("records.binaryPath") ||
        e.affectsConfiguration("records.ollamaEndpoint") ||
        e.affectsConfiguration("records.ollamaModel")
      ) {
        void this.probeCLI();
      }
    });

    webviewView.onDidDispose(() => {
      configListener.dispose();
      this.view = undefined;
    });

    void this.probeCLI();
  }

  private async probeCLI() {
    try {
      const result = await this.runCLI("config", {});
      const ollama = this.ollamaConfig();
      this.postMessage({
        type: "update-status",
        content: `records CLI ready — dir: ${result.records_dir} — ollama: ${
          ollama ? ollama.model || "model unset" : "off"
        }`,
      });
    } catch (e) {
      const notFound = (e as NodeJS.ErrnoException).code === "ENOENT";
      this.postMessage({
        type: "setup",
        error: notFound ? "records CLI not found" : String(e),
      });
    }
  }

  private async handleMessage(message: MessageFromView) {
    try {
      if (message.type === "slash") {
        await this.handleSlash(message.command || "", message.args || "");
      } else if (message.type === "message") {
        if (this.recording?.ollama) {
          await this.appendOllamaTurn(message.text || "");
        } else if (this.recording) {
          await this.appendUserMessage(message.text || "");
          this.postMessage({ type: "update-status", content: "Message recorded." });
        } else {
          this.postMessage({ type: "error", error: "No active recording session." });
        }
      } else if (message.type === "stop-recording") {
        this.recording = undefined;
        this.postMessage({ type: "update-status", content: "Recording stopped." });
      } else if (message.type === "open-settings") {
        await vscode.commands.executeCommand(
          "workbench.action.openSettings",
          "records.binaryPath"
        );
      }
    } catch (e) {
      this.postMessage({ type: "error", error: String(e) });
    }
  }

  private async handleSlash(command: string, args: string) {
    const tokens = command.split(/\s+/);
    const cmd = tokens[0];
    const rest = tokens.slice(1).join(" ");

    switch (cmd) {
      case "record":
      case "all":
      case "me":
        await this.startRecording(cmd, args);
        break;
      case "esc":
        this.recording = undefined;
        this.postMessage({ type: "update-status", content: "Recording stopped." });
        break;
      case "stick":
        await this.stickRecord(args);
        break;
      case "gc":
      case "gcp":
      case "cpd":
        await this.commit(cmd, rest || args);
        break;
      case "myname":
        await this.myname(args);
        break;
      case "mucke":
        await this.mucke();
        break;
      case "config":
        await this.config();
        break;
      default:
        this.postMessage({ type: "error", error: `Unknown command: ${cmd}` });
    }
  }

  private ollamaConfig(): OllamaConfig | undefined {
    const cfg = vscode.workspace.getConfiguration("records");
    const endpoint = (cfg.get<string>("ollamaEndpoint") || "").trim().replace(/\/+$/, "");
    if (!endpoint) return undefined;
    return { endpoint, model: (cfg.get<string>("ollamaModel") || "").trim() };
  }

  private async startRecording(mode: string, args: string) {
    const draft = mode === "me";
    let ollama = mode === "record" ? this.ollamaConfig() : undefined;
    if (ollama && !ollama.model) {
      this.postMessage({
        type: "error",
        error: "Set records.ollamaModel to enable two-sided /record — recording user-only.",
      });
      ollama = undefined;
    }
    try {
      const result = await this.runCLI("new", {
        arguments: args,
        ...(draft && { draft: true }),
      });
      this.recording = { file: result.path as string, draft, ollama };
      this.postMessage({
        type: "update-status",
        content: `Recording (${mode}${ollama ? ` · ollama ${ollama.model}` : ""}): ${result.path}`,
      });
    } catch (e) {
      this.postMessage({ type: "error", error: `Failed to start recording: ${e}` });
    }
  }

  private async appendUserMessage(text: string) {
    if (!this.recording) throw new Error("No recording session");
    await this.runCLI("append", { file: this.recording.file, text });
  }

  private async appendOllamaTurn(text: string) {
    const { file, ollama } = this.recording!;
    const { endpoint, model } = ollama!;
    this.postMessage({ type: "busy", content: `${model} is thinking…` });
    try {
      const result = await this.runCLI("ollama-reply", { file, endpoint, model, human: text });
      this.postMessage({ type: "response", content: result.reply as string });
    } catch (e) {
      await this.runCLI("append", { file, text });
      this.postMessage({
        type: "error",
        error: `Ollama failed — recorded your message user-only. (${
          e instanceof Error ? e.message : e
        })`,
      });
    }
  }

  private async stickRecord(slug: string) {
    try {
      const result = await this.runCLI("stick", { slug });
      this.postMessage({ type: "output", content: `Featured: ${result.path}` });
    } catch (e) {
      this.postMessage({ type: "error", error: `Failed to feature: ${e}` });
    }
  }

  private async commit(mode: string, message: string) {
    const push = mode !== "gc";
    const deploy = mode === "cpd";

    if (!message) {
      message = await vscode.window.showInputBox({
        prompt: "Commit message",
        placeHolder: "Enter commit message (required)",
      }) || "";
    }

    if (!message) {
      this.postMessage({ type: "error", error: "Commit message required" });
      return;
    }

    try {
      await this.runCLI("commit", {
        message,
        ...(push && { push: true }),
        ...(deploy && { deploy: true }),
      });
      this.postMessage({
        type: "output",
        content: `Commit ${push ? "(pushed)" : "(staged)"}: ${message}`,
      });
    } catch (e) {
      this.postMessage({ type: "error", error: `Commit failed: ${e}` });
    }
  }

  private async myname(name: string) {
    if (!name) {
      name = await vscode.window.showInputBox({
        prompt: "Your name",
        placeHolder: "Enter your name",
      }) || "";
    }

    if (!name) return;

    try {
      await this.runCLI("myname", { name });
      this.postMessage({ type: "output", content: `Saved your name: ${name}` });
    } catch (e) {
      this.postMessage({ type: "error", error: `Failed to save name: ${e}` });
    }
  }

  private async mucke() {
    try {
      const editor = vscode.window.activeTextEditor;
      if (!editor) {
        this.postMessage({
          type: "error",
          error: "No active editor — please open a file first",
        });
        return;
      }
      const file = editor.document.uri.fsPath;
      const result = await this.runCLI("mucke", { file });
      this.postMessage({
        type: "output",
        content: `Mucke: ${result.title} • ${result.artist}`,
      });
    } catch (e) {
      this.postMessage({ type: "error", error: `Mucke failed: ${e}` });
    }
  }

  private async config() {
    try {
      const result = await this.runCLI("config", {});
      this.postMessage({
        type: "output",
        content: `Records dir: ${result.records_dir}`,
      });
    } catch (e) {
      this.postMessage({ type: "error", error: `Config failed: ${e}` });
    }
  }

  private async runCLI(
    command: string,
    opts: Record<string, string | boolean>
  ): Promise<Record<string, unknown>> {
    const cfg = vscode.workspace.getConfiguration("records");
    const bin = cfg.get<string>("binaryPath") || "records";
    // CLI discovers the records dir from cwd — run it from the workspace, not the extension host
    const cwd = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;

    const args: string[] = [command];
    for (const [k, v] of Object.entries(opts)) {
      if (k === "arguments") {
        if (v) args.push(v as string);
      } else if (v === true) {
        args.push(`--${k}`);
      } else if (v && typeof v === "string") {
        args.push(`--${k}`, v);
      }
    }

    return new Promise((resolve, reject) => {
      child_process.execFile(bin, args, { encoding: "utf-8", cwd }, (err, stdout) => {
        if (err) {
          // the CLI reports failures as {"error": ...} on stdout before exiting non-zero
          try {
            const parsed = JSON.parse(stdout);
            if (parsed && typeof parsed.error === "string") {
              reject(new Error(parsed.error));
              return;
            }
          } catch {
            // fall through to the raw error
          }
          reject(err);
          return;
        }
        try {
          resolve(JSON.parse(stdout));
        } catch (e) {
          reject(new Error(`Invalid CLI response: ${stdout}`));
        }
      });
    });
  }

  private postMessage(message: MessageToView) {
    this.view?.webview.postMessage(message);
  }

  private getWebviewContent(): string {
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
      border: 1px solid var(--vscode-border-color);
      padding: 0.5rem;
      margin-bottom: 0.5rem;
      background: var(--vscode-textCodeBlock-background);
      border-radius: 4px;
      font-size: 0.9rem;
      font-family: monospace;
    }
    .message { margin-bottom: 0.5rem; }
    .status { color: var(--vscode-symbolIcon-functionForeground); }
    .error { color: var(--vscode-errorForeground); }
    .output { color: var(--vscode-terminal-ansiBrightCyan); }
    .response { color: var(--vscode-terminal-ansiBrightGreen); white-space: pre-wrap; }
    .busy { color: var(--vscode-descriptionForeground); font-style: italic; }
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
  </style>
</head>
<body>
  <div id="output"></div>
  <div id="input-area">
    <input id="input" type="text" placeholder="Slash command or message…" />
  </div>
  <script>
    const vscode = acquireVsCodeApi();
    const output = document.getElementById("output");
    const input = document.getElementById("input");

    window.addEventListener("message", (e) => {
      const msg = e.data;
      if (msg.type === "busy") {
        const div = addLine(msg.content, "busy");
        div.id = "busy";
        input.disabled = true;
        return;
      }
      clearBusy();
      if (msg.type === "update-status") {
        addLine(\`[\${new Date().toLocaleTimeString()}] \${msg.content}\`, "status");
      } else if (msg.type === "error") {
        addLine(\`ERROR: \${msg.error}\`, "error");
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

    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        const text = input.value.trim();
        if (!text) return;
        addLine(\`> \${text}\`, "status");
        input.value = "";

        if (text.startsWith("/")) {
          const parts = text.split(/\\s+/);
          const cmd = parts[0].slice(1);
          const args = parts.slice(1).join(" ");
          vscode.postMessage({ type: "slash", command: cmd, args });
        } else {
          vscode.postMessage({ type: "message", text });
        }
      }
    });

    function addLine(text, cls = "") {
      const div = document.createElement("div");
      div.className = \`message \${cls}\`;
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
      pip.textContent = "pip install -e others/python";
      div.appendChild(pip);

      const pipx = document.createElement("code");
      pipx.textContent = "pipx install ./others/python";
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
  </script>
</body>
</html>`;
  }
}
