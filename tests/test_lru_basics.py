from lru_cache.core import LRUCache
import pytest

def test_put_get_and_eviction():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    assert c.get("a") == 1      # access a -> a is MRU, b is LRU
    c.put("c", 3)               # evicts b
    with pytest.raises(KeyError):
        c.get("b")
    assert c.get("a") == 1
    assert c.get("c") == 3

def test_update_moves_to_mru():
    c = LRUCache(2)
    c.put("x", 10)
    c.put("y", 20)
    c.put("x", 11)              # update value; x becomes MRU
    c.put("z", 30)              # evicts y (since y is LRU)
    with pytest.raises(KeyError):
        c.get("y")
    assert c.get("x") == 11
    assert c.get("z") == 30
