from typing import Any, Dict, Optional

class _Node:
    def __init__(self, key: Any, value: Any):
        self.key = key
        self.value = value
        self.prev: Optional["_Node"] = None
        self.next: Optional["_Node"] = None


class _DoublyLinkedList:
    def __init__(self):
        self.head = _Node(None, None)
        self.tail = _Node(None, None)
        self.head.next = self.tail
        self.tail.prev = self.head
        self.size = 0

    def push_front(self, node: _Node):
        nxt = self.head.next
        node.next, node.prev = nxt, self.head
        self.head.next = node
        nxt.prev = node
        self.size += 1

    def move_to_front(self, node: _Node):
        # detach
        node.prev.next = node.next
        node.next.prev = node.prev
        # move to front
        self.push_front(node)

    def pop_back(self) -> Optional[_Node]:
        if self.size == 0:
            return None
        node = self.tail.prev
        self.tail.prev = node.prev
        node.prev.next = self.tail
        self.size -= 1
        return node


class LRUCache:
    """O(1) LRU cache using dict + doubly linked list."""
    def __init__(self, maxsize: int):
        if maxsize <= 0:
            raise ValueError("maxsize must be > 0")
        self.maxsize = maxsize
        self.map: Dict[Any, _Node] = {}
        self.dll = _DoublyLinkedList()

    def get(self, key: Any) -> Any:
        node = self.map.get(key)
        if node is None:
            raise KeyError(key)
        self.dll.move_to_front(node)
        return node.value

    def put(self, key: Any, value: Any) -> None:
        if key in self.map:
            node = self.map[key]
            node.value = value
            self.dll.move_to_front(node)
            return

        node = _Node(key, value)
        self.map[key] = node
        self.dll.push_front(node)

        if len(self.map) > self.maxsize:
            old = self.dll.pop_back()
            if old:
                self.map.pop(old.key, None)
