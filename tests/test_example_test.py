import pytest

@pytest.mark.asyncio
async def test_example():
    assert True

def test_comparison_dict():
    assert {"a": 2, "b": 2} == {"a": 2, "b": 2}

def test_comparison_dict_with_async():
    assert {"a": 1} == {"a": 1}

