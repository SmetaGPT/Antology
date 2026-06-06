import fs from 'node:fs';
import path from 'node:path';

const repoRoot = process.cwd();
const statePath = path.join(repoRoot, '.agent', 'state.json');

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

const state = readJson(statePath);
const mode = process.argv[2] ?? 'cross-module';
const bundleName = state.startup.paths?.[mode];

if (!bundleName) {
  console.error(`Unknown startup mode: ${mode}`);
  process.exit(1);
}

const files = state.startup.bundles?.[bundleName];

if (!Array.isArray(files) || files.length === 0) {
  console.error(`Bundle is missing or empty: ${bundleName}`);
  process.exit(1);
}

console.log(`Mode: ${mode}`);
console.log(`Bundle: ${bundleName}`);
for (const file of files) {
  console.log(`- ${file}`);
}
