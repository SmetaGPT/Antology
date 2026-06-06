import fs from 'node:fs';
import path from 'node:path';

const repoRoot = process.cwd();
const statePath = path.join(repoRoot, '.agent', 'state.json');

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function estimateFile(filePath) {
  const absolutePath = path.join(repoRoot, filePath);
  const content = fs.readFileSync(absolutePath, 'utf8');
  const chars = content.length;
  const lines = content.split('\n').length;
  const bytes = Buffer.byteLength(content, 'utf8');
  const estimatedTokens = Math.ceil(chars / 4);

  return { filePath, chars, lines, bytes, estimatedTokens };
}

function summarizeBundle(name, files) {
  const breakdown = files.map(estimateFile);
  const totals = breakdown.reduce(
    (acc, file) => {
      acc.chars += file.chars;
      acc.lines += file.lines;
      acc.bytes += file.bytes;
      acc.estimatedTokens += file.estimatedTokens;
      return acc;
    },
    { chars: 0, lines: 0, bytes: 0, estimatedTokens: 0 }
  );

  return { name, files, breakdown, totals };
}

const state = readJson(statePath);
const bundles = [
  { name: 'default', files: state.startup.defaultBundle },
  { name: 'snapshot-only', files: state.startup.bundles['snapshot-only'] },
  { name: 'hot-only', files: state.startup.bundles['hot-only'] },
  { name: 'full-state', files: state.startup.bundles['full-state'] },
  { name: 'release', files: state.startup.bundles.release },
  { name: 'architecture', files: state.startup.bundles.architecture }
].map((bundle) => summarizeBundle(bundle.name, bundle.files));

for (const bundle of bundles) {
  console.log(`Bundle: ${bundle.name}`);
  console.log(`  Files: ${bundle.files.join(', ')}`);
  console.log(`  Totals: ${bundle.totals.estimatedTokens} tokens est, ${bundle.totals.chars} chars, ${bundle.totals.lines} lines, ${bundle.totals.bytes} bytes`);
  for (const file of bundle.breakdown) {
    console.log(`    - ${file.filePath}: ${file.estimatedTokens} tokens est, ${file.lines} lines`);
  }
}

console.log('Paths:');
for (const [mode, bundle] of Object.entries(state.startup.paths ?? {})) {
  console.log(`  ${mode} -> ${bundle}`);
}
