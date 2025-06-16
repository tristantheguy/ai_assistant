from types import SimpleNamespace

import system_controller


def test_open_file_uses_subprocess(monkeypatch):
    called = {}

    def fake_popen(cmd):
        called['cmd'] = cmd

    monkeypatch.setattr(system_controller, 'subprocess', SimpleNamespace(Popen=fake_popen))
    # ensure os.startfile not used regardless of platform
    monkeypatch.setattr(system_controller, 'os', SimpleNamespace(startfile=lambda p: called.setdefault('start', p)))
    system_controller.open_file('foo.txt')
    assert called


def test_close_active_window_prefers_pyautogui(monkeypatch):
    sent = {}

    class DummyPG:
        def hotkey(self, *args):
            sent['hotkey'] = args

    monkeypatch.setattr(system_controller, 'pyautogui', DummyPG())
    assert system_controller.close_active_window()
    assert sent['hotkey'] == ('alt', 'f4')


def test_start_process(monkeypatch):
    launched = {}

    def fake_popen(cmd, shell=False):
        launched['cmd'] = cmd
        launched['shell'] = shell
        return 'proc'

    monkeypatch.setattr(system_controller.subprocess, 'Popen', fake_popen)
    proc = system_controller.start_process('echo hi')
    assert proc == 'proc'
    assert launched['cmd'] == 'echo hi'
    assert launched['shell']
