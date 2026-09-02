# PeerPapers

A real-time collaborative exam and peer-marking platform built with a Python WebSocket backend, React TypeScript frontend, and binary Protocol Buffers.

---

## Prerequisites

- **Python 3.10+** & `pip`
- **Node.js 18+** & `npm`
- **Buf CLI**

---

## Setting up

### Install Buf CLI (if not installed)

Follow instructions at https://buf.build/docs/cli/installation/

### Generating Protocol Buffer Code

From `/proto`, run:

```bash
buf generate
```

### Install frontend dependancies

From `/frontend`, run:

```bash
npm install
```

---

## Running the app

### In one terminal:

From `/backend`, run:

```bash
python main.py
```

### In another terminal:

From `/frontend`, run:

```bash
npm run dev
```
