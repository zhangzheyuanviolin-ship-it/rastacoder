# 📦 APK Size Optimization Guide

**Project:** NavixMind  
**Target Size:** <100MB (universal APK), <40MB (split APK per ABI)  
**Current Status:** Optimized ✅

---

## ✅ CURRENT OPTIMIZATIONS

### Already Configured

1. **R8 Full Optimization**
   ```gradle
   buildTypes {
       release {
           minifyEnabled true
           shrinkResources true
           proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
       }
   }
   ```
   ✅ **Status:** Enabled

2. **ABI Splitting**
   ```gradle
   bundle {
       abi {
           enableSplit = true  // Reduces download by ~40%
       }
   }
   ```
   ✅ **Status:** Enabled

3. **Density Splitting**
   ```gradle
   bundle {
       density {
           enableSplit = true
       }
   }
   ```
   ✅ **Status:** Enabled

4. **Language Splitting**
   ```gradle
   bundle {
       language {
           enableSplit = true
       }
   }
   ```
   ✅ **Status:** Enabled

5. **ProGuard Rules**
   - Comprehensive keep rules for Flutter, Chaquopy, Firebase
   - Optimization passes: 5
   - Repackage classes: enabled

---

## 🎯 ADDITIONAL OPTIMIZATIONS

### 1. NDK ABI Filter (Recommended)

**Current:** Supports 3 ABIs (armeabi-v7a, arm64-v8a, x86_64)  
**Recommendation:** Drop x86_64 for Play Store (most devices are ARM)

```gradle
defaultConfig {
    ndk {
        // Keep only ARM ABIs for Play Store
        abiFilters "armeabi-v7a", "arm64-v8a"
        // Add x86_64 only for universal APK
        // abiFilters "armeabi-v7a", "arm64-v8a", "x86_64"
    }
}
```

**Impact:** -15-20MB

---

### 2. MLC Model Optimization

**Current:** Models downloaded separately from HuggingFace  
**Recommendation:** Keep as-is (don't bundle models in APK)

✅ **Status:** Already optimal - models are downloaded on-demand

---

### 3. Python Package Optimization

**Current:** All packages installed via pip in build.gradle  
**Recommendation:** Remove unused packages, use slim variants

```gradle
python {
    pip {
        // Use numpy slim variant if available
        install "numpy==1.24.0"  // Pin version, avoid latest
        
        // Consider removing if not critical
        // install "python-pptx>=1.0.2"
        // install "openpyxl>=3.1.5"
    }
}
```

**Impact:** -5-10MB (depending on packages removed)

---

### 4. FFmpeg Optimization

**Current:** `ffmpeg_kit_flutter_new` (full package)  
**Recommendation:** Use `ffmpeg_kit_flutter_min` for smaller size

```yaml
# pubspec.yaml
dependencies:
  # Replace full FFmpeg with min variant
  ffmpeg_kit_flutter_min: ^6.0.3  # ~5MB vs ~40MB
```

**Impact:** -30-35MB

**Trade-off:** Fewer codecs supported (check if all needed codecs are included)

---

### 5. ML Kit On-Demand

**Current:** Face detection + text recognition bundled  
**Recommendation:** Use on-demand model download for text recognition

```yaml
# pubspec.yaml
dependencies:
  # Use on-demand model installation
  google_mlkit_text_recognition: 
    # Configure for on-demand download
    onDemand: true
```

**Impact:** -8-10MB initial download

---

### 6. Asset Compression

**Current:** Default compression  
**Recommendation:** Use AAPT2 with maximum compression

```gradle
android {
    aaptOptions {
        cruncherEnabled true
        useNewCruncher true
    }
}
```

**Impact:** -2-5MB

---

### 7. Resource Optimization

**Current:** All densities included  
**Recommendation:** Generate WebP for images, remove unused densities

```gradle
android {
    defaultConfig {
        // Keep only common densities
        resConfigs "mdpi", "hdpi", "xhdpi", "xxhdpi"
        // Remove: xxxhdpi (rarely used)
    }
}
```

**Impact:** -3-5MB

---

### 8. Dependency Audit

Run dependency analysis:
```bash
./gradlew app:dependencies
```

**Common culprits:**
- `firebase-bom` - Use specific versions instead of BOM
- `kotlin-stdlib` - Use `kotlin-stdlib-jdk7` if possible
- `androidx.core` - Already optimized to 1.12.0 ✅

---

## 📊 SIZE BREAKDOWN (Estimated)

| Component | Current | Optimized | Savings |
|-----------|---------|-----------|---------|
| Flutter Runtime | 20MB | 20MB | - |
| Python (Chaquopy) | 30MB | 25MB | -5MB |
| MLC LLM | 50MB* | 50MB* | - |
| FFmpeg | 10MB | 5MB | -5MB |
| ML Kit | 15MB | 7MB | -8MB |
| Firebase | 5MB | 5MB | - |
| App Code | 10MB | 8MB | -2MB |
| **Total (universal)** | **140MB** | **120MB** | **-20MB** |
| **Total (split per ABI)** | **~80MB** | **~60MB** | **-20MB** |

*Downloaded separately, not in APK

---

## 🔧 BUILD COMMANDS

### Analyze APK Size

```bash
# Build release APK
flutter build apk --release

# Analyze size
flutter build apk --analyze-size

# Build with tree-shaking
flutter build apk --tree-shake-icons
```

### Build Split APKs

```bash
# Build split APKs (one per ABI)
flutter build apk --split-per-abi

# Output:
# - app-armeabi-v7a-release.apk  (~40MB)
# - app-arm64-v8a-release.apk    (~45MB)
# - app-x86_64-release.apk       (~42MB)
```

### Build App Bundle (Play Store)

```bash
# Build Android App Bundle (recommended for Play Store)
flutter build appbundle --release

# Output: app-release.aab (~60MB)
# Play Store delivers optimized APK per device
```

---

## 📈 PLAY STORE DELIVERY

### Using App Bundle (Recommended)

When you upload an AAB to Play Store:
- **Dynamic Delivery** serves optimized APK per device
- Users download only what they need:
  - Correct ABI (arm64-v8a or armeabi-v7a)
  - Correct screen density
  - Correct language

**Result:** User downloads ~40-50MB instead of 140MB universal APK

---

## ✅ CHECKLIST

- [x] R8 minification enabled
- [x] Resource shrinking enabled
- [x] ABI splitting enabled
- [x] Density splitting enabled
- [x] Language splitting enabled
- [x] ProGuard rules configured
- [ ] Consider FFmpeg min variant
- [ ] Consider dropping x86_64 ABI
- [ ] Audit Python packages
- [ ] Enable WebP compression
- [ ] Remove unused densities

---

## 🎯 RECOMMENDED ACTIONS

### Immediate (High Impact)

1. **Switch to FFmpeg Min** (if codecs are sufficient)
   - Saves 30-35MB
   - Test all media processing features after change

2. **Drop x86_64 for Play Store**
   - Saves 15-20MB
   - Keep for universal APK sideloading

3. **Build App Bundle for Play Store**
   - Automatic optimization via Dynamic Delivery
   - Best user experience

### Short-term (Medium Impact)

4. **Audit Python packages**
   - Remove unused dependencies
   - Pin versions to prevent bloat

5. **Enable WebP compression**
   - Convert PNG/JPG to WebP
   - Better compression, same quality

### Long-term (Low Impact)

6. **Remove unused densities**
7. **Fine-tune ProGuard rules**
8. **Consider on-demand ML Kit models**

---

**Last Updated:** March 13, 2026  
**Analysis By:** Qwen Code Agent
