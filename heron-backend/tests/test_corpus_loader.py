"""Legal corpus integrity tests.

The corpus is the legal ground truth of the product: statutory text must be
loaded verbatim, and a bad file must never crash the app.
"""

import asyncio
import json
import shutil

import pytest

from app.engine.corpus_loader import CORPUS_DIR, CorpusLoader

EMPCO_4A_OFFICIAL_TEXT = (
    "Making a generic environmental claim for which the trader is not able to "
    "demonstrate recognised excellent environmental performance relevant to the claim."
)


@pytest.fixture(scope="module")
def corpus_files() -> dict:
    index = json.loads((CORPUS_DIR / "corpus_index.json").read_text(encoding="utf-8"))
    files = {}
    for entry in index["corpora"]:
        files[entry["id"]] = json.loads(
            (CORPUS_DIR / entry["file"]).read_text(encoding="utf-8")
        )
    return {"index": index, "files": files}


def test_all_corpus_files_load(corpus_files):
    assert len(corpus_files["files"]) == 3
    for corpus_id, data in corpus_files["files"].items():
        assert data["corpus"]["id"] == corpus_id
        assert data["articles"], f"{corpus_id} has no articles"


def test_index_lists_three_active_corpora(corpus_files):
    active = [c for c in corpus_files["index"]["corpora"] if c["status"] == "active"]
    assert {c["id"] for c in active} == {"EMPCO_2024_825", "FR_CONSUMER_CODE", "FR_ENV_CODE"}


def test_empco_4a_full_text_is_verbatim_statutory_text(corpus_files):
    articles = {a["id"]: a for a in corpus_files["files"]["EMPCO_2024_825"]["articles"]}
    assert articles["EMPCO_2024_825_ANNEX_4A"]["full_text"] == EMPCO_4A_OFFICIAL_TEXT


def test_empco_4c_mentions_offsetting(corpus_files):
    articles = {a["id"]: a for a in corpus_files["files"]["EMPCO_2024_825"]["articles"]}
    assert "offsetting of greenhouse gas emissions" in articles["EMPCO_2024_825_ANNEX_4C"]["full_text"]


def test_l132_2_turnover_percentage(corpus_files):
    articles = {a["id"]: a for a in corpus_files["files"]["FR_CONSUMER_CODE"]["articles"]}
    penalties = articles["FR_CC_L132_2"]["penalties"]
    assert penalties["proportional"]["turnover_percentage"] == 0.10
    # Current L132-2 (LOI 2024-420): 80% of ad spend for environmental claims
    assert penalties["proportional"]["env_claims_ad_spend_percentage"] == 0.80
    assert penalties["natural_person"]["online_fine_eur"] == 750000


def test_l121_2_full_text_verified(corpus_files):
    articles = {a["id"]: a for a in corpus_files["files"]["FR_CONSUMER_CODE"]["articles"]}
    article = articles["FR_CC_L121_2"]
    assert article["verification_status"] == "verified_source"
    assert "notamment son impact environnemental" in article["full_text"]
    assert "La portée des engagements de l'annonceur, notamment en matière environnementale" in article["full_text"]


def test_r541_223_full_text_verified(corpus_files):
    articles = {a["id"]: a for a in corpus_files["files"]["FR_ENV_CODE"]["articles"]}
    article = articles["FR_EC_R541_223"]
    assert article["verification_status"] == "verified_source"
    # Décret 2022-748 wording: 'allégation environnementale équivalente'
    assert "toute autre allégation environnementale équivalente" in article["full_text"]
    assert "biodégradable" in article["full_text"]


def test_all_articles_have_verified_sources(corpus_files):
    pending = [
        a["id"]
        for data in corpus_files["files"].values()
        for a in data["articles"]
        if a.get("verification_status") != "verified_source"
    ]
    assert pending == [], f"Unverified statutory text: {pending}"


def test_l541_9_1_full_text_verified(corpus_files):
    articles = {a["id"]: a for a in corpus_files["files"]["FR_ENV_CODE"]["articles"]}
    article = articles["FR_EC_L541_9_1"]
    assert article["verification_status"] == "verified_source"
    assert "Afin d'améliorer l'information des consommateurs" in article["full_text"]
    # The legislative twin of R541-223 lives in this article
    assert "biodégradable" in article["full_text"]
    assert "toute autre mention équivalente" in article["full_text"]


def test_l132_2_full_text_matches_legifrance(corpus_files):
    articles = {a["id"]: a for a in corpus_files["files"]["FR_CONSUMER_CODE"]["articles"]}
    text = articles["FR_CC_L132_2"]["full_text"]
    assert "10 % du chiffre d'affaires moyen annuel" in text
    assert "porté à 80 %" in text
    assert "cinq ans d'emprisonnement et à 750 000 euros" in text
    assert articles["FR_CC_L132_2"]["verification_status"] == "verified_source"


def test_corpus_loads_into_db(initialized_db):
    from app.database import _connect

    async def run():
        db = await _connect(initialized_db)
        try:
            loader = CorpusLoader()
            summary = await loader.get_corpus_summary(db)
            article = await loader.get_article("EMPCO_2024_825_ANNEX_4A", db)
            rule_articles = await loader.get_articles_for_rule("VLX-EMP-004", db)
        finally:
            await db.close()
        return summary, article, rule_articles

    summary, article, rule_articles = asyncio.run(run())
    assert {c["id"] for c in summary} == {"EMPCO_2024_825", "FR_CONSUMER_CODE", "FR_ENV_CODE"}
    assert all(c["article_count"] > 0 for c in summary)
    assert article["full_text"] == EMPCO_4A_OFFICIAL_TEXT
    # Carbon rule links both the Annex I 4c ban and Article 6(2)(d)
    linked = {a["id"] for a in rule_articles}
    assert linked == {"EMPCO_2024_825_ANNEX_4C", "EMPCO_2024_825_ART_6_2D"}


def test_invalid_corpus_file_is_skipped_not_fatal(initialized_db, tmp_path):
    """A corrupt corpus file must be logged and skipped, never crash."""
    custom_dir = tmp_path / "corpus"
    custom_dir.mkdir()
    for f in CORPUS_DIR.iterdir():
        shutil.copy(f, custom_dir / f.name)
    (custom_dir / "broken.json").write_text("{not valid json", encoding="utf-8")
    index = json.loads((custom_dir / "corpus_index.json").read_text(encoding="utf-8"))
    index["corpora"].append({"id": "BROKEN", "file": "broken.json", "status": "active", "priority": 9})
    (custom_dir / "corpus_index.json").write_text(json.dumps(index), encoding="utf-8")

    from app.database import _connect

    async def run():
        db = await _connect(initialized_db)
        try:
            return await CorpusLoader(corpus_dir=custom_dir).load_all(db)
        finally:
            await db.close()

    corpora, articles = asyncio.run(run())
    assert corpora == 3  # the 3 valid ones loaded, BROKEN skipped
    assert articles > 0


def test_new_corpus_detected_by_check_for_updates(initialized_db, tmp_path):
    """Adding a corpus JSON + index entry is picked up with zero code changes."""
    custom_dir = tmp_path / "corpus"
    custom_dir.mkdir()
    for f in CORPUS_DIR.iterdir():
        shutil.copy(f, custom_dir / f.name)
    new_corpus = {
        "corpus": {
            "id": "GREEN_CLAIMS_DIR", "short_name": "Green Claims Directive",
            "full_name": "Proposal for a Directive on substantiation of green claims",
            "jurisdiction": "EU", "law_type": "directive",
            "official_reference": "COM(2023) 166", "publication_date": "2023-03-22",
            "application_date": "2028-01-01", "status": "active",
        },
        "articles": [{
            "id": "GCD_ART_3", "article_ref": "Article 3",
            "full_text": "Placeholder statutory text pending adoption.",
            "summary": "Substantiation of explicit environmental claims.",
            "applies_to": "all", "prohibited_behaviour": "Unsubstantiated explicit claims",
            "effective_from": "2028-01-01",
        }],
    }
    (custom_dir / "green_claims.json").write_text(json.dumps(new_corpus), encoding="utf-8")
    index = json.loads((custom_dir / "corpus_index.json").read_text(encoding="utf-8"))
    index["corpora"].append(
        {"id": "GREEN_CLAIMS_DIR", "file": "green_claims.json", "status": "active", "priority": 4}
    )
    (custom_dir / "corpus_index.json").write_text(json.dumps(index), encoding="utf-8")

    from app.database import _connect

    async def run():
        db = await _connect(initialized_db)
        try:
            loader = CorpusLoader(corpus_dir=custom_dir)
            changed = await loader.check_for_updates(db)
            await loader.load_all(db)
            article = await loader.get_article("GCD_ART_3", db)
        finally:
            await db.close()
        return changed, article

    changed, article = asyncio.run(run())
    assert "GREEN_CLAIMS_DIR" in changed
    assert article is not None
