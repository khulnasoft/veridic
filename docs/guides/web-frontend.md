# Web Frontend (Next.js)

The Next.js web frontend provides a user interface for the Veridic platform.

## Structure

The frontend files are currently in the root directory and include:
- `app/` - Next.js app directory
- `components/` - React components
- `lib/` - Utility libraries
- `public/` - Static assets
- `styles/` - Global styles
- `package.json` - Node.js dependencies

## Optional: Move to web/ directory

To better organize the repository, you may want to move the frontend to a `web/` subdirectory:

```bash
mkdir web
mv app components lib public styles hooks web/
mv package.json pnpm-lock.yaml next.config.mjs next-env.d.ts web/
mv tsconfig.json tailwind.config.ts postcss.config.mjs components.json web/
cd web && pnpm install
```

Then update the `docker-compose.yml` and documentation accordingly.

## Development

```bash
# If in root
npm install
npm run dev

# If moved to web/
cd web
npm install
npm run dev
```

The application will be available at http://localhost:3000
