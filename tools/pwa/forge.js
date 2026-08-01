// Forgejo/Gitea contents API. One adapter, one forge — Codeberg is the canonical
// host and the only one this has been tested against.
//
// GitHub's API is shaped almost identically (PUT with sha, base64 body) and its
// CORS is open, so an adapter would be short. It is deliberately not here: the
// project does not ship provider support it has not exercised.

// btoa() works on latin1 code points, so UTF-8 has to be flattened to bytes
// first or every non-ASCII character in a record comes back corrupted.
export function toBase64(text) {
  const bytes = new TextEncoder().encode(text);
  let binary = "";
  for (let i = 0; i < bytes.length; i += 0x8000) {
    binary += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
  }
  return btoa(binary);
}

export function fromBase64(encoded) {
  const binary = atob(String(encoded).replace(/\s+/g, ""));
  const bytes = Uint8Array.from(binary, (c) => c.charCodeAt(0));
  return new TextDecoder().decode(bytes);
}

export class ForgeError extends Error {
  constructor(message, { status = 0, blocked = false } = {}) {
    super(message);
    this.status = status;
    this.blocked = blocked;
  }
}

export function forgejo({ url, owner, repo, branch = "main", token }) {
  const root = String(url).replace(/\/+$/, "");
  const base = `${root}/api/v1/repos/${owner}/${repo}/contents`;
  const auth = { Authorization: `token ${token}`, "Content-Type": "application/json" };

  async function call(method, path, body) {
    const target = `${base}/${path.split("/").map(encodeURIComponent).join("/")}`;
    let response;
    try {
      response = await fetch(target, {
        method,
        headers: auth,
        body: body === undefined ? undefined : JSON.stringify(body),
      });
    } catch (e) {
      // fetch rejects without a response for both a blocked preflight and a
      // dead connection, and the two need different advice.
      throw new ForgeError(
        navigator.onLine
          ? `${root} refused the request from this page. Forgejo ships CORS off; ` +
            `an admin enables it with [cors] ENABLED = true in app.ini. ` +
            `Codeberg has it on already.`
          : "Offline — queued until the connection is back.",
        { blocked: navigator.onLine },
      );
    }
    if (response.status === 404) return null;
    if (!response.ok) {
      let detail = "";
      try {
        detail = (await response.json()).message || "";
      } catch { /* a non-JSON error body is still an error */ }
      throw new ForgeError(
        `${method} ${path} → ${response.status}${detail ? ` (${detail})` : ""}`,
        { status: response.status },
      );
    }
    return response.status === 204 ? null : response.json();
  }

  return {
    // null when the file is not there yet — the signal to create rather than update.
    async read(path) {
      const found = await call("GET", `${path}?ref=${encodeURIComponent(branch)}`);
      return found && { sha: found.sha, text: fromBase64(found.content) };
    },

    // sha absent = create (POST), present = update (PUT). Returns the new sha,
    // so a series of appends never has to re-read the file.
    async write(path, text, message, sha) {
      const body = { content: toBase64(text), message, branch };
      if (sha) body.sha = sha;
      const result = await call(sha ? "PUT" : "POST", path, body);
      return result?.content?.sha;
    },

    // Cheap credential check for the settings panel.
    async check() {
      const target = `${root}/api/v1/repos/${owner}/${repo}`;
      const response = await fetch(target, { headers: auth });
      if (!response.ok) throw new ForgeError(`${owner}/${repo} → ${response.status}`, { status: response.status });
      const repoInfo = await response.json();
      if (!repoInfo.permissions?.push) {
        throw new ForgeError("That token can read this repo but not write to it.");
      }
      return repoInfo.full_name;
    },
  };
}
