# backend/tests/test_sources.py

"""
Testes unitários para o pipeline de fontes (sources.py).
Usa apenas Source objects fabricados — sem chamadas de API.
"""

import pytest
from app.models import Source
from app.agent.sources import (
    classify_recency,
    deduplicate,
    rerank,
    extract_used_sources,
    process_sources,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _src(title: str, url: str, snippet: str = "") -> Source:
    return Source(title=title, url=url, snippet=snippet)


# ===========================================================================
# 1. classify_recency
# ===========================================================================
class TestClassifyRecency:
    def test_normal_url_is_current(self):
        sources = [_src("Artigo 238.º — Código do Trabalho", "https://www.pgdlisboa.pt/leis/lei_mostra_articulado.php?artigo_id=1238")]
        result = classify_recency(sources)
        assert result[0].is_current is True

    def test_lei_velhas_url_is_not_current(self):
        sources = [_src("Artigo 238.º — CT (versão anterior)", "https://www.pgdlisboa.pt/leis/lei_velhas/artigo_id=1238")]
        result = classify_recency(sources)
        assert result[0].is_current is False

    def test_revogado_title_is_not_current(self):
        sources = [_src("Lei n.º 7/2009 — Revogada", "https://diariodarepublica.pt/lei-7-2009")]
        result = classify_recency(sources)
        assert result[0].is_current is False

    def test_historico_url_is_not_current(self):
        sources = [_src("Artigo 263.º", "https://example.pt/historico/artigo-263")]
        result = classify_recency(sources)
        assert result[0].is_current is False

    def test_current_sorted_before_historical(self):
        s_current = _src("Artigo 238.º", "https://www.pgdlisboa.pt/artigo-238")
        s_old = _src("Artigo 238.º (antiga)", "https://www.pgdlisboa.pt/leis/lei_velhas/artigo-238")
        result = classify_recency([s_old, s_current])
        assert result[0].is_current is True
        assert result[1].is_current is False


# ===========================================================================
# 2. deduplicate
# ===========================================================================
class TestDeduplicate:
    def test_same_article_collapsed(self):
        s1 = _src("Artigo 238.º — Subsídio de férias", "https://pgdlisboa.pt/artigo-238")
        s1.is_current = True
        s2 = _src("Art. 238 — versão anterior", "https://pgdlisboa.pt/lei_velhas/artigo-238")
        s2.is_current = False
        result = deduplicate([s1, s2])
        assert len(result) == 1
        assert result[0].is_current is True

    def test_historical_replaced_by_current(self):
        """Se o histórico aparece primeiro, é substituído pelo vigente."""
        s_old = _src("Art. 263 — CT anterior", "https://pgdlisboa.pt/lei_velhas/art-263")
        s_old.is_current = False
        s_new = _src("Artigo 263.º — Subsídio de Natal", "https://pgdlisboa.pt/art-263")
        s_new.is_current = True
        result = deduplicate([s_old, s_new])
        assert len(result) == 1
        assert result[0].is_current is True

    def test_distinct_articles_not_collapsed(self):
        s1 = _src("Artigo 238.º", "https://pgdlisboa.pt/artigo-238")
        s2 = _src("Artigo 263.º", "https://pgdlisboa.pt/artigo-263")
        result = deduplicate([s1, s2])
        assert len(result) == 2

    def test_no_article_uses_path_key(self):
        s1 = _src("Página TSU", "https://seg-social.pt/tsu/info")
        s2 = _src("Informação TSU", "https://seg-social.pt/tsu/info")
        result = deduplicate([s1, s2])
        assert len(result) == 1


# ===========================================================================
# 3. rerank
# ===========================================================================
class TestRerank:
    def test_most_relevant_first(self):
        s1 = _src("Portal ACT", "https://portal.act.gov.pt", "informações gerais")
        s2 = _src("Subsídio de Natal — Art. 263.º", "https://pgdlisboa.pt/art-263", "subsídio natal cálculo proporcional")
        s3 = _src("Código do Trabalho", "https://pgdlisboa.pt", "legislação laboral")
        result = rerank([s1, s2, s3], "subsídio de Natal")
        # s2 tem mais sobreposição com a query
        assert result[0].title == "Subsídio de Natal — Art. 263.º"

    def test_relevance_scores_set(self):
        s1 = _src("Subsídio de férias", "https://pgdlisboa.pt/art-264", "férias subsídio")
        result = rerank([s1], "subsídio de férias")
        assert result[0].relevance_score > 0

    def test_empty_sources(self):
        result = rerank([], "qualquer query")
        assert result == []


# ===========================================================================
# 4. extract_used_sources
# ===========================================================================
class TestExtractUsedSources:
    def test_cited_article_is_used(self):
        s1 = _src("Artigo 263.º — Subsídio de Natal", "https://pgdlisboa.pt/art-263")
        s2 = _src("Portal ACT", "https://portal.act.gov.pt")
        response = "Nos termos do art. 263.º do Código do Trabalho, o subsídio de Natal..."
        used, unused = extract_used_sources([s1, s2], response)
        assert len(used) == 1
        assert used[0].title == "Artigo 263.º — Subsídio de Natal"
        assert len(unused) == 1

    def test_cited_domain_is_used(self):
        s1 = _src("Seg Social", "https://www.seg-social.pt/tsu")
        response = "Segundo informações do seg-social.pt, a taxa é de 11%."
        used, unused = extract_used_sources([s1], response)
        assert len(used) == 1

    def test_no_citation_returns_all_unused(self):
        s1 = _src("Artigo 238.º", "https://pgdlisboa.pt/art-238")
        s2 = _src("Artigo 263.º", "https://pgdlisboa.pt/art-263")
        response = "O salário mínimo em Portugal é de 870 EUR."
        used, unused = extract_used_sources([s1, s2], response)
        assert len(used) == 0
        assert len(unused) == 2

    def test_empty_response_returns_all_unused(self):
        s1 = _src("Artigo 238.º", "https://pgdlisboa.pt/art-238")
        used, unused = extract_used_sources([s1], "")
        assert len(used) == 0
        assert len(unused) == 1


# ===========================================================================
# 5. process_sources (pipeline completa)
# ===========================================================================
class TestProcessSources:
    def test_full_pipeline_deduplicates_and_ranks(self):
        sources = [
            _src("Art. 263 — versão anterior", "https://pgdlisboa.pt/lei_velhas/art-263", "natal subsídio"),
            _src("Artigo 263.º — Subsídio de Natal", "https://pgdlisboa.pt/art-263", "subsídio natal cálculo"),
            _src("Portal ACT", "https://portal.act.gov.pt/geral", "informações gerais"),
        ]
        result = process_sources(sources, "subsídio de Natal")
        # Deduplicação: as duas versões do art. 263 devem colapsar para 1
        assert len(result) == 2
        # A versão vigente deve ter sobrevivido
        art_263 = [s for s in result if "263" in s.title]
        assert len(art_263) == 1
        assert art_263[0].is_current is True

    def test_empty_sources(self):
        result = process_sources([], "qualquer query")
        assert result == []
