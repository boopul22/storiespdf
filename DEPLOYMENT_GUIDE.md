# 🚀 Deployment Guide - Daily Auto-Publishing

This guide will help you deploy your Tamil Story website to Vercel with automatic daily publishing of scheduled posts.

## ✅ What You Already Have

Your website is already configured with:
- ✅ 209 blog posts scheduled from Dec 09, 2025 to Jun 19, 2026
- ✅ Vercel cron job configuration (`vercel.json`)
- ✅ API endpoint for daily rebuilds (`/api/cron/daily-publish`)
- ✅ Astro configured for server-side rendering with Vercel adapter

## 📋 Step-by-Step Deployment

### Step 1: Push Your Code to GitHub

```bash
# Make sure you're in the project directory
cd /Users/bipulkumar/Documents/WebsiteUpdate/Tamil_Story

# Add all files
git add .

# Commit your changes
git commit -m "Add 209 scheduled posts for daily publishing"

# Push to GitHub
git push origin main
```

### Step 2: Deploy to Vercel

1. **Go to Vercel Dashboard**: https://vercel.com/dashboard
2. **Import Your Repository**:
   - Click "Add New..." → "Project"
   - Select your GitHub repository
   - Click "Import"

3. **Configure Build Settings**:
   - Framework Preset: **Astro**
   - Build Command: `npm run build` (should be auto-detected)
   - Output Directory: `dist` (should be auto-detected)
   - Install Command: `npm install` (should be auto-detected)

4. **Click "Deploy"** and wait for the first deployment to complete

### Step 3: Set Up Environment Variables

After deployment, you need to configure two environment variables:

1. **Go to your project settings** in Vercel:
   - Click on your project
   - Go to "Settings" → "Environment Variables"

2. **Add CRON_SECRET**:
   - Name: `CRON_SECRET`
   - Value: Create a random secret (e.g., `your-super-secret-key-12345`)
   - Click "Add"

3. **Add VERCEL_DEPLOY_HOOK**:
   - First, create a Deploy Hook:
     - Go to "Settings" → "Git" → "Deploy Hooks"
     - Click "Create Hook"
     - Name: `Daily Publish`
     - Branch: `main` (or your default branch)
     - Click "Create Hook"
     - **Copy the URL** (it looks like: `https://api.vercel.com/v1/integrations/deploy/...`)
   
   - Then add it as an environment variable:
     - Go back to "Settings" → "Environment Variables"
     - Name: `VERCEL_DEPLOY_HOOK`
     - Value: Paste the Deploy Hook URL you just copied
     - Click "Add"

4. **Redeploy** your site to apply the environment variables:
   - Go to "Deployments"
   - Click the three dots (⋯) on the latest deployment
   - Click "Redeploy"

### Step 4: Enable Vercel Cron Jobs

1. **Verify Cron Job is Active**:
   - Go to your project in Vercel
   - Click on "Settings" → "Cron Jobs"
   - You should see: `daily-publish` scheduled for `30 0 * * *` (12:30 AM UTC daily)

2. **Adjust Schedule if Needed**:
   - The current schedule is `30 0 * * *` = **12:30 AM UTC** = **6:00 AM IST**
   - If you want a different time, update `vercel.json`:
     ```json
     {
       "crons": [
         {
           "path": "/api/cron/daily-publish",
           "schedule": "30 0 * * *"  // Change this
         }
       ]
     }
     ```
   - Common schedules:
     - `0 0 * * *` = Midnight UTC (5:30 AM IST)
     - `30 0 * * *` = 12:30 AM UTC (6:00 AM IST) ← **Current**
     - `0 1 * * *` = 1:00 AM UTC (6:30 AM IST)

## 🎯 How It Works

### Daily Publishing Flow:

1. **Every day at 6:00 AM IST** (12:30 AM UTC):
   - Vercel cron job triggers `/api/cron/daily-publish`
   
2. **The API endpoint**:
   - Verifies the cron secret for security
   - Triggers a new deployment via Deploy Hook
   
3. **Vercel rebuilds your site**:
   - Astro checks all post dates
   - Posts with `pubDate` ≤ today become visible
   - Future-dated posts remain hidden

4. **Your site updates automatically**:
   - One new post appears each day
   - No manual intervention needed!

## 📅 Your Current Schedule

- **Total Posts**: 209 posts
- **Start Date**: December 9, 2025
- **End Date**: June 19, 2026
- **Frequency**: 1 post per day
- **Auto-publish Time**: 6:00 AM IST daily

## 🔍 How to Verify It's Working

### Check Cron Job Logs:
1. Go to Vercel Dashboard → Your Project
2. Click "Logs" → Filter by "Cron"
3. You should see daily executions at 6:00 AM IST

### Check Deploy Logs:
1. Go to "Deployments"
2. Look for automated deployments triggered daily
3. Each should show "Triggered via Deploy Hook"

### Test the Cron Endpoint Manually:
```bash
# Replace with your actual values
curl -X GET https://your-site.vercel.app/api/cron/daily-publish \
  -H "Authorization: Bearer your-cron-secret"
```

## 🛠️ Troubleshooting

### Posts Not Appearing?
1. **Check the date format** in your posts:
   ```yaml
   pubDate: 'Dec 09 2025'  # ✅ Correct
   ```

2. **Verify cron job is running**:
   - Check Vercel Logs for cron executions
   - Look for any errors

3. **Check environment variables**:
   - Make sure `CRON_SECRET` and `VERCEL_DEPLOY_HOOK` are set
   - Redeploy after adding them

### Cron Job Not Triggering?
1. **Verify vercel.json** is in the root directory
2. **Check the cron schedule** is valid
3. **Ensure you're on a Vercel Pro plan** (cron jobs require Pro plan)
   - If on Hobby plan, you can use GitHub Actions instead (see below)

## 💡 Alternative: GitHub Actions (For Hobby Plan)

If you're on Vercel's Hobby plan (which doesn't support cron jobs), use GitHub Actions instead:

1. Create `.github/workflows/daily-publish.yml`:
```yaml
name: Daily Publish

on:
  schedule:
    - cron: '30 0 * * *'  # 6:00 AM IST daily
  workflow_dispatch:  # Allow manual trigger

jobs:
  trigger-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Vercel Deploy
        run: |
          curl -X POST ${{ secrets.VERCEL_DEPLOY_HOOK }}
```

2. Add `VERCEL_DEPLOY_HOOK` to GitHub Secrets:
   - Go to your GitHub repo → Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `VERCEL_DEPLOY_HOOK`
   - Value: Your Vercel Deploy Hook URL
   - Click "Add secret"

## 📊 Monitoring Your Posts

### View Scheduled Posts:
```bash
# See all posts with their publish dates
grep -r "pubDate:" src/content/blog/*.md | head -20
```

### Count Posts by Month:
```bash
# Count posts scheduled for each month
grep -r "pubDate:" src/content/blog/*.md | cut -d"'" -f2 | cut -d' ' -f1 | sort | uniq -c
```

## 🎉 You're All Set!

Once deployed with the environment variables configured:
- ✅ Your site will rebuild automatically every day at 6:00 AM IST
- ✅ One new post will appear each day
- ✅ You have 209 days of content scheduled
- ✅ No manual work required!

## 📝 Adding More Posts Later

When you want to add more posts:

1. Create new markdown files with future dates
2. Push to GitHub
3. Vercel will automatically deploy
4. The new posts will appear on their scheduled dates

---

**Need Help?** Check the Vercel documentation:
- [Cron Jobs](https://vercel.com/docs/cron-jobs)
- [Deploy Hooks](https://vercel.com/docs/deployments/deploy-hooks)
- [Environment Variables](https://vercel.com/docs/environment-variables)
