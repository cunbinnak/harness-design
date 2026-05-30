---
name: ref-frontend-config
description: Mẫu cấu hình FE — package.json scripts, env vars, build config, FE-specific docker.
---

# Reference: Frontend Config Patterns

> **Purpose:** Mẫu cấu hình chuẩn cho frontend — package.json, .env, build tool config (Vite/Webpack), Dockerfile FE.
> **Audience:** `dev:frontend`, `review:frontend`.
> **Tuning:** Theo framework + bundler.

## package.json scripts (chuẩn)

```json
{
  "name": "{boundary_id}",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage",
    "test:e2e": "cypress run --headless",
    "lint": "eslint src --ext .ts,.tsx",
    "lint:fix": "eslint src --ext .ts,.tsx --fix",
    "a11y": "vitest run --testPathPattern=a11y",
    "type-check": "tsc --noEmit"
  }
}
```

## .env.example (FE)

```env
# API base URLs (Vite uses VITE_ prefix; CRA uses REACT_APP_)
VITE_API_BASE_URL=http://localhost:8080
VITE_API_TIMEOUT_MS=10000

# Auth
VITE_TOKEN_STORAGE=memory  # memory | httpOnlyCookie (NOT localStorage)

# Feature flags (optional)
VITE_FEATURE_NEW_DASHBOARD=true

# Sentry/observability (optional)
# VITE_SENTRY_DSN=
```

## docker-compose FE service entry

```yaml
services:
  {boundary_id}:
    build:
      context: ../../services/{boundary_id}
      dockerfile: Dockerfile
      target: production
    image: {project_name}/{boundary_id}:latest
    ports:
      - "${FE_PORT:-3000}:80"
    environment:
      # FE thường serve qua nginx — env baked vào build, không runtime
      VITE_API_BASE_URL: ${API_BASE_URL:-http://localhost:8080}
    depends_on:
      - {be_boundary}
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:80/"]
      interval: 10s
      timeout: 5s
      retries: 3
```

## Dockerfile FE (multi-stage)

```dockerfile
# Stage 1: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Serve via nginx
FROM nginx:alpine AS production
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

## tsconfig.json (chuẩn)

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "jsx": "react-jsx",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"]
}
```

## ESLint + Prettier (gợi ý)

```json
// .eslintrc.json
{
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:react/recommended",
    "plugin:react-hooks/recommended",
    "plugin:jsx-a11y/recommended",
    "prettier"
  ],
  "rules": {
    "no-console": ["warn", { "allow": ["warn", "error"] }],
    "@typescript-eslint/no-unused-vars": "error"
  }
}
```

## Forbidden config patterns

- Token / API key trong source code — luôn qua `VITE_*` env vars
- Build dev với secret production — separate `.env.production`
- Disable ESLint cho cả file (`/* eslint-disable */`) — fix root cause
- Console.log trong production build — strip qua Vite/Webpack config
- `localStorage` cho JWT/auth token — XSS risk

## Khi nào tuning

- Framework khác (Vue/Nuxt): scripts khác, build tool khác
- SSR/SSG: thêm cấu hình server-side
- Mobile (React Native): cấu trúc + scripts riêng
- Micro-frontend: module federation config

Đồng bộ với `docs/architecture/adr/ADR-001-tech-stack.md` (FE stack) + `ADR-004-ui-kit.md`.

