#!/usr/bin/env python3
"""Harden MLC streamed tool-call accumulation for v6.

MLC may split one structured function call across multiple stream chunks. The
v5/v4 code keyed each fragment by map size, which can create a new accumulator
for every fragment. v6 keys by the tool-call index and merges argument maps.
"""
from pathlib import Path

p = Path('android/app/src/main/kotlin/ai/navixmind/services/MLCInferenceChannel.kt')
text = p.read_text(encoding='utf-8')
old = '''                            choice.delta.tool_calls?.forEachIndexed { _, tc ->
                                val acc = toolCallAccumulators.getOrPut(toolCallAccumulators.size) {
                                    ToolCallAccumulator()
                                }
                                if (tc.id.isNotEmpty()) acc.id = tc.id
                                if (tc.function.name.isNotEmpty()) acc.name = tc.function.name
                                tc.function.arguments?.let { args ->
                                    acc.arguments = args
                                }
                            }
'''
new = '''                            choice.delta.tool_calls?.forEachIndexed { index, tc ->
                                // A single structured tool call may arrive over several
                                // chunks. Reuse the same accumulator by call index instead
                                // of allocating a new entry for each streamed fragment.
                                val acc = toolCallAccumulators.getOrPut(index) {
                                    ToolCallAccumulator()
                                }
                                if (tc.id.isNotEmpty()) acc.id = tc.id
                                if (tc.function.name.isNotEmpty()) acc.name = tc.function.name
                                tc.function.arguments?.let { args ->
                                    val merged = (acc.arguments ?: emptyMap<String, String>()).toMutableMap()
                                    merged.putAll(args)
                                    acc.arguments = merged
                                }
                            }
'''
count = text.count(old)
if count != 1:
    raise SystemExit(f'Expected one MLC tool-call accumulator anchor, found {count}')
text = text.replace(old, new, 1)
p.write_text(text, encoding='utf-8')
print('Applied RastaCoder v6 MLC structured tool-call accumulation hardening')
