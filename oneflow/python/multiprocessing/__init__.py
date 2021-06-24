"""
ref: torch.multiprocessing
"""
import sys
from .reductions import init_reductions
import multiprocessing

__all__ = ['set_sharing_strategy', 'get_sharing_strategy',
           'get_all_sharing_strategies']


from multiprocessing import *  # noqa: F403


__all__ += multiprocessing.__all__  # type: ignore[attr-defined]



"""Add helper function to spawn N processes and wait for completion of any of
them. This depends `mp.get_context` which was added in Python 3.4."""
from .spawn import spawn, SpawnContext, start_processes, ProcessContext, \
    ProcessRaisedException, ProcessExitedException


if sys.platform == 'darwin' or sys.platform == 'win32':
    _sharing_strategy = 'file_system'
    _all_sharing_strategies = {'file_system'}
else:
    _sharing_strategy = 'file_descriptor'
    _all_sharing_strategies = {'file_descriptor', 'file_system'}


def set_sharing_strategy(new_strategy):
    """Sets the strategy for sharing CPU tensors.

    Args:
        new_strategy (str): Name of the selected strategy. Should be one of
            the values returned by :func:`get_all_sharing_strategies()`.
    """
    global _sharing_strategy
    assert new_strategy in _all_sharing_strategies
    _sharing_strategy = new_strategy


def get_sharing_strategy():
    """Returns the current strategy for sharing CPU tensors."""
    return _sharing_strategy


def get_all_sharing_strategies():
    """Returns a set of sharing strategies supported on a current system."""
    return _all_sharing_strategies


init_reductions()

