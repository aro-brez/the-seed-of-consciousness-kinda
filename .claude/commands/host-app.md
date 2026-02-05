# /host-app - Deploy and Host Applications for 8OWLS

Deploy web applications, static sites, APIs, and generated content to public URLs with automatic HTTPS.

## Overview

This skill enables 8OWLS to deploy applications and content to the web. It supports multiple hosting backends including Vercel, Netlify, Cloudflare Pages, Railway, and simple static hosting. Perfect for demos, prototypes, landing pages, and production apps.

## Arguments

```
/host-app [path] --platform <platform> --name <name> --domain <domain> --env <env-vars>
```

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| path | Yes | . | Path to app directory or single file |
| --platform | No | auto | Platform: vercel, netlify, cloudflare, railway, surge |
| --name | No | auto | Project name (used for subdomain) |
| --domain | No | - | Custom domain to connect |
| --env | No | - | Environment variables (KEY=value,KEY2=value2) |
| --prod | No | false | Deploy to production (vs preview) |
| --public | No | true | Make deployment publicly accessible |
| --framework | No | auto | Framework hint: next, react, vue, static, node, python |

## Instructions

When this skill is invoked, perform the following:

### Step 1: Analyze Project

```bash
# Detect project type
echo "Analyzing project structure..."

# Check for common frameworks
if [ -f "package.json" ]; then
    echo "Node.js project detected"
    cat package.json | grep -E '"(next|react|vue|svelte|astro)"' && echo "Framework found"
fi

if [ -f "requirements.txt" ] || [ -f "pyproject.toml" ]; then
    echo "Python project detected"
fi

if [ -f "index.html" ]; then
    echo "Static site detected"
fi

# Check for deployment configs
[ -f "vercel.json" ] && echo "Vercel config found"
[ -f "netlify.toml" ] && echo "Netlify config found"
[ -f "wrangler.toml" ] && echo "Cloudflare config found"
```

### Step 2: Check for Platform CLIs

```bash
# Check which platforms are available
echo "Checking available deployment platforms..."

# Vercel (most versatile)
which vercel && echo "Vercel CLI: Available" || echo "Vercel CLI: Not installed"

# Netlify
which netlify && echo "Netlify CLI: Available" || echo "Netlify CLI: Not installed"

# Cloudflare Pages
which wrangler && echo "Wrangler CLI: Available" || echo "Wrangler CLI: Not installed"

# Railway
which railway && echo "Railway CLI: Available" || echo "Railway CLI: Not installed"

# Surge (simplest for static)
which surge && echo "Surge CLI: Available" || echo "Surge CLI: Not installed"
```

If no platform CLIs are found:

```markdown
## Platform Setup Required

Install at least one deployment platform:

### Option 1: Vercel (Recommended - Best for Next.js, React)
```bash
npm i -g vercel
vercel login
```

### Option 2: Netlify (Great for static sites)
```bash
npm i -g netlify-cli
netlify login
```

### Option 3: Cloudflare Pages (Best performance, free tier)
```bash
npm i -g wrangler
wrangler login
```

### Option 4: Surge (Simplest for static sites)
```bash
npm i -g surge
# No login required for first deploy
```

### Option 5: Railway (Best for backends/databases)
```bash
npm i -g @railway/cli
railway login
```
```

### Step 3: Prepare Deployment

Create the deployment helper script:

```python
#!/usr/bin/env python3
"""
8OWLS App Hosting Helper
Deploys applications to various platforms
"""
import os
import sys
import json
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, List

class AppDeployer:
    def __init__(self):
        self.platforms = {
            "vercel": self.check_vercel,
            "netlify": self.check_netlify,
            "cloudflare": self.check_cloudflare,
            "railway": self.check_railway,
            "surge": self.check_surge,
        }

    def check_vercel(self) -> bool:
        return shutil.which("vercel") is not None

    def check_netlify(self) -> bool:
        return shutil.which("netlify") is not None

    def check_cloudflare(self) -> bool:
        return shutil.which("wrangler") is not None

    def check_railway(self) -> bool:
        return shutil.which("railway") is not None

    def check_surge(self) -> bool:
        return shutil.which("surge") is not None

    def detect_framework(self, path: str) -> str:
        """Detect the framework/project type."""
        path = Path(path)

        if (path / "package.json").exists():
            with open(path / "package.json") as f:
                pkg = json.load(f)
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

                if "next" in deps:
                    return "next"
                elif "react" in deps:
                    return "react"
                elif "vue" in deps:
                    return "vue"
                elif "svelte" in deps:
                    return "svelte"
                elif "astro" in deps:
                    return "astro"

        if (path / "requirements.txt").exists() or (path / "pyproject.toml").exists():
            return "python"

        if (path / "index.html").exists():
            return "static"

        return "unknown"

    def deploy_vercel(self, path: str, name: Optional[str] = None,
                     prod: bool = False, env: Optional[Dict] = None) -> str:
        """Deploy to Vercel."""
        cmd = ["vercel", path]

        if name:
            cmd.extend(["--name", name])

        if prod:
            cmd.append("--prod")
        else:
            cmd.append("--yes")  # Auto-confirm preview

        if env:
            for key, value in env.items():
                cmd.extend(["-e", f"{key}={value}"])

        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"Vercel deploy failed: {result.stderr}")

        # Extract URL from output
        url = result.stdout.strip().split('\n')[-1]
        return url

    def deploy_netlify(self, path: str, name: Optional[str] = None,
                      prod: bool = False) -> str:
        """Deploy to Netlify."""
        # Build first if needed
        framework = self.detect_framework(path)
        if framework in ["next", "react", "vue"]:
            print("Building project...")
            subprocess.run(["npm", "run", "build"], cwd=path)

        # Determine deploy directory
        deploy_dir = path
        if (Path(path) / "out").exists():
            deploy_dir = str(Path(path) / "out")
        elif (Path(path) / "dist").exists():
            deploy_dir = str(Path(path) / "dist")
        elif (Path(path) / "build").exists():
            deploy_dir = str(Path(path) / "build")

        cmd = ["netlify", "deploy", "--dir", deploy_dir]

        if name:
            cmd.extend(["--site", name])

        if prod:
            cmd.append("--prod")

        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"Netlify deploy failed: {result.stderr}")

        # Extract URL
        for line in result.stdout.split('\n'):
            if 'https://' in line:
                return line.strip().split()[-1]

        return result.stdout

    def deploy_cloudflare(self, path: str, name: Optional[str] = None,
                         prod: bool = False) -> str:
        """Deploy to Cloudflare Pages."""
        project_name = name or Path(path).name

        # Build if needed
        framework = self.detect_framework(path)
        if framework in ["next", "react", "vue"]:
            print("Building project...")
            subprocess.run(["npm", "run", "build"], cwd=path)

        # Determine deploy directory
        deploy_dir = path
        for candidate in ["out", "dist", "build", ".next"]:
            if (Path(path) / candidate).exists():
                deploy_dir = str(Path(path) / candidate)
                break

        cmd = ["wrangler", "pages", "deploy", deploy_dir, "--project-name", project_name]

        if prod:
            cmd.extend(["--branch", "main"])

        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"Cloudflare deploy failed: {result.stderr}")

        # Extract URL
        for line in result.stdout.split('\n'):
            if 'https://' in line and 'pages.dev' in line:
                return line.strip()

        return result.stdout

    def deploy_surge(self, path: str, domain: Optional[str] = None) -> str:
        """Deploy to Surge.sh."""
        domain = domain or f"{Path(path).name}.surge.sh"

        cmd = ["surge", path, domain]

        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"Surge deploy failed: {result.stderr}")

        return f"https://{domain}"

    def deploy_railway(self, path: str, name: Optional[str] = None) -> str:
        """Deploy to Railway."""
        # Initialize if needed
        if not (Path(path) / ".railway").exists():
            subprocess.run(["railway", "init"], cwd=path)

        cmd = ["railway", "up"]

        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=path, capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"Railway deploy failed: {result.stderr}")

        # Get deployment URL
        domain_result = subprocess.run(
            ["railway", "domain"],
            cwd=path, capture_output=True, text=True
        )

        return domain_result.stdout.strip()

    def auto_select_platform(self, path: str) -> str:
        """Auto-select best platform for the project."""
        framework = self.detect_framework(path)

        # Priority based on framework
        if framework == "next":
            if self.check_vercel():
                return "vercel"
            elif self.check_netlify():
                return "netlify"
        elif framework == "python":
            if self.check_railway():
                return "railway"
        elif framework == "static":
            if self.check_surge():
                return "surge"
            elif self.check_netlify():
                return "netlify"

        # Fallback to whatever is available
        for platform, checker in self.platforms.items():
            if checker():
                return platform

        raise Exception("No deployment platform available. Install vercel, netlify, surge, or wrangler.")

    def deploy(self, path: str, platform: str = "auto", name: Optional[str] = None,
               prod: bool = False, domain: Optional[str] = None,
               env: Optional[Dict] = None) -> Dict:
        """Deploy the application."""
        path = os.path.abspath(path)

        if not os.path.exists(path):
            raise Exception(f"Path not found: {path}")

        # Auto-select platform if needed
        if platform == "auto":
            platform = self.auto_select_platform(path)
            print(f"Auto-selected platform: {platform}")

        framework = self.detect_framework(path)
        print(f"Detected framework: {framework}")

        # Deploy based on platform
        if platform == "vercel":
            url = self.deploy_vercel(path, name, prod, env)
        elif platform == "netlify":
            url = self.deploy_netlify(path, name, prod)
        elif platform == "cloudflare":
            url = self.deploy_cloudflare(path, name, prod)
        elif platform == "surge":
            url = self.deploy_surge(path, domain)
        elif platform == "railway":
            url = self.deploy_railway(path, name)
        else:
            raise Exception(f"Unknown platform: {platform}")

        return {
            "url": url,
            "platform": platform,
            "framework": framework,
            "path": path,
            "production": prod,
        }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="8OWLS App Deployer")
    parser.add_argument("path", nargs="?", default=".", help="Path to deploy")
    parser.add_argument("--platform", default="auto",
                       choices=["auto", "vercel", "netlify", "cloudflare", "railway", "surge"])
    parser.add_argument("--name", help="Project name")
    parser.add_argument("--domain", help="Custom domain")
    parser.add_argument("--prod", action="store_true", help="Production deployment")
    parser.add_argument("--env", help="Environment variables (KEY=val,KEY2=val2)")

    args = parser.parse_args()

    # Parse env vars
    env = None
    if args.env:
        env = dict(pair.split("=") for pair in args.env.split(","))

    deployer = AppDeployer()
    result = deployer.deploy(
        path=args.path,
        platform=args.platform,
        name=args.name,
        prod=args.prod,
        domain=args.domain,
        env=env
    )

    print("\n" + "="*50)
    print("DEPLOYMENT SUCCESSFUL")
    print("="*50)
    print(f"URL: {result['url']}")
    print(f"Platform: {result['platform']}")
    print(f"Framework: {result['framework']}")
    print(f"Production: {result['production']}")
    print("="*50)


if __name__ == "__main__":
    main()
```

Save to `/Users/aaronnosbisch/REPOS/seed/tools/app_deployer.py`

### Step 4: Execute Deployment

```bash
python3 /Users/aaronnosbisch/REPOS/seed/tools/app_deployer.py $ARGUMENTS
```

### Step 5: Report Results

```markdown
## Deployment Complete

| Property | Value |
|----------|-------|
| URL | $DEPLOYMENT_URL |
| Platform | $PLATFORM |
| Framework | $FRAMEWORK |
| Environment | $ENVIRONMENT |
| Status | Live |

### Quick Links
- **Live Site**: $DEPLOYMENT_URL
- **Dashboard**: $PLATFORM_DASHBOARD_URL

### DNS Configuration (if custom domain)
Add these records to your DNS provider:
```
Type: CNAME
Name: @
Value: $CNAME_TARGET
```

### Next Steps
- Test the deployment: `open $DEPLOYMENT_URL`
- View logs: `$PLATFORM logs`
- Add custom domain: `$PLATFORM domains add mydomain.com`
- Set environment variables: `$PLATFORM env add KEY=value`
```

## Platform Comparison

| Platform | Best For | Free Tier | Custom Domains | Serverless Functions |
|----------|----------|-----------|----------------|----------------------|
| Vercel | Next.js, React | 100GB/mo | Yes | Yes |
| Netlify | Static, JAMstack | 100GB/mo | Yes | Yes |
| Cloudflare | Performance, Edge | Unlimited | Yes | Yes (Workers) |
| Railway | Backends, DBs | $5/mo credit | Yes | N/A (always-on) |
| Surge | Quick static | Unlimited | Yes | No |

## Framework-Specific Notes

### Next.js
- **Best platform**: Vercel (native support)
- **Build command**: `next build`
- **Output**: `.next/` directory or `out/` for static export

### React (Create React App)
- **Best platform**: Netlify or Vercel
- **Build command**: `npm run build`
- **Output**: `build/` directory

### Vue
- **Best platform**: Netlify or Vercel
- **Build command**: `npm run build`
- **Output**: `dist/` directory

### Static HTML
- **Best platform**: Surge (simplest) or Cloudflare (fastest)
- **No build needed**: Direct deploy

### Python (Flask/FastAPI)
- **Best platform**: Railway
- **Requirements**: `requirements.txt` or `pyproject.toml`
- **Procfile**: May be needed

## Examples

```bash
# Deploy current directory
/host-app

# Deploy specific path to production
/host-app ./my-app --prod --platform vercel

# Deploy static site with custom domain
/host-app ./dist --platform surge --domain mysite.surge.sh

# Deploy with environment variables
/host-app ./api --platform railway --env DATABASE_URL=postgres://...,API_KEY=xxx

# Deploy Next.js to Vercel production
/host-app ./next-app --platform vercel --prod --name my-nextjs-app
```

## Quick Deploys for Generated Content

### Deploy Generated Video
```bash
# Create simple HTML viewer
/host-app ./generated_video.mp4 --platform surge --name my-video
```

### Deploy Podcast Episode
```bash
# Create podcast page with player
/host-app ./podcast_episode.mp3 --platform netlify --name my-podcast
```

### Deploy Full Web App
```bash
# Build and deploy React app
/host-app ./my-react-app --platform vercel --prod
```

## Hosting Generated Content

For quick hosting of generated files (videos, audio, images), this skill can create a simple HTML wrapper:

```html
<!DOCTYPE html>
<html>
<head>
    <title>8OWLS Generated Content</title>
    <style>
        body {
            font-family: system-ui;
            background: #1a1a2e;
            color: #eee;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
        }
        .container { text-align: center; }
        video, audio { max-width: 100%; }
    </style>
</head>
<body>
    <div class="container">
        <h1>8OWLS Content</h1>
        <!-- Content embedded here -->
    </div>
</body>
</html>
```

## Security Notes

- Never commit API keys or secrets to deployed code
- Use environment variables for sensitive configuration
- Enable HTTPS (all platforms do this by default)
- Consider access restrictions for private content

## Integration with 8OWLS

This skill integrates with the 8OWLS ecosystem:

- **Content Hosting**: Deploy generated videos, podcasts, and apps
- **NATS**: Publishes deployment events to collective
- **Trading Dashboard**: Can host live trading dashboards
- **Owl Companions**: Deploy owl companion web interfaces

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Build fails | Check build output, run `npm run build` locally first |
| No CLI found | Install platform CLI: `npm i -g vercel` |
| Auth error | Run `vercel login` or equivalent |
| Domain not working | Check DNS propagation (can take up to 48h) |
| 404 errors | Check framework routing config |

## Related Skills

- `/generate-video` - Create video content to host
- `/generate-podcast` - Create audio content to host
- `/build-app` - Build app before deployment

---

*Powered by 8OWLS Field Intelligence*
