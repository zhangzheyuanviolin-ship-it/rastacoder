"""Independent web-search provider tools for RastaCoder v8.

Ports the four search Skills already present in local-agent-plaza while keeping
provider credentials outside the model-visible tool arguments.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

import requests

from ..bridge import ToolError

_TIMEOUT = 45
_PROVIDER_LABELS = {
    "anysearch": "AnySearch",
    "exa": "Exa",
    "langsearch": "LangSearch",
    "tavily": "Tavily",
}


def _api_key(context: Optional[Dict[str, Any]], provider: str) -> str:
    keys = (context or {}).get("search_api_keys", {})
    key = keys.get(provider) if isinstance(keys, dict) else None
    if not isinstance(key, str) or not key.strip():
        label = _PROVIDER_LABELS.get(provider, provider)
        raise ToolError(f"{label} API Key 未配置。请在工具管理页面配置该搜索技能的 API Key。")
    return key.strip()


def _provider_settings(context: Optional[Dict[str, Any]], provider: str, defaults: Dict[str, Any]) -> Dict[str, Any]:
    all_settings = (context or {}).get("search_provider_settings", {})
    configured = all_settings.get(provider) if isinstance(all_settings, dict) else None
    merged = dict(defaults)
    if isinstance(configured, dict):
        merged.update(configured)
    return merged


def _bounded_int(value: Any, default: int, minimum: int = 1, maximum: int = 10) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(parsed, maximum))


def _choice(value: Any, allowed: set[str], default: str) -> str:
    text = str(value or "").strip()
    return text if text in allowed else default


def _domain_list(value: Any, limit: int = 10) -> list[str]:
    if isinstance(value, str):
        values = [x.strip() for x in value.split(",")]
    elif isinstance(value, (list, tuple, set)):
        values = [str(x).strip() for x in value]
    else:
        values = []
    return [x for x in values if x][:limit]


def _raise_http(label: str, response: requests.Response) -> None:
    if response.ok:
        return
    detail = (response.text or "").strip().replace("\n", " ")[:1000]
    raise ToolError(f"{label} HTTP {response.status_code}: {detail}")


def _compact(value: Any, max_chars: int = 16000) -> str:
    text = str(value or "").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n...[TRUNCATED]"


def anysearch_search(query: str, _context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    clean_query = (query or "").strip()
    if not clean_query:
        raise ToolError("AnySearch query is required.")
    settings = _provider_settings(_context, "anysearch", {"max_results": 5, "domain": "", "sub_domain": ""})
    arguments: Dict[str, Any] = {"query": clean_query, "max_results": _bounded_int(settings.get("max_results"), 5)}
    domain = str(settings.get("domain") or "").strip().lower()
    sub_domain = str(settings.get("sub_domain") or "").strip()
    if domain:
        arguments["domain"] = domain
        if sub_domain:
            arguments["sub_domain"] = sub_domain
    text = _anysearch_call("search", arguments, _context)
    return {"success": True, "provider": "anysearch", "operation": "search", "query": clean_query, "settings_applied": {"max_results": arguments["max_results"], "domain": domain, "sub_domain": sub_domain}, "content": _compact(text, 12000)}

def anysearch_extract(
    url: str,
    _context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    clean_url = (url or "").strip()
    if not clean_url.lower().startswith(("http://", "https://")):
        raise ToolError("AnySearch extract only supports http(s) URLs.")
    text = _anysearch_call("extract", {"url": clean_url}, _context)
    return {
        "success": True,
        "provider": "anysearch",
        "operation": "extract",
        "url": clean_url,
        "content": _compact(text, 16000),
    }


def anysearch_get_sub_domains(
    domain: str = "",
    domains: Optional[Iterable[str]] = None,
    _context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    clean_domains = [str(x).strip().lower() for x in (domains or []) if str(x).strip()][:5]
    arguments: Dict[str, Any] = {}
    if clean_domains:
        arguments["domains"] = clean_domains
    else:
        clean_domain = (domain or "").strip().lower()
        if not clean_domain:
            raise ToolError("AnySearch domain is required.")
        arguments["domain"] = clean_domain
    text = _anysearch_call("get_sub_domains", arguments, _context)
    return {
        "success": True,
        "provider": "anysearch",
        "operation": "get_sub_domains",
        "content": _compact(text, 10000),
    }


def _anysearch_call(tool_name: str, arguments: Dict[str, Any], context: Optional[Dict[str, Any]]) -> str:
    key = _api_key(context, "anysearch")
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }
    try:
        response = requests.post(
            "https://api.anysearch.com/mcp",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "X-Anysearch-Client": "rastacoder/8.0",
                "Authorization": f"Bearer {key}",
            },
            timeout=_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise ToolError(f"AnySearch request failed: {exc}") from exc
    _raise_http("AnySearch", response)
    try:
        body = response.json()
    except ValueError as exc:
        raise ToolError("AnySearch returned a non-JSON response.") from exc
    if isinstance(body, dict) and body.get("error"):
        error = body["error"]
        message = error.get("message") if isinstance(error, dict) else str(error)
        raise ToolError(f"AnySearch: {message}")
    result = body.get("result", {}) if isinstance(body, dict) else {}
    content = result.get("content", []) if isinstance(result, dict) else []
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                return str(item.get("text", ""))
    return _compact(result)


def exa_search(query: str, _context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    clean_query = (query or "").strip()
    if not clean_query:
        raise ToolError("Exa query is required.")
    key = _api_key(_context, "exa")
    settings = _provider_settings(_context, "exa", {"num_results": 5, "topic": "general", "search_type": "auto", "start_published_date": "", "include_domains": [], "exclude_domains": [], "include_text": True, "include_summary": True, "include_highlights": False})
    num_results = _bounded_int(settings.get("num_results"), 5)
    topic = _choice(settings.get("topic"), {"general", "news"}, "general")
    search_type = _choice(settings.get("search_type"), {"auto", "neural", "fast", "deep"}, "auto")
    contents: Dict[str, Any] = {}
    if bool(settings.get("include_text", True)):
        contents["text"] = {"maxCharacters": 5000}
    if bool(settings.get("include_summary", True)):
        contents["summary"] = True
    if bool(settings.get("include_highlights", False)):
        contents["highlights"] = True
    payload: Dict[str, Any] = {"query": clean_query, "topic": topic, "type": search_type, "numResults": num_results}
    if contents:
        payload["contents"] = contents
    start_date = str(settings.get("start_published_date") or "").strip()
    if start_date:
        payload["startPublishedDate"] = start_date
    included = _domain_list(settings.get("include_domains")); excluded = _domain_list(settings.get("exclude_domains"))
    if included:
        payload["includeDomains"] = included
    if excluded:
        payload["excludeDomains"] = excluded
    try:
        response = requests.post("https://api.exa.ai/search", json=payload, headers={"Content-Type": "application/json", "x-api-key": key}, timeout=_TIMEOUT)
    except requests.RequestException as exc:
        raise ToolError(f"Exa request failed: {exc}") from exc
    _raise_http("Exa", response)
    try:
        body = response.json()
    except ValueError as exc:
        raise ToolError("Exa returned a non-JSON response.") from exc
    return {"success": True, "provider": "exa", "query": clean_query, "settings_applied": {"num_results": num_results, "topic": topic, "search_type": search_type, "start_published_date": start_date}, "results": body.get("results", []) if isinstance(body, dict) else [], "autoprompt_string": body.get("autopromptString") if isinstance(body, dict) else None}

def langsearch_search(query: str, _context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    clean_query = (query or "").strip()
    if not clean_query:
        raise ToolError("LangSearch query is required.")
    key = _api_key(_context, "langsearch")
    settings = _provider_settings(_context, "langsearch", {"count": 5, "freshness": "noLimit", "summary": True})
    count = _bounded_int(settings.get("count"), 5)
    freshness = _choice(settings.get("freshness"), {"oneDay", "oneWeek", "oneMonth", "oneYear", "noLimit"}, "noLimit")
    summary = bool(settings.get("summary", True))
    payload = {"query": clean_query, "freshness": freshness, "summary": summary, "count": count}
    try:
        response = requests.post("https://api.langsearch.com/v1/web-search", json=payload, headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"}, timeout=_TIMEOUT)
    except requests.RequestException as exc:
        raise ToolError(f"LangSearch request failed: {exc}") from exc
    _raise_http("LangSearch", response)
    try:
        body = response.json()
    except ValueError as exc:
        raise ToolError("LangSearch returned a non-JSON response.") from exc
    if isinstance(body, dict) and body.get("code") not in (None, 200):
        raise ToolError(f"LangSearch: {body.get('message') or body.get('code')}")
    data = body.get("data", {}) if isinstance(body, dict) else {}; pages = data.get("webPages", {}) if isinstance(data, dict) else {}
    return {"success": True, "provider": "langsearch", "query": clean_query, "settings_applied": {"count": count, "freshness": freshness, "summary": summary}, "results": pages.get("value", []) if isinstance(pages, dict) else []}

def tavily_search(query: str, _context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    clean_query = (query or "").strip()
    if not clean_query:
        raise ToolError("Tavily query is required.")
    key = _api_key(_context, "tavily")
    settings = _provider_settings(_context, "tavily", {"max_results": 5, "topic": "general", "search_depth": "basic", "include_answer": True, "time_range": "", "include_domains": [], "exclude_domains": [], "include_raw_content": False})
    max_results = _bounded_int(settings.get("max_results"), 5)
    topic = _choice(settings.get("topic"), {"general", "news"}, "general")
    depth = _choice(settings.get("search_depth"), {"basic", "advanced"}, "basic")
    answer = bool(settings.get("include_answer", True)); raw = bool(settings.get("include_raw_content", False))
    time_range = _choice(settings.get("time_range"), {"", "day", "week", "month", "year"}, "")
    payload: Dict[str, Any] = {"query": clean_query, "topic": topic, "search_depth": depth, "max_results": max_results, "include_answer": answer, "include_raw_content": raw}
    if time_range:
        payload["time_range"] = time_range
    included = _domain_list(settings.get("include_domains")); excluded = _domain_list(settings.get("exclude_domains"))
    if included:
        payload["include_domains"] = included
    if excluded:
        payload["exclude_domains"] = excluded
    try:
        response = requests.post("https://api.tavily.com/search", json=payload, headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"}, timeout=_TIMEOUT)
    except requests.RequestException as exc:
        raise ToolError(f"Tavily request failed: {exc}") from exc
    _raise_http("Tavily", response)
    try:
        body = response.json()
    except ValueError as exc:
        raise ToolError("Tavily returned a non-JSON response.") from exc
    return {"success": True, "provider": "tavily", "query": clean_query, "settings_applied": {"max_results": max_results, "topic": topic, "search_depth": depth, "include_answer": answer, "time_range": time_range}, "answer": body.get("answer") if isinstance(body, dict) else None, "results": body.get("results", []) if isinstance(body, dict) else []}
