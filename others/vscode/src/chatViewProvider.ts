import * as vscode from "vscode";
import * as child_process from "child_process";
import { getWebviewContent } from "./webviewContent";
import { COMMANDS } from "./commands";

interface OllamaConfig {
  endpoint: string;
  model: string;
}

interface RecordingSession {
  file: string;
  draft: boolean;
  ollama?: OllamaConfig;
}

interface Attachment {
  path: string;
  kind: "file" | "dir";
}

type MessageToView = {
  type:
    | "update-status"
    | "response"
    | "error"
    | "output"
    | "setup"
    | "busy"
    | "model-info"
    | "file-list"
    | "active-editor"
    | "settings-values";
  content?: string;
  error?: string;
  model?: string;
  endpoint?: string;
  files?: { path: string; type: "file" | "dir" }[];
  path?: string;
};

type MessageFromView = {
  type:
    | "ready"
    | "slash"
    | "message"
    | "open-settings"
    | "list-files"
    | "get-settings"
    | "save-settings";
  command?: string;
  args?: string;
  text?: string;
  attachments?: Attachment[];
  activeEditor?: string;
  endpoint?: string;
  model?: string;
};

const FIND_EXCLUDES =
  "{**/node_modules/**,**/.git/**,**/out/**,**/dist/**,**/.venv/**,**/__pycache__/**,**/public/**}";

export class ChatViewProvider implements vscode.WebviewViewProvider {
  static readonly viewType = "recordsChat";

  private view?: vscode.WebviewView;
  private recording: RecordingSession | undefined;

  constructor(private readonly extensionUri: vscode.Uri) {}

  resolveWebviewView(webviewView: vscode.WebviewView): void {
    this.view = webviewView;
    webviewView.webview.options = { enableScripts: true };
    webviewView.webview.html = getWebviewContent(JSON.stringify(COMMANDS));

    webviewView.webview.onDidReceiveMessage((message: MessageFromView) =>
      this.handleMessage(message)
    );

    const configListener = vscode.workspace.onDidChangeConfiguration((e) => {
      if (
        e.affectsConfiguration("records.binaryPath") ||
        e.affectsConfiguration("records.ollamaEndpoint") ||
        e.affectsConfiguration("records.ollamaModel")
      ) {
        this.postModelInfo();
        void this.probeCLI();
      }
    });

    const editorListener = vscode.window.onDidChangeActiveTextEditor((editor) =>
      this.postActiveEditor(editor)
    );

    webviewView.onDidDispose(() => {
      configListener.dispose();
      editorListener.dispose();
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
      if (message.type === "ready") {
        this.postModelInfo();
        this.postActiveEditor(vscode.window.activeTextEditor);
      } else if (message.type === "slash") {
        await this.handleSlash(message.command || "", message.args || "");
      } else if (message.type === "message") {
        await this.handleChatMessage(message);
      } else if (message.type === "list-files") {
        await this.listFiles();
      } else if (message.type === "get-settings") {
        this.getSettings();
      } else if (message.type === "save-settings") {
        await this.saveSettings(message.endpoint || "", message.model || "");
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

  private async handleChatMessage(message: MessageFromView) {
    const text = message.text || "";
    const attachments = message.attachments || [];
    const files = attachments.filter((a) => a.kind === "file").map((a) => a.path);
    const dirs = attachments.filter((a) => a.kind === "dir").map((a) => a.path);
    if (message.activeEditor && !files.includes(message.activeEditor)) {
      files.push(message.activeEditor);
    }

    if (this.recording?.ollama) {
      await this.appendOllamaTurn(text, files, dirs);
    } else if (this.recording) {
      await this.appendUserMessage(text);
      this.postMessage({
        type: "update-status",
        content:
          files.length || dirs.length
            ? "Message recorded (attachments ignored — no model configured)."
            : "Message recorded.",
      });
    } else {
      this.postMessage({ type: "error", error: "No active recording session." });
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

  private postModelInfo() {
    const ollama = this.ollamaConfig();
    this.postMessage({
      type: "model-info",
      model: ollama?.model || undefined,
      endpoint: ollama?.endpoint,
    });
  }

  private postActiveEditor(editor: vscode.TextEditor | undefined) {
    // undefined fires when the webview itself takes focus — keep the last real editor
    if (!editor) return;
    const uri = editor.document.uri;
    if (uri.scheme !== "file") return;
    const rel = vscode.workspace.asRelativePath(uri, false);
    if (rel === uri.fsPath) return; // outside the workspace
    this.postMessage({ type: "active-editor", path: rel });
  }

  private async listFiles() {
    const ws = vscode.workspace.workspaceFolders?.[0];
    if (!ws) {
      this.postMessage({ type: "file-list", files: [] });
      this.postMessage({ type: "error", error: "No workspace folder open." });
      return;
    }
    const uris = await vscode.workspace.findFiles("**/*", FIND_EXCLUDES, 2000);
    const files = uris.map((u) => vscode.workspace.asRelativePath(u, false));
    const dirs = new Set<string>();
    for (const f of files) {
      const parts = f.split("/");
      for (let i = 1; i < parts.length; i++) dirs.add(parts.slice(0, i).join("/"));
    }
    const list: { path: string; type: "file" | "dir" }[] = [
      ...[...dirs].sort().map((d) => ({ path: d, type: "dir" as const })),
      ...files.sort().map((f) => ({ path: f, type: "file" as const })),
    ];
    this.postMessage({ type: "file-list", files: list });
  }

  private getSettings() {
    const cfg = vscode.workspace.getConfiguration("records");
    this.postMessage({
      type: "settings-values",
      endpoint: cfg.get<string>("ollamaEndpoint") || "",
      model: cfg.get<string>("ollamaModel") || "",
    });
  }

  private async saveSettings(endpoint: string, model: string) {
    try {
      const cfg = vscode.workspace.getConfiguration("records");
      await cfg.update("ollamaEndpoint", endpoint.trim(), vscode.ConfigurationTarget.Global);
      await cfg.update("ollamaModel", model.trim(), vscode.ConfigurationTarget.Global);
      this.postMessage({ type: "update-status", content: "Ollama settings saved." });
    } catch (e) {
      this.postMessage({ type: "error", error: `Failed to save settings: ${e}` });
    }
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

  private async appendOllamaTurn(
    text: string,
    contextFiles: string[] = [],
    contextDirs: string[] = []
  ) {
    const { file, ollama } = this.recording!;
    const { endpoint, model } = ollama!;
    this.postMessage({ type: "busy", content: `${model} is thinking…` });
    try {
      const result = await this.runCLI("ollama-reply", {
        file,
        endpoint,
        model,
        human: text,
        "context-file": contextFiles,
        "context-dir": contextDirs,
      });
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
    opts: Record<string, string | boolean | string[]>
  ): Promise<Record<string, unknown>> {
    const cfg = vscode.workspace.getConfiguration("records");
    const bin = cfg.get<string>("binaryPath") || "records";
    // CLI discovers the records dir from cwd — run it from the workspace, not the extension host
    const cwd = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;

    const args: string[] = [command];
    for (const [k, v] of Object.entries(opts)) {
      if (k === "arguments") {
        if (v) args.push(v as string);
      } else if (Array.isArray(v)) {
        for (const item of v) if (item) args.push(`--${k}`, item);
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
}
