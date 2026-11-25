# Pointman Antigravity CLI client

A client extension for Google's [Antigravity CLI](https://antigravity.google/docs/cli) (`agy`).
Repository: `pointman-ai/pointman-antigravity`. Requires a Pointman node with the
`agy-stream` decoder, the update-manifest installer and `[client.sign_in] files`.

## Sign in once

Run `agy` once in a terminal on any machine and sign in with your Google account
(AI Pro or Ultra quota). On its terms screen, Tab moves to the buttons.

agy keeps that sign-in in `~/.gemini/antigravity-cli/antigravity-oauth-token`.
Before each run the node copies that one file, owner-only, into the agent's own
home, so one sign-in serves every agent on the machine. Nothing else from your
own `~/.gemini` is copied.

The node also seals that file in the workspace's vault for the machines the client is on,
and writes it into their homes, so one sign-in serves every machine. It's sealed again only
when its refresh token changes. To undo it, revoke `antigravity.signin` in the vault and sign
out on each machine: revoking alone leaves the copies already written.

Each run sets `SSH_CONNECTION`, so agy keeps refreshed sign-ins in that token file
and never writes to the OS keyring. Without it, a refresh on a Mac asks a keychain that
doesn't exist in the agent's home, and macOS shows a "Keychain Not Found" dialog.
Tools the agent runs inherit it, so they think they are in an SSH session too: one that
acts differently over SSH (opens no browser to sign in, skips a GUI prompt or the clipboard)
will do the same here. agy doesn't promise this check; if the dialog comes back after an
agy update, look for "Using file-based token storage" in a run's log.

A Gemini API key also works with agy, but only with `"modelProvider": "gemini"`
in its settings; this version doesn't set that up.

## Install and home

The node installs agy from Google's update manifest (sha-512 checked) and runs it
with `AGY_CLI_DISABLE_AUTO_UPDATE=true`, so the node alone decides its version.

Each agent gets its own `HOME`. Behaviours go to `<home>/.gemini/GEMINI.md` and the
node's MCP servers to `<home>/.gemini/config/mcp_config.json` under `mcpServers`
(`url` becomes agy's `serverUrl`).

## Runs

A wake is one headless run that exits when the turn ends:

```sh
agy -p <prompt> --output-format stream-json [--conversation <id>] \
  [--model <model>] --dangerously-skip-permissions [--add-dir <dir>]
```

- agy names its own conversations: the node keeps each one beside core's session
  id in `<home>/.gemini/pointman-sessions` and resumes it with `--conversation`.
- The stream is `init`, `step_update`s and a `result` (`tests/fixtures/native.jsonl`
  is a real agy 1.5.14 run that calls an MCP tool).
- Limit errors are spotted by their words (resource_exhausted, quota, rate limit,
  credits balance is too low, usage limit).

## Modes

| Pointman mode | agy | What it does |
|---|---|---|
| default | `--dangerously-skip-permissions` | Tools run without asking. |
| auto | `--dangerously-skip-permissions` | The same: a headless run can't stop to ask. |

**plan** and **acceptEdits** aren't supported: headless agy refuses every tool that
needs a review, the board's own tools too. (`--mode auto` isn't offered on every
account.)

## Tests

`python3 -m unittest discover tests` checks the manifest and the fixture offline.
