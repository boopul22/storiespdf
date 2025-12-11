# 🚀 Quick Deployment Checklist

## Before Deploying

- [x] 209 posts scheduled (Dec 09, 2025 - Jun 19, 2026)
- [x] Cron job configured in `vercel.json`
- [x] API endpoint ready at `/api/cron/daily-publish`
- [ ] Code pushed to GitHub
- [ ] Deployed to Vercel
- [ ] Environment variables set
- [ ] Cron job verified

## Deployment Steps

### 1. Push to GitHub
```bash
git add .
git commit -m "Add scheduled posts for daily publishing"
git push origin main
```

### 2. Deploy to Vercel
1. Go to https://vercel.com/dashboard
2. Click "Add New..." → "Project"
3. Import your GitHub repository
4. Click "Deploy"

### 3. Set Environment Variables
In Vercel Dashboard → Your Project → Settings → Environment Variables:

**CRON_SECRET**
- Create a random secret key
- Example: `my-super-secret-key-12345`

**VERCEL_DEPLOY_HOOK**
- Go to Settings → Git → Deploy Hooks
- Create hook named "Daily Publish" for branch "main"
- Copy the URL
- Add as environment variable

### 4. Redeploy
- Go to Deployments
- Click ⋯ on latest deployment
- Click "Redeploy"

## Verify It's Working

✅ **Check Cron Jobs**
- Vercel Dashboard → Your Project → Settings → Cron Jobs
- Should show: `daily-publish` at `30 0 * * *`

✅ **Check First Publish**
- Wait until 6:00 AM IST next day
- Visit your site
- First post should appear!

✅ **Check Logs**
- Vercel Dashboard → Logs → Filter "Cron"
- Should see daily executions

## Schedule Details

- **Publish Time**: 6:00 AM IST (12:30 AM UTC)
- **Frequency**: 1 post per day
- **Total Posts**: 209
- **Duration**: ~7 months

## Important Notes

⚠️ **Vercel Pro Plan Required** for cron jobs
- If on Hobby plan, use GitHub Actions instead (see DEPLOYMENT_GUIDE.md)

⚠️ **Environment Variables Must Be Set**
- Site won't auto-publish without them
- Remember to redeploy after adding them

⚠️ **Time Zone**
- Cron runs in UTC
- `30 0 * * *` = 12:30 AM UTC = 6:00 AM IST

## Quick Commands

```bash
# Check scheduled posts
grep -r "pubDate:" src/content/blog/*.md | head -10

# Count total posts
ls src/content/blog/*.md | wc -l

# Test cron endpoint (replace values)
curl -X GET https://your-site.vercel.app/api/cron/daily-publish \
  -H "Authorization: Bearer your-cron-secret"
```

## Need Help?

📖 See full guide: `DEPLOYMENT_GUIDE.md`
🌐 Vercel Docs: https://vercel.com/docs/cron-jobs
