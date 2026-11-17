#!/usr/bin/env python3
"""One process, one ResearchContainer, JSON-lines over stdin/stdout.

This transport is not a harness, authorization mechanism, or tool sandbox.
See README.md for the protocol, cleanup obligations, and security boundary.
"""
import json
import sys


def serve(source, sink, diagnostics, task):
    """Serve sequential requests; return nonzero if final cleanup is uncertain."""
    closed = False
    failed = False

    def reply(op, result):
        sink.write(json.dumps({'op': op, 'result': result}, ensure_ascii=True) + '\n')
        sink.flush()

    try:
        reply('ready', {'container': task.name})
        for line in source:
            try:
                request = json.loads(line)
            except (ValueError, RecursionError):
                reply(None, {'ok': False, 'error': 'invalid_json',
                             'message': 'Send one JSON object per line.'})
                continue
            if not isinstance(request, dict):
                reply(None, {'ok': False, 'error': 'invalid_request',
                             'message': 'Send a JSON object with an op.'})
                continue
            op = request.get('op')
            allowed = {'start': {'op'}, 'execute': {'op', 'command', 'timeout'}, 'close': {'op'}}
            if not isinstance(op, str) or op not in allowed:
                reply(None, {'ok': False, 'error': 'invalid_op',
                             'message': 'Use start, execute, or close.'})
                continue
            if set(request) - allowed[op]:
                reply(op, {'ok': False, 'error': 'invalid_request',
                           'message': 'Remove unsupported fields.'})
                continue
            if op == 'start':
                try:
                    result = task.start()
                except RuntimeError:
                    result = {'ok': False, 'error': 'start_invalid_state',
                              'message': 'The task has already started or closed; use a new process for a new task.'}
            elif op == 'execute':
                result = task.execute(request.get('command'), request.get('timeout', 15))
            else:
                result = task.close()
                closed = result.get('cleanup') in ('not_started', 'absent_at_check')
            reply(op, result)
            if closed:
                break
    except Exception:
        failed = True
        print('research_stdio: transport failed; cleanup will be attempted; inspect the container name in earlier replies.',
              file=diagnostics, flush=True)
    finally:
        if not closed:
            try:
                result = task.close()
                closed = result.get('cleanup') in ('not_started', 'absent_at_check')
                print(json.dumps({'op': 'cleanup', 'result': result}), file=diagnostics, flush=True)
            except Exception:
                print(json.dumps({'op': 'cleanup', 'result': {'container': task.name,
                      'cleanup': 'unverified', 'message': 'Reconcile this exact container name on the original Docker daemon.'}}),
                      file=diagnostics, flush=True)
                closed = False
    return 0 if closed and not failed else 1


def main():
    from research_container import ResearchContainer
    return serve(sys.stdin, sys.stdout, sys.stderr, ResearchContainer())


if __name__ == '__main__':
    sys.exit(main())
