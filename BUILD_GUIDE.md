# 🦁 RastaCoder Build Guide

**App Name:** RastaCoder  
**Package:** `ai.rastacoder`  
**Platform:** Android (API 24+)

---

## 🚀 Quick Build Options

### Option 1: GitHub Actions (Recommended - No Setup Required)

1. **Push code to GitHub:**
   ```bash
   cd ~/navixmind
   git add .
   git commit -m "Build RastaCoder"
   git push origin main
   ```

2. **Wait for build (5-10 minutes):**
   - Go to: `https://github.com/alexandertaboriskiy/rastacoder/actions`
   - Click on the latest workflow run
   - Download APK from artifacts

3. **Install APK:**
   - Download the `arm64-v8a-debug.apk` to your phone
   - Install manually

**Pros:** ✅ No setup, ✅ Reliable, ✅ Free  
**Cons:** ⏱️ Takes 5-10 minutes per build

---

### Option 2: Local Build (Linux/Mac/Windows with Flutter)

**Prerequisites:**
- Flutter SDK 3.x
- Java 17
- Android SDK

**Build Steps:**
```bash
# Clone repository
git clone https://github.com/alexandertaboriskiy/rastacoder.git
cd rastacoder

# Run build script
bash build-rastacoder.sh

# Or manual build
flutter pub get
flutter build apk --debug --split-per-abi
```

**Output:**
```
build/app/outputs/flutter-apk/
├── app-arm64-v8a-debug.apk    (for most modern phones)
├── app-armeabi-v7a-debug.apk  (for older phones)
└── app-x86_64-debug.apk       (for tablets/emulators)
```

**Install:**
```bash
adb install -r build/app/outputs/flutter-apk/app-arm64-v8a-debug.apk
```

---

### Option 3: Build in Proot Linux (Advanced - Termux Users)

**Step 1: Install Arch Linux proot**
```bash
proot-distro install archlinux
```

**Step 2: Setup Flutter in Arch**
```bash
proot-distro login archlinux

# Inside Arch
pacman -Syu
pacman -S flutter android-tools android-sdk android-sdk-build-tools java17-openjdk

# Set JAVA_HOME
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk
```

**Step 3: Build RastaCoder**
```bash
# Bind mount the project
proot-distro login archlinux \
  --bind /data/data/com.termux/files/home/navixmind:/navixmind \
  --bind /sdcard:/sdcard

cd /navixmind
flutter pub get
flutter build apk --debug
```

**Pros:** ✅ Runs on phone, ✅ Free  
**Cons:** ⚙️ Complex setup, ⏱️ Slow build (30+ min)

---

## 📱 Installing the APK

### Via ADB (USB Debugging Required)
```bash
# Enable USB debugging on phone
# Connect to computer
adb devices  # Verify connection
adb install -r build/app/outputs/flutter-apk/app-arm64-v8a-debug.apk
```

### Via File Transfer
1. Copy APK to phone
2. Open file manager
3. Tap APK to install
4. Allow "Install from unknown sources"

---

## 🔧 Troubleshooting

### Build Fails with "Package not found"
```bash
flutter clean
rm -rf .dart_tool/
flutter pub get
```

### Gradle Build Fails
```bash
cd android
./gradlew clean
cd ..
flutter build apk
```

### "No devices found"
```bash
# Enable USB debugging
# Connect via USB
adb devices
# If not listed, check USB cable and drivers
```

### App Crashes on Launch
```bash
# Check logs
adb logcat -s flutter,PythonBridge,ai.rastacoder

# Uninstall and reinstall
adb uninstall ai.rastacoder
adb install -r build/app/outputs/flutter-apk/app-arm64-v8a-debug.apk
```

---

## 📊 Build Configuration

### Debug Build
- **Purpose:** Development & testing
- **Size:** ~80-100MB (split per ABI)
- **Performance:** Slower, more logging
- **Signing:** Debug key

### Release Build
```bash
flutter build apk --release --split-per-abi
```
- **Purpose:** Production
- **Size:** ~40-60MB (split per ABI)
- **Performance:** Optimized
- **Signing:** Release key (required for Play Store)

---

## 🎯 Post-Build Testing Checklist

- [ ] App launches successfully
- [ ] Python bridge connects
- [ ] Offline LLM models download
- [ ] Tools execute correctly
- [ ] No crashes in logcat
- [ ] UI renders properly
- [ ] Permissions work (storage, etc.)

---

## 📝 Version Information

| Component | Version |
|-----------|---------|
| **App** | 1.0.0+1 |
| **Flutter** | 3.x |
| **Android SDK** | 35 (compileSdk) |
| **Min SDK** | 24 (Android 7.0) |
| **Python** | 3.11 (via Chaquopy) |

---

## 🔗 Useful Commands

```bash
# Check Flutter setup
flutter doctor -v

# List connected devices
flutter devices

# Run on device (hot reload)
flutter run

# Build for specific ABI
flutter build apk --debug --target-platform android-arm64

# View build size
ls -lh build/app/outputs/flutter-apk/

# Analyze code
flutter analyze
```

---

## 🦁 RastaCoder Specific Notes

### Package Name Change
- **Old:** `ai.coderasta` (NavixMind)
- **New:** `ai.rastacoder` (RastaCoder)

⚠️ **Important:** Users must uninstall old version before installing new one (different package ID).

### First Launch
- App will request permissions (storage, etc.)
- Python runtime initializes (~5-10 seconds)
- On-device models download on-demand from Settings

---

**Build Script:** `build-rastacoder.sh`  
**GitHub Actions:** `.github/workflows/build-apk.yml`  
**Last Updated:** March 13, 2026

*Bless up! 🦁🇯🇲*
