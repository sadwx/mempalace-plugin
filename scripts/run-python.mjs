#!/usr/bin/env node
/**
 * Cross-platform Python resolver.
 *
 * Finds the best available Python interpreter and spawns it with the
 * arguments passed to this script.  Used by .mcp.json and hooks so
 * the plugin works regardless of how Python is installed.
 *
 * Resolution order:
 *   1. uv  (runs: uv run python <args>)
 *   2. python3  (preferred on Unix — often missing on Windows)
 *   3. python   (preferred on Windows — often missing on modern Linux)
 */
import { spawn, execFileSync } from "node:child_process";
import process from "node:process";

const args = process.argv.slice(2);

function has(cmd) {
  try {
    execFileSync(process.platform === "win32" ? "where" : "which", [cmd], {
      stdio: "ignore",
    });
    return true;
  } catch {
    return false;
  }
}

function run(cmd, cmdArgs) {
  const child = spawn(cmd, cmdArgs, { stdio: "inherit" });
  child.on("error", (err) => {
    process.stderr.write(`run-python: ${err.message}\n`);
    process.exit(1);
  });
  child.on("close", (code) => process.exit(code ?? 1));
}

if (has("uv")) {
  run("uv", ["run", "python", ...args]);
} else if (has("python3")) {
  run("python3", args);
} else if (has("python")) {
  run("python", args);
} else {
  process.stderr.write(
    "ERROR: No Python interpreter found.\n" +
      "Install python3 or uv (https://docs.astral.sh/uv/).\n"
  );
  process.exit(1);
}
