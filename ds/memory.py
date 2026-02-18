from collections import deque

class ConversationMemory:
    def __init__(self, maxlen=8):
        self.mem = deque(maxlen=maxlen)

    def add(self, role: str, text: str):
        self.mem.append({'role': role, 'text': text})

    def as_list(self):
        return list(self.mem)


class SimpleLRUNode:
    def __init__(self, key, val):
        self.key = key
        self.val = val
        self.prev = None
        self.next = None


class SimpleLRU:
    """Minimal LRU cache using a dict + doubly linked list."""
    def __init__(self, capacity=128):
        self.capacity = capacity
        self.map = {}
        # dummy head/tail
        self.head = SimpleLRUNode(None, None)
        self.tail = SimpleLRUNode(None, None)
        self.head.next = self.tail
        self.tail.prev = self.head

    def _remove(self, node):
        p, n = node.prev, node.next
        p.next = n
        n.prev = p

    def _add_to_front(self, node):
        node.next = self.head.next
        node.prev = self.head
        self.head.next.prev = node
        self.head.next = node

    def get(self, key):
        node = self.map.get(key)
        if not node:
            return None
        self._remove(node)
        self._add_to_front(node)
        return node.val

    def put(self, key, val):
        node = self.map.get(key)
        if node:
            node.val = val
            self._remove(node)
            self._add_to_front(node)
            return
        node = SimpleLRUNode(key, val)
        self.map[key] = node
        self._add_to_front(node)
        if len(self.map) > self.capacity:
            # evict least recently used
            lru = self.tail.prev
            self._remove(lru)
            del self.map[lru.key]
