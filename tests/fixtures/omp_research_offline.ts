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
    if (!process.env.OMP_TEST_REAL_STDIO) throw Error('real stdio server is required for lifecycle tests');
    if (!process.env.OMP_TEST_CASE || process.env.OMP_TEST_CASE === 'slow') {
      process.env.OMP_TEST_CLOSE_DELAY = '16';
      const slowCloseMock = createMockModel({ responses: [{ content: [{ type: 'text', text: 'done' }] }] });
      const slowReceipts: any[] = [];
      writeFileSync(log, '');
      await runResearchSession({ cwd: root, model: parent.model, modelRegistry: parent.modelRegistry }, {
        prompt: 'Return.', stdioScript: root + '/tests/fixtures/omp_research_stdio_fake.py',
        daemonIdentity: 'fake-daemon', record: async r => { slowReceipts.push(r); },
        configureSession: s => { s.agent.streamFn = slowCloseMock.stream; },
      });
      delete process.env.OMP_TEST_CLOSE_DELAY;
      if (slowReceipts.at(-1)?.process?.code !== 0 || slowReceipts.at(-1)?.result?.cleanup !== 'absent_at_check') throw Error('slow cleanup not verified');
      if (readFileSync(log, 'utf8') !== 'start\nclose\n') throw Error('slow close was interrupted');
    }
    if (!process.env.OMP_TEST_CASE || process.env.OMP_TEST_CASE === 'abort') {
      process.env.OMP_TEST_EXEC_DELAY = '4';
      const abortMock = createMockModel({ responses: [
        { content: [{ type: 'toolCall', id: 'abort', name: 'research_container', arguments: { command: 'sleep' } }] },
        { content: [{ type: 'text', text: 'unexpected completion' }] },
      ] });
      const controller = new AbortController();
      const abortReceipts: any[] = [];
      writeFileSync(log, '');
      let aborted = false;
      const running = runResearchSession({ cwd: root, model: parent.model, modelRegistry: parent.modelRegistry }, {
        prompt: 'Use the tool.', stdioScript: root + '/tests/fixtures/omp_research_stdio_fake.py',
        daemonIdentity: 'fake-daemon', record: async r => { abortReceipts.push(r); }, signal: controller.signal,
        configureSession: s => { s.agent.streamFn = abortMock.stream; },
      }).catch(() => { aborted = true; });
      const deadline = Date.now() + 5000;
      while (!readFileSync(log, 'utf8').includes('execute\n')) {
        if (Date.now() > deadline) throw Error('execute did not start');
        await new Promise(resolve => setTimeout(resolve, 10));
      }
      const began = Date.now();
      controller.abort();
      await running;
      const elapsed = Date.now() - began;
      delete process.env.OMP_TEST_EXEC_DELAY;
      if (!aborted || elapsed > 750) throw Error('abort did not interrupt execute promptly: ' + elapsed + 'ms');
      if (readFileSync(log, 'utf8') !== 'start\nexecute\nclose\n') throw Error('abort did not invoke task cleanup');
      if (abortReceipts[0]?.container !== 'research-task-offline-fixture' || abortReceipts.at(-1)?.container !== abortReceipts[0]?.container) throw Error('abort lost exact name');
      if (abortReceipts.at(-1)?.result?.cleanup !== 'unverified') throw Error('interrupted cleanup must remain unverified');
      const diagnostic = abortReceipts.at(-1)?.stderr ?? '';
      if (!diagnostic.includes('"op": "cleanup"') || !diagnostic.includes('research-task-offline-fixture')) throw Error('server finally cleanup diagnostic missing');
      console.error('LIFECYCLE PASS: interrupt ' + elapsed + 'ms');

      // The command must be interrupted promptly even if cleanup itself is slow;
      // the caller still waits for bounded cleanup and records uncertainty.
      process.env.OMP_TEST_EXEC_DELAY = '4';
      process.env.OMP_TEST_CLOSE_DELAY = '2';
      const delayedMock = createMockModel({ responses: [
        { content: [{ type: 'toolCall', id: 'delayed', name: 'research_container', arguments: { command: 'sleep' } }] },
        { content: [{ type: 'text', text: 'unexpected completion' }] },
      ] });
      const delayedController = new AbortController();
      writeFileSync(log, '');
      const delayed = runResearchSession({ cwd: root, model: parent.model, modelRegistry: parent.modelRegistry }, {
        prompt: 'Use the tool.', stdioScript: root + '/tests/fixtures/omp_research_stdio_fake.py',
        daemonIdentity: 'fake-daemon', record: async () => {}, signal: delayedController.signal,
        configureSession: s => { s.agent.streamFn = delayedMock.stream; },
      }).then(() => { throw Error('cancel unexpectedly succeeded'); }, () => {});
      const executeDeadline = Date.now() + 5000;
      while (!readFileSync(log, 'utf8').includes('execute\n')) {
        if (Date.now() > executeDeadline) throw Error('delayed execute did not start');
        await new Promise(resolve => setTimeout(resolve, 10));
      }
      const interruptedAt = Date.now();
      delayedController.abort();
      while (!readFileSync(log, 'utf8').includes('close\n')) {
        if (Date.now() - interruptedAt > 750) throw Error('slow cleanup did not begin promptly');
        await new Promise(resolve => setTimeout(resolve, 10));
      }
      await delayed;
      const delayedElapsed = Date.now() - interruptedAt;
      delete process.env.OMP_TEST_EXEC_DELAY;
      delete process.env.OMP_TEST_CLOSE_DELAY;
      if (delayedElapsed < 1900 || delayedElapsed > 3500) throw Error('did not wait for delayed cleanup: ' + delayedElapsed + 'ms');
      console.error('LIFECYCLE PASS: interrupt before slow cleanup; return ' + delayedElapsed + 'ms');
    }
    if (!process.env.OMP_TEST_CASE || process.env.OMP_TEST_CASE === 'closeabort') {
      process.env.OMP_TEST_CLOSE_DELAY = '2';
      const closeMock = createMockModel({ responses: [{ content: [{ type: 'text', text: 'done' }] }] });
      const controller = new AbortController();
      const closeReceipts: any[] = [];
      writeFileSync(log, '');
      const running = runResearchSession({ cwd: root, model: parent.model, modelRegistry: parent.modelRegistry }, {
        prompt: 'Return.', stdioScript: root + '/tests/fixtures/omp_research_stdio_fake.py',
        daemonIdentity: 'fake-daemon', record: async r => { closeReceipts.push(r); }, signal: controller.signal,
        configureSession: s => { s.agent.streamFn = closeMock.stream; },
      }).then(() => null, e => e);
      const deadline = Date.now() + 5000;
      while (!readFileSync(log, 'utf8').includes('close\n')) {
        if (Date.now() > deadline) throw Error('normal cleanup did not start');
        await new Promise(resolve => setTimeout(resolve, 10));
      }
      const began = Date.now();
      controller.abort();
      const error = await running;
      delete process.env.OMP_TEST_CLOSE_DELAY;
      if (!error || !String(error).includes('cancelled')) throw Error('abort during close returned success or did not report cancellation: ' + error);
      if (Date.now() - began < 1500) throw Error('abort interrupted normal cleanup');
      if (readFileSync(log, 'utf8') !== 'start\nclose\n') throw Error('abort during close disrupted cleanup');
      const receipt = closeReceipts.at(-1);
      if (closeReceipts.map(r => r.event).join(',') !== 'identity,cleanup' ||
          receipt?.container !== closeReceipts[0]?.container || receipt?.result?.cleanup !== 'absent_at_check' ||
          receipt?.process?.code !== 0) throw Error('abort during close lost cleanup receipt');
      console.error('LIFECYCLE PASS: abort during normal close retains receipt');

      const receiptMock = createMockModel({ responses: [{ content: [{ type: 'text', text: 'done' }] }] });
      const receiptController = new AbortController();
      const persisted: any[] = [];
      const receiptError = await runResearchSession({ cwd: root, model: parent.model, modelRegistry: parent.modelRegistry }, {
        prompt: 'Return.', stdioScript: root + '/tests/fixtures/omp_research_stdio_fake.py',
        daemonIdentity: 'fake-daemon', signal: receiptController.signal,
        record: async (r: any) => { persisted.push(r); if (r.event === 'cleanup') receiptController.abort(); },
        configureSession: s => { s.agent.streamFn = receiptMock.stream; },
      }).then(() => null, e => e);
      if (!receiptError || !String(receiptError).includes('cancelled') || persisted.at(-1)?.result?.cleanup !== 'absent_at_check') throw Error('abort during cleanup receipt not honored');
      console.error('LIFECYCLE PASS: abort during receipt persistence');

      process.env.OMP_TEST_BAD_CLOSE = '1';
      process.env.OMP_TEST_CLOSE_DELAY = '2';
      const uncertainMock = createMockModel({ responses: [{ content: [{ type: 'text', text: 'done' }] }] });
      const uncertainController = new AbortController();
      const uncertainReceipts: any[] = [];
      writeFileSync(log, '');
      const uncertain = runResearchSession({ cwd: root, model: parent.model, modelRegistry: parent.modelRegistry }, {
        prompt: 'Return.', stdioScript: root + '/tests/fixtures/omp_research_stdio_fake.py',
        daemonIdentity: 'fake-daemon', signal: uncertainController.signal,
        record: async r => { uncertainReceipts.push(r); },
        configureSession: s => { s.agent.streamFn = uncertainMock.stream; },
      }).then(() => null, e => e);
      const uncertainDeadline = Date.now() + 5000;
      while (!readFileSync(log, 'utf8').includes('close\n')) {
        if (Date.now() > uncertainDeadline) throw Error('uncertain cleanup did not start');
        await new Promise(resolve => setTimeout(resolve, 10));
      }
      uncertainController.abort();
      const uncertainError = await uncertain;
      delete process.env.OMP_TEST_BAD_CLOSE;
      delete process.env.OMP_TEST_CLOSE_DELAY;
      if (!uncertainError || !String(uncertainError).includes('cancelled') ||
          uncertainReceipts.at(-1)?.container !== uncertainReceipts[0]?.container ||
          uncertainReceipts.at(-1)?.result?.cleanup !== 'unverified') throw Error('cancel lost cleanup uncertainty');
      console.error('LIFECYCLE PASS: abort retains unverified cleanup');
    }
    if (!process.env.OMP_TEST_CASE || process.env.OMP_TEST_CASE === 'timeout') {
      process.env.OMP_TEST_CLOSE_DELAY = '60';
      const timeoutMock = createMockModel({ responses: [{ content: [{ type: 'text', text: 'done' }] }] });
      const timeoutReceipts: any[] = [];
      writeFileSync(log, '');
      let timeoutFailed = false;
      const began = Date.now();
      try {
        await runResearchSession({ cwd: root, model: parent.model, modelRegistry: parent.modelRegistry }, {
          prompt: 'Return.', stdioScript: root + '/tests/fixtures/omp_research_stdio_fake.py',
          daemonIdentity: 'fake-daemon', record: async r => { timeoutReceipts.push(r); },
          configureSession: s => { s.agent.streamFn = timeoutMock.stream; },
        });
      } catch { timeoutFailed = true; }
      delete process.env.OMP_TEST_CLOSE_DELAY;
      const elapsed = Date.now() - began;
      if (!timeoutFailed || elapsed < 50000 || elapsed > 57000) throw Error('close timeout not bounded as expected: ' + elapsed + 'ms');
      if (readFileSync(log, 'utf8') !== 'start\nclose\nSIGTERM\n') throw Error('timeout did not terminate blocked transport');
      if (timeoutReceipts.at(-1)?.container !== timeoutReceipts[0]?.container || timeoutReceipts.at(-1)?.result?.cleanup !== 'unverified') throw Error('timeout lost identity or uncertainty');
      console.error('LIFECYCLE PASS: genuine timeout ' + elapsed + 'ms');
    }
    console.error('OMP ADAPTER OFFLINE PASS');
  } finally { await parent.dispose(); }
}
