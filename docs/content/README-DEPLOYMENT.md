# 📚 QuantumForge Documentation Server

Beautiful, searchable documentation powered by MkDocs Material running on port **3002**.

## 🚀 Quick Start

### Option 1: Automatic Setup (Recommended)

```bash
cd docs/
./start-docs-server.sh
```

Follow the interactive menu:
- Option 1: Development server (localhost)
- Option 3: Docker (production-ready)

### Option 2: Manual Setup

```bash
cd docs/

# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start server
mkdocs serve --dev-addr=0.0.0.0:3002
```

### Option 3: Docker

```bash
cd docs/

# Build and run
docker-compose -f docker-compose.docs.yml up -d

# View logs
docker-compose -f docker-compose.docs.yml logs -f

# Stop
docker-compose -f docker-compose.docs.yml down
```

---

## 🌐 Access Documentation

After starting the server:

- **Local**: http://localhost:3002
- **Network**: http://YOUR_IP:3002
- **Search**: http://localhost:3002/search

---

## 📁 Project Structure

```
docs/
├── mkdocs.yml                 # MkDocs configuration
├── index.md                   # Homepage
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker image
├── docker-compose.docs.yml    # Docker Compose config
├── start-docs-server.sh       # Startup script
├── stylesheets/
│   └── extra.css             # Custom styles
├── javascripts/
│   └── extra.js              # Custom scripts
└── user-guide/               # User documentation
    ├── README.md
    ├── 01-getting-started.md
    ├── 02-creating-your-first-bot.md
    ├── 03-bot-configuration.md
    ├── 04-llm-integration.md
    ├── 05-prompt-engineering.md
    ├── 06-multi-pair-trading.md
    ├── 07-publishing-to-marketplace.md
    ├── 08-risk-management.md
    ├── 09-backtesting.md
    ├── faq.md
    └── troubleshooting.md
```

---

## ⚙️ Configuration

### Port Configuration

Edit `mkdocs.yml` or command line:

```bash
# Change port from 3002 to another
mkdocs serve --dev-addr=0.0.0.0:8080
```

### Theme Customization

Edit `mkdocs.yml`:

```yaml
theme:
  name: material
  palette:
    primary: deep purple  # Change color
    accent: purple
```

### Add New Pages

1. Create markdown file in appropriate directory
2. Add to `nav` section in `mkdocs.yml`:

```yaml
nav:
  - User Guide:
    - Your New Page: user-guide/new-page.md
```

---

## 🔧 Available Commands

### Development

```bash
# Start dev server with live reload
mkdocs serve --dev-addr=0.0.0.0:3002

# Build static site
mkdocs build

# Clean build artifacts
mkdocs build --clean
```

### Production

```bash
# Build optimized static site
mkdocs build --clean --strict

# Serve static files (nginx)
nginx -c nginx.conf
```

### Docker

```bash
# Build image
docker build -t quantumforge-docs .

# Run container
docker run -d -p 3002:3002 --name docs quantumforge-docs

# View logs
docker logs -f docs

# Stop container
docker stop docs && docker rm docs
```

---

## 🎨 Features

### ✅ Enabled Features

- **Search** - Full-text search across all documentation
- **Dark Mode** - Automatic dark/light theme switching
- **Navigation** - Tabbed navigation with breadcrumbs
- **Code Highlighting** - Syntax highlighting for 100+ languages
- **Copy Button** - One-click code copying
- **Mermaid Diagrams** - Draw diagrams in markdown
- **Git Integration** - Shows last update time
- **Mobile Responsive** - Works on all devices

### 🎯 Custom Features

- Reading time estimator
- Smooth scrolling
- External link indicators
- Enhanced code blocks
- Custom purple theme
- Animated page transitions

---

## 📊 Performance

### Build Stats

```
Pages: 30+
Build time: ~5 seconds
Site size: ~15 MB
Load time: <1 second
```

### Optimization

- Minified HTML/CSS/JS
- Compressed images
- Lazy loading
- CDN-ready

---

## 🔒 Production Deployment

### Using Nginx

1. **Build static site:**
   ```bash
   mkdocs build --clean
   ```

2. **Configure Nginx:**
   ```nginx
   server {
       listen 80;
       server_name docs.quantumforge.ai;
       
       root /path/to/docs/site;
       index index.html;
       
       location / {
           try_files $uri $uri/ =404;
       }
   }
   ```

3. **Restart Nginx:**
   ```bash
   sudo nginx -s reload
   ```

### Using Docker + Nginx

```bash
# Build and run
docker-compose -f docker-compose.docs.yml up -d

# Nginx will serve on port 80/443
```

### Using GitHub Pages

```bash
# Deploy to GitHub Pages
mkdocs gh-deploy
```

---

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Find process using port 3002
lsof -i :3002

# Kill process
kill -9 <PID>
```

### Dependencies Issues

```bash
# Clean install
rm -rf venv/
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Docker Issues

```bash
# Rebuild image
docker-compose -f docker-compose.docs.yml build --no-cache

# Remove all containers
docker-compose -f docker-compose.docs.yml down -v
```

### Build Errors

```bash
# Check for errors
mkdocs build --strict

# Validate config
mkdocs build --verbose
```

---

## 📝 Contributing

### Adding Documentation

1. Create/edit markdown file
2. Add to navigation in `mkdocs.yml`
3. Test locally: `mkdocs serve`
4. Build: `mkdocs build`
5. Commit changes

### Style Guide

- Use clear headings (H1-H4)
- Add code examples
- Include diagrams where helpful
- Link to related pages
- Add admonitions for important notes

**Example:**

```markdown
# Page Title

Brief introduction.

## Section

Content here.

!!! tip "Pro Tip"
    Helpful information

\`\`\`python
# Code example
print("Hello World")
\`\`\`

[Link to another page](./other-page.md)
```

---

## 🔄 Auto-Deployment (CI/CD)

### GitHub Actions

Create `.github/workflows/docs.yml`:

```yaml
name: Deploy Docs

on:
  push:
    branches: [main]
    paths: ['docs/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: 3.11
      - name: Install dependencies
        run: |
          cd docs
          pip install -r requirements.txt
      - name: Build docs
        run: |
          cd docs
          mkdocs build
      - name: Deploy
        run: |
          # Your deployment script
```

---

## 📚 Resources

- [MkDocs Documentation](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [Markdown Guide](https://www.markdownguide.org/)
- [Mermaid Diagrams](https://mermaid.js.org/)

---

## 🆘 Support

- 📧 Email: docs@quantumforge.ai
- 💬 Discord: [Join Community](https://discord.gg/quantumforge)
- 🐛 Issues: [GitHub](https://github.com/quantumforge/docs/issues)

---

## 📜 License

Documentation is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

Code examples are licensed under [MIT License](https://opensource.org/licenses/MIT).

---

**Built with ❤️ by the QuantumForge Team**

