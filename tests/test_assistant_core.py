from unittest import mock

import assistant_core


def _run_with_inputs(inputs):
    a = assistant_core.AIAssistant()
    with mock.patch('builtins.input', side_effect=inputs):
        a.run()


def test_run_parses_commands(monkeypatch):
    calls = {}
    monkeypatch.setattr(assistant_core, 'open_file', lambda p: calls.setdefault('open', p))
    monkeypatch.setattr(assistant_core, 'close_active_window', lambda: calls.setdefault('close', True))
    monkeypatch.setattr(assistant_core, 'start_process', lambda c: calls.setdefault('start', c))

    _run_with_inputs(['open foo', 'close', 'start echo hi', 'quit'])

    assert calls['open'] == 'foo'
    assert calls['close'] is True
    assert calls['start'] == 'echo hi'
