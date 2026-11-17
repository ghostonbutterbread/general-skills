import { createAgentSession, SessionManager } from '@oh-my-pi/pi-coding-agent';
import { createMockModel } from '@oh-my-pi/pi-ai/providers/mock';
import { readFileSync, writeFileSync, readdirSync, statSync } from 'node:fs';
import fixtureExtension from './omp_research_entry_extension';

export default async function () {
  const root = process.cwd();
  const log = root + '/entry-events.log';
  process.env.OMP_TEST_LOG = log;
  process.env.OMP_TEST_REAL_STDIO = root + '/shared_research_stdio.py';
  writeFileSync(log, '');
  // Exercise loading the production extension by path, not just the test wrapper.
  const pathModel = createMockModel({ responses: [] });
  const pathSession = await createAgentSession({ cwd: root, model: pathModel.model,
    sessionManager: SessionManager.inMemory(), disableExtensionDiscovery: true,
    preloadedExtensionPaths: [root + '/skills/safe-fetch/scripts/omp_research_extension.ts'],
    enableMCP: false, enableLsp: false, enableIrc: false, skipPythonPreflight: true,
    cacheWarming: false, skills: [], rules: [], contextFiles: [], noContextFiles: true,
    promptTemplates: [], slashCommands: [], bindProcessState: false, disableModelFallback: true });
  if (!pathSession.session.getActiveToolNames().includes('research_task')) throw Error('production extension did not register by path');
  await pathSession.session.dispose();
  let parent: any;
  let childMock: any;
  let mode = 'normal';
  let inherited = 0;
  (globalThis as any).__researchFixture = {
    selectDaemon: async () => ({ socket: '/fake/docker.sock', id: 'offline-daemon' }),
    stdioScript: root + '/tests/fixtures/omp_research_entry_fake.py',
    configureSession: (session: any) => {
      if (session.model !== parent.model || session.modelRegistry !== parent.modelRegistry) throw Error('model/registry mismatch');
      inherited++;
      const calls = mode === 'normal' ? [
        { content: [{ type: 'toolCall', id: 'b', name: 'bash', arguments: { command: 'forbidden' } }] },
        { content: [{ type: 'toolCall', id: 'r', name: 'read', arguments: { path: '/etc/passwd' } }] },
        { content: [{ type: 'toolCall', id: 't', name: 'task', arguments: { prompt: 'forbidden' } }] },
        { content: [{ type: 'toolCall', id: 'cross', name: 'research_container', arguments: { command: 'wrong task', container: (() => { const first = readFileSync(log, 'utf8').trim().split('\n')[0]; return first ? JSON.parse(first).name : 'research-task-other'; })() } }] },
        { content: [{ type: 'toolCall', id: 'x', name: 'research_container', arguments: { command: 'evidence' } }] },
        { content: [{ type: 'text', text: 'untrusted result' }] },
      ] : [
        { content: [{ type: 'toolCall', id: 'x', name: 'research_container', arguments: { command: mode === 'abort' ? 'slow' : 'evidence' } }] },
        { content: [{ type: 'text', text: 'result' }] },
      ];
      childMock = createMockModel({ responses: calls });
      session.agent.streamFn = childMock.stream;
    },
  };
  async function run(kind: string) {
    mode = kind;
    const mock = createMockModel({ responses: [
      { content: [{ type: 'toolCall', id: 'parent-call', name: 'research_task', arguments: { prompt: 'Find evidence' } }] },
      { content: [{ type: 'text', text: 'parent done' }] },
    ] });
    const created = await createAgentSession({ cwd: root, model: mock.model, sessionManager: SessionManager.inMemory(),
      disableExtensionDiscovery: true, extensions: [fixtureExtension],
      enableMCP: false, enableLsp: false, enableIrc: false, skipPythonPreflight: true, cacheWarming: false,
      skills: [], rules: [], contextFiles: [], noContextFiles: true, promptTemplates: [], slashCommands: [],
      autoApprove: true, bindProcessState: false, disableModelFallback: true, systemPrompt: 'offline parent',
    });
    parent = created.session;
    parent.modelRegistry.authStorage.keys.setRuntime('mock', 'offline-fixture');
    parent.agent.streamFn = mock.stream;
    // SDK embeddings must initialize the runner as CLI modes do.
    const noop = () => {};
    parent.extensionRunner.initialize({ sendMessage: noop, sendUserMessage: noop, appendEntry: noop,
      getActiveTools: () => parent.getActiveToolNames(), getAllTools: () => [], setActiveTools: noop,
      getCommands: () => [], setModel: noop, getThinkingLevel: noop, setThinkingLevel: noop,
      getSessionName: noop, setSessionName: noop },
      { getModel: () => parent.model, isIdle: () => true, abort: noop, hasPendingMessages: () => false, shutdown: noop });
    if (!parent.getActiveToolNames().includes('research_task')) throw Error('extension not registered');
    try {
      if (kind === 'bad-close') process.env.OMP_TEST_BAD_CLOSE = '1';
      const promise = parent.prompt('Research');
      if (kind === 'abort') {
        const deadline = Date.now() + 5000;
        while (!readFileSync(log, 'utf8').includes('"op": "execute"')) {
          if (Date.now() > deadline) throw Error('execute did not start');
          await new Promise(resolve => setTimeout(resolve, 10));
        }
        await parent.abort();
      }
      await promise.catch(() => {});
      if (kind !== 'abort') {
        const response = mock.calls[1]?.context.messages.find((m: any) => m.role === 'toolResult' && m.toolCallId === 'parent-call');
        if (!response) throw Error('parent did not get tool result');
        if (kind === 'normal' && (response.isError || !JSON.stringify(response).includes('UNTRUSTED RESEARCH FINDINGS'))) { console.error('BAD PARENT', JSON.stringify(response)); throw Error('bad parent result'); }
        if (kind === 'bad-close' && !response.isError) throw Error('unverified cleanup accepted');
      }
      if (kind === 'normal') {
        if (JSON.stringify(childMock.calls[0]?.context.tools?.map((t: any) => t.name)) !== '["research_container"]') throw Error('incorrect child tool list');
        const all = childMock.calls.at(-1).context.messages;
        for (const id of ['b', 'r', 't']) if (!all.find((m: any) => m.role === 'toolResult' && m.toolCallId === id && m.isError)) throw Error('host tool not denied: ' + id);
        if (!JSON.stringify(all).includes('UNTRUSTED CONTAINER OUTPUT')) throw Error('tool output not marked');
      }
    } finally { delete process.env.OMP_TEST_BAD_CLOSE; await parent.dispose(); }
  }
  await run('normal');
  await run('normal');
  const normalEvents = readFileSync(log, 'utf8').trim().split('\n').map(s => JSON.parse(s));
  const starts = normalEvents.filter(e => e.op === 'start');
  if (starts.length !== 2 || starts[0].name === starts[1].name) throw Error('fake tasks not independent');
  for (const s of starts) {
    const events = normalEvents.filter(e => e.name === s.name);
    if (events.map(e => e.op).join(',') !== 'start,execute,execute,close' || events[1].command !== 'wrong task') throw Error('cross-task selector escaped its bound task');
  }
  await run('bad-close');
  writeFileSync(log, '');
  await run('abort');
  const lines = readFileSync(log, 'utf8').trim().split('\n').map(s => JSON.parse(s));
  if (lines.map(x => x.op).join(',') !== 'start,execute,close') throw Error('abort did not close exact task: ' + JSON.stringify(lines));
  const base = root + '/.local/state/omp-research';
  const dirs = readdirSync(base);
  if (dirs.length !== 4 || inherited !== 4) throw Error('missing task or inheritance');
  const names = new Set();
  const statuses: string[] = [];
  for (const d of dirs) {
    const path = base + '/' + d;
    if ((statSync(path).mode & 0o077) || (statSync(path + '/receipts.jsonl').mode & 0o077)) throw Error('receipts not private');
    const rows = readFileSync(path + '/receipts.jsonl', 'utf8').trim().split('\n').map(s => JSON.parse(s));
    if (rows.length !== 2 || rows[0].event !== 'identity' || rows[1].event !== 'cleanup' || rows[0].container !== rows[1].container) throw Error('receipt mismatch');
    if (!rows[0].daemon.includes('offline-daemon')) throw Error('daemon missing');
    names.add(rows[0].container);
    statuses.push(rows[1].result.cleanup);
  }
  if (names.size !== 4) throw Error('tasks reused container identity');
  if (statuses.filter(x => x === 'absent_at_check').length !== 2 || statuses.filter(x => x === 'unverified').length !== 2) throw Error('cleanup outcomes not recorded accurately: ' + statuses);
  console.error('OMP ENTRY OFFLINE PASS');
}
