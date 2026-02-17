#!/usr/bin/env bun
// bun-do CLI entry point — run with: bunx bun-do
import { join } from "path";
import { homedir } from "os";

// Default data dir to ~/.bun-do when not set (matches bin/bun-do behavior)
if (!process.env.BUNDO_DATA_DIR) {
  process.env.BUNDO_DATA_DIR = join(homedir(), ".bun-do");
}

import "./server.ts";
