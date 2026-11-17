import { existsSync } from 'node:fs';
import { spawn } from 'node:child_process';
import { homedir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const candidates = [
  process.env.PYTHON,
  join(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python'),
  join(homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'),
].filter(Boolean);
const python = candidates.find(path => existsSync(path)) ?? (process.platform === 'win32' ? 'python' : 'python3');
const mode = process.argv[2];
function run(args) {
  return new Promise((resolve, reject) => {
    const child = spawn(python, args, { cwd: root, stdio: 'inherit', windowsHide: true });
    child.on('error', reject);
    child.on('exit', (code, signal) => resolve(signal ? 130 : (code ?? 1)));
    const interrupt = () => child.kill('SIGINT');
    process.on('SIGINT', interrupt);
    child.on('close', () => process.off('SIGINT', interrupt));
  });
}
try {
  let code;
  const externalCommands = {
    '--external-fetch': 'lab/sportec_fetch.py',
    '--external-prepare': 'lab/sportec_adapter.py',
    '--external-train': 'lab/external_train.py',
    '--external-evaluate': 'lab/external_evaluate.py',
    '--external-gapfill': 'lab/external_calibrate.py',
    '--external-tune': 'lab/external_control_tune.py',
    '--external-validate': 'lab/external_validate.py',
  };
  if (mode in externalCommands) {
    code = await run([externalCommands[mode], ...process.argv.slice(3)]);
  } else if (mode === '--external-manifest') {
    code = await run(['lab/external_manifest.py']);
  } else if (mode === '--benchmark') {
    code = await run(['lab/synthetic_benchmark.py', ...process.argv.slice(3)]);
  } else if (mode === '--test') {
    code = await run(['-m', 'unittest', 'discover', '-s', 'lab', '-p', 'test_*.py', '-v']);
  } else if (mode === '--rebuild') {
    code = 0;
    for (const args of [
      ['lab/setup_data.py', process.env.MTAH_DOWNLOAD_DIR ?? join(homedir(), 'Downloads/hackathon-resources')],
      ['starter/baseline.py'], ['lab/build.py'],
      ['evaluation/validate_submission.py', 'evaluation/results/experimental_temporal.csv'],
      ['evaluation/validate_submission.py', 'evaluation/results/experimental_control_v2.csv'],
      ['evaluation/validate_submission.py', 'evaluation/results/experimental_control_v5.csv'],
      ['evaluation/validate_submission.py', 'evaluation/results/baseline_smooth50.csv'],
    ]) {
      code = await run(args);
      if (code !== 0) break;
    }
  } else {
    if (!existsSync(join(root, '.local/summary.json'))) throw new Error('Run npm run rebuild-data first.');
    if (!existsSync(join(root, 'ui/dist/interface/browser/index.html'))) throw new Error('Run npm run build first.');
    code = await run(['-u', 'lab/server.py', ...process.argv.slice(2)]);
  }
  process.exitCode = code;
} catch (error) {
  console.error(error.message);
  console.error('Install Python and the dependencies in requirements-lab.txt, or set PYTHON to your Python executable.');
  process.exitCode = 1;
}
