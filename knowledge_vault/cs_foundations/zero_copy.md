---
card: cs_foundations.zero_copy
domain: computer_science
---

# Zero-Copy I/O

## What it is
Moving data between device, kernel, and application WITHOUT copying through intermediate
buffers — the win is not the copy itself but the CPU cycles, cache pollution, context
switches, and latency each crossing costs.

## The classic problem
Naive file->socket: read() does disk->page cache->user buffer (2 copies, 2 switches);
write() does user->socket buffer->NIC (2 more). Payload crosses the CPU four times.

## Mechanisms that actually exist
- sendfile(): file->socket in-kernel; with scatter-gather NICs the socket-buffer copy vanishes.
- splice(): moves pages between kernel buffers via a pipe pivot; no user copy.
- mmap(): file pages mapped into VA space; llama.cpp loads .gguf this way — the file stays
  on disk, pages fault in on demand, and the OS evicts under pressure. This is exactly why
  a 16.8 GB model can function on 16 GB RAM: resident set < file size, paid for in fault stalls.
- io_uring: shared submission/completion rings (a ring buffer — symbol
  systems.concurrency.ring_buffer); batches syscalls toward zero, registered buffers pin DMA.
- DMA/RDMA: device reads/writes memory directly; CPU only programs descriptors.

## Invariants
- The win is measured: copies avoided per byte x bytes moved.
- Registered buffers must outlive in-flight operations; mmap pages must not be truncated under readers.
- Ring slot ownership transitions exactly once.

## Failure modes
- mmap on a truncated file -> SIGBUS. sendfile from a socket -> EINVAL.
- io_uring registered buffer reused before CQE -> silent corruption.
