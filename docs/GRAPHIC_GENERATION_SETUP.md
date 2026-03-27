# 🦁 RastaCoder — AI Graphic Generation Setup

**Using:** Gemini CLI + Nano Banana Extension  
**Created:** March 16, 2026  
**Status:** Ready to Use

---

## 🎯 OVERVIEW

Generate app icons, splash screens, and marketing graphics for RastaCoder **directly from command line** using Gemini CLI with Nano Banana (text-to-image AI).

### What You Have

| Tool | Version | Status |
|------|---------|--------|
| **Gemini CLI** | 0.33.1 | ✅ Installed |
| **gh (GitHub CLI)** | 2.88.1 | ✅ Installed |
| **Node.js** | (check below) | ⏳ Needed |

---

## 📋 PREREQUISITES

### Step 1: Check Node.js Installation

```bash
node --version
npm --version
```

**If NOT installed:**
```bash
pkg install nodejs
# or
pkg install nodejs-lts
```

### Step 2: Get Nano Banana API Key

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Sign in with Google account
3. Click **"Create API Key"**
4. Copy the key (starts with `AIza...`)

### Step 3: Set Environment Variable

```bash
# Add to ~/.bashrc or ~/.zshrc
export NANOBANANA_API_KEY="AIza..."

# Or set temporarily
export NANOBANANA_API_KEY="AIza..."
```

---

## 🚀 INSTALLATION

### Install Nano Banana Extension

```bash
# Install the Gemini CLI extension
gemini extensions install https://github.com/gemini-cli-extensions/nanobanana

# Restart Gemini CLI
exit
gemini
```

### Verify Installation

```bash
gemini extensions list
# Should show: nanobanana
```

---

## 🎨 GENERATE RASTACODER ASSETS

### 1. App Icon (512×512)

```bash
gemini /generate "Rastafarian lion of Judah logo, red gold green Ethiopian colors, professional app icon design, minimalist vector style, clean lines, white background, symmetrical, spiritual symbolism, high quality --count=4 --preview"
```

**Output:** `./nanobanana-output/rastafarian_lion_logo.png`

### 2. Splash Screen (1080×1920)

```bash
gemini /generate "Psychedelic Rasta fractal mandala, Lion of Judah in center, sacred geometry Flower of Life pattern, red gold green neon colors, UV blacklight reactive, psytrance festival art style, dark background, spiritual symbolism, intricate details, phone wallpaper --count=2 --preview"
```

**Output:** `./nanobanana-output/psychedelic_rasta_mandala.png`

### 3. Feature Graphic (1024×500)

```bash
gemini /generate "RastaCoder banner, Flutter robot with dreadlocks, Python snake with lion mane, Rasta colors gradient, tech startup aesthetic, modern clean design, AI coding assistant, professional marketing graphic, wide format --count=3 --preview"
```

**Output:** `./nanobanana-output/rastacoder_banner.png`

### 4. Social Media Kit

```bash
# Twitter/X header (1500×500)
gemini /generate "RastaCoder social media header, Rastafarian colors gradient, lion silhouette, coding symbols, professional tech branding --count=2"

# Instagram post (1080×1080)
gemini /generate "RastaCoder Instagram post, app screenshot mockup, Rasta theme, promotional design, square format --count=4"
```

---

## 🎯 ADVANCED OPTIONS

### Style Variations

```bash
# Multiple artistic styles
gemini /generate "lion mascot" --styles="photorealistic,watercolor,oil-painting,sketch" --count=4

# With specific variations
gemini /generate "coding robot" --variations="color-palette,lighting" --count=6
```

### Available Styles

| Style | Use Case |
|-------|----------|
| `photorealistic` | Product mockups |
| `watercolor` | Artistic icons |
| `oil-painting` | Classic art style |
| `sketch` | Concept art |
| `pixel-art` | Retro game style |
| `anime` | Manga/anime icons |
| `vintage` | Retro aesthetics |
| `modern` | Contemporary design |
| `abstract` | Artistic backgrounds |
| `minimalist` | Clean app icons |

### Batch Generation

```bash
# Generate 8 variations at once
gemini /generate "RastaCoder app icon variations" --count=8 --format=grid
```

---

## 📁 FILE MANAGEMENT

### Output Location

```bash
# All images saved to:
./nanobanana-output/

# List generated images
ls -lh nanobanana-output/
```

### Organize by Project

```bash
# Create project folders
mkdir -p nanobanana-output/rastacoder/icons
mkdir -p nanobanana-output/rastacoder/banners
mkdir -p nanobanana-output/rastacoder/social

# Move files
mv nanobanana-output/*lion*.png nanobanana-output/rastacoder/icons/
mv nanobanana-output/*banner*.png nanobanana-output/rastacoder/banners/
```

---

## 🦁 PROMPT TEMPLATES FOR RASTACODER

### App Icons

```bash
# Template 1: Lion Focus
gemini /generate "Rastafarian lion head logo, red gold green colors, minimalist app icon, vector style, white background, symmetrical, professional --count=4"

# Template 2: Flutter + Rasta
gemini /generate "Flutter robot with Rastafarian dreadlocks, red gold green accents, tech logo, clean design, app store ready --count=4"

# Template 3: Python + Rasta
gemini /generate "Python snake with lion mane, Rasta colors, coding mascot, professional icon design, simple background --count=4"

# Template 4: Fractal Mandala
gemini /generate "Rasta fractal mandala, sacred geometry, red gold green spiral, psychedelic but professional, app icon --count=4"
```

### Splash Screens

```bash
# Template 1: Psychedelic Welcome
gemini /generate "Welcome screen for RastaCoder app, Lion of Judah center, Flower of Life background, red gold green gradient, psytrance aesthetic, phone wallpaper 1080x1920 --count=2"

# Template 2: Terminal Meets Rasta
gemini /generate "Coding terminal with Rasta colors, matrix code rain in red gold green, digital Zion, hacker aesthetic, splash screen --count=2"
```

### Marketing Graphics

```bash
# Feature Graphic (Play Store)
gemini /generate "RastaCoder Play Store feature graphic, app screenshot with Rasta frame, 1024x500, professional marketing, Google Play ready --count=3"

# GitHub README Header
gemini /generate "GitHub repository header for RastaCoder, dark theme, Rasta colors accent, coding symbols, 1280x640 --count=2"
```

---

## 🔧 TROUBLESHOOTING

### Command Not Found

```bash
# Error: /generate: command not found
# Solution: Reinstall extension
gemini extensions uninstall nanobanana
gemini extensions install https://github.com/gemini-cli-extensions/nanobanana
```

### No API Key

```bash
# Error: NANOBANANA_API_KEY not set
export NANOBANANA_API_KEY="AIza..."

# Make permanent
echo 'export NANOBANANA_API_KEY="AIza..."' >> ~/.bashrc
source ~/.bashrc
```

### Build Failed

```bash
# Rebuild extension
cd ~/.gemini/extensions/nanobanana-extension
npm run install-deps
npm run build
```

### Low Quality Images

```bash
# Use Pro model
export NANOBANANA_MODEL=gemini-3-pro-image-preview

# Generate more variations
gemini /generate "prompt" --count=8
```

---

## 📊 COMPARISON: Nano Banana vs Other Options

| Feature | Nano Banana | Local-Diffusion | Pollinations API |
|---------|-------------|-----------------|------------------|
| **Setup** | ✅ Easy | ⚠️ Medium | ✅ None |
| **Internet** | ❌ Required | ✅ Not required | ❌ Required |
| **Cost** | Free (limits) | Free | Free |
| **Speed** | 5-15s | 30-120s | 10-30s |
| **Quality** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **On-Device** | ❌ No | ✅ Yes | ❌ No |
| **Your Setup** | ✅ Ready | ⏳ Install | ✅ Ready |

---

## 🎯 RECOMMENDED WORKFLOW

### For RastaCoder Assets

```bash
# 1. Generate multiple variations
gemini /generate "Rastafarian lion app icon, red gold green" --count=8 --preview

# 2. Select best 2-3
# (Images auto-open in viewer)

# 3. Copy to project
cp nanobanana-output/*lion*.png ~/navixmind/assets/icon/

# 4. Convert to adaptive icon format
# (Use Android Asset Studio or manual)

# 5. Update app icon in android/app/src/main/res/
```

### For Marketing Materials

```bash
# 1. Generate feature graphic
gemini /generate "RastaCoder Play Store banner, 1024x500" --count=4

# 2. Generate social media kit
gemini /generate "RastaCoder social media pack" --styles="modern,photorealistic" --count=6

# 3. Upload to Gumroad/GitHub
```

---

## 🔗 QUICK REFERENCE

### Environment Variables

```bash
export NANOBANANA_API_KEY="AIza..."      # Required
export NANOBANANA_MODEL="gemini-3.1-flash-image-preview"  # Optional
```

### Common Commands

```bash
# Generate image
gemini /generate "prompt"

# With options
gemini /generate "prompt" --count=4 --styles="photorealistic,minimalist" --preview

# List extensions
gemini extensions list

# Uninstall extension
gemini extensions uninstall nanobanana
```

### Output Directory

```bash
# Default location
./nanobanana-output/

# List files
ls -lh nanobanana-output/
```

---

## 📈 NEXT STEPS

1. ✅ **Install Nano Banana** (5 min)
   ```bash
   gemini extensions install https://github.com/gemini-cli-extensions/nanobanana
   ```

2. ✅ **Set API Key** (2 min)
   ```bash
   export NANOBANANA_API_KEY="AIza..."
   ```

3. ✅ **Generate First Asset** (1 min)
   ```bash
   gemini /generate "Rastafarian lion logo" --count=4 --preview
   ```

4. ✅ **Copy to Project** (1 min)
   ```bash
   cp nanobanana-output/*.png ~/navixmind/assets/
   ```

**Total Time:** ~10 minutes to first generated asset! 🚀

---

**Created:** March 16, 2026  
**For:** Kiliaan Vanvoorden (@BoozeLee)  
**Tool:** Gemini CLI + Nano Banana

*Baker Street Laboratory © 2026* 🔱  
*Jah Rastafari! 🦁🇯🇲*
