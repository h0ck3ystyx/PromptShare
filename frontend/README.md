# PromptShare Frontend

Vue.js 3 frontend application for PromptShare, built with Vite, Tailwind CSS, and Pinia.

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

1. Install dependencies:
```bash
npm install
```

2. Create `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
```

3. Update `.env` with your API URL:
```env
VITE_API_BASE_URL=http://localhost:7999/api
VITE_APP_NAME=PromptShare
```

### Development

Start the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### Build

Build for production:
```bash
npm run build
```

The built files will be in the `dist/` directory.

### Preview Production Build

Preview the production build:
```bash
npm run preview
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/      # Vue components
│   │   ├── layout/     # Layout components (NavBar, Footer)
│   │   ├── prompts/    # Prompt-related components
│   │   └── comments/   # Comment components
│   ├── views/          # Page components
│   ├── router/         # Vue Router configuration
│   ├── stores/         # Pinia stores
│   ├── services/       # API service layer
│   ├── App.vue         # Root component
│   └── main.js         # Application entry point
├── public/             # Static assets
└── index.html          # HTML template
```

## 🎨 Features

- **Authentication**: Login/logout with JWT tokens
- **Prompt Management**: Browse, create, edit, and delete prompts
- **Search**: Full-text search with filters
- **Collections**: Browse featured collections
- **Comments & Ratings**: Interactive feedback system
- **One-Click Copy**: Copy prompts with visual feedback
- **Responsive Design**: Mobile-first approach with Tailwind CSS
- **Admin Dashboard**: Analytics and management (admin only)

## 🔧 Configuration

### Environment Variables

- `VITE_API_BASE_URL`: Backend API base URL (default: `http://localhost:7999/api`)
- `VITE_APP_NAME`: Application name (default: `PromptShare`)

### Tailwind CSS

Tailwind CSS is configured in `tailwind.config.js`. Customize the theme and add plugins as needed.

## 📚 API Integration

The frontend uses Axios for API communication. All API calls are centralized in `src/services/api.js` with automatic token injection and error handling.

## 🧪 Testing

### Run Tests

Run tests in watch mode:
```bash
npm test
```

Run tests with UI:
```bash
npm run test:ui
```

Run tests with coverage:
```bash
npm run test:coverage
```

### Writing Tests

Tests are located in the `tests/` directory. Example test structure:

```javascript
import { describe, it, expect } from 'vitest'
import { mount } from '@testing-library/vue'

describe('ComponentName', () => {
  it('should render correctly', () => {
    // Test implementation
  })
})
```

## 🔍 Linting

### Run Linter

Check for linting errors:
```bash
npm run lint:check
```

Fix linting errors automatically:
```bash
npm run lint
```

## 📝 Development Notes

- Uses Vue 3 Composition API
- State management with Pinia
- Routing with Vue Router 4
- Styling with Tailwind CSS
- API communication with Axios

## 🚀 Deployment

For production deployment:

1. Build the application:
```bash
npm run build
```

2. Serve the `dist/` directory with a web server (nginx, Apache, etc.)

3. Configure CORS on the backend to allow requests from your frontend domain.
