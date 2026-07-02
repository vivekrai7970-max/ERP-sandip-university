# Render Deployment Guide

## Step-by-Step Instructions

### 1. Push Your Code to GitHub

```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### 2. Create a Render Account

1. Go to [render.com](https://render.com)
2. Sign up using your GitHub account (recommended for easy integration)

### 3. Connect Your GitHub Repository

1. In Render Dashboard, click **New +** → **Web Service**
2. Select **Connect a repository**
3. Find your GitHub repository and connect it

### 4. Configure the Web Service

Fill in the following settings:

| Setting | Value |
|---------|-------|
| **Name** | `sandip-university-erp` |
| **Environment** | `Python 3.12` |
| **Region** | Select closest to your users |
| **Branch** | `main` (or your default branch) |
| **Build Command** | `pip install -r requirements.txt && python sandip_university/manage.py collectstatic --no-input && python sandip_university/manage.py migrate` |
| **Start Command** | `gunicorn sandip_university.wsgi:application --bind 0.0.0.0:$PORT` |
| **Plan** | Free (or upgrade as needed) |

### 5. Set Environment Variables

In the Render Dashboard, go to **Environment** and add:

```
DJANGO_SECRET_KEY = <your-secure-random-key>
DJANGO_DEBUG = False
DJANGO_ALLOWED_HOSTS = your-app-name.onrender.com
RAZORPAY_KEY_ID = your-razorpay-key-id
RAZORPAY_KEY_SECRET = your-razorpay-secret-key
```

To generate a secure secret key, run in your terminal:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 6. Deploy

1. Click **Create Web Service**
2. Render will automatically:
   - Install dependencies from `requirements.txt`
   - Run migrations
   - Collect static files
   - Start your application

Your app will be live at `https://your-app-name.onrender.com`

## Important Notes

- **SQLite Limitations**: SQLite works on Render but has limitations for production. For better performance with concurrent users, consider upgrading to PostgreSQL:
  1. In Render Dashboard, create a new PostgreSQL database
  2. Update your `DATABASES` in `settings.py` to use PostgreSQL
  3. Add the database URL to environment variables

- **Logs**: Check deployment logs in Render Dashboard → **Logs** tab
- **Auto-deploys**: Render auto-deploys when you push to your connected branch
- **Custom Domain**: Add your domain in Settings → **Custom Domains**

## Troubleshooting

### 502 Bad Gateway
- Check logs for errors
- Ensure `DJANGO_ALLOWED_HOSTS` includes your Render domain
- Verify `DJANGO_SECRET_KEY` is set

### Static Files Not Loading
- Run migrations and rebuild from Render Dashboard
- Check `STATIC_ROOT` and `STATIC_URL` settings

### Database Connection Issues
- If using PostgreSQL, verify the DATABASE_URL in environment variables
- Check database credentials in `settings.py`

## Optional: Use render.yaml for Infrastructure as Code

Instead of configuring via the dashboard, Render automatically detects `render.yaml` in your repo root. This file is already configured in your project.

To manually trigger a new deploy:
- Push a new commit to your connected branch
- Or click **Manual Deploy** in Render Dashboard
