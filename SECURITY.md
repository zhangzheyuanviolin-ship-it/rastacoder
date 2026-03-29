# Security Policy

## 🛡️ Supported Versions

| Version | Supported |
|---------|-----------|
| `main` | ✅ Active |
| Older   | ❌ Not supported |

## 🔒 Reporting a Vulnerability

**Please do NOT report security vulnerabilities via public GitHub Issues.**

Report security vulnerabilities responsibly:

1. **Email:** [security@bakerstreetproject221b.store](mailto:security@bakerstreetproject221b.store)
2. **GitHub Private Advisory:** Use [GitHub's private security advisory feature](https://github.com/BoozeLee/rastacoder/security/advisories/new)

### Response Timeline

- **Acknowledgement:** Within 48 hours
- **Initial Assessment:** Within 5 business days
- **Fix & Disclosure:** Coordinated with reporter

## 🔐 Privacy & Data Handling

RastaCoder is designed with **privacy-first** principles:

### Offline Mode
- **Zero telemetry** — no data leaves your device
- **No analytics** — we don't know what you're doing
- **Local storage only** — all data stays on your phone
- Models run on your GPU — never uploaded to any server

### Cloud Mode (Claude API)
- Your Claude API key is stored using **Flutter Secure Storage** (encrypted, hardware-backed where available)
- API key is never logged, cached to disk unencrypted, or transmitted to our servers
- You communicate directly with Anthropic's servers — we are not a proxy

## 🚨 Known Security Considerations

### API Key Storage
- API keys use Android Keystore-backed encryption
- Keys are never logged to logcat
- Uninstalling the app removes all stored keys

### Python Runtime Security
- The embedded Python runtime (Chaquopy) runs in the app's sandboxed process
- Python cannot access other apps' data
- All `python_execute` tool calls are sandboxed within the app process

## 🔐 Security Best Practices for Contributors

1. **No hardcoded secrets** — Use environment variables in CI
2. **No logging of sensitive data** — Never log API keys or user content
3. **Validate all Python code** before execution in the embedded runtime
4. Run security checks before pushing:
   ```bash
   dart pub audit
   flutter analyze
   ```

---

*Maintained by [Bakertreet Labs](https://github.com/Bakery-street-project)*
