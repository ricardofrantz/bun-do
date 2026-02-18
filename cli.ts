#!/usr/bin/env bun
// bun-do CLI — service manager + server entry point
import { join } from "path";
import { homedir } from "os";
import {
  existsSync,
  readFileSync,
  writeFileSync,
  unlinkSync,
  mkdirSync,
  openSync,
  copyFileSync,
} from "fs";
import { spawn } from "child_process";
import { createConnection } from "net";

const DATA_DIR = process.env.BUNDO_DATA_DIR || join(homedir(), ".bun-do");
if (!existsSync(DATA_DIR)) mkdirSync(DATA_DIR, { recursive: true });
if (!process.env.BUNDO_DATA_DIR) process.env.BUNDO_DATA_DIR = DATA_DIR;

const PID_FILE = join(DATA_DIR, "bun-do.pid");
const LOG_FILE = join(DATA_DIR, "bun-do.log");

const args = process.argv.slice(2);

// --version / -v: print version from package.json and exit
if (args.includes("--version") || args.includes("-v")) {
  const pkg = JSON.parse(readFileSync(join(import.meta.dir, "package.json"), "utf-8"));
  console.log(pkg.version);
  process.exit(0);
}

// --serve: internal flag — run server in foreground (used by background spawner)
// Must be checked before service manager code — execution must not fall through.
if (args.includes("--serve")) {
  await import("./server.ts");
  // server.ts calls Bun.serve() which keeps the event loop alive
} else {
// Parse command and --port
const command =
  args.find((a) =>
    ["start", "stop", "restart", "status", "open", "install-skill"].includes(a)
  ) || "start";
const portArgs = args.filter((a) => a.startsWith("--port="));
const port = portArgs[0]?.split("=")[1] || "8000";
const url = `http://localhost:${port}`;

function getPid(): number | null {
  if (!existsSync(PID_FILE)) return null;
  const pid = parseInt(readFileSync(PID_FILE, "utf-8").trim());
  return isNaN(pid) ? null : pid;
}

function isRunning(pid: number): boolean {
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}

async function waitForReady(): Promise<boolean> {
  const portNum = parseInt(port);
  for (let i = 0; i < 40; i++) {
    const up = await new Promise<boolean>((resolve) => {
      const s = createConnection({ host: "127.0.0.1", port: portNum });
      s.once("connect", () => { s.destroy(); resolve(true); });
      s.once("error", () => resolve(false));
    });
    if (up) return true;
    await Bun.sleep(100);
  }
  return false;
}

function stop(): boolean {
  const pid = getPid();
  if (pid && isRunning(pid)) {
    process.kill(pid, "SIGTERM");
    const deadline = Date.now() + 3000;
    while (Date.now() < deadline && isRunning(pid)) {
      Bun.sleepSync(100);
    }
    if (isRunning(pid)) process.kill(pid, "SIGKILL");
    try { unlinkSync(PID_FILE); } catch {}
    console.log(`[bun-do] stopped (pid ${pid})`);
    return true;
  }
  try { unlinkSync(PID_FILE); } catch {}
  console.log("[bun-do] not running");
  return false;
}

async function start(): Promise<boolean> {
  const pid = getPid();
  if (pid && isRunning(pid)) {
    console.log(`[bun-do] already running (pid ${pid})`);
    return true;
  }

  const logFd = openSync(LOG_FILE, "a");
  const child = spawn("bun", [import.meta.filename, "--serve", ...portArgs], {
    detached: true,
    stdio: ["ignore", logFd, logFd],
    env: { ...process.env, BUNDO_DATA_DIR: DATA_DIR },
  });
  child.unref();

  writeFileSync(PID_FILE, String(child.pid));

  const pkg = JSON.parse(readFileSync(join(import.meta.dir, "package.json"), "utf-8"));
  const ready = await waitForReady();
  if (!ready) {
    console.log(`[bun-do] v${pkg.version} started (pid ${child.pid}) but not yet responding`);
  } else {
    console.log(`[bun-do] v${pkg.version} started (pid ${child.pid})`);
  }
  console.log(`[bun-do] ${url}`);
  console.log(`[bun-do] log: ${LOG_FILE}`);
  return ready;
}

function status() {
  const pid = getPid();
  if (pid && isRunning(pid)) {
    console.log(`[bun-do] running (pid ${pid})`);
  } else {
    try { unlinkSync(PID_FILE); } catch {}
    console.log("[bun-do] not running");
  }
}

function openBrowser() {
  const cmd = process.platform === "darwin" ? "open" : "xdg-open";
  spawn(cmd, [url], { detached: true, stdio: "ignore" }).unref();
}

function installSkill() {
  const src = join(import.meta.dir, "skill", "SKILL.md");
  const destDir = join(homedir(), ".claude", "skills", "bun-do-api");
  const dest = join(destDir, "SKILL.md");
  if (!existsSync(src)) {
    console.log("[bun-do] skill/SKILL.md not found in package");
    process.exit(1);
  }
  mkdirSync(destDir, { recursive: true });
  copyFileSync(src, dest);
  console.log(`[bun-do] skill installed → ${dest}`);
  console.log("[bun-do] reload Claude Code to activate (or start a new session)");
}

switch (command) {
  case "start":
    await start();
    break;
  case "stop":
    stop();
    break;
  case "restart":
    stop();
    await start();
    break;
  case "status":
    status();
    break;
  case "open":
    await start();
    openBrowser();
    break;
  case "install-skill":
    installSkill();
    break;
}
} // end else (service manager)
