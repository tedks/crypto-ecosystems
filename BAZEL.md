# Bazel package graph

The first Bazel targets are `//src:shlex_test_binary` and `//src:shlex_test`. They compile the existing `src/shlex.zig` unit tests with this repository's committed Zig 0.14.0 Linux x86-64 archive and run the resulting binary. The action declares the source, archive, and managed Python compiler/extractor. Bazel tracks source content, while the tool verifies the exact archive digest and rejects unsafe archive entries and size excesses. Both targets declare Linux x86-64 execution and target constraints.

With Bazel 8.7.0 available, run from this repository root:

```bash
bazel test //src:shlex_test --jobs=2 --local_resources=memory=2048
```

`./run.sh` and `zig build test` remain the native full-application workflows. This Bazel package covers the five shell-tokenizer tests only; it does not include migrations, taxonomy, timestamp, or the generated application. The committed Linux toolchain archive is 49,091,960 bytes, so remote qualification must account for its exact single-file input rather than silently raising generic candidate limits.
