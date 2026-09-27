// SPDX-FileCopyrightText: 2026 tb4
// SPDX-License-Identifier: AGPL-3.0-or-later

// Single source of truth for slash commands: dispatch in chatViewProvider, autocomplete in the webview.
export interface CommandSpec {
  name: string;
  args: string;
  description: string;
}

export const COMMANDS: CommandSpec[] = [
  { name: "record", args: "[#tag] [title]", description: "Start recording (two-sided when Ollama is configured)" },
  { name: "all", args: "[#tag] [title]", description: "Start user-only recording" },
  { name: "me", args: "[#tag] [title]", description: "Start draft recording (kept off the site)" },
  { name: "esc", args: "", description: "Stop recording" },
  { name: "stick", args: "<slug>", description: "Feature a record" },
  { name: "gc", args: "[message]", description: "Commit" },
  { name: "gcp", args: "[message]", description: "Commit and push" },
  { name: "cpd", args: "[message]", description: "Commit, push, deploy" },
  { name: "myname", args: "[name]", description: "Save your name locally" },
  { name: "mucke", args: "", description: "Stamp the now-playing track" },
  { name: "airtime", args: "", description: "Human vs Assistant token share" },
  { name: "config", args: "", description: "Show the resolved records directory" },
  { name: "watch", args: "", description: "Start records watch in the background" },
  { name: "watchstop", args: "", description: "Stop records watch" },
];
