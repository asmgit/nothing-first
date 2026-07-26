# Judge calibration

Before a judge's or auditor's counts are recorded, it must rank these two reference answers correctly on every metric it reports: A strictly worse than B on entities, failure modes, human steps, logic ops, and LOC — and A flagged non-compliant, B compliant. A judge that fails this pair is not trusted for the run.

Task: "Cache results of `parse_template(path)` — it re-parses the same files."

## Reference A — over-built (must lose)

```python
class _Node:
    __slots__ = ('key', 'value', 'prev', 'next')

class LRUCache:
    def __init__(self, maxsize=256):
        self._map = {}
        self._lock = threading.Lock()
        self._head = _Node()
        self._tail = _Node()
        self._head.next = self._tail
        self._tail.prev = self._head

    def get(self, key):
        with self._lock:
            node = self._map.get(key)
            if node is None:
                return None
            self._unlink(node)
            self._push_front(node)
            return node.value

    def put(self, key, value):
        with self._lock:
            if len(self._map) >= 256:
                self._evict()
            ...

_template_cache = LRUCache()

def parse_template(path):
    cached = _template_cache.get(path)
    if cached is not None:
        return cached
    result = _parse_template_impl(path)
    _template_cache.put(path, result)
    return result
```

Expected counts: entities ≥ 3 (class, node class, module singleton), logic ops ≥ 4, failure modes ≥ 2 (hand-synced map/list, check-then-act wiring), LOC ≥ 30.

## Reference B — minimal (must win)

```python
@functools.lru_cache(maxsize=256)
def parse_template(path):
    ...
```

Expected counts: entities 0, logic ops 0, failure modes ≤ 1 (staleness if files change mid-run — named, not hidden), LOC ≤ 3.
