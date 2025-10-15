from lru_cache.core import LRUCache
from collections import OrderedDict
import pytest

def simulate_ordered_dict(seq, cap):
    """Reference LRU using OrderedDict (MRU at front)."""
    ref = OrderedDict()
    for op, key, *val in seq:
        if op == "put":
            v = val[0]
            if key in ref:
                ref.move_to_end(key, last=False)
                ref[key] = v
            else:
                ref[key] = v
                ref.move_to_end(key, last=False)
                if len(ref) > cap:
                    ref.popitem(last=True)  # pop LRU
        elif op == "get":
            if key in ref:
                ref.move_to_end(key, last=False)
            else:
                # miss: do nothing to ref structure
                pass
    return list(ref.keys())  # MRU -> LRU

def current_keys_mru_to_lru(cache: LRUCache):
    # internal walk from head to tail
    # (we rely on attribute names from our implementation)
    node = cache.dll.head.next
    keys = []
    while node is not cache.dll.tail:
        keys.append(node.key)
        node = node.next
    return keys

def test_eviction_order_matches_reference():
    cap = 3
    seq = [
        ("put", "a", 1),
        ("put", "b", 2),
        ("put", "c", 3),
        ("get", "a"),        # a -> MRU
        ("put", "d", 4),     # evicts b
        ("get", "c"),        # c -> MRU
        ("put", "e", 5),     # evicts a
        ("put", "f", 6),     # evicts d
        ("get", "e"),        # e -> MRU
        ("put", "g", 7),     # evicts c
    ]

    # run reference
    ref_keys = simulate_ordered_dict(seq, cap)

    # run our cache
    c = LRUCache(cap)
    for op, key, *val in seq:
        if op == "put":
            c.put(key, val[0])
        elif op == "get":
            try:
                c.get(key)
            except KeyError:
                pass

    our_keys = current_keys_mru_to_lru(c)
    assert our_keys == ref_keys

def test_read_updates_recency():
    c = LRUCache(2)
    c.put("x", 1)
    c.put("y", 2)
    # Access x so y becomes LRU
    assert c.get("x") == 1
    # Inserting z now should evict y
    c.put("z", 3)
    with pytest.raises(KeyError):
        c.get("y")
    assert c.get("x") == 1
    assert c.get("z") == 3
