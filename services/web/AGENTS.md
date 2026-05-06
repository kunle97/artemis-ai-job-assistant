<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

## Frontend API Architecture

- Use `axios` for all API calls in this frontend app.
- Place API logic under `src/services/` and organize by backend domain (for example `src/services/auth/`, `src/services/applications/`).
- Do not place API-calling logic in `src/app/lib/`.
- Pages/components should call service functions rather than making inline HTTP requests.
