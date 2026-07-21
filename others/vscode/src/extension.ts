import * as vscode from "vscode";
import { RecordsChatPanel } from "./panel";

export function activate(context: vscode.ExtensionContext) {
  let panel: RecordsChatPanel | undefined;

  const command = vscode.commands.registerCommand("records.openChat", () => {
    if (panel) {
      panel.reveal();
    } else {
      panel = new RecordsChatPanel(context.extensionUri);
      panel.onDisposed(() => {
        panel = undefined;
      });
    }
  });

  context.subscriptions.push(command);
}

export function deactivate() {}
