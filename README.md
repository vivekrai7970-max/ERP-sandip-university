# vivekprojecterp

This repository contains a Django app for Sandip University ERP.

## Deploying to Vercel

1. Add the repository to Vercel.
2. Set the following environment variables in Vercel Dashboard:
   - `DJANGO_SECRET_KEY`
   - `DJANGO_DEBUG` (set to `False` in production)
   - `DJANGO_ALLOWED_HOSTS` (e.g. `your-domain.vercel.app`)
   - `RAZORPAY_KEY_ID`
   - `RAZORPAY_KEY_SECRET`
3. Vercel should detect `requirements.txt` and use `app.py` as the entrypoint.
4. Set the root directory to the repository root.

## Notes

- The project uses SQLite, which is not ideal for production on serverless platforms.
- For production, consider using a managed database and updating `DATABASES` in `sandip_university/settings.py`.
