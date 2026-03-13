#!/bin/bash
# RastaCoder Build Script
# Run this on a machine with Flutter installed (Linux/Mac/Windows)

set -e

echo "🦁🇯🇲 RastaCoder Build Script 🇯🇲🦁"
echo "=================================="

# Check if Flutter is installed
if ! command -v flutter &> /dev/null; then
    echo "❌ Flutter not found. Please install Flutter first."
    echo "   Download from: https://docs.flutter.dev/get-started/install"
    exit 1
fi

echo "✅ Flutter found: $(flutter --version)"

# Clean previous build
echo ""
echo "🧹 Cleaning previous builds..."
flutter clean

# Get dependencies
echo ""
echo "📦 Fetching dependencies..."
flutter pub get

# Build debug APK
echo ""
echo "🔨 Building Debug APK..."
flutter build apk --debug --split-per-abi

# Show build output
echo ""
echo "✅ Build Complete!"
echo ""
echo "📍 Debug APKs location:"
ls -lh build/app/outputs/flutter-apk/app-*-debug.apk 2>/dev/null || echo "   (build may have failed)"

echo ""
echo "📱 To install on device:"
echo "   adb install -r build/app/outputs/flutter-apk/arm64-v8a-debug.apk"
echo ""
echo "🦁 Bless up! Your RastaCoder APK is ready!"
