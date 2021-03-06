import pytest
from axopy.timing import Counter, Timer


class TimeoutReceiver(object):

    def __init__(self):
        self.received = False

    def rx(self):
        self.received = True


def test_incremental_timer():
    timer = Counter(2)
    recv = TimeoutReceiver()
    timer.timeout.connect(recv.rx)

    assert timer.count == 0

    timer.increment()
    assert not recv.received
    assert timer.count == 1
    assert timer.progress == 0.5
    timer.increment()
    assert recv.received
    assert timer.count == 0

    with pytest.raises(ValueError):
        Counter(-1)
        Counter(0)


def test_incremental_timer_float():
    timer = Counter(3.5)
    recv = TimeoutReceiver()
    timer.timeout.connect(recv.rx)

    timer.increment()
    assert not recv.received
    timer.increment()
    timer.increment()
    assert recv.received


def test_incremental_timer_noreset():
    timer = Counter(2, reset_on_timeout=False)

    assert timer.count == 0
    timer.increment()
    timer.increment()
    assert timer.count == 2
    timer.reset()
    assert timer.count == 0


def test_timer(qtbot):
    timer = Timer(0.1)
    recv = TimeoutReceiver()
    timer.timeout.connect(recv.rx)
    assert not recv.received
    with qtbot.waitSignal(timer.timeout):
        timer.start()
    assert recv.received

    recv.received = False
    timer.start()
    timer.stop()
    assert not recv.received
