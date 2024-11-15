from collections import Counter
from collections.abc import Mapping
from copy import deepcopy
from enum import Enum
from functools import reduce, partial
from typing import Any, MutableMapping


class Strategy(Enum):
    # Replace `destination` item with one from `source` (default).
    REPLACE = 0
    # Combine `list`, `tuple`, `set`, or `Counter` types into one collection.
    ADDITIVE = 1
    # Alias to: `TYPESAFE_REPLACE`
    TYPESAFE = 2
    # Raise `TypeError` when `destination` and `source` types differ. Otherwise, perform a `REPLACE` merge.
    TYPESAFE_REPLACE = 3
    # Raise `TypeError` when `destination` and `source` types differ. Otherwise, perform a `ADDITIVE` merge.
    TYPESAFE_ADDITIVE = 4


def _handle_merge_replace(destination, source, key):
    if isinstance(destination[key], Counter) and isinstance(source[key], Counter):
        # Merge both destination and source `Counter` as if they were a standard dict.
        _deepmerge(destination[key], source[key])
    else:
        # If a key exists in both objects and the values are `different`, the value from the `source` object will be used.
        destination[key] = deepcopy(source[key])


def _handle_merge_additive(destination, source, key):
    # Values are combined into one long collection.
    if isinstance(destination[key], list) and isinstance(source[key], list):
        # Extend destination if both destination and source are `list` type.
        destination[key].extend(deepcopy(source[key]))
    elif isinstance(destination[key], set) and isinstance(source[key], set):
        # Update destination if both destination and source are `set` type.
        destination[key].update(deepcopy(source[key]))
    elif isinstance(destination[key], tuple) and isinstance(source[key], tuple):
        # Update destination if both destination and source are `tuple` type.
        destination[key] = destination[key] + deepcopy(source[key])
    elif isinstance(destination[key], Counter) and isinstance(source[key], Counter):
        # Update destination if both destination and source are `Counter` type.
        destination[key].update(deepcopy(source[key]))
    else:
        _handle_merge[Strategy.REPLACE](destination, source, key)


def _handle_merge_typesafe(destination, source, key, strategy):
    # Raise a TypeError if the destination and source types differ.
    if type(destination[key]) is not type(source[key]):
        raise TypeError(
            f'destination type: {type(destination[key])} differs from source type: {type(source[key])} for key: "{key}"'
        )
    else:
        _handle_merge[strategy](destination, source, key)


_handle_merge = {
    Strategy.REPLACE: _handle_merge_replace,
    Strategy.ADDITIVE: _handle_merge_additive,
    Strategy.TYPESAFE: partial(_handle_merge_typesafe, strategy=Strategy.REPLACE),
    Strategy.TYPESAFE_REPLACE: partial(_handle_merge_typesafe, strategy=Strategy.REPLACE),
    Strategy.TYPESAFE_ADDITIVE: partial(_handle_merge_typesafe, strategy=Strategy.ADDITIVE),
}


def _is_recursive_merge(a, b):
    both_mapping = isinstance(a, Mapping) and isinstance(b, Mapping)
    both_counter = isinstance(a, Counter) and isinstance(b, Counter)
    return both_mapping and not both_counter


def _deepmerge(dst, src, strategy=Strategy.REPLACE):
    if src is None:
        return dst

    for key in src:
        if key in dst:
            if _is_recursive_merge(dst[key], src[key]):
                # If the key for both `dst` and `src` are both Mapping types (e.g. dict), then recurse.
                _deepmerge(dst[key], src[key], strategy)
            elif dst[key] is src[key]:
                # If a key exists in both objects and the values are `same`, the value from the `dst` object will be used.
                pass
            else:
                _handle_merge.get(strategy)(dst, src, key)
        else:
            # If the key exists only in `src`, the value from the `src` object will be used.
            dst[key] = deepcopy(src[key])
    return dst


def merge(destination: MutableMapping[str, Any], *sources: Mapping[str, Any], strategy: Strategy = Strategy.REPLACE) -> MutableMapping[str, Any]:
    """
    A deep merge function for 🐍.

    :param destination: The destination mapping.
    :param sources: The source mappings.
    :param strategy: The merge strategy.
    :return:
    """
    return reduce(partial(_deepmerge, strategy=strategy), sources, destination)
