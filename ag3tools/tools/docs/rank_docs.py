import re
from typing import List

import tldextract

from ag3tools.core.types import RankDocsInput, RankedResult, SearchResult
from ag3tools.core.registry import register_tool


DOC_KEYWORDS = {
    "docs",
    "documentation",
    "guide",
    "guides",
    "api",
    "reference",
    "handbook",
    "manual",
    "developer",
    "developers",
}

DOC_PATH_HINTS = {"/docs", "/documentation", "/api", "/reference", "/handbook", "/manual"}
UNOFFICIAL_HINTS = {
    "stackoverflow.com",
    "medium.com",
    "dev.to",
    "reddit.com",
    "news.ycombinator.com",
    "quora.com",
    "zhihu.com",
    "baidu.com",
    "bilibili.com",
    "youtube.com",
    "x.com",
    "twitter.com",
    "facebook.com",
    "linkedin.com",
    "stackshare.io",
}
REPO_SITES = {"github.com", "gitlab.com", "bitbucket.org"}
PACKAGE_INDEX_SITES = {"pypi.org", "npmjs.com", "crates.io", "rubygems.org", "packagist.org"}


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip().lower()


def ext_domain_equals(tech_norm: str, url: str) -> bool:
    try:
        ext = tldextract.extract(url)
        return ext.domain.lower() == tech_norm
    except Exception:
        return False


def _domain_parts(url: str):
    ext = tldextract.extract(url)
    sub = ext.subdomain.lower()
    dom = f"{ext.domain}.{ext.suffix}".lower() if ext.suffix else ext.domain.lower()
    fqdn = f"{sub}.{dom}" if sub else dom
    return sub, dom, fqdn


def _score(res: SearchResult, tech: str) -> float:
    tech_norm = _normalize(tech)
    title = _normalize(res.title)
    snippet = _normalize(res.snippet)
    sub, dom, fqdn = _domain_parts(res.url)
    lower_url = res.url.lower()
    path = lower_url.split(dom, 1)[-1] if dom in lower_url else lower_url

    score = 0.0
    if tech_norm in title or tech_norm in snippet or tech_norm in lower_url:
        score += 3.0
    if any(k in title for k in DOC_KEYWORDS):
        score += 2.5
    if any(k in path for k in DOC_PATH_HINTS):
        score += 2.0
    if "docs" in sub or "developer" in sub or "developers" in sub:
        score += 2.0
    if dom.endswith("readthedocs.io") or dom.endswith("github.io"):
        score += 1.5
    if ext_domain_equals(tech_norm, res.url):
        score += 1.5

    if tech_norm == "langgraph" and ("langchain-ai.github.io" in fqdn or dom in {"langchain.com", "langchain.dev", "langgraph.dev"}):
        score += 4.0

    if "official" in title or "official" in snippet:
        score += 1.0

    if any(u in dom for u in UNOFFICIAL_HINTS):
        score -= 2.5
    if any(u in dom for u in PACKAGE_INDEX_SITES):
        score -= 1.5
    if any(u in dom for u in REPO_SITES):
        if not ("/wiki" in path or "/docs" in path or "/documentation" in path):
            score -= 1.5
    if not any(k in title for k in DOC_KEYWORDS) and not any(k in path for k in DOC_PATH_HINTS):
        score -= 0.5

    return score


@register_tool(
    description="Rank candidate documentation URLs by heuristic scores favoring likely official docs.",
    input_model=RankDocsInput,
    tags=["docs", "ranking"],
)
def rank_docs(input: RankDocsInput) -> List[RankedResult]:
    ranked = [RankedResult(result=r, score=_score(r, input.technology)) for r in input.candidates]
    ranked.sort(key=lambda x: x.score, reverse=True)
    return ranked


