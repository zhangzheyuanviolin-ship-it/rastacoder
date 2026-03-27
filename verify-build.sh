#!/bin/bash
# RastaCoder Build Verification Script
# Run this on a machine with Flutter installed (Linux/Mac/Windows)

set -e

echo "🦁🇯🇲 RastaCoder Build Verification 🇯🇲🦁"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0

# Helper functions
pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

info() {
    echo -e "${YELLOW}→${NC} $1"
}

# Section headers
section() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo " $1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Check prerequisites
section "Prerequisites Check"

if command -v flutter &> /dev/null; then
    pass "Flutter installed: $(flutter --version --machine 2>/dev/null | head -1 || flutter --version)"
else
    fail "Flutter not found"
    echo "   Install from: https://docs.flutter.dev/get-started/install"
    exit 1
fi

if command -v java &> /dev/null; then
    JAVA_VER=$(java -version 2>&1 | head -1)
    pass "Java installed: $JAVA_VER"
else
    fail "Java not found (required: Java 17)"
fi

if command -v adb &> /dev/null; then
    pass "ADB installed: $(adb --version | head -1)"
else
    info "ADB not found (optional, for device testing)"
fi

# Check Flutter doctor
section "Flutter Doctor"
flutter doctor -v 2>&1 | head -20

# Clean build
section "Step 1: Clean Build"
info "Running flutter clean..."
flutter clean
pass "Flutter clean completed"

info "Running flutter pub get..."
flutter pub get
if [ $? -eq 0 ]; then
    pass "Dependencies fetched"
else
    fail "Failed to fetch dependencies"
    exit 1
fi

# Run tests
section "Step 2: Run Tests"

info "Running Flutter tests..."
flutter test 2>&1 | tail -20
if [ $? -eq 0 ]; then
    pass "Flutter tests passed"
else
    fail "Flutter tests failed"
fi

info "Running Python tests..."
cd python && pytest -v 2>&1 | tail -30
if [ $? -eq 0 ]; then
    pass "Python tests passed"
    cd ..
else
    fail "Python tests failed"
    cd ..
fi

# Lint analysis
section "Step 3: Lint Analysis"
info "Running flutter analyze..."
flutter analyze 2>&1 | tail -50
ANALYZE_RESULT=$?
if [ $ANALYZE_RESULT -eq 0 ]; then
    pass "No lint errors"
else
    fail "Lint errors found"
fi

# Build debug APK
section "Step 4: Build Debug APK"
info "Building debug APK..."
flutter build apk --debug --split-per-abi
if [ $? -eq 0 ]; then
    pass "Debug APK built successfully"
    
    # Check APK sizes
    info "APK Sizes:"
    ls -lh build/app/outputs/flutter-apk/app-*-debug.apk 2>/dev/null || info "APKs not found"
else
    fail "Debug APK build failed"
fi

# Build release APK
section "Step 5: Build Release APK"
info "Building release APK..."
flutter build apk --release --split-per-abi
if [ $? -eq 0 ]; then
    pass "Release APK built successfully"
    
    # Check APK sizes
    info "Release APK Sizes:"
    ls -lh build/app/outputs/flutter-apk/app-*-release.apk 2>/dev/null || info "APKs not found"
    
    # Check if APK is under 100MB
    for apk in build/app/outputs/flutter-apk/app-*-release.apk; do
        if [ -f "$apk" ]; then
            SIZE=$(stat -f%z "$apk" 2>/dev/null || stat -c%s "$apk" 2>/dev/null || echo "0")
            SIZE_MB=$((SIZE / 1024 / 1024))
            if [ $SIZE_MB -lt 100 ]; then
                pass "$apk: ${SIZE_MB}MB (< 100MB target)"
            else
                fail "$apk: ${SIZE_MB}MB (> 100MB target - optimization needed)"
            fi
        fi
    done
else
    fail "Release APK build failed"
fi

# Build App Bundle
section "Step 6: Build App Bundle"
info "Building App Bundle..."
flutter build appbundle --release
if [ $? -eq 0 ]; then
    pass "App Bundle built successfully"
    
    # Check AAB size
    info "App Bundle Size:"
    ls -lh build/app/outputs/bundle/release/app-release.aab 2>/dev/null || info "AAB not found"
else
    fail "App Bundle build failed"
fi

# Install on device (if connected)
section "Step 7: Install on Device"
if adb devices | grep -q "device$"; then
    info "Device detected, installing..."
    adb install -r build/app/outputs/flutter-apk/app-arm64-v8a-debug.apk
    if [ $? -eq 0 ]; then
        pass "App installed successfully"
    else
        fail "Installation failed"
    fi
else
    info "No device connected (skipping installation)"
fi

# Summary
section "Build Verification Summary"
echo ""
echo "  Passed: $PASSED"
echo "  Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🦁 Bless up! All verifications passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Test app manually on device"
    echo "  2. Run Week 2 tasks (Rasta theme, demo video)"
    echo "  3. Prepare for launch (Week 3)"
    exit 0
else
    echo -e "${RED}❌ Some verifications failed${NC}"
    echo ""
    echo "Please fix the failures above and re-run."
    exit 1
fi
