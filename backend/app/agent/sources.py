# backend\app\agent\sources.py

"""
Pipeline de tratamento de fontes (sources) do agente.

Aplica 4 transformações sequenciais aos resultados Tavily:
  1. classify_recency  — identifica versões revogadas/históricas
  2. deduplicate       — colapsa duplicados sobre o mesmo artigo
  3. rerank            — ordena por pertinência à query (keyword-overlap)
  4. extract_used      — separa fontes citadas na resposta das não usadas

Uso: process_sources(sources, query) encadeia as 3 primeiras.
"""

import re
from typing import List, Tuple, Optional
from urllib.parse import urlparse

from ..models import Source


_REVOKED_URL_PATTERNS = re.compile(
    r"lei_velhas|historico|/versao/|revogad|versoes[-_]?anteriores|antiga",
    re.IGNORECASE,
)

_REVOKED_TITLE_PATTERNS = re.compile(
    r"revogad[oa]|versão\s+anterior|versão\s+histórica|anterior\s+a\s+\d|"
    r"antiga\s+reda[cç][ãa]o|alterad[oa]\s+por|vers[ãa]o\s+inicial",
    re.IGNORECASE,
)

# Captura padrões como: artigo-238, art-238, art238, art. 238, artigo 238.º
_ARTICLE_RE = re.compile(
    r"art(?:igo)?[-_.\s]*(\d{1,4})[.ºª]?",
    re.IGNORECASE,
)


def _extract_article_key(url: str, title: str) -> Optional[str]:
    """
    Extrai uma chave canónica de artigo a partir da URL ou título.
    Retorna ex: 'art_238' ou None se não for possível identificar.
    """
    for text in (url, title):
        m = _ARTICLE_RE.search(text)
        if m:
            return f"art_{m.group(1)}"
    return None


def _extract_path_key(url: str) -> str:
    """Extrai o path da URL como chave de fallback para deduplicação."""
    try:
        parsed = urlparse(url)
        path = parsed.path.rstrip("/")
        return f"{parsed.netloc}{path}"
    except Exception:
        return url


def classify_recency(sources: List[Source]) -> List[Source]:
    """
    Marca cada fonte como vigente (is_current=True) ou histórica/revogada
    (is_current=False) com base em padrões na URL e título.
    Ordena: vigentes primeiro, históricas depois.
    """
    for s in sources:
        is_revoked = bool(
            _REVOKED_URL_PATTERNS.search(s.url)
            or _REVOKED_TITLE_PATTERNS.search(s.title)
        )
        s.is_current = not is_revoked

    return sorted(sources, key=lambda s: (not s.is_current,))


def deduplicate(sources: List[Source]) -> List[Source]:
    """
    Colapsa fontes que referem o mesmo artigo jurídico.
    Quando há duplicados, mantém a versão vigente (is_current=True) ou a
    primeira encontrada.
    """
    seen: dict[str, int] = {}
    result: List[Source] = []

    for s in sources:
        key = _extract_article_key(s.url, s.title) or _extract_path_key(s.url)

        if key in seen:
            idx = seen[key]
            existing = result[idx]
            # Substitui se o existente é histórico mas o novo é vigente
            if not existing.is_current and s.is_current:
                result[idx] = s
        else:
            seen[key] = len(result)
            result.append(s)

    return result


_STOP_WORDS = {
    "o",
    "a",
    "os",
    "as",
    "um",
    "uma",
    "de",
    "do",
    "da",
    "dos",
    "das",
    "em",
    "no",
    "na",
    "nos",
    "nas",
    "por",
    "para",
    "com",
    "sem",
    "ao",
    "à",
    "e",
    "ou",
    "que",
    "se",
    "é",
    "são",
    "como",
    "qual",
    "quais",
    "ter",
    "tem",
    "têm",
    "ser",
    "foi",
    "está",
}


def _tokenize(text: str) -> set[str]:
    """Tokeniza texto em lowercase, removendo stop words e pontuação."""
    tokens = re.findall(r"[a-záàâãéêíóôõúç\d]+", text.lower())
    return {t for t in tokens if t not in _STOP_WORDS and len(t) > 1}


def rerank(sources: List[Source], query: str) -> List[Source]:
    """
    Ordena fontes por sobreposição de keywords com a query do utilizador.
    Define relevance_score em cada fonte.
    """
    query_tokens = _tokenize(query)
    if not query_tokens:
        return sources

    scored: List[Tuple[float, int, Source]] = []
    for i, s in enumerate(sources):
        source_text = f"{s.title} {s.snippet or ''}"
        source_tokens = _tokenize(source_text)
        overlap = len(query_tokens & source_tokens)
        score = overlap / len(query_tokens) if query_tokens else 0.0
        s.relevance_score = round(score, 3)
        # Score negativo para sort descendente; índice garante estabilidade
        scored.append((-score, i, s))

    scored.sort()
    return [s for _, _, s in scored]


def extract_used_sources(
    sources: List[Source], response_text: str
) -> Tuple[List[Source], List[Source]]:
    """
    Determina quais fontes foram efectivamente citadas na resposta do modelo.

    Uma fonte é considerada "usada" se a resposta contém:
      - O domínio da sua URL (ex: 'portal.act.gov.pt')
      - O número de artigo presente no título/URL (ex: 'art. 238', '238.º')
      - Um fragmento significativo do título (≥ 3 palavras consecutivas)

    Returns:
        (used, unused) — duas listas de Source
    """
    if not response_text:
        return [], list(sources)

    text_lower = response_text.lower()
    used: List[Source] = []
    unused: List[Source] = []

    for s in sources:
        if _source_cited(s, text_lower):
            used.append(s)
        else:
            unused.append(s)

    return used, unused


def _source_cited(source: Source, response_lower: str) -> bool:
    """Verifica se uma fonte foi citada no texto da resposta (já em lowercase)."""
    try:
        domain = urlparse(source.url).netloc.lstrip("www.")
        if domain and domain in response_lower:
            return True
    except Exception:
        pass

    article_match = _ARTICLE_RE.search(source.title) or _ARTICLE_RE.search(source.url)
    if article_match:
        art_num = article_match.group(1)
        # Procura variantes: "art. 238", "artigo 238", "238.º", "238º"
        art_patterns = [
            f"art. {art_num}",
            f"art.º {art_num}",
            f"artigo {art_num}",
            f"{art_num}.º",
            f"{art_num}º",
        ]
        if any(p in response_lower for p in art_patterns):
            return True

    title_tokens = [t for t in _tokenize(source.title) if len(t) > 2]
    if len(title_tokens) >= 3:
        title_lower = source.title.lower()
        words = re.findall(r"[a-záàâãéêíóôõúç\d]+", title_lower)
        significant = [w for w in words if w not in _STOP_WORDS and len(w) > 2]
        for i in range(len(significant) - 2):
            fragment = f"{significant[i]} {significant[i+1]} {significant[i+2]}"
            if fragment in response_lower:
                return True

    return False


def process_sources(sources: List[Source], query: str) -> List[Source]:
    """Aplica classify_recency → deduplicate → rerank."""
    if not sources:
        return sources
    sources = classify_recency(sources)
    sources = deduplicate(sources)
    sources = rerank(sources, query)
    return sources
