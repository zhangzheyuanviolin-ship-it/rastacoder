#!/bin/bash
# RastaCoder - Quick Graphic Generation Setup
# Run this after getting your Gemini API key

echo "🦁🌀 RastaCoder Graphic Generation Setup 🌀🦁"
echo "=============================================="
echo ""

# Check if API key is set
if [ -z "$NANOBANANA_API_KEY" ]; then
    echo "⚠️  NANOBANANA_API_KEY not set!"
    echo ""
    echo "📋 Get your API key:"
    echo "   1. Go to: https://aistudio.google.com/apikey"
    echo "   2. Sign in with Google"
    echo "   3. Click 'Create API Key'"
    echo "   4. Copy the key (starts with AIza...)"
    echo ""
    echo "🔧 Then run:"
    echo "   export NANOBANANA_API_KEY=\"AIza...\""
    echo ""
    echo "💡 Or add to ~/.bashrc for permanent setup:"
    echo "   echo 'export NANOBANANA_API_KEY=\"AIza...\"' >> ~/.bashrc"
    echo "   source ~/.bashrc"
    echo ""
    exit 1
fi

echo "✅ API key found!"
echo ""

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VER=$(node --version)
    echo "✅ Node.js: $NODE_VER"
else
    echo "❌ Node.js not found!"
    echo "   Install: pkg install nodejs"
    exit 1
fi

# Check Gemini CLI
if command -v gemini &> /dev/null; then
    GEMINI_VER=$(gemini --version)
    echo "✅ Gemini CLI: $GEMINI_VER"
else
    echo "❌ Gemini CLI not found!"
    exit 1
fi

echo ""
echo "📦 Installing Nano Banana extension..."
gemini extensions install https://github.com/gemini-cli-extensions/nanobanana

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Installation complete!"
    echo ""
    echo "🎨 Generate your first RastaCoder asset:"
    echo ""
    echo "   gemini /generate \"Rastafarian lion logo, red gold green, app icon\" --count=4 --preview"
    echo ""
    echo "📂 Output will be saved to: ./nanobanana-output/"
    echo ""
    echo "🦁 Bless up! Your graphic generator is ready!"
else
    echo ""
    echo "❌ Installation failed!"
    echo "   Check error messages above"
    exit 1
fi
