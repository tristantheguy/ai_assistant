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


def test_close_window_by_name(monkeypatch):
    calls = {}

    class DummyWindow:
        def close(self):
            calls['closed'] = True

    class DummyApp:
        def connect(self, title_re=None):
            calls['title'] = title_re
            return SimpleNamespace(top_window=lambda: DummyWindow())

    monkeypatch.setattr(system_controller, 'Application', DummyApp)

    assert system_controller.close_window_by_name('Calculator')
    assert calls['title'] == 'Calculator'
    assert calls['closed']


def test_close_window_by_name_psutil(monkeypatch):
    terminations = []

    class DummyProc:
        def __init__(self, name):
            self.info = {'name': name}

        def terminate(self):
            terminations.append(self.info['name'])

    def fake_iter(attrs):
        return [
            DummyProc('calc.exe'),
            DummyProc('calc-helper.exe'),
            DummyProc('notepad.exe'),
        ]

    monkeypatch.setattr(system_controller, 'Application', None)
    monkeypatch.setattr(system_controller, 'psutil', SimpleNamespace(process_iter=fake_iter))

    assert system_controller.close_window_by_name('calc')
    assert 'calc.exe' in terminations
    assert 'calc-helper.exe' in terminations
    assert 'notepad.exe' not in terminations


def test_close_window_by_name_multiple_matches(monkeypatch):
    terminations = []

    class DummyProc:
        def __init__(self, name):
            self.info = {'name': name}

        def terminate(self):
            terminations.append(self.info['name'])

    def fake_iter(attrs):
        return [
            DummyProc('foo.exe'),
            DummyProc('foo.exe'),
            DummyProc('bar.exe'),
        ]

    monkeypatch.setattr(system_controller, 'Application', None)
    monkeypatch.setattr(system_controller, 'psutil', SimpleNamespace(process_iter=fake_iter))

    assert system_controller.close_window_by_name('foo')
    assert terminations == ['foo.exe', 'foo.exe']
