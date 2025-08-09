# PeerPapers

A real-time collaborative paper review and annotation platform built with Python FastAPI backend and React TypeScript frontend.

![Static Badge](https://img.shields.io/badge/Python_version-3.10-lime)  ![Static Badge](https://img.shields.io/badge/React-19.1-blue)

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- pip
- virtualenv 
- Node.js 16+
- npm

### One-Command Setup
```bash
python scripts-dev/setup.py
```

This single command will:
- Set up Python virtual environment
- Install all backend dependencies
- Install all frontend dependencies  
- Generate TypeScript types from Python models
- Prepare your development environment

## 🏃‍♂️ Development

### Running the Application

**Backend Server:**
```bash
python scripts-dev/runBackend.py
```
The API will be available at: http://127.0.0.1:8000/docs (usually)

**Frontend Server:**
```bash
python scripts-dev/runFrontend.py
```
The application will be available at: http://localhost:5173/ (usually)


### Type Generation

One of the key features of this project is **automated type consistency** between backend and frontend:

- **Single Source of Truth**: Python Pydantic models define all data structures
- **Automatic Generation**: TypeScript types are generated from Python models
- **Runtime Safety**: Type guards ensure message validation
- **Zero Manual Sync**: Types stay consistent automatically

To regenerate types (happens automatically during setup):
```bash
python scripts-dev/generateFrontendTypes.py
```

## 📁 Project Structure

```
PeerPapers/
├── backend/                 # Python FastAPI backend
│   ├── shared/
│   │   └── message.py      # Pydantic models (source of truth)
│   └── main.py             # FastAPI application
├── frontend/               # React TypeScript frontend
│   ├── src/
│   │   ├── generated/      # Auto-generated types (gitignored)
│   │   └── ...
│   └── package.json
├── scripts-dev/            # Development automation
│   ├── setup.py           # Master setup script
│   ├── setupBackend.py    # Backend environment setup
│   ├── setupFrontend.py   # Frontend setup + type generation
│   ├── runBackend.py      # Backend development server
│   ├── runFrontend.py     # Frontend development server
│   ├── generateFrontendTypes.py  # Type generation
│   └── common.py          # Cross-platform utilities
└── README.md
```

## 🔧 Development Scripts

Our development scripts provide a streamlined workflow:

| Script | Purpose |
|--------|---------|
| `setup.py` | Complete project setup - run this first |
| `setupBackend.py` | Set up Python environment and dependencies |
| `setupFrontend.py` | Set up Node.js environment and generate types |
| `runBackend.py` | Start the FastAPI development server |
| `runFrontend.py` | Start the React development server |
| `generateFrontendTypes.py` | Regenerate TypeScript types from Python models |

## 🔄 Type Consistency System

This project implements automated type consistency between backend and frontend:

### How It Works
1. **Python Models**: Define all data structures using Pydantic in `backend/shared/message.py`
2. **Type Generation**: `pydantic-to-typescript` converts Python models to TypeScript interfaces
3. **Runtime Guards**: `ts-auto-guard` generates type guards for runtime validation
4. **Import Optimization**: Generated imports use `import type` for better performance

### Benefits
- ✅ Single source of truth for all type definitions
- ✅ Compile-time type safety in both backend and frontend
- ✅ Runtime validation prevents type mismatches
- ✅ Zero manual synchronization required
- ✅ Automatic IDE autocomplete and error detection

### Usage in Frontend
```typescript
// Generated types are automatically available
import type { IncomingMessage, OutgoingMessage } from './generated/message';
import { isIncomingMessage } from './generated/message.guard';

// Runtime type checking
if (isIncomingMessage(data)) {
    // TypeScript knows this is IncomingMessage
    console.log(data.type);
}
```

## 🆕 Migration from Manual Setup

If you're coming from the old manual setup process:

1. **Pull the latest changes** with the new scripts
2. **Run the setup command**: `python scripts-dev/setup.py`
3. **Update your workflow**: Use the new run scripts instead of manual commands
4. **Remove old type definitions**: The frontend now uses generated types

## 🛠️ Technical Details

### Backend
- **Framework**: FastAPI with WebSockets for real-time communication
- **Type System**: Pydantic models for data validation and serialization
- **Development**: Hot reload enabled for rapid development

### Frontend  
- **Framework**: React with TypeScript
- **Build Tool**: Vite for fast development and building
- **Type Safety**: Generated types ensure consistency with backend
- **WebSocket**: Real-time communication with type-safe messages

### Cross-Platform Support
All development scripts work seamlessly on:
- Windows (using `.\venv\Scripts\activate`)
- macOS/Linux (using `source venv/bin/activate`)
- Platform detection is automatic

## 📝 Adding New Message Types

When you need to add new WebSocket message types:

1. **Define the Python model** in `backend/shared/message.py`
2. **Run type generation**: `python scripts-dev/generateFrontendTypes.py` (or restart frontend setup)
3. **Use in frontend**: Import the generated TypeScript types
4. **That's it!** No manual synchronization needed

## 🤝 Contributing

1. Fork the repository
2. Run `python scripts-dev/setup.py` to set up your development environment
3. Make your changes
4. Ensure types are properly generated and tests pass
5. Submit a pull request

---

**Note**: The `frontend/src/generated/` directory is gitignored as types are generated automatically during development setup.
