from typing import Iterable


def batch_yielder(yielder, batch_size: int) -> Iterable[list]:
    '''
    yielder: list or yielder of items
    yield a sublist containing batch_size items
    '''
    res = []
    for item in yielder:
        if len(res) == int(batch_size):
            yield res
            res = []
        res.append(item)
    if res:
        yield res
