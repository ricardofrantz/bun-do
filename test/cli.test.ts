import { afterAll, describe, expect, test } from "bun:test";
import { existsSync, mkdtempSync, readFileSync, rmSync } from "fs";
import { tmpdir } from "os";
import { join } from "path";
import { freePort, ROOT } from "./helpers";

const dataDir = mkdtempSync(join(tmpdir(), "bun-do-cli-"));
const port = freePort();

function cli(...args: string[]): { code: number; out: string } {
  const res = Bun.spawnSync(["bun", join(ROOT, "cli.ts"), ...args], {
    env: { ...process.env, BUNDO_DATA_DIR: dataDir },
  });
  return { code: res.exitCode, out: res.stdout.toString() + res.stderr.toString() };
}

afterAll(() => {
  cli("stop");
  rmSync(dataDir, { recursive: true, force: true });
});

describe("cli", () => {
  test("--version prints the package version", () => {
    const pkg = JSON.parse(readFileSync(join(ROOT, "package.json"), "utf-8"));
    expect(cli("--version").out.trim()).toBe(pkg.version);
  });

  test("start, status and stop manage one background server", async () => {
    const started = cli("start", `--port=${port}`);
    expect(started.out).toContain("started");
    expect(existsSync(join(dataDir, "bun-do.pid"))).toBe(true);

    const res = await fetch(`http://127.0.0.1:${port}/api/tasks`);
    expect(res.status).toBe(200);

    expect(cli("start", `--port=${port}`).out).toContain("already running");
    expect(cli("status").out).toContain("running (pid");

    expect(cli("stop").out).toContain("stopped");
    expect(existsSync(join(dataDir, "bun-do.pid"))).toBe(false);
    expect(cli("status").out).toContain("not running");
  });
});
