// Entry point for the make.fun news-image-20261124 entry.
// The front page is drawn by gen.py into entry.png; this program copies
// that file into the output directory the harness gives it through
// MAKEFUN_OUTPUT_DIR, so both runs write the same bytes.

import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const outDir = process.env.MAKEFUN_OUTPUT_DIR;
if (!outDir) {
  console.error("MAKEFUN_OUTPUT_DIR is not set");
  process.exit(1);
}

const here = dirname(fileURLToPath(import.meta.url));
mkdirSync(outDir, { recursive: true });
const dest = join(outDir, "entry.png");
copyFileSync(join(here, "entry.png"), dest);
console.log("entry.png copied to " + dest);
