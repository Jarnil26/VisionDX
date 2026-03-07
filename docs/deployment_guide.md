# VisionDX Deployment Guide (Go Live)

This guide will help you deploy your VisionDX platform (Backend & Frontend) to **Render.com**.

## 🏗️ Prerequisites
1. A **GitHub** or GitLab account with your code pushed.
2. A **Render.com** account.

## 🚀 Step 1: Deploy with Blueprint
Render uses the `render.yaml` file in your repository to automatically set up both the Backend and Frontend.

1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** and select **Blueprint**.
3. Connect your GitHub repository.
4. Render will detect the `render.yaml` file. Click **Apply**.

## 🔑 Step 2: Set Environment Variables
The blueprint sets up many variables automatically, but you should verify these in the **Environment** tab of the `visiondx-api` service:

| Variable | Recommended Value |
| :--- | :--- |
| `DATABASE_URL` | `postgresql://user:pass@host/db` (See Step 3) |
| `DATABASE_URL_SYNC` | `postgresql://user:pass@host/db` |
| `SECRET_KEY` | Auto-generated (or set a strong random string) |
| `APP_ENV` | `production` |
| `ALLOWED_ORIGINS` | `https://your-frontend-url.onrender.com` |

## 📦 Step 3: Persistence (Recommended)
By default, the app uses a temporary SQLite database (`/tmp/visiondx.db`). **Data will be lost on every redeploy.**

### Using Managed PostgreSQL (Best for Production)
1. In Render, click **New +** -> **PostgreSQL**.
2. Create the database.
3. Copy the **Internal Database URL**.
4. Paste it into the `DATABASE_URL` and `DATABASE_URL_SYNC` environment variables of your `visiondx-api` service.

## 🧪 Step 4: Final Verification
1. Once both services are "Live" in Render:
2. Visit your API URL: `https://visiondx-api.onrender.com/health` (should return healthy).
3. Visit your Frontend URL: `https://visiondx-frontend.onrender.com`.
4. Try logging in or uploading a report to test the connection.

## 🛠️ Troubleshooting
- **Build Fails**: Check the logs in Render. Common issues include missing dependencies in `requirements.txt` or `package.json`.
- **API Connection Error**: Ensure `NEXT_PUBLIC_API_URL` in the Frontend environment variables matches your actual Backend URL.
