# 🔐 Dashboard Security & Password Setup

## Local Development

The password is stored in `.streamlit/secrets.toml`:
```toml
dashboard_password = "admin123"
```

To change the local password, edit this file and restart the dashboard.

## Streamlit Cloud Deployment

### Setting the Password in Streamlit Cloud

1. **Go to Streamlit Cloud**: https://share.streamlit.io
2. **Select your app** (marketing-analytics-dashboard)
3. **Click on "Manage app"** (top right)
4. **Go to "Secrets"** tab
5. **Add the password**:
   ```
   dashboard_password = "your-secure-password-here"
   ```
6. **Click "Save"** - app will automatically redeploy with the new password

### Sharing the Link

Once deployed:
1. Share your Streamlit Cloud app URL: `https://share.streamlit.io/[your-username]/marketing-analytics-dashboard`
2. Users will see the password prompt when they visit
3. Only people who know the password can access the dashboard

### Best Practices

✅ Use a strong password (8+ characters, mix of letters/numbers/symbols)  
✅ Change password regularly  
✅ Don't share password in unsecured channels  
✅ For multiple users, use different passwords in different environments  

## Current Default Password

Local testing: `admin123`

⚠️ **CHANGE THIS IMMEDIATELY** in Streamlit Cloud to your secure password!
