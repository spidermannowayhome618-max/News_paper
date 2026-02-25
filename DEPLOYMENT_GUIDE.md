# PythonAnywhere Deployment Guide for News Website

## Step 1: Create PythonAnywhere Account
1. Go to [pythonanywhere.com](https://www.pythonanywhere.com)
2. Sign up for a free account (Free tier is sufficient for basic usage)

## Step 2: Upload Your Files
1. Go to **Files** tab in PythonAnywhere dashboard
2. Upload all your project files:
   - `app.py`
   - `requirements.txt`
   - `templates/` folder (with index.html and article.html)
   - `static/` folder (if you add any CSS/JS files)

**Upload Methods:**
- Use the web interface (Files → Upload a file)
- Or use PythonAnywhere console with git:
  ```bash
  git clone your-repo-url
  ```

## Step 3: Set Up Virtual Environment
1. Go to **Consoles** tab
2. Start a new **Bash** console
3. Create virtual environment:
   ```bash
   virtualenv venv
   source venv/bin/activate
   ```

## Step 4: Install Dependencies
In your Bash console, run:
```bash
pip install -r requirements.txt
```

## Step 5: Configure Web Application
1. Go to **Web** tab
2. Click **"Add a new web app"**
3. Choose:
   - **Framework**: Flask
   - **Python version**: 3.9 or 3.10
   - **Project path**: `/home/yourusername/News_paper`
4. Edit the **WSGI configuration file**:
   - Click on the WSGI file link
   - Replace the content with:
   ```python
   import sys
   import os
   
   # Add your project directory to the Python path
   project_home = '/home/yourusername/News_paper'
   if project_home not in sys.path:
       sys.path = [project_home] + sys.path
   
   # Import your Flask app
   from app import app as application
   ```

## Step 6: Update Flask App for Production
Make sure your `app.py` has this at the end:
```python
if __name__ == '__main__':
    app.run(debug=True)
```

The production server will use `app` object directly.

## Step 7: Test Your Application
1. Go back to **Web** tab
2. Click **"Reload"** button
3. Your website should be available at: `http://yourusername.pythonanywhere.com`

## Step 8: Troubleshooting Common Issues

### If you get "ModuleNotFoundError":
- Make sure you activated virtual environment
- Reinstall dependencies: `pip install -r requirements.txt`

### If you get "Template not found":
- Check that templates folder is in the correct location
- Verify file paths in your Flask app

### If the site is slow:
- Free tier has limited CPU, this is normal
- Consider upgrading to paid tier for better performance

## Step 9: Custom Domain (Optional)
1. Go to **Web** tab → **"Set up a custom domain"**
2. Follow the instructions to point your domain
3. Free SSL certificate is provided

## Important Notes:
- **Free tier limitations**: 100,000 requests/month, limited CPU
- **Your site URL**: `http://yourusername.pythonanywhere.com`
- **Always reload** after making code changes
- **Check error logs** in Web tab if something goes wrong

## File Structure After Upload:
```
/home/yourusername/
└── News_paper/
    ├── app.py
    ├── requirements.txt
    └── templates/
        ├── index.html
        └── article.html
```

## Next Steps:
1. Upload your files
2. Follow the steps above
3. Test your live website
4. Share the URL with others!
