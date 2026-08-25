#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'lib/features/chat/presentation/chat_screen.dart'
text = path.read_text(encoding='utf-8')

old = """      final shouldShowInChat = msg.startsWith('Thinking:') ||\n          msg.startsWith('Tool:') ||"""
new = """      // Keep model reasoning content private/collapsed by default.\n      // Live chat messages focus on observable tool activity and results.\n      final shouldShowInChat = msg.startsWith('Tool:') ||"""
if old not in text:
    raise SystemExit('thinking visibility anchor missing')
text = text.replace(old, new, 1)

old = """      } else {\n        setState(() {\n          _statusMessage = msg;\n        });\n      }"""
new = """      } else {\n        setState(() {\n          // A Thinking: log may contain a preview of the model's hidden\n          // reasoning. Expose only a generic progress state here; the full\n          // <think> block remains available through the collapsed control\n          // attached to the final assistant message.\n          _statusMessage = msg.startsWith('Thinking:')\n              ? '正在思考…'\n              : _localizeAgentLog(msg);\n        });\n      }"""
if old not in text:
    raise SystemExit('status sanitization anchor missing')
text = text.replace(old, new, 1)

path.write_text(text, encoding='utf-8')
print('Iteration v2 stage3 reasoning-visibility patch applied successfully.')
