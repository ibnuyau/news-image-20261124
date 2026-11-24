// Entry point for the make.fun news-image-20261124 entry.
//
// The front page itself is drawn by gen.py into entry.png. All this
// program does is place that file where the harness expects it: it reads
// MAKEFUN_OUTPUT_DIR, makes the directory if needed, copies entry.png
// there, and checks the copy landed with the right size. When the
// variable is missing it complains on stderr and exits non-zero.

import { copyFileSync, existsSync, mkdirSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ENTRY_NAME = "entry.png";
const OUTPUT_ENV = "MAKEFUN_OUTPUT_DIR";

function die(message: string): never {
  console.error(`news-image-20261124: ${message}`);
  process.exit(1);
}

function scriptDir(): string {
  return dirname(fileURLToPath(import.meta.url));
}

function outputDir(): string {
  const found = process.env[OUTPUT_ENV];
  if (!found) {
    die(`${OUTPUT_ENV} is not set`);
  }
  return found;
}

function placeEntry(): void {
  const source = join(scriptDir(), ENTRY_NAME);
  if (!existsSync(source)) {
    die(`cannot find ${ENTRY_NAME} next to main.ts`);
  }
  const targetDir = outputDir();
  mkdirSync(targetDir, { recursive: true });
  const target = join(targetDir, ENTRY_NAME);
  copyFileSync(source, target);
  const want = statSync(source).size;
  const got = statSync(target).size;
  if (want !== got) {
    die(`copy of ${ENTRY_NAME} is ${got} bytes, expected ${want}`);
  }
  console.log(`${ENTRY_NAME} copied to ${target} (${got} bytes)`);
}

placeEntry();
