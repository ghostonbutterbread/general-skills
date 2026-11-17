// Run with node --experimental-vm-modules --no-warnings. No OMP or daemon is used.
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import * as childProcess from 'node:child_process';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { stripTypeScriptTypes } from 'node:module';
import { SourceTextModule, SyntheticModule } from 'node:vm';

const scratch = await fs.mkdtemp(join(tmpdir(), 'omp-receipt-test-'));
const previous = Object.fromEntries(['XDG_STATE_HOME', 'OMP_TEST_LOG', 'OMP_TEST_REAL_STDIO', 'OMP_TEST_BAD_CLOSE', 'OMP_TEST_CLOSE_DELAY', 'OMP_TEST_EXEC_DELAY'].map(key => [key, process.env[key]]));
const state = join(scratch, 'new', 'state');
const root = join(state, 'omp-research');
const synced = [];
let failPath;
let failIdentity = false;
let started = 0;
let syncsAtStart = [];
const wrappedFs = { ...fs, open: async (path, ...args) => {
  const handle = await fs.open(path, ...args);
  const sync = handle.sync.bind(handle);
  handle.sync = async () => {
    synced.push(String(path));
    if (String(path) === failPath || (failIdentity && String(path).endsWith('/receipts.jsonl'))) throw Error('injected fsync failure');
    return sync();
  };
  return handle;
} };
async function synthetic(namespace) {
  const names = Object.keys(namespace);
  return new SyntheticModule(names, function () { for (const name of names) this.setExport(name, namespace[name]); });
}
const wrappedChildProcess = { ...childProcess, spawn: (...args) => {
  const child = childProcess.spawn(...args);
  const write = child.stdin.write.bind(child.stdin);
  child.stdin.write = (chunk, ...rest) => {
    if (JSON.parse(String(chunk)).op === 'start') { syncsAtStart = [...synced]; started++; }
    return write(chunk, ...rest);
  };
  return child;
} };
const typebox = { Type: { Object: x => x, String: () => ({}), Integer: () => ({}), Optional: x => x } };
const sdk = { SessionManager: { inMemory: () => ({}) }, createAgentSession: async () => ({ session: {
  getActiveToolNames: () => ['research_container'], messages: [{ role: 'assistant', content: [{ type: 'text', text: 'fake' }], stopReason: 'stop' }],
  prompt: async () => {}, dispose: async () => {},
} }) };
async function loadTs(path) {
  const url = pathToFileURL(resolve(path)).href;
  const source = stripTypeScriptTypes(await fs.readFile(resolve(path), 'utf8'), { mode: 'transform' });
  return new SourceTextModule(source, { identifier: url, initializeImportMeta: meta => { meta.url = url; } });
}
const module = await loadTs('skills/safe-fetch/scripts/omp_research_extension.ts');
await module.link(async specifier => {
  if (specifier === 'node:fs/promises') return synthetic(wrappedFs);
  if (specifier === 'node:child_process') return synthetic(wrappedChildProcess);
  if (specifier === '@sinclair/typebox') return synthetic(typebox);
  if (specifier === '@oh-my-pi/pi-coding-agent') return synthetic(sdk);
  if (specifier === './omp_research_session') return loadTs('skills/safe-fetch/scripts/omp_research_session.ts');
  return synthetic(await import(specifier));
});
await module.evaluate();
let tool;
module.namespace.registerResearchTool({ registerTool: value => { tool = value; } }, {
  selectDaemon: async () => ({ socket: '/fake', id: 'fake-daemon' }),
  stdioScript: resolve('tests/fixtures/omp_research_stdio_fake.py'),
});
const invoke = () => tool.execute('id', { prompt: 'offline' }, undefined, undefined, { cwd: scratch, model: {}, modelRegistry: {} });
try {
  process.env.XDG_STATE_HOME = state;
  process.env.OMP_TEST_LOG = join(scratch, 'transport.log');
  for (const key of ['OMP_TEST_REAL_STDIO', 'OMP_TEST_BAD_CLOSE', 'OMP_TEST_CLOSE_DELAY', 'OMP_TEST_EXEC_DELAY']) delete process.env[key];
  // The actual user must be able to use an existing private root beneath a
  // search-only ancestor, without gaining read permission on that ancestor.
  const searchOnly = join(scratch, 'search-only');
  const existingState = searchOnly;
  await fs.mkdir(join(existingState, 'omp-research'), { recursive: true, mode: 0o700 });
  await fs.chmod(searchOnly, 0o100);
  try {
    await assert.rejects(fs.readdir(searchOnly), { code: 'EACCES' });
    process.env.XDG_STATE_HOME = existingState;
    const existing = await invoke();
    assert.equal((await fs.stat(existing.details.receiptDirectory)).mode & 0o077, 0);
    assert.equal(started, 1);
  } finally {
    await fs.chmod(searchOnly, 0o700);
  }
  started = 0;
  synced.length = 0;
  await fs.rm(process.env.OMP_TEST_LOG, { force: true });
  process.env.XDG_STATE_HOME = state;
  // A failed first-run ancestor sync fails before start; retry remains usable.
  failPath = scratch;
  await assert.rejects(invoke(), error => /Cannot sync research receipt directory/.test(error.message) && error.cause?.message === 'injected fsync failure');
  assert.equal(started, 0);
  assert.ok(synced.includes(scratch));
  failPath = undefined;
  // The task entry's required sync must also fail closed before transport start.
  failPath = root;
  await assert.rejects(invoke(), error => /Cannot sync research receipt directory/.test(error.message) && error.cause?.message === 'injected fsync failure');
  assert.equal(started, 0);
  failPath = undefined;
  await fs.chmod(root, 0o755);
  await assert.rejects(invoke(), /owned by the user and private/);
  assert.equal(started, 0);
  await fs.chmod(root, 0o700);
  failIdentity = true;
  await assert.rejects(invoke(), error => error.cause?.message === 'injected fsync failure');
  assert.equal(started, 0);
  // A retry uses existing directories; their older entries may remain unsynced.
  failIdentity = false;
  synced.length = 0;
  const result = await invoke();
  assert.equal(started, 1);
  assert.ok(syncsAtStart.includes(root), 'task parent not synced before start');
  assert.ok(!syncsAtStart.includes(scratch), 'retry must not require unrelated ancestors');
  const dir = result.details.receiptDirectory;
  const file = join(dir, 'receipts.jsonl');
  assert.ok(syncsAtStart.includes(dir), 'task directory not synced before start');
  assert.ok(syncsAtStart.includes(file), 'identity receipt not synced before start');
  assert.equal((await fs.stat(root)).mode & 0o077, 0);
  assert.equal((await fs.stat(dir)).mode & 0o077, 0);
  assert.equal((await fs.stat(file)).mode & 0o077, 0);
  const receipts = (await fs.readFile(file, 'utf8')).trim().split('\n').map(line => JSON.parse(line));
  assert.equal(receipts.length, 2);
  assert.equal(receipts[0].event, 'identity');
  assert.equal(receipts[0].container, 'research-task-offline-fixture');
  assert.match(receipts[0].daemon, /fake-daemon/);
  assert.equal(receipts[1].event, 'cleanup');
  // Also exercise an entirely fresh, successful first invocation.
  const freshState = join(scratch, 'another', 'state');
  process.env.XDG_STATE_HOME = freshState;
  synced.length = 0;
  const fresh = await invoke();
  assert.equal(started, 2);
  for (const path of [join(freshState, 'omp-research'), freshState, dirname(freshState), scratch]) {
    assert.ok(syncsAtStart.includes(path), `first-run directory not synced before start: ${path}`);
  }
  const freshFile = join(fresh.details.receiptDirectory, 'receipts.jsonl');
  assert.ok(syncsAtStart.includes(freshFile));
  assert.equal((await fs.stat(freshFile)).mode & 0o077, 0);
  assert.deepEqual((await fs.readFile(process.env.OMP_TEST_LOG, 'utf8')).trim().split('\n'), ['close', 'start', 'close', 'start', 'close']);
  console.log('OMP receipt durability fixture: PASS');
} finally {
  for (const [key, value] of Object.entries(previous)) {
    if (value === undefined) delete process.env[key]; else process.env[key] = value;
  }
  await fs.rm(scratch, { recursive: true, force: true });
}
