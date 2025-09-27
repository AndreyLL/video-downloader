# 🚀 Deploy to Render.com - Step by Step

## Prerequisites
- GitHub account
- Render.com account (free)

## Step 1: Push Code to GitHub

1. Create a new repository on GitHub
2. Push these files:
```bash
git init
git add app.py requirements.txt render.yaml
git commit -m "Video downloader server"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/video-downloader-server.git
git push -u origin main
```

## Step 2: Deploy on Render.com

### Method 1: Using render.yaml (Automatic)

1. Go to https://dashboard.render.com
2. Click **New +** → **Web Service**
3. Connect your GitHub account if not connected
4. Select your repository: `video-downloader-server`
5. Render will detect `render.yaml` automatically
6. Click **Create Web Service**

### Method 2: Manual Setup

1. Go to https://dashboard.render.com
2. Click **New +** → **Web Service**
3. Connect GitHub and select your repo
4. Configure:
   - **Name**: `video-downloader` (or any name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
5. Click **Create Web Service**

## Step 3: Wait for Deployment

- Render will build and deploy automatically
- Takes about 3-5 minutes
- You'll get a URL like: `https://video-downloader-xxx.onrender.com`

## Step 4: Test Your API

```bash
# Test the API
curl -X POST https://your-app.onrender.com/download \
  -H "Content-Type: application/json" \
  -d '{"url":"https://customer-jzsbiavb05u7bp8k.cloudflarestream.com/879af0ce5977583ce66a6703c7f506de/manifest/video.m3u8"}'
```

## Step 5: Create Frontend Client

Create `client.html` to use with your API:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Video Downloader Client</title>
    <style>
        body {
            font-family: Arial;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
        }
        input, button {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
        }
        button {
            background: #5469d4;
            color: white;
            border: none;
            cursor: pointer;
        }
        #status {
            margin-top: 20px;
            padding: 10px;
            background: #f0f0f0;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <h1>Video Downloader</h1>
    <input type="url" id="videoUrl" placeholder="Enter video URL">
    <button onclick="downloadVideo()">Download Video</button>
    <div id="status"></div>

    <script>
        const API_URL = 'https://your-app.onrender.com'; // Replace with your Render URL

        async function downloadVideo() {
            const url = document.getElementById('videoUrl').value;
            const status = document.getElementById('status');

            status.innerHTML = 'Starting download...';

            try {
                // Start download
                const response = await fetch(`${API_URL}/download`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url })
                });

                const data = await response.json();
                const downloadId = data.id;

                // Check status
                status.innerHTML = 'Processing...';

                const checkStatus = setInterval(async () => {
                    const statusRes = await fetch(`${API_URL}/status/${downloadId}`);
                    const statusData = await statusRes.json();

                    if (statusData.status === 'completed') {
                        clearInterval(checkStatus);
                        status.innerHTML = `
                            <a href="${API_URL}/file/${downloadId}" download>
                                Download Video (Click here)
                            </a>
                        `;
                    } else if (statusData.status === 'failed') {
                        clearInterval(checkStatus);
                        status.innerHTML = 'Download failed: ' + statusData.error;
                    }
                }, 2000);

            } catch (error) {
                status.innerHTML = 'Error: ' + error.message;
            }
        }
    </script>
</body>
</html>
```

## Important Notes

### Free Tier Limitations:
- **Sleeps after 15 min of inactivity** (first request will be slow)
- **Limited to 750 hours/month** (enough for personal use)
- **512 MB RAM** (sufficient for video downloading)

### To Keep Active:
- Use UptimeRobot.com to ping your service every 14 minutes
- Or upgrade to paid plan ($7/month)

### Environment Variables (Optional):
In Render dashboard → Environment:
- Add any needed API keys
- Set `PYTHON_VERSION=3.11.0`

## Troubleshooting

If deployment fails:
1. Check Logs in Render dashboard
2. Make sure `yt-dlp` is in requirements.txt
3. Try adding to requirements.txt:
```
ffmpeg-python==0.2.0
```

## Alternative: Quick Deploy Button

Add this to your GitHub README.md:

```markdown
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/YOUR_USERNAME/video-downloader-server)
```

Then anyone can deploy with one click!