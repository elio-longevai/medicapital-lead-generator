# MediCapital Lead Generation Engine - Frontend

## Project Overview

AI-powered lead generation system frontend for MediCapital Solutions. Built with React, TypeScript, and modern web technologies to provide an intuitive interface for managing B2B prospects.

## Development Setup

### Prerequisites
- Node.js (v18+) - [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating)
- Bun package manager

### Getting Started

```sh
# Navigate to frontend directory
cd frontend

# Install dependencies
bun install

# Start development server
bun run dev
```

The frontend will be available at http://localhost:8080

### Available Scripts

- `bun run dev` - Start development server with hot reload
- `bun run build` - Build for production
- `bun run lint` - Run ESLint
- `bun run preview` - Preview production build

## Technologies Used

- **Vite** - Build tool and dev server
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **shadcn/ui** - Component library
- **React Query** - Data fetching and caching
- **React Router** - Navigation

## Project Structure

```
src/
├── components/     # Reusable UI components
├── hooks/         # Custom React hooks
├── pages/         # Page components
├── services/      # API services
└── lib/           # Utilities and helpers
```

## API Integration

The frontend connects to the FastAPI backend running on port 8000. See the backend README for setup instructions.
