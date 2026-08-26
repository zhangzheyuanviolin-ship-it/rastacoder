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


def anysearch_search(
    query: str,
    max_results: int = 5,
    domain: str = "",
    sub_domain: str = "",
    sub_domain_params: Optional[Dict[str, Any]] = None,
    _context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Search through AnySearch MCP, matching local-agent-plaza behavior."""
    clean_query = (query or "").strip()
    if not clean_query:
        raise ToolError("AnySearch query is required.")
    arguments: Dict[str, Any] = {
        "query": clean_query,
        "max_results": max(1, min(int(max_results or 5), 10)),
    }
    if (domain or "").strip():
        arguments["domain"] = domain.strip().lower()
        if (sub_domain or "").strip():
            arguments["sub_domain"] = sub_domain.strip()
        if isinstance(sub_domain_params, dict) and sub_domain_params:
            arguments["sub_domain_params"] = sub_domain_params
    text = _anysearch_call("search", arguments, _context)
    return {
        "success": True,
        "provider": "anysearch",
        "operation": "search",
        "query": clean_query,
        "content": _compact(text, 12000),
    }


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


def exa_search(
    query: str,
    num_results: int = 5,
    topic: str = "general",
    search_type: str = "auto",
    start_published_date: str = "",
    include_domains: Optional[Iterable[str]] = None,
    exclude_domains: Optional[Iterable[str]] = None,
    include_text: bool = True,
    include_summary: bool = True,
    include_highlights: bool = False,
    _context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    clean_query = (query or "").strip()
    if not clean_query:
        raise ToolError("Exa query is required.")
    key = _api_key(_context, "exa")
    contents: Dict[str, Any] = {}
    if include_text:
        contents["text"] = {"maxCharacters": 5000}
    if include_summary:
        contents["summary"] = True
    if include_highlights:
        contents["highlights"] = True
    payload: Dict[str, Any] = {
        "query": clean_query,
        "topic": topic,
        "type": search_type,
        "numResults": max(1, min(int(num_results or 5), 10)),
    }
    if contents:
        payload["contents"] = contents
    if (start_published_date or "").strip():
        payload["startPublishedDate"] = start_published_date.strip()
    included = [str(x).strip() for x in (include_domains or []) if str(x).strip()]
    excluded = [str(x).strip() for x in (exclude_domains or []) if str(x).strip()]
    if included:
        payload["includeDomains"] = included[:10]
    if excluded:
        payload["excludeDomains"] = excluded[:10]
    try:
        response = requests.post(
            "https://api.exa.ai/search",
            json=payload,
            headers={"Content-Type": "application/json", "x-api-key": key},
            timeout=_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise ToolError(f"Exa request failed: {exc}") from exc
    _raise_http("Exa", response)
    try:
        body = response.json()
    except ValueError as exc:
        raise ToolError("Exa returned a non-JSON response.") from exc
    return {
        "success": True,
        "provider": "exa",
        "query": clean_query,
        "results": body.get("results", []) if isinstance(body, dict) else [],
        "autoprompt_string": body.get("autopromptString") if isinstance(body, dict) else None,
    }


def langsearch_search(
    query: str,
    count: int = 5,
    freshness: str = "noLimit",
    summary: bool = True,
    _context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    clean_query = (query or "").strip()
    if not clean_query:
        raise ToolError("LangSearch query is required.")
    key = _api_key(_context, "langsearch")
    payload = {
        "query": clean_query,
        "freshness": freshness,
        "summary": bool(summary),
        "count": max(1, min(int(count or 5), 10)),
    }
    try:
        response = requests.post(
            "https://api.langsearch.com/v1/web-search",
            json=payload,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
            timeout=_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise ToolError(f"LangSearch request failed: {exc}") from exc
    _raise_http("LangSearch", response)
    try:
        body = response.json()
    except ValueError as exc:
        raise ToolError("LangSearch returned a non-JSON response.") from exc
    if isinstance(body, dict) and body.get("code") not in (None, 200):
        raise ToolError(f"LangSearch: {body.get('message') or body.get('code')}")
    data = body.get("data", {}) if isinstance(body, dict) else {}
    pages = data.get("webPages", {}) if isinstance(data, dict) else {}
    return {
        "success": True,
        "provider": "langsearch",
        "query": clean_query,
        "results": pages.get("value", []) if isinstance(pages, dict) else [],
    }


def tavily_search(
    query: str,
    max_results: int = 5,
    topic: str = "general",
    search_depth: str = "basic",
    include_answer: bool = True,
    time_range: str = "",
    include_domains: Optional[Iterable[str]] = None,
    exclude_domains: Optional[Iterable[str]] = None,
    include_raw_content: bool = False,
    _context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    clean_query = (query or "").strip()
    if not clean_query:
        raise ToolError("Tavily query is required.")
    key = _api_key(_context, "tavily")
    payload: Dict[str, Any] = {
        "query": clean_query,
        "topic": topic,
        "search_depth": search_depth,
        "max_results": max(1, min(int(max_results or 5), 10)),
        "include_answer": bool(include_answer),
        "include_raw_content": bool(include_raw_content),
    }
    if (time_range or "").strip():
        payload["time_range"] = time_range.strip()
    included = [str(x).strip() for x in (include_domains or []) if str(x).strip()]
    excluded = [str(x).strip() for x in (exclude_domains or []) if str(x).strip()]
    if included:
        payload["include_domains"] = included[:10]
    if excluded:
        payload["exclude_domains"] = excluded[:10]
    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json=payload,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
            timeout=_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise ToolError(f"Tavily request failed: {exc}") from exc
    _raise_http("Tavily", response)
    try:
        body = response.json()
    except ValueError as exc:
        raise ToolError("Tavily returned a non-JSON response.") from exc
    return {
        "success": True,
        "provider": "tavily",
        "query": clean_query,
        "answer": body.get("answer") if isinstance(body, dict) else None,
        "results": body.get("results", []) if isinstance(body, dict) else [],
    }
