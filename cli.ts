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
} from "fs";
import { spawn } from "child_process";

const DATA_DIR = process.env.BUNDO_DATA_DIR || join(homedir(), ".bun-do");
if (!existsSync(DATA_DIR)) mkdirSync(DATA_DIR, { recursive: true });
if (!process.env.BUNDO_DATA_DIR) process.env.BUNDO_DATA_DIR = DATA_DIR;

const PID_FILE = join(DATA_DIR, "bun-do.pid");
const LOG_FILE = join(DATA_DIR, "bun-do.log");

const args = process.argv.slice(2);

// --serve: internal flag — run server in foreground (used by background spawner)
if (args.includes("--serve")) {
  await import("./server.ts");
  // server.ts calls Bun.serve() which keeps the event loop alive — don't exit
}

// Parse command and --port
const command =
  args.find((a) => ["start", "stop", "restart", "status", "open"].includes(a)) ||
  "start";
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
  for (let i = 0; i < 40; i++) {
    try {
      await fetch(url);
      return true;
    } catch {
      await Bun.sleep(100);
    }
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

  const ready = await waitForReady();
  if (!ready) {
    console.log(`[bun-do] started (pid ${child.pid}) but not yet responding`);
  } else {
    console.log(`[bun-do] started (pid ${child.pid})`);
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
}
