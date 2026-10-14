# Vercel Web Analytics Setup Guide

This document explains how Vercel Web Analytics has been configured for this HealthMate AI Streamlit application.

## What Was Implemented

### 1. Analytics Script Injection
Added Vercel Web Analytics tracking script to `app.py` using Streamlit's `components.v1.html` function. This injects the analytics script into every page of the application.

### 2. Implementation Details

The analytics integration is located in `app.py` immediately after the page configuration:

```python
from streamlit.components.v1 import html

# Inject Vercel Analytics script
vercel_analytics_script = """
<script>
  window.va = window.va || function () { 
    (window.vaq = window.vaq || []).push(arguments); 
  };
</script>
<script defer src="/_vercel/insights/script.js"></script>
"""
html(vercel_analytics_script, height=0)
```

### 3. Vercel Configuration
Created `vercel.json` to ensure proper deployment configuration for the Streamlit application on Vercel.

## How It Works

1. **Script Loading**: The analytics script is loaded from Vercel's CDN via the `/_vercel/insights/script.js` endpoint
2. **Page Tracking**: Analytics automatically tracks page views and user interactions
3. **Data Collection**: Visitor data is collected and sent to Vercel's analytics dashboard
4. **Zero Height Injection**: Using `height=0` ensures the HTML component doesn't create visible space in the UI

## Enabling Analytics in Vercel Dashboard

To activate analytics for your deployed application:

1. Go to your project in the [Vercel Dashboard](https://vercel.com/dashboard)
2. Navigate to the **Analytics** tab
3. Click the **Enable** button
4. Deploy your application (or redeploy if already deployed)
5. The `/_vercel/insights/*` routes will be automatically added

## Verifying Analytics

After deployment, verify that analytics is working:

1. Visit your deployed application
2. Open browser DevTools (F12)
3. Go to the **Network** tab
4. Look for requests to `/_vercel/insights/script.js` and `/_vercel/insights/view`
5. If these requests are present, analytics is working correctly

## Viewing Analytics Data

Analytics data will appear in your Vercel dashboard after:
- You enable analytics in the dashboard
- Your application receives visitor traffic
- A few days have passed (data is processed in batches)

## Framework-Specific Considerations

Since this is a **Streamlit (Python)** application rather than a JavaScript framework:

- We cannot use the `@vercel/analytics` npm package directly
- Instead, we inject the analytics script using Streamlit's HTML component feature
- This approach is equivalent to the "HTML/Static Sites" method from the Vercel docs
- All standard Vercel Analytics features are supported with this method

## Performance Impact

- The script loads asynchronously (`defer` attribute)
- No blocking of page rendering
- Minimal performance overhead
- Script is cached by browsers after first load

## Privacy & Data Collection

Vercel Web Analytics:
- Does not use cookies
- Does not track personal information
- Collects only aggregated visitor metrics
- Is GDPR and privacy-regulation compliant
- Does not require cookie consent banners

## Troubleshooting

If analytics data isn't appearing:

1. **Check Dashboard**: Ensure analytics is enabled in Vercel dashboard
2. **Verify Deployment**: Confirm the app is deployed to Vercel (not local development)
3. **Check Network**: Use browser DevTools to verify script loads successfully
4. **Wait for Data**: Analytics data may take a few days to appear initially
5. **Check Blockers**: Ad blockers or privacy extensions may block analytics scripts

## Additional Resources

- [Vercel Web Analytics Quickstart](https://vercel.com/docs/analytics/quickstart)
- [Vercel Analytics Package Documentation](https://vercel.com/docs/analytics/package)
- [Streamlit HTML Components](https://docs.streamlit.io/library/components/components-api)

---

**Note**: This implementation follows the official Vercel documentation and best practices for integrating analytics into non-JavaScript framework applications.
