import copy

import pytest

from achlab.demo import build_demo


@pytest.fixture
def demo():
    return build_demo()


@pytest.fixture
def demo_copy(demo):
    return copy.deepcopy(demo)
