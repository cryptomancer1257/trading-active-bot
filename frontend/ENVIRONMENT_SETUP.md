# Frontend Environment Setup

## Environment Variables

Create a `.env.local` file in the frontend directory with the following variables:

```bash
# Studio Backend Configuration
NEXT_PUBLIC_STUDIO_BASE_URL=http://localhost:8000

# Marketplace API Configuration  
NEXT_PUBLIC_MARKETPLACE_API_KEY=marketplace_dev_api_key_12345
```

## Configuration

The frontend uses a centralized config system in `lib/config.ts` that:

- Reads environment variables with fallback defaults
- Manages API endpoints
- Handles trial configuration
- Provides type safety

## Usage

```typescript
import config from '@/lib/config'

// Use config values
const apiUrl = config.studioBaseUrl
const endpoint = config.endpoints.marketplaceSubscription
const apiKey = config.marketplaceApiKey
```

## Development vs Production

- **Development**: Uses `http://localhost:8000` as default
- **Production**: Set `NEXT_PUBLIC_STUDIO_BASE_URL` to your production backend URL
- **API Key**: Update `NEXT_PUBLIC_MARKETPLACE_API_KEY` for production environment
