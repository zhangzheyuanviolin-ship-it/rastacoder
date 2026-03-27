# 🔐 Local Vault Setup — RastaCoder

**Location:** `~/.termux-vault/`  
**Status:** ✅ Already Installed & Configured  
**Encryption:** AES-256 with PBKDF2 (480k iterations)

---

## 📊 YOUR VAULT STATUS

| Component | Status | Location |
|-----------|--------|----------|
| **Vault Script** | ✅ Installed | `~/.termux-vault/vault.py` |
| **Encrypted Data** | ✅ Created | `~/.termux-vault/vault.enc` |
| **Master Key** | ✅ Configured | `~/.termux-vault/.key` |
| **Salt** | ✅ Generated | `~/.termux-vault/salt` |
| **Helper Functions** | ✅ Loaded | `~/.bashrc` |

---

## 🎯 QUICK COMMANDS

### View All Secrets
```bash
vault list
```

### Add New Secret
```bash
vault add <service> <key> <value>

# Examples
vault add gemini api_key "AIza..."
vault add pollinations test "value"
```

### Get Secret
```bash
vault get <service> <key>

# Examples
vault get gemini api_key
vault get nvidia api_key
```

### Interactive Mode
```bash
vault
```

---

## 🔑 PRE-CONFIGURED SERVICES

Your vault has helper functions for:

| Service | Command | Environment Variable |
|---------|---------|---------------------|
| **Kaggle** | `load_kaggle` | `KAGGLE_USERNAME`, `KAGGLE_KEY` |
| **NVIDIA** | `load_nvidia` | `NVIDIA_API_KEY` |
| **Hugging Face** | `load_huggingface` | `HF_TOKEN` |

---

## 🦁 SETUP FOR RASTACODER

### Add Gemini API Key

```bash
# Option 1: Interactive
vault add gemini api_key

# Option 2: Direct
vault add gemini api_key "AIzaSy..."

# Load into environment
load_gemini 2>/dev/null || export GEMINI_API_KEY=$(vault get gemini api_key)

# Verify
echo $GEMINI_API_KEY
```

### Add Hugging Face Token

```bash
vault add huggingface token "hf_xxxxx"
export HF_TOKEN=$(vault get huggingface token)
```

### Add Multiple API Keys

```bash
# Gemini
vault add gemini api_key "AIza..."

# Hugging Face
vault add huggingface token "hf_..."

# Pollinations (if they add auth)
vault add pollinations api_key "..."

# List all
vault list
```

---

## 📁 VAULT STRUCTURE

```
~/.termux-vault/
├── vault.py           # Main Python script
├── vault.sh           # Bash helper functions
├── vault.enc          # Encrypted secrets (AES-256)
├── .key               # Master key (protected)
├── salt               # PBKDF2 salt
├── .env               # Environment template
└── README.md          # Documentation
```

---

## 🔒 SECURITY FEATURES

| Feature | Implementation |
|---------|---------------|
| **Encryption** | AES-256-CBC |
| **Key Derivation** | PBKDF2-SHA256 (480,000 iterations) |
| **File Permissions** | 600 (owner read/write only) |
| **Master Password** | Required for decryption |
| **Salt** | Unique per vault |

---

## 🎨 INTEGRATE WITH RASTACODER

### Option 1: Load in Build Script

```bash
#!/bin/bash
# generate-rasta-assets.sh

# Load API keys from vault
source ~/.termux-vault/vault.sh
load_gemini 2>/dev/null || export GEMINI_API_KEY=$(vault get gemini api_key)

# Generate images using Gemini API
python3 << EOF
import os
from google import genai

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
# ... generate RastaCoder assets
EOF
```

### Option 2: Auto-load in .bashrc

```bash
# Add to ~/.bashrc
echo '# Load API credentials' >> ~/.bashrc
echo 'load_gemini 2>/dev/null' >> ~/.bashrc
echo 'load_huggingface 2>/dev/null' >> ~/.bashrc

# Reload
source ~/.bashrc
```

### Option 3: Use in Python Scripts

```python
import subprocess
import os

def get_vault_secret(service, key):
    """Get secret from termux vault"""
    result = subprocess.run(
        ['vault', 'get', service, key],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

# Usage
GEMINI_API_KEY = get_vault_secret('gemini', 'api_key')
HF_TOKEN = get_vault_secret('huggingface', 'token')
```

---

## 📋 AVAILABLE VAULT COMMANDS

| Command | Description |
|---------|-------------|
| `vault` | Open interactive menu |
| `vault add <service> <key> <value>` | Add secret |
| `vault get <service> <key>` | Retrieve secret |
| `vault list` | List all services |
| `vault list <service>` | List keys for service |
| `vault delete <service> <key>` | Delete secret |
| `vault export` | Export to env format |
| `load_<service>` | Load service creds to env |

---

## 🆚 ALTERNATIVE: .env FILES

Your vault also supports `.env` files:

### Current .env Files Found

| Location | Purpose |
|----------|---------|
| `~/.env` | Global env (OLLAMA, NVIDIA) |
| `~/.nim.env` | Nim API keys |
| `~/.perplexity_labs.env` | Perplexity creds |
| `~/.openclaw/.env` | OpenCLAW project |

### Create RastaCoder .env

```bash
# Create in project
cat > ~/navixmind/.env << 'EOF'
# RastaCoder API Keys
GEMINI_API_KEY=AIza...
HF_TOKEN=hf_...
EOF

# Load in scripts
set -a
source ~/navixmind/.env
set +a
```

---

## 🔗 RELATED VAULTS FOUND

| Vault | Location | Status |
|-------|----------|--------|
| **Termux Vault** | `~/.termux-vault/` | ✅ Active |
| **Secure Keys** | `~/.secure_keys/` | ✅ Encrypted |
| **Global .env** | `~/.env` | ✅ Has NVIDIA key |

---

## 🎯 RECOMMENDED WORKFLOW

### For RastaCoder Development

1. **Store API keys in vault:**
   ```bash
   vault add gemini api_key "AIza..."
   vault add huggingface token "hf_..."
   ```

2. **Load before generation:**
   ```bash
   load_gemini
   load_huggingface
   ```

3. **Generate assets:**
   ```bash
   cd ~/navixmind
   python3 generate_images.py
   ```

4. **Keys auto-cleanup:**
   - Not stored in scripts
   - Not in git history
   - Encrypted at rest

---

## 📞 QUICK REFERENCE

### Add Gemini Key (For Image Generation)
```bash
vault add gemini api_key "AIza..."
export GEMINI_API_KEY=$(vault get gemini api_key)
```

### Verify Key Loaded
```bash
echo $GEMINI_API_KEY
# Should show: AIza...
```

### Use in Python
```python
import os
from google import genai

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
```

---

**Last Updated:** March 16, 2026  
**Vault Status:** ✅ Operational  
**Encryption:** ✅ AES-256 Active

*Baker Street Laboratory © 2026* 🔱
