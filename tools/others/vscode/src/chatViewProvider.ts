// SPDX-FileCopyrightText: 2026 tb4
// SPDX-License-Identifier: AGPL-3.0-or-later

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
    | "settings-values"
    | "focus-input"
    | "stream-token"
    | "watch-status";
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
  private chatHistory: { role: "user" | "assistant"; content: string }[] = [];
  private pendingFocus = false;
  // hundehus 3: the dog's editor half. `records watch` writes no state file, so status comes from
  // parsing the --json events of the watch process this provider itself spawns — watch.py untouched.
  private watchProc: child_process.ChildProcessWithoutNullStreams | undefined;
  private watchBuf = "";

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
      this.watchProc?.kill();
      this.watchProc = undefined;
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
        if (this.pendingFocus) {
          this.pendingFocus = false;
          this.postMessage({ type: "focus-input" });
        }
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
    } else if (this.ollamaConfig()?.model) {
      await this.ephemeralChat(text, files, dirs);
    } else {
      this.postMessage({
        type: "update-status",
        content:
          "No recording — /record to start, or set an Ollama model (⚙) to chat without recording.",
      });
    }
  }

  private streamEnabled(): boolean {
    return vscode.workspace.getConfiguration("records").get<boolean>("stream") || false;
  }

  private async ephemeralChat(text: string, contextFiles: string[], contextDirs: string[]) {
    const { endpoint, model } = this.ollamaConfig()!;
    this.postMessage({ type: "busy", content: `${model} is thinking… (not recorded)` });
    try {
      const opts = {
        endpoint,
        model,
        human: text,
        history: "-",
        "context-file": contextFiles,
        "context-dir": contextDirs,
      };
      const result = this.streamEnabled()
        ? await this.runCLIStream(
            "ollama-chat",
            { ...opts, stream: true },
            (token) => this.postMessage({ type: "stream-token", content: token }),
            JSON.stringify(this.chatHistory)
          )
        : await this.runCLI("ollama-chat", opts, JSON.stringify(this.chatHistory));
      const reply = result.reply as string;
      this.chatHistory.push({ role: "user", content: text }, { role: "assistant", content: reply });
      this.postMessage({ type: "response", content: reply });
    } catch (e) {
      this.postMessage({
        type: "error",
        error: `Ollama failed — nothing recorded. (${e instanceof Error ? e.message : e})`,
      });
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
        this.chatHistory = [];
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
      case "airtime":
        await this.airtime();
        break;
      case "config":
        await this.config();
        break;
      case "watch":
        this.watchStart();
        break;
      case "watchstop":
        this.watchStop();
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
      this.chatHistory = [];
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
      const opts = {
        file,
        endpoint,
        model,
        human: text,
        "context-file": contextFiles,
        "context-dir": contextDirs,
      };
      const result = this.streamEnabled()
        ? await this.runCLIStream("ollama-reply", { ...opts, stream: true }, (token) =>
            this.postMessage({ type: "stream-token", content: token })
          )
        : await this.runCLI("ollama-reply", opts);
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

  private async airtime() {
    try {
      // the active recording's file, else the memory-only chat (empty → "Human: 0%, Assistant: 0%")
      const result = this.recording
        ? await this.runCLI("airtime", { file: this.recording.file })
        : await this.runCLI("airtime", { history: "-" }, JSON.stringify(this.chatHistory));
      this.postMessage({ type: "output", content: String(result.line) });
    } catch (e) {
      this.postMessage({ type: "error", error: `Airtime failed: ${e}` });
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

  focusInput() {
    if (this.view) {
      this.postMessage({ type: "focus-input" });
    } else {
      // view not resolved yet — flushed when the webview posts "ready"
      this.pendingFocus = true;
    }
  }

  private cliBin(): string {
    return vscode.workspace.getConfiguration("records").get<string>("binaryPath") || "records";
  }

  // CLI discovers the records dir from cwd — run it from the workspace, not the extension host.
  private cliCwd(): string | undefined {
    return vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
  }

  private buildArgs(command: string, opts: Record<string, string | boolean | string[]>): string[] {
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
    return args;
  }

  private async runCLI(
    command: string,
    opts: Record<string, string | boolean | string[]>,
    stdinData?: string
  ): Promise<Record<string, unknown>> {
    const bin = this.cliBin();
    const cwd = this.cliCwd();
    const args = this.buildArgs(command, opts);

    return new Promise((resolve, reject) => {
      const child = child_process.execFile(bin, args, { encoding: "utf-8", cwd }, (err, stdout) => {
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
      if (stdinData !== undefined) {
        child.stdin?.write(stdinData);
        child.stdin?.end();
      }
    });
  }

  // Streaming twin of runCLI(): `command` is expected to emit NDJSON on stdout — one
  // {"token": "…"} object per chunk, then one final object shaped like the non-streaming reply
  // (the postkasse 2 cli.py contract, reported but not yet applied — see the road's notes).
  // onToken fires per chunk; the returned promise resolves with the same shape runCLI() would
  // have resolved with, or rejects the same way, so callers don't need to know which path ran.
  private async runCLIStream(
    command: string,
    opts: Record<string, string | boolean | string[]>,
    onToken: (token: string) => void,
    stdinData?: string
  ): Promise<Record<string, unknown>> {
    const bin = this.cliBin();
    const cwd = this.cliCwd();
    const args = this.buildArgs(command, opts);

    return new Promise((resolve, reject) => {
      const child = child_process.spawn(bin, args, { cwd });
      let buf = "";
      let finalObj: Record<string, unknown> | undefined;
      let errMsg: string | undefined;
      let stderrText = "";

      child.stdout.setEncoding("utf-8");
      child.stdout.on("data", (chunk: string) => {
        buf += chunk;
        const lines = buf.split("\n");
        buf = lines.pop() ?? "";
        for (const line of lines) {
          if (!line) continue;
          try {
            const obj = JSON.parse(line);
            if (typeof obj?.token === "string") {
              onToken(obj.token);
            } else if (typeof obj?.error === "string") {
              errMsg = obj.error;
            } else {
              finalObj = obj;
            }
          } catch {
            // NDJSON is the contract — a non-JSON line here means a bug upstream, not user input
          }
        }
      });
      child.stderr.setEncoding("utf-8");
      child.stderr.on("data", (chunk: string) => {
        stderrText += chunk;
      });
      child.on("error", (err) => reject(err));
      child.on("close", (code) => {
        if (errMsg) {
          reject(new Error(errMsg));
        } else if (finalObj) {
          resolve(finalObj);
        } else if (code !== 0) {
          reject(new Error(stderrText.trim() || `records ${command} exited ${code}`));
        } else {
          reject(new Error(`no result from records ${command}`));
        }
      });

      if (stdinData !== undefined) {
        child.stdin.write(stdinData);
        child.stdin.end();
      }
    });
  }

  // hundehus 3: start/stop `records watch --json` ourselves and read its events — recordkit's
  // watch.py itself is untouched and stays state-file-free; this is purely a reader of its stdout.
  private watchStart() {
    if (this.watchProc) {
      this.postMessage({ type: "output", content: "records watch is already running." });
      return;
    }
    const child = child_process.spawn(this.cliBin(), ["watch", "--json"], { cwd: this.cliCwd() });
    this.watchProc = child;
    this.watchBuf = "";
    this.postWatchStatus("running — no build yet");

    child.stdout.setEncoding("utf-8");
    child.stdout.on("data", (chunk: string) => {
      this.watchBuf += chunk;
      const lines = this.watchBuf.split("\n");
      this.watchBuf = lines.pop() ?? "";
      for (const line of lines) {
        if (!line) continue;
        try {
          this.handleWatchEvent(JSON.parse(line));
        } catch {
          // not a JSON line — ignore
        }
      }
    });
    child.on("exit", () => {
      this.watchProc = undefined;
      this.postWatchStatus("not running");
    });
    child.on("error", () => {
      this.watchProc = undefined;
      this.postWatchStatus("failed to start — is the recordkit CLI installed?");
    });
  }

  private watchStop() {
    if (!this.watchProc) {
      this.postMessage({ type: "output", content: "records watch is not running." });
      return;
    }
    this.watchProc.kill();
    this.watchProc = undefined;
    this.postWatchStatus("not running");
  }

  private handleWatchEvent(event: Record<string, unknown>) {
    if (event.event === "missing") {
      this.postWatchStatus(`running — ${event.message}`);
      return;
    }
    const ok = event.ok as boolean;
    const time = event.time as string;
    this.postWatchStatus(`running — ${ok ? "last build ok" : "last build FAILED"} (${time})`);
  }

  private postWatchStatus(content: string) {
    this.postMessage({ type: "watch-status", content: `records watch: ${content}` });
  }

  private postMessage(message: MessageToView) {
    this.view?.webview.postMessage(message);
  }
}
