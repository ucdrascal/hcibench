import pytest
from axopy import util
from axopy.task import Task
from axopy.task.base import _TaskIter
from axopy.messaging import transmitter


@pytest.fixture
def simple_design():
    design = [
        [{'block': 0, 'trial': 0}, {'block': 0, 'trial': 1}],
        [{'block': 1, 'trial': 0}, {'block': 1, 'trial': 1}]
    ]
    return design


def test_empty_design():
    it = _TaskIter()
    assert it.next_block() is not None
    assert it.next_trial() is not None
    assert it.next_block() is None
    assert it.next_trial() is None


def test_task_iter(simple_design):
    d = simple_design

    it = _TaskIter(d)
    b = it.next_block()
    assert b == d[0]
    t = it.next_trial()
    assert t == b[0]
    t = it.next_trial()
    assert t == b[1]
    t = it.next_trial()
    assert t is None

    b = it.next_block()
    assert b == d[1]
    b = it.next_block()
    assert b is None


def test_base_task(simple_design):
    task = Task()
    task.design(simple_design)

    # task prepare hooks
    task.prepare_view(None)
    task.prepare_input_stream(None)
    task.prepare_storage(None)

    task.run()
    assert task.block == simple_design[0]
    # task is waiting for key press to advance
    assert not hasattr(task, 'trial')
    task.key_press(util.key_return)
    assert task.trial == simple_design[0][0]

    # automatically advance to next block
    task.advance_block_key = None
    task.next_trial()
    task.next_trial()

    assert task.block == simple_design[1]
    assert task.trial == simple_design[1][0]

    class recv(object):
        def finish(self):
            self.finish_received = True

    r = recv()
    task.finished.connect(r.finish)
    task.next_block()
    assert r.finish_received


count = 0


def test_task_transmitters():
    """Check to make sure transmitter/receiver interface works for tasks."""

    class CustomTask(Task):

        @transmitter()
        def tx(self):
            return

        def rx(self):
            global count
            count += 1

    # create two of hte same task, make sure rx is called the appropriate
    # number of times
    t1 = CustomTask()
    t2 = CustomTask()

    # using "raw" connect, both t1.tx and t2.tx will connect since those are
    # the same underlying transmitter object
    t1.tx.connect(t1.rx)
    t1.tx()
    assert count == 1
    # here we neglect to disconnect t1.tx, so rx is called twice
    t2.tx.connect(t2.rx)
    t2.tx()
    assert count == 3

    t1.tx.disconnect(t1.rx)
    t2.tx()
    assert count == 4

    # now implement Experiment to ensure doesn't happen
    t1.tx.disconnect(t1.rx)
    t2.tx.disconnect(t2.rx)

    t1.connect(t1.tx, t1.rx)
    t1.tx()
    assert count == 5
    t1.disconnect_all()

    t2.connect(t2.tx, t2.rx)
    t2.tx()
    assert count == 6
