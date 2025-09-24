# TradeBotHub Frontend

Modern React/Next.js frontend application for the AI Trading Bot Marketplace.

## Features

### Authentication System
- **Login/Register**: Secure user authentication with JWT tokens
- **User Profiles**: Complete profile management for users and developers
- **Role-based Access**: Support for USER, DEVELOPER, and ADMIN roles
- **Protected Routes**: Automatic redirection for unauthorized access

### Bot Management
- **Bot Marketplace**: Browse and discover trading bots
- **Bot Creation**: Rich form for creating new bots with file upload
- **My Bots**: Dashboard for developers to manage their bots
- **Bot Details**: Comprehensive bot information and statistics

### UI/UX Features
- **Responsive Design**: Mobile-first approach with Tailwind CSS
- **Modern Components**: Headless UI components with smooth animations
- **Form Validation**: Client-side validation with Zod schemas
- **Toast Notifications**: User-friendly feedback system
- **Loading States**: Skeleton loaders and loading indicators

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS + Headless UI
- **State Management**: React Query for server state
- **Forms**: React Hook Form + Zod validation
- **Icons**: Heroicons
- **HTTP Client**: Axios with interceptors

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn
- Backend API running on http://localhost:8000

### Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The application will be available at http://localhost:3000

### Environment Variables

Create `.env.local` file:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Project Structure

```
frontend/
├── app/                    # Next.js App Router pages
│   ├── auth/              # Authentication pages
│   ├── dashboard/         # User dashboard
│   ├── developer/         # Developer-specific pages
│   ├── marketplace/       # Bot marketplace
│   └── profile/           # User profile
├── components/            # Reusable components
│   ├── auth/             # Authentication components
│   ├── bots/             # Bot management components
│   └── layout/           # Layout components
├── contexts/             # React contexts
├── hooks/               # Custom React hooks
├── lib/                 # Utilities and types
└── public/              # Static assets
```

## Key Components

### Authentication
- `LoginForm`: User login with email/password
- `RegisterForm`: User registration with role selection
- `ProfileForm`: Profile editing for developers

### Bot Management
- `BotList`: Grid view of available bots with filters
- `BotForm`: Create/edit bot with file upload
- `MyBotsList`: Developer's bot management dashboard

### Layout
- `Navbar`: Responsive navigation with user menu
- `AuthProvider`: Authentication context and state

## API Integration

The frontend communicates with the FastAPI backend through:

- **Authentication**: JWT token-based auth
- **Bot Operations**: CRUD operations for bots
- **File Upload**: Multipart form data for bot files
- **Error Handling**: Centralized error management

## Development

### Available Scripts

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
npm run type-check   # TypeScript type checking
```

### Code Style

- TypeScript for type safety
- ESLint + Prettier for code formatting
- Tailwind CSS for consistent styling
- Component-based architecture

## Features Implemented

### ✅ Authentication System
- [x] Login form with validation
- [x] Registration form with role selection
- [x] User profile management
- [x] JWT token handling
- [x] Protected routes

### ✅ Bot Management
- [x] Bot marketplace with search/filter
- [x] Bot creation form with file upload
- [x] Developer bot dashboard
- [x] Bot editing and deletion
- [x] Bot statistics and metrics

### ✅ UI/UX
- [x] Responsive design
- [x] Loading states
- [x] Error handling
- [x] Toast notifications
- [x] Form validation
- [x] Modern component library

## Next Steps

To further enhance the application:

1. **Real-time Features**: WebSocket integration for live bot performance
2. **Advanced Analytics**: Charts and graphs for bot performance
3. **Payment Integration**: Subscription management UI
4. **Admin Dashboard**: Complete admin panel for system management
5. **Mobile App**: React Native version for mobile users

## Contributing

1. Follow TypeScript and ESLint rules
2. Use Tailwind CSS for styling
3. Write tests for new components
4. Update documentation for new features

## License

This project is part of the TradeBotHub marketplace system.

