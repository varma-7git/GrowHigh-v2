# Deploy GrowHigh free (demo)

Stack: Neon (PostgreSQL) + Render (Django) + Netlify (React). No card needed.

## 1. Push to GitHub
Git Bash in the project root: `git add . && git commit -m "Add deployment config" && git push`

## 2. Database — neon.tech
1. Sign up, create project `growhigh` (region: Singapore/Mumbai nearest).
2. Copy the **connection string** (postgresql://...neon.tech/neondb?sslmode=require). Keep it secret.

## 3. Backend — render.com
1. New + > **Blueprint** > pick the GrowHigh-v2 repo (it reads render.yaml). Or New > Web Service with the same settings.
2. Fill the 3 asked variables:
   - DATABASE_URL = the Neon string
   - CORS_ALLOWED_ORIGINS = your Netlify URL (add after step 4, e.g. https://growhigh.netlify.app — no trailing slash)
   - CSRF_TRUSTED_ORIGINS = your Render URL (https://growhigh-api.onrender.com)
3. After deploy open `https://<your-api>.onrender.com/api/v1/health/` — should say ok.
4. Render > service > **Shell** (free plan: use your PC instead, see below) and run:
   `python manage.py create_admin YOURID --password "StrongPass@123"`
   `python manage.py seed_academics` (and the seed_* lesson commands if you want demo data)

No Shell on free plan? Run these from your PC against Neon: in Command Prompt set
`set DATABASE_URL=<neon string>` and `set DJANGO_SETTINGS_MODULE=config.settings.prod`, `set SECRET_KEY=x`, `set ALLOWED_HOSTS=localhost`, then run the same commands.

## 4. Frontend — netlify.com
1. Add new site > Import from GitHub > GrowHigh-v2.
2. Base directory: `09_Frontend/growhigh-frontend` (build command and publish folder are read from netlify.toml).
3. Environment variable: `REACT_APP_API_URL` = `https://<your-api>.onrender.com/api/v1`
4. Deploy, then put the Netlify URL into Render's CORS_ALLOWED_ORIGINS and redeploy the backend.

## Limits of the free plan
- Render sleeps after 15 min idle; first request takes ~50 s. Open the health URL before a demo.
- Uploaded files (videos, PDFs, student uploads, recordings) are stored on Render's disk and are **lost on every redeploy/restart**. Fine for a demo; for real use move media to cloud storage (Cloudinary / S3).
- Email prints to logs unless EMAIL_* variables are set.
