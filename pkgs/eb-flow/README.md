# eb-flow

Common flow primitives for everybase.

## Installation

```bash
pip install eb-flow
```

## Overview

This package provides a rich set of flow primitives organized by category:

- **Control Flows**: Sequence, If, While, DoWhile, Forever, Switch
- **Parallel Flows**: Parallel, Race, All, Any
- **Timing Flows**: Delay, Timeout, Throttle, Debounce
- **Iteration Flows**: ForEach, ForEachSequence, ForRange
- **Reactive Flows**: Once, OnChange, OnChangeWhile
- **Error Handling**: TryCatch, Retry, Assert
- **I/O Flows**: Print, Log, Debug
- **Profiling Flows**: Timed, Accumulate, Count, Trace, Tap, Sample

## Usage

```python
from eb_flow import Sequence, If, Parallel
# ... more examples to come
```
