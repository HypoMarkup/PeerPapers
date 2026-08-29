# PeerPapers

A real-time collaborative exam and peer-marking platform built with a Python FastAPI backend, React TypeScript frontend, and Protocol Buffers over WebSockets.

---

## Prerequisites

- **Python 3.10+** & `pip`
- **Node.js 18+** & `npm`
- **Buf CLI**

---

## Setting up

### Install Buf CLI (if not installed)

Follow instructions at https://buf.build/docs/cli/installation/

---

### Generating Protocol Buffer Code

To compile the `.proto` definitions in `proto/` into Python models (`backend/generated/`) and TypeScript interfaces (`frontend/src/generated/`), run:

```bash
cd proto
buf generate
```
