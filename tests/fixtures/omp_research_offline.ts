import { createAgentSession, SessionManager } from '@oh-my-pi/pi-coding-agent';
import { createMockModel } from '@oh-my-pi/pi-ai/providers/mock';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { runResearchSession } from '../../skills/safe-fetch/scripts/omp_research_session';

export default async function () {
  const root = process.cwd();
  const log = root + '/events.log';
  process.env.OMP_TEST_LOG = log;
  if (existsSync(root + '/shared_research_stdio.py')) process.env.OMP_TEST_REAL_STDIO = root + '/shared_research_stdio.py';
  const mock = createMockModel({ responses: [
    { content: [{ type: 'toolCall', id: 'one', name: 'research_container', arguments: { command: 'echo fake' } }] },
    { content: [{ type: 'text', text: 'fixture answer' }] },
  ] });
  const { session: parent } = await createAgentSession({
    cwd: root, model: mock.model, sessionManager: SessionManager.inMemory(),
    disableExtensionDiscovery: true, enableMCP: false, enableLsp: false, enableIrc: false,
    skipPythonPreflight: true, cacheWarming: false, skills: [], rules: [], contextFiles: [],
    noContextFiles: true, promptTemplates: [], slashCommands: [], autoApprove: true,
    bindProcessState: false, disableModelFallback: true, systemPrompt: 'offline fixture',
  });
  parent.modelRegistry.authStorage.keys.setRuntime('mock', 'offline-fixture');
  try {
    const receipts: any[] = [];
    writeFileSync(log, '');
    const result = await runResearchSession({ cwd: root, model: parent.model, modelRegistry: parent.modelRegistry }, {
      prompt: 'Use the research tool.', stdioScript: root + '/tests/fixtures/omp_research_stdio_fake.py',
      daemonIdentity: 'fake-daemon', record: async r => { receipts.push(r); },
      configureSession: s => {
        if (s.model !== parent.model || s.modelRegistry !== parent.modelRegistry) throw Error('parent inheritance failed');
        s.agent.streamFn = mock.stream;
      },
    });
    const advertised = mock.calls[0]?.context.tools?.map((t: any) => t.name);
    if (JSON.stringify(advertised) !== '["research_container"]') throw Error('advertised tools incorrect: '+JSON.stringify(advertised));
    if (result.content !== 'fixture answer' || result.trust !== 'untrusted_research_result') throw Error('bad result');
    if (readFileSync(log, 'utf8') !== 'start\nexecute\nclose\n') throw Error('protocol order wrong');
    if (receipts.map(r => r.event).join(',') !== 'identity,cleanup') throw Error('receipts wrong');
    const response = mock.calls[1]?.context.messages.find((m: any) => m.role === 'toolResult');
    if (!JSON.stringify(response).includes('UNTRUSTED CONTAINER OUTPUT')) throw Error('missing trust marker');
    writeFileSync(log, '');
    let failed = false;
    try {
      await runResearchSession({ cwd: root, model: parent.model, modelRegistry: parent.modelRegistry }, {
        prompt: 'never started', stdioScript: root + '/tests/fixtures/omp_research_stdio_fake.py', daemonIdentity: 'fake-daemon',
        record: async (r: any) => { if (r.event === 'identity') throw Error('receipt persistence failed'); },
      });
    } catch { failed = true; }
    if (!failed || readFileSync(log, 'utf8').includes('start')) throw Error('failed receipt must prevent start');
    const forbidden = createMockModel({ responses: [
      { content: [{ type: 'toolCall', id: 'bad', name: 'bash', arguments: { command: 'must not run' } }] },
      { content: [{ type: 'text', text: 'denied' }] },
    ] });
    writeFileSync(log, '');
    await runResearchSession({ cwd: root, model: parent.model, modelRegistry: parent.modelRegistry }, {
      prompt: 'Attempt an unavailable tool.', stdioScript: root + '/tests/fixtures/omp_research_stdio_fake.py',
      daemonIdentity: 'fake-daemon', record: async () => {}, configureSession: s => { s.agent.streamFn = forbidden.stream; },
    });
    const denied = forbidden.calls[1]?.context.messages.find((m: any) => m.role === 'toolResult' && m.toolCallId === 'bad');
    if (!denied?.isError || readFileSync(log, 'utf8') !== 'start\nclose\n') throw Error('built-in tool did not fail closed');
    process.env.OMP_TEST_BAD_CLOSE = '1';
    const badCleanupMock = createMockModel({ responses: [{ content: [{ type: 'text', text: 'done' }] }] });
    let badCleanupRejected = false;
    try {
      await runResearchSession({ cwd: root, model: parent.model, modelRegistry: parent.modelRegistry }, {
        prompt: 'Return.', stdioScript: root + '/tests/fixtures/omp_research_stdio_fake.py',
        daemonIdentity: 'fake-daemon', record: async () => {}, configureSession: s => { s.agent.streamFn = badCleanupMock.stream; },
      });
    } catch { badCleanupRejected = true; }
    delete process.env.OMP_TEST_BAD_CLOSE;
    if (!badCleanupRejected) throw Error('unverified cleanup accepted');
    console.error('OMP ADAPTER OFFLINE PASS');
  } finally { await parent.dispose(); }
}
