#!/bin/bash
# RastaCoder - Quick Image Generation with Pollinations.ai
# NO API KEY REQUIRED - 100% FREE

echo "🦁🌀 RastaCoder - Pollinations AI Image Generator 🌀🦁"
echo "======================================================="
echo ""

# Output directory
OUTPUT_DIR="nanobanana-output"
mkdir -p "$OUTPUT_DIR"

echo "📂 Output directory: $OUTPUT_DIR"
echo ""

# Function to generate image
generate_image() {
    local prompt="$1"
    local filename="$2"
    local width="${3:-1024}"
    local height="${4:-1024}"
    local seed="${5:-$RANDOM}"
    
    echo "🎨 Generating: $filename"
    echo "   Prompt: $prompt"
    echo "   Size: ${width}x${height}"
    echo "   Seed: $seed"
    
    local encoded_prompt=$(python3 -c "import urllib.parse; print(urllib.parse.quote('''$prompt'''))")
    
    curl -s -o "$OUTPUT_DIR/$filename" \
      "https://image.pollinations.ai/prompt/$encoded_prompt?width=$width&height=$height&seed=$seed&model=flux"
    
    if [ -f "$OUTPUT_DIR/$filename" ] && [ -s "$OUTPUT_DIR/$filename" ]; then
        local size=$(ls -lh "$OUTPUT_DIR/$filename" | awk '{print $5}')
        echo "   ✅ Saved: $OUTPUT_DIR/$filename ($size)"
        echo ""
    else
        echo "   ❌ Failed to generate image"
        echo ""
    fi
}

# Generate RastaCoder assets
echo "🚀 Generating RastaCoder assets..."
echo ""

# 1. App Icon variants
echo "📱 App Icons..."
generate_image \
  "Rastafarian lion of Judah logo, red gold green Ethiopian colors, minimalist app icon, vector style, white background, professional" \
  "app_icon_1.png" 512 512

generate_image \
  "Flutter robot with Rastafarian dreadlocks, red gold green accents, tech logo, clean design, app store ready" \
  "app_icon_2.png" 512 512

generate_image \
  "Python snake with lion mane, Rasta colors, coding mascot, professional icon design, simple background" \
  "app_icon_3.png" 512 512

generate_image \
  "Rasta fractal mandala, sacred geometry, red gold green spiral, psychedelic but professional, app icon" \
  "app_icon_4.png" 512 512

# 2. Splash Screen
echo "🎨 Splash Screens..."
generate_image \
  "Psychedelic Rasta fractal mandala, Lion of Judah center, sacred geometry Flower of Life pattern, red gold green neon, UV blacklight, psytrance art, dark background" \
  "splash_1.png" 1080 1920

generate_image \
  "Coding terminal with Rasta colors, matrix code rain red gold green, digital Zion, hacker aesthetic, phone wallpaper" \
  "splash_2.png" 1080 1920

# 3. Feature Graphics
echo "📰 Feature Graphics..."
generate_image \
  "RastaCoder banner, Flutter robot with dreadlocks, Python snake with lion mane, Rasta colors gradient, tech startup, marketing graphic, wide format" \
  "feature_1.png" 1024 500

generate_image \
  "RastaCoder GitHub header, dark theme, Rasta colors accent, coding symbols, professional repository banner" \
  "feature_2.png" 1280 640

# 4. Social Media
echo "📱 Social Media..."
generate_image \
  "RastaCoder Twitter header, Rastafarian colors gradient, lion silhouette, coding symbols, social media banner" \
  "twitter_header.png" 1500 500

generate_image \
  "RastaCoder Instagram post, app screenshot mockup, Rasta theme, promotional design, square format" \
  "instagram_post.png" 1080 1080

echo "========================================"
echo ""
echo "📊 Generated files:"
ls -lh "$OUTPUT_DIR"/*.png 2>/dev/null | awk '{print "   " $9 " (" $5 ")"}'
echo ""
echo "✅ Generation complete!"
echo ""
echo "🎨 To generate more:"
echo "   bash $0"
echo ""
echo "🦁 Bless up! Your RastaCoder graphics are ready!"
