# Markdown with TAP

This document demonstrates the [Test Anything Protocol (TAP)](https://testanything.org/) embedded in Markdown.

## What is TAP?

TAP is a simple text-based interface between testing modules in a test harness. It decouples test producers from test consumers.

## Basic TAP Example

```tap
TAP version 14
1..4
ok 1 - Input file opened
not ok 2 - First line of the input valid
ok 3 - Read the rest of the file
not ok 4 - Summarized correctly # TODO Not written yet
```

## TAP with Diagnostics

```tap
TAP version 14
1..3
ok 1 - retrieving servers from the database
  ---
  elapsed: 0.0123
  ---
ok 2 - pinged server 1
  ---
  message: 'ping ok'
  server: 192.168.1.1
  ---
not ok 3 - pinged server 2
  ---
  message: 'timeout'
  server: 192.168.1.2
  ---
```

## TAP with Subtests

```tap
TAP version 14
1..2
# Subtest: parser
    ok 1 - parses empty input
    ok 2 - parses single token
    ok 3 - parses nested structures
    1..3
ok 1 - parser
# Subtest: evaluator
    ok 1 - evaluates literals
    not ok 2 - evaluates expressions
    1..2
not ok 2 - evaluator
```

## Directives

| Directive | Meaning                                       |
|-----------|-----------------------------------------------|
| `# SKIP`  | Test was skipped (not a failure)              |
| `# TODO`  | Test is expected to fail (work in progress)   |

```tap
ok 1 - database connection
ok 2 - cache warmup # SKIP redis unavailable
not ok 3 - new feature # TODO awaiting implementation
```

## Anatomy of a TAP Line

- `ok` / `not ok` — test outcome
- test number — sequential, matches the plan
- `-` — separator
- description — human-readable name
- `#` — optional directive or comment
