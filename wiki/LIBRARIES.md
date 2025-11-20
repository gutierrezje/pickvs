# PickVs - Libraries & Dependencies

## Backend (Python)

### Web Framework & Server
- **fastapi**: High-performance, async API framework
- **uvicorn[standard]**: ASGI server that runs FastAPI

### Database
- **asyncpg**: Async PostgreSQL driver for connecting to Neon PostgreSQL (with built-in connection pooling)

### External APIs
- **requests**: For making HTTP requests to The Odds API (used in Lambda functions)

### Authentication & Security
- **PyJWT**: For creating and verifying JSON Web Tokens (JWT)
- **bcrypt**: For securely hashing and verifying user passwords

### Configuration
- **python-dotenv**: For managing environment variables and secrets

### AWS
- **boto3**: AWS SDK for interacting with Lambda, EventBridge, Secrets Manager

### Analytics
- **posthog**: For tracking user events and measuring KPIs (activation, retention, engagement)

---

## Frontend (Node.js / React)

### UI Framework
- **react**: JavaScript library for building user interfaces
- **react-dom**: React package for rendering to the DOM

### HTTP Client
- **axios**: For making API requests to the FastAPI backend

### State & Authentication
- **jwt-decode**: For decoding JWT tokens stored in localStorage

### Analytics
- **posthog-js**: JavaScript SDK for tracking user events and measuring KPIs

### Build & Development
- **vite**: Fast build tool for modern web apps (or Next.js if using full-stack framework)
- **typescript**: Optional but recommended for type safety in React