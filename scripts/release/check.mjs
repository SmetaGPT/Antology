import { execSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import path from 'node:path';

const repoRoot = process.cwd();

function resolveNpmCommand() {
  return process.platform === 'win32' ? 'npm.cmd' : 'npm';
}

function resolvePythonCommand() {
  const candidates = process.platform === 'win32'
    ? [
        path.join(repoRoot, 'backend', '.venv', 'Scripts', 'python.exe'),
        'python',
      ]
    : [
        path.join(repoRoot, 'backend', '.venv', 'bin', 'python'),
        'python3',
        'python',
      ];

  return candidates.find((candidate) => candidate.includes(path.sep) ? existsSync(candidate) : true);
}

function quoteIfNeeded(value) {
  return value.includes(' ') ? `"${value}"` : value;
}

const npmCommand = resolveNpmCommand();
const pythonCommand = resolvePythonCommand();

if (!pythonCommand) {
  console.error('Unable to resolve a Python interpreter for backend checks.');
  process.exit(1);
}

const commands = [
  `${quoteIfNeeded(npmCommand)} run agent:check`,
  `${quoteIfNeeded(npmCommand)} run typecheck`,
  `${quoteIfNeeded(npmCommand)} run build`,
  `${quoteIfNeeded(pythonCommand)} -m pytest backend/tests`,
];

for (const command of commands) {
  execSync(command, {
    cwd: repoRoot,
    stdio: 'inherit',
  });
}