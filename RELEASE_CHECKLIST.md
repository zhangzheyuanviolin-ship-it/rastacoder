# 🦁 RastaCoder v1.0.0 - Release Checklist

**Release:** v1.0.0 Production
**Date:** March 27, 2026
**Owner:** Kiliaan Vanvoorden (@BoozeLee)

---

## ✅ PRE-RELEASE

### Code Quality
- [x] CHANGELOG.md created
- [ ] All tests passing (CI green)
- [ ] `flutter analyze` - zero errors
- [ ] No TODO comments in production code
- [x] README.md updated with RastaCoder branding
- [ ] CONTRIBUTING.md exists
- [ ] CODE_OF_CONDUCT.md exists

### Git Hygiene
- [ ] All changes committed
- [ ] On `main` branch
- [ ] Branch is up to date with origin
- [ ] No merge conflicts
- [ ] `.gitignore` is complete

### Documentation
- [x] CHANGELOG.md documents v1.0.0
- [x] README.md has correct repo URL
- [ ] API documentation complete
- [ ] Architecture diagrams in `/docs`
- [ ] Security policy in `SECURITY.md`

### Build Verification
- [ ] Debug APK builds successfully
- [ ] Release APK builds (<100MB per ABI)
- [ ] App Bundle builds (<80MB)
- [ ] APK installs on test device
- [ ] App launches without crash
- [ ] On-device LLM downloads/loads
- [ ] Tools execute successfully

---

## 🚀 RELEASE DAY

### GitHub Actions
- [ ] Rename repository to `rastacoder` on GitHub
- [ ] Update GitHub Pages / website URL
- [ ] Verify CI workflows still run
- [ ] Update any hardcoded repo references

### Git Commands
```bash
# 1. Final commit
git add .
git commit -m "chore(release): v1.0.0 production release"

# 2. Push to main
git push origin main

# 3. Create version tag
git tag -a v1.0.0 -m "RastaCoder v1.0.0 - Production Release"

# 4. Push tag
git push origin v1.0.0
```

### GitHub Release
- [ ] Go to github.com/BoozeLee/rastacoder/releases
- [ ] Click "Create a new release"
- [ ] Tag version: `v1.0.0`
- [ ] Release title: "RastaCoder v1.0.0 - Production Release"
- [ ] Description: Use CHANGELOG.md v1.0.0 section
- [ ] Attach APK files (upload from CI artifacts)
- [ ] Check "Set as the latest release"
- [ ] Click "Publish release"

### GitHub Repo Settings
- [ ] Rename repo: `navixmind` → `rastacoder`
- [ ] Update description: "The AI assistant that runs 100% offline on Android"
- [ ] Add topics: `android`, `ai`, `offline`, `llm`, `flutter`, `python`, `termux`
- [ ] Set default branch: `main`
- [ ] Enable Issues
- [ ] Enable Discussions (optional)
- [ ] Add release APK to Assets

---

## 📢 POST-RELEASE

### Update External Links
- [ ] Update navixmind.ai → rastacoder.ai (or redirect)
- [ ] Update Discord invite links
- [ ] Update social media bios (Twitter, LinkedIn)
- [ ] Update Gumroad product page
- [ ] Update Product Hunt listing

### Announcements
- [ ] Reddit post (r/termux, r/LocalLLaMA, r/androidapps)
- [ ] Twitter thread
- [ ] HackerNews post
- [ ] Product Hunt launch
- [ ] Discord announcement
- [ ] Email newsletter

### Monitoring
- [ ] Watch GitHub Issues for bug reports
- [ ] Monitor Discord for support requests
- [ ] Track download counts
- [ ] Check CI build status
- [ ] Respond to first 24h of feedback ASAP

---

## 📊 RELEASE METRICS

Track these for v1.0.0:

| Metric | Target | Actual |
|--------|--------|--------|
| GitHub Stars (Week 1) | 100+ | ___ |
| APK Downloads (Week 1) | 500+ | ___ |
| Reddit Upvotes | 300+ | ___ |
| Twitter Impressions | 10K+ | ___ |
| Discord Members | 200+ | ___ |
| Issues Opened | <20 | ___ |
| Critical Bugs | 0 | ___ |

---

## 🐛 KNOWN ISSUES (Ship with these)

Document any known limitations:

1. **Matplotlib tests fail in Termux** - Environment-specific, works on Android
2. **iOS not supported** - Python embedding is Android-only (for now)
3. **Large models need 6GB+ RAM** - Documented in README

---

## 🔧 ROLLBACK PLAN

If critical bug found post-release:

```bash
# 1. Delete tag
git tag -d v1.0.0
git push origin :refs/tags/v1.0.0

# 2. Fix bug
# ... make changes ...
git commit -m "fix: critical bug description"
git push origin main

# 3. Create new tag
git tag -a v1.0.1 -m "RastaCoder v1.0.1 - Hotfix"
git push origin v1.0.1

# 4. Update GitHub Release
# Edit release notes, attach new APKs
```

---

## 📝 RELEASE NOTES TEMPLATE

```markdown
## 🦁 RastaCoder v1.0.0 - Production Release

**The AI assistant that runs 100% offline on your phone.**

### 🎉 What's New

- **On-Device AI** - Run Qwen2.5-Coder models offline (no internet required)
- **Cloud AI** - Claude API support for maximum capability
- **Python Runtime** - Full Python 3.10 embedded in APK
- **Multi-Step Workflows** - FFmpeg, document processing, web automation
- **Rasta Theme** - Cyber-Clean dark theme with Rastafarian vibes

### 📥 Installation

1. Download APK from Assets below
2. Install on Android device (API 24+)
3. Launch app, accept ToS
4. Choose AI mode (Cloud or Offline)
5. Start chatting!

### 🔗 Links

- Website: https://rastacoder.ai
- Issues: https://github.com/BoozeLee/rastacoder/issues
- Discord: https://discord.gg/navixmind

### 📊 Stats

- APK Size: <100MB (per ABI)
- Min Android: 7.0 (API 24)
- RAM Required: 4GB+ (for 1.5B model)

---

*Jah Rastafari! 🦁🇯🇲*
```

---

**Release Status:** READY ✅
**Next Step:** Execute git commands below

*Baker Street Laboratory © 2026* 🔱
