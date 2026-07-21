import * as vscode from "vscode";
import * as child_process from "child_process";
import * as path from "path";

interface RecordingSession {
  file: string;
  draft: boolean;
}

type MessageToPanel = {
  type: "update-status" | "response" | "error" | "output";
  content?: string;
  json?: Record<string, unknown>;
  error?: string;
};

type MessageFromPanel = {
  type: "slash" | "message" | "stop-recording";
  command?: string;
  args?: string;
  text?: string;
};

export class RecordsChatPanel {
  private panel: vscode.WebviewPanel;
  private disposables: vscode.Disposable[] = [];
  private recording: RecordingSession | undefined;
  private _onDisposed: vscode.EventEmitter<void> = new vscode.EventEmitter();
  readonly onDisposed = this._onDisposed.event;

  constructor(extensionUri: vscode.Uri) {
    this.panel = vscode.window.createWebviewPanel(
      "recordsChat",
      "Records Chat",
      vscode.ViewColumn.Beside,
      { enableScripts: true }
    );

    this.panel.webview.html = this.getWebviewContent();
    this.panel.onDidDispose(() => {
      this.disposables.forEach((d) => d.dispose());
      this._onDisposed.fire();
    });

    this.panel.webview.onDidReceiveMessage(
      (message: MessageFromPanel) => this.handleMessage(message),
      undefined,
      this.disposables
    );
  }

  reveal() {
    this.panel.reveal(vscode.ViewColumn.Beside);
  }

  private async handleMessage(message: MessageFromPanel) {
    try {
      if (message.type === "slash") {
        await this.handleSlash(message.command || "", message.args || "");
      } else if (message.type === "message") {
        if (this.recording) {
          await this.appendUserMessage(message.text || "");
          this.postMessage({ type: "update-status", content: "Message recorded." });
        } else {
          this.postMessage({ type: "error", error: "No active recording session." });
        }
      } else if (message.type === "stop-recording") {
        this.recording = undefined;
        this.postMessage({ type: "update-status", content: "Recording stopped." });
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

  private async startRecording(mode: string, args: string) {
    const draft = mode === "me";
    try {
      const result = await this.runCLI("new", {
        arguments: args,
        ...(draft && { draft: "true" }),
      });
      this.recording = { file: result.path as string, draft };
      this.postMessage({
        type: "update-status",
        content: `Recording (${mode}): ${result.path}`,
      });
    } catch (e) {
      this.postMessage({ type: "error", error: `Failed to start recording: ${e}` });
    }
  }

  private async appendUserMessage(text: string) {
    if (!this.recording) throw new Error("No recording session");
    await this.runCLI("append", { file: this.recording.file, text });
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
      const result = await this.runCLI("commit", {
        message,
        ...(push && { push: "true" }),
        ...(deploy && { deploy: "true" }),
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

    const args: string[] = [command];
    for (const [k, v] of Object.entries(opts)) {
      if (k === "arguments") {
        args.push(v as string);
      } else if (v === true) {
        args.push(`--${k}`);
      } else if (v && typeof v === "string") {
        args.push(`--${k}`, v);
      }
    }

    return new Promise((resolve, reject) => {
      child_process.execFile(bin, args, { encoding: "utf-8" }, (err, stdout) => {
        if (err) reject(err);
        try {
          resolve(JSON.parse(stdout));
        } catch (e) {
          reject(new Error(`Invalid CLI response: ${stdout}`));
        }
      });
    });
  }

  private postMessage(message: MessageToPanel) {
    this.panel.webview.postMessage(message);
  }

  private getWebviewContent(): string {
    return `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Records Chat</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: system-ui, -apple-system, sans-serif;
      background: var(--vscode-editor-background);
      color: var(--vscode-editor-foreground);
      display: flex;
      flex-direction: column;
      height: 100vh;
      padding: 1rem;
    }
    #output {
      flex: 1;
      overflow-y: auto;
      border: 1px solid var(--vscode-border-color);
      padding: 0.5rem;
      margin-bottom: 1rem;
      background: var(--vscode-textCodeBlock-background);
      border-radius: 4px;
      font-size: 0.9rem;
      font-family: monospace;
    }
    .message { margin-bottom: 0.5rem; }
    .status { color: var(--vscode-symbolIcon-functionForeground); }
    .error { color: var(--vscode-errorForeground); }
    .output { color: var(--vscode-terminal-ansiBrightCyan); }
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
      padding: 0.5rem 1rem;
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
      if (msg.type === "update-status") {
        addLine(\`[\${new Date().toLocaleTimeString()}] \${msg.content}\`, "status");
      } else if (msg.type === "error") {
        addLine(\`ERROR: \${msg.error}\`, "error");
      } else if (msg.type === "output") {
        addLine(msg.content, "output");
      }
    });

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
    }
  </script>
</body>
</html>`;
  }
}
