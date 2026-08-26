import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))

import navixmind.agent as agent
from navixmind.tools import (
    ALL_LOCAL_SKILL_IDS,
    LOCAL_SKILLS,
    OFFLINE_TOOLS_SCHEMA,
    TOOLS_SCHEMA,
    get_enabled_tool_names,
    get_local_tool_argument_classes,
    get_offline_tools_for_skills,
)
from navixmind.tools.compat import normalize_tool_call


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def schema_by_name(schemas, name):
    return next(tool for tool in schemas if tool.get('name') == name)


def props(tool):
    return (tool.get('input_schema') or {}).get('properties') or {}


def test_catalogue_and_generated_argument_classification():
    names = {tool['name'] for tool in OFFLINE_TOOLS_SCHEMA}
    require(len(names) == 37, f'expected exactly 37 canonical local functions, got {len(names)}: {sorted(names)}')
    require(get_enabled_tool_names(ALL_LOCAL_SKILL_IDS) == names, 'Skill catalogue no longer covers exactly every local function')
    require(len(LOCAL_SKILLS) == 25, f'expected 25 user-controlled Skills, got {len(LOCAL_SKILLS)}')

    classes = get_local_tool_argument_classes()
    require(set(classes) == names, 'argument classification missing a function')
    allowed = {'model_essential', 'app_defaultable', 'advanced_optional'}
    for tool in OFFLINE_TOOLS_SCHEMA:
        name = tool['name']
        tool_props = props(tool)
        require(set(classes[name]) == set(tool_props), f'unclassified schema property for {name}: {set(tool_props) - set(classes[name])}')
        require(set(classes[name].values()) <= allowed, (name, classes[name]))


def test_model_facing_projection_keeps_executor_contract_strict():
    local = get_offline_tools_for_skills(ALL_LOCAL_SKILL_IDS)
    local_docx = schema_by_name(local, 'read_docx')
    local_pptx = schema_by_name(local, 'read_pptx')
    local_xlsx = schema_by_name(local, 'read_xlsx')
    local_web = schema_by_name(local, 'web_fetch')

    require(set(props(local_docx)) == {'docx_path'}, props(local_docx))
    require(set(props(local_pptx)) == {'pptx_path'}, props(local_pptx))
    require('extract' not in props(local_xlsx), props(local_xlsx))
    require({'xlsx_path', 'sheet', 'range'} <= set(props(local_xlsx)), props(local_xlsx))
    require('extract_mode' not in props(local_web), props(local_web))

    strict_docx = schema_by_name(TOOLS_SCHEMA, 'read_docx')
    strict_pptx = schema_by_name(TOOLS_SCHEMA, 'read_pptx')
    strict_xlsx = schema_by_name(TOOLS_SCHEMA, 'read_xlsx')
    strict_web = schema_by_name(TOOLS_SCHEMA, 'web_fetch')
    require('extract' in props(strict_docx), 'strict DOCX executor schema was mutated')
    require('extract' in props(strict_pptx), 'strict PPTX executor schema was mutated')
    require('extract' in props(strict_xlsx), 'strict XLSX executor schema was mutated')
    require('extract_mode' in props(strict_web), 'strict web_fetch executor schema was mutated')


def test_schema_aware_primitive_and_enum_coercion():
    _, args, notes = normalize_tool_call('read_docx', {'docx_path': 'a.docx', 'extract': True})
    require(args.get('extract') == 'all', (args, notes))
    require(any('extract:bool->all' in note for note in notes), notes)

    _, args, notes = normalize_tool_call('read_docx', {'docx_path': 'a.docx', 'extract': 'TRUE'})
    require(args.get('extract') == 'all', (args, notes))

    _, args, notes = normalize_tool_call('read_pptx', {'pptx_path': 'a.pptx', 'extract': False})
    require(args.get('extract') == 'all', (args, notes))

    _, args, notes = normalize_tool_call('read_pptx', {'pptx_path': 'a.pptx', 'extract': 'TeXt'})
    require(args.get('extract') == 'text', (args, notes))

    _, args, notes = normalize_tool_call('read_xlsx', {'xlsx_path': 'a.xlsx', 'extract': 'FALSE'})
    require(args.get('extract') == 'values', (args, notes))

    _, args, notes = normalize_tool_call('read_xlsx', {'xlsx_path': 'a.xlsx', 'extract': 'FORMULAS'})
    require(args.get('extract') == 'formulas', (args, notes))

    _, args, notes = normalize_tool_call('read_pdf', {'pdf_path': 'a.pdf', 'pages': 3})
    require(args.get('pages') == '3', (args, notes))

    _, args, notes = normalize_tool_call('read_pdf', {'pdf_path': 'a.pdf', 'pages': None})
    require('pages' not in args, (args, notes))

    _, args, notes = normalize_tool_call('read_xlsx', {'xlsx_path': 'a.xlsx', 'sheet': 2, 'range': None})
    require(args.get('sheet') == '2' and 'range' not in args, (args, notes))

    _, args, notes = normalize_tool_call('web_fetch', {'url': 'https://example.com', 'extract_mode': True})
    require(args.get('extract_mode') == 'text', (args, notes))


def test_generated_surface_fuzz_for_every_canonical_function():
    # Every canonical function must tolerate the parser wrappers/name casing that
    # small models commonly emit. This is intentionally a normalization gate,
    # not a promise that an empty call passes required-argument validation.
    for tool in OFFLINE_TOOLS_SCHEMA:
        name = tool['name']
        canonical, args, notes = normalize_tool_call(name.upper(), {'arguments': {}})
        require(canonical == name, (name, canonical, notes))
        require(isinstance(args, dict), (name, args))

        tool_props = list(props(tool))
        if tool_props:
            key = tool_props[0]
            canonical2, args2, notes2 = normalize_tool_call(
                name,
                {f'{key}?': None},
            )
            require(canonical2 == name, (name, canonical2, notes2))
            require(isinstance(args2, dict), (name, args2))
            require(f'{key}?' not in args2, (name, args2, notes2))


def test_complete_long_document_partition_and_ingestion_contract():
    source = ''.join(chr(65 + (i % 26)) for i in range(45015))
    chunks = agent._split_complete_document_text(source, 7000)
    require(''.join(chunks) == source, 'document chunking lost or duplicated source characters')
    require(len(chunks) >= 6, len(chunks))

    calls = []

    class FakeLocalLLMClient:
        def __init__(self, *args, **kwargs):
            self.model_id = kwargs.get('model_id', 'fake')
            self.model = self.model_id

        def create_message(self, messages, system='', tools=None, max_tokens=0, retry_count=1):
            calls.append(messages[0]['content'])
            idx = len(calls)
            return {
                'stop_reason': 'end_turn',
                'content': [{'type': 'text', 'text': f'evidence-{idx}: retained facts from chunk {idx}'}],
                'usage': {},
            }

    original = agent.LocalLLMClient
    agent.LocalLLMClient = FakeLocalLLMClient
    try:
        context = {
            'offline_model_info': {'id': 'qwen3-4b'},
            'local_context_tokens': 8192,
            '_diagnostics': [],
        }
        outer = type('OuterClient', (), {'model_id': 'qwen3-4b', 'model': 'qwen3-4b'})()
        payload = agent._document_result_for_local_model(
            outer,
            'Summarize all important facts in this document.',
            'read_docx',
            {'path': 'long.docx', 'text': source, 'paragraph_count': 900},
            context,
            2048,
        )
    finally:
        agent.LocalLLMClient = original

    require(len(calls) == len(chunks), (len(calls), len(chunks)))
    require('DOCUMENT_INGESTION' in payload, payload[:500])
    require(f'source_chars: {len(source)}' in payload, payload[:500])
    require(f'chunks_processed: {len(chunks)}' in payload, payload[:500])
    require('coverage: complete executor-returned text was partitioned across all chunks' in payload, payload[:700])
    require('[context-safe truncation]' not in payload, 'ingestion digest fell back to generic head/tail truncation')
    require(any(e.get('stage') == 'document_ingestion_complete' for e in context['_diagnostics']), context['_diagnostics'])


def test_short_document_keeps_direct_result_path():
    context = {
        'offline_model_info': {'id': 'qwen3-4b'},
        'local_context_tokens': 8192,
        '_diagnostics': [],
    }
    outer = type('OuterClient', (), {'model_id': 'qwen3-4b', 'model': 'qwen3-4b'})()
    payload = agent._document_result_for_local_model(
        outer,
        'Read it.',
        'read_docx',
        {'path': 'short.docx', 'text': 'short document payload'},
        context,
        2048,
    )
    require('TOOL_RESULT' in payload and 'short document payload' in payload, payload)
    require('DOCUMENT_INGESTION' not in payload, payload)


def test_provider_routing_source_contract():
    model_source = (ROOT / 'lib/core/models/model_registry.dart').read_text(encoding='utf-8')
    chat_source = (ROOT / 'lib/features/chat/presentation/chat_screen.dart').read_text(encoding='utf-8')
    require('enum ModelRouteProvider { local, anthropic, openAICompatible }' in model_source, 'provider identity missing')
    require("id == 'openai-compatible'" in model_source, 'OpenAI-compatible identity missing')
    require('ModelRouteProvider.openAICompatible' in chat_source, 'OpenAI-compatible route branch missing')
    require("getOpenAICompatibleConfig()" in chat_source, 'OpenAI-compatible config readiness missing')
    require("(config['base_url'] ?? '').trim().isNotEmpty" in chat_source, 'Base URL readiness missing')
    require("(config['model'] ?? '').trim().isNotEmpty" in chat_source, 'Model ID readiness missing')
    require('API Key 可按服务商要求选填' in chat_source, 'optional provider API key contract missing')
    require('Claude 云端模型' in chat_source, 'Anthropic-specific key gate missing')

    ready_start = chat_source.index('RASTACODER_V13_PROVIDER_ROUTE_READY')
    ready_end = chat_source.index('void _addRoutingError', ready_start)
    ready = chat_source[ready_start:ready_end]
    compat_pos = ready.index('ModelRouteProvider.openAICompatible')
    claude_key_pos = ready.index('final hasKey = await StorageService.instance.hasApiKey()', compat_pos)
    require(compat_pos < claude_key_pos, 'OpenAI-compatible route still falls through Claude-key readiness')


if __name__ == '__main__':
    test_catalogue_and_generated_argument_classification()
    test_model_facing_projection_keeps_executor_contract_strict()
    test_schema_aware_primitive_and_enum_coercion()
    test_generated_surface_fuzz_for_every_canonical_function()
    test_complete_long_document_partition_and_ingestion_contract()
    test_short_document_keeps_direct_result_path()
    test_provider_routing_source_contract()
    print('RastaCoder v13 validation passed: all 37 local functions are classified, local model schemas hide deterministic executor selectors, schema-aware coercion repairs small-model enum/primitive mistakes, long-document ingestion covers every source chunk, and provider readiness separates local, Anthropic, and OpenAI-compatible routes.')
