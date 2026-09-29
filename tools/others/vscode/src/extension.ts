// SPDX-FileCopyrightText: 2026 tb4
// SPDX-License-Identifier: AGPL-3.0-or-later

import * as vscode from "vscode";
import { ChatViewProvider } from "./chatViewProvider";
import { RecordsTreeProvider } from "./recordsTree";

// Extensions may contribute to the secondary side bar from VS Code 1.106 on.
function supportsSecondarySidebar(): boolean {
  const [major, minor] = vscode.version.split(".").map(Number);
  return major > 1 || (major === 1 && minor >= 106);
}

export function activate(context: vscode.ExtensionContext) {
  const secondary = supportsSecondarySidebar();
  if (!secondary) {
    void vscode.commands.executeCommand("setContext", "records.doesNotSupportSecondarySidebar", true);
  }

  const provider = new ChatViewProvider(context.extensionUri);
  const records = new RecordsTreeProvider(() => provider.recordsDir());
  const chatView = secondary ? ChatViewProvider.secondaryViewType : ChatViewProvider.viewType;

  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider(chatView, provider, {
      webviewOptions: { retainContextWhenHidden: true },
    }),
    records,
    vscode.window.registerTreeDataProvider(RecordsTreeProvider.viewType, records),
    vscode.commands.registerCommand("records.refreshList", () => records.refresh()),
    vscode.commands.registerCommand("records.openChat", async () => {
      await vscode.commands.executeCommand(`${chatView}.focus`);
      provider.focusInput();
    }),
    vscode.workspace.onDidChangeConfiguration((e) => {
      if (e.affectsConfiguration("records.binaryPath")) records.refresh();
    })
  );
}

export function deactivate() {}
