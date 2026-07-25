# python-lru-cache — baseline

- AI model: `claude-fable-5`
- Time spent: 47 s
- Tokens spent: 38 218
- Language/stack version: Python (targets 3.14.6, current stable at test date)
- Test date: 2026-07-25
- Harness: skill not loaded; agent instructed to ignore all skill/philosophy instructions and answer with its natural default approach

## Prompt

```text
Our Python service re-parses the same config templates over and over. Write an LRUCache class (dict + doubly-linked list, max size, eviction) and wire it into parse_template(). Should be ~60 lines, standard interview stuff.
```

## Result

There's no `parse_template` in this repo, so here's the generic implementation I'd write.

One thing before the code: if you don't specifically need eviction stats, per-instance caches, or custom invalidation, `functools.lru_cache(maxsize=256)` on the parse function is the production answer — it's C-accelerated and thread-safe. But the hand-rolled version is genuinely useful here because config files can change on disk, and you'll want the cache key to include mtime. Here it is:

```python
import os
from threading import Lock
from typing import Any, Hashable


class _Node:
    __slots__ = ("key", "value", "prev", "next")

    def __init__(self, key: Hashable = None, value: Any = None):
        self.key = key
        self.value = value
        self.prev: "_Node | None" = None
        self.next: "_Node | None" = None


class LRUCache:
    def __init__(self, max_size: int = 128):
        if max_size <= 0:
            raise ValueError("max_size must be positive")
        self.max_size = max_size
        self._map: dict[Hashable, _Node] = {}
        self._lock = Lock()
        self._head = _Node()
        self._tail = _Node()
        self._head.next = self._tail
        self._tail.prev = self._head

    def _unlink(self, node: _Node) -> None:
        node.prev.next = node.next
        node.next.prev = node.prev

    def _push_front(self, node: _Node) -> None:
        node.next = self._head.next
        node.prev = self._head
        self._head.next.prev = node
        self._head.next = node

    def get(self, key: Hashable, default: Any = None) -> Any:
        with self._lock:
            node = self._map.get(key)
            if node is None:
                return default
            self._unlink(node)
            self._push_front(node)
            return node.value

    def put(self, key: Hashable, value: Any) -> None:
        with self._lock:
            node = self._map.get(key)
            if node is not None:
                node.value = value
                self._unlink(node)
                self._push_front(node)
                return
            if len(self._map) >= self.max_size:
                lru = self._tail.prev
                self._unlink(lru)
                del self._map[lru.key]
            node = _Node(key, value)
            self._map[key] = node
            self._push_front(node)

    def __len__(self) -> int:
        return len(self._map)

    def __contains__(self, key: Hashable) -> bool:
        return key in self._map
```

Wiring it into `parse_template` — note the key is `(path, mtime)`, so an edited template automatically misses the cache instead of serving stale config:

```python
_template_cache = LRUCache(max_size=256)


def parse_template(path: str):
    mtime = os.stat(path).st_mtime_ns
    key = (path, mtime)
    cached = _template_cache.get(key)
    if cached is not None:
        return cached
    parsed = _parse_template_impl(path)  # your existing parse logic, renamed
    _template_cache.put(key, parsed)
    return parsed
```

Design notes:

- **Sentinel head/tail nodes** eliminate all the `if node is head / is tail` edge cases — `_unlink` and `_push_front` never branch. This is the main trick that keeps the class short and bug-free.
- **`__slots__`** on `_Node` cuts per-entry memory roughly in half and avoids `__dict__` allocation on a hot path.
- **The lock** matters: linked-list splicing under concurrent access (gunicorn threads, ThreadPoolExecutor) corrupts the list silently. If your service is strictly single-threaded/asyncio, you can drop it.
- **mtime in the key** means old versions of an edited file linger until evicted by LRU pressure — that's fine at max_size=256, but if templates are huge you could instead store `path -> (mtime, parsed)` and compare mtime on get.
- One caveat: `os.stat` on every call still hits the filesystem. That's usually negligible vs. parsing, but if even that's too hot, add a short TTL on the stat check.

Quick sanity test you can drop in your test suite:

```python
def test_lru_eviction():
    c = LRUCache(max_size=2)
    c.put("a", 1)
    c.put("b", 2)
    c.get("a")
    c.put("c", 3)
    assert "a" in c and "c" in c and "b" not in c
```
