import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const repoRoot = process.cwd();
const agentDir = path.join(repoRoot, '.agent');
const statePath = path.join(agentDir, 'state.json');
const snapshotPath = path.join(agentDir, 'snapshot.md');

function fail(message) {
  console.error(`ERROR: ${message}`);
  process.exit(1);
}

function assert(condition, message) {
  if (!condition) {
    fail(message);
  }
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function rel(filePath) {
  return path.relative(repoRoot, filePath).replace(/\\/g, '/');
}

assert(fs.existsSync(statePath), `Missing ${rel(statePath)}`);
assert(fs.existsSync(snapshotPath), `Missing ${rel(snapshotPath)}`);

const state = readJson(statePath);
assert(Number.isInteger(state.schemaVersion), 'schemaVersion must be an integer');

const requiredProjectFields = ['name', 'objective', 'phase', 'lastUpdated', 'targets'];
for (const field of requiredProjectFields) {
  assert(state.project?.[field], `project.${field} is required`);
}

const requiredNowFields = ['task', 'owner', 'status', 'next', 'areas'];
for (const field of requiredNowFields) {
  assert(state.now?.[field], `now.${field} is required`);
}

assert(state.tasks && typeof state.tasks === 'object', 'tasks is required');
assert(Array.isArray(state.tasks.inProgress) && state.tasks.inProgress.length > 0, 'tasks.inProgress must not be empty');
assert(Array.isArray(state.tasks.next), 'tasks.next must be an array');
assert(Array.isArray(state.tasks.later), 'tasks.later must be an array');
assert(Array.isArray(state.blockers), 'blockers must be an array');
assert(Array.isArray(state.startup?.defaultBundle) && state.startup.defaultBundle.length > 0, 'startup.defaultBundle must not be empty');
assert(state.startup?.bundles?.['snapshot-only'], 'startup.bundles.snapshot-only is required');
assert(state.startup?.bundles?.['hot-only'], 'startup.bundles.hot-only is required');
assert(state.startup?.bundles?.['full-state'], 'startup.bundles.full-state is required');
assert(state.startup?.paths, 'startup.paths is required');

const taskIds = new Set();
for (const task of [...state.tasks.inProgress, ...state.tasks.next, ...state.tasks.later]) {
  assert(task.id && task.title && task.track, `Task is missing required fields: ${JSON.stringify(task)}`);
  assert(!taskIds.has(task.id), `Duplicate task id: ${task.id}`);
  taskIds.add(task.id);
}

const blockerIds = new Set();
for (const blocker of state.blockers) {
  assert(blocker.id && blocker.title && blocker.sev && blocker.next, `Blocker is missing required fields: ${JSON.stringify(blocker)}`);
  assert(!blockerIds.has(blocker.id), `Duplicate blocker id: ${blocker.id}`);
  blockerIds.add(blocker.id);
  assert(Array.isArray(blocker.ref) && blocker.ref.length > 0, `Blocker ${blocker.id} must include lookup references`);
}

assert(taskIds.has(state.now.task), `now.task must exist in tasks: ${state.now.task}`);

const canonicalEntries = Object.entries(state.canon ?? {});
assert(canonicalEntries.length > 0, 'canonicalFiles must not be empty');

for (const file of [...state.startup.defaultBundle, ...Object.values(state.startup.bundles), ...canonicalEntries.map(([, filePath]) => filePath)].flat()) {
  const absolutePath = path.join(repoRoot, file);
  assert(fs.existsSync(absolutePath), `Referenced file does not exist: ${file}`);
}

const syncResult = spawnSync(process.execPath, [path.join(repoRoot, 'scripts', 'agent', 'sync-snapshot.mjs')], {
  cwd: repoRoot,
  encoding: 'utf8'
});

assert(syncResult.status === 0, `Snapshot sync failed during validation:\n${syncResult.stderr || syncResult.stdout}`);

const snapshot = fs.readFileSync(snapshotPath, 'utf8');
assert(snapshot.includes(state.now.task), 'snapshot.md does not reflect now.task');
assert(snapshot.includes(state.now.next), 'snapshot.md does not reflect now.next');

console.log('Agent harness validation passed.');
