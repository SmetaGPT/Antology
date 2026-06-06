import fs from 'node:fs';
import path from 'node:path';

const repoRoot = process.cwd();
const statePath = path.join(repoRoot, '.agent', 'state.json');
const snapshotPath = path.join(repoRoot, '.agent', 'snapshot.md');

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function rel(filePath) {
  return path.relative(repoRoot, filePath).replace(/\\/g, '/');
}

function renderList(items, mapper) {
  if (!items.length) {
    return ['- none'];
  }

  return items.map((item) => `- ${mapper(item)}`);
}

function renderSnapshot(state) {
  const generatedAt = new Date().toISOString();
  const defaultBundle = state.startup.defaultBundle;
  const pathMap = state.startup.paths ?? {};
  const inProgress = state.tasks.inProgress ?? [];
  const nextTasks = state.tasks.next ?? [];
  const laterTasks = state.tasks.later ?? [];

  return [
    '<!-- generated: run npm run agent:sync -->',
    `<!-- source: ${rel(statePath)} -->`,
    `<!-- generatedAt: ${generatedAt} -->`,
    '',
    '# Agent Startup',
    '',
    `- Goal: ${state.project.objective}`,
    `- Phase: \`${state.project.phase}\``,
    `- Default: ${defaultBundle.map((item) => `\`${item}\``).join(' -> ')}`,
    '',
    '## Now',
    ...renderList(inProgress, (task) => `[\`${task.id}\`] ${task.title} (${task.track})`),
    `- Owner: \`${state.now.owner}\``,
    `- Status: \`${state.now.status}\``,
    `- Next: ${state.now.next}`,
    `- Areas: ${state.now.areas.map((area) => `\`${area}\``).join(', ')}`,
    '',
    '## Next',
    ...renderList(nextTasks, (task) => `[\`${task.id}\`] ${task.title} (${task.track})`),
    '',
    '## Later',
    ...renderList(laterTasks, (task) => `[\`${task.id}\`] ${task.title} (${task.track})`),
    '',
    '## Blockers',
    ...renderList(state.blockers, (blocker) => `[\`${blocker.id}\`] ${blocker.title} (${blocker.sev}) -> ${blocker.next}`),
    '',
    '## Canonical',
    `- Now: \`${state.canon.now}\``,
    `- Remaining: \`${state.canon.remaining}\``,
    `- Release: \`${state.canon.release}\``,
    `- Decisions: \`${state.canon.decisions}\``,
    '',
    '## Paths',
    ...Object.entries(pathMap).map(([mode, bundle]) => `- \`${mode}\` -> \`${bundle}\``)
  ].join('\n');
}

const state = readJson(statePath);
const snapshot = renderSnapshot(state);

fs.mkdirSync(path.dirname(snapshotPath), { recursive: true });
fs.writeFileSync(snapshotPath, `${snapshot}\n`, 'utf8');

console.log(`Snapshot synchronized: ${rel(snapshotPath)}`);
