"""Public legal corpus endpoints — power the frontend 'Textes de loi' page.

The full_text returned here is verbatim statutory text from the corpus
tables. It is never generated or transformed.
"""

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_db
from app.engine.corpus_loader import CorpusLoader

router = APIRouter(prefix="/corpus", tags=["corpus"])

loader = CorpusLoader()

ARTICLE_FIELDS = (
    "id", "article_ref", "article_title", "full_text", "summary",
    "prohibited_behaviour", "evidence_required", "effective_from",
    "verification_status",
)


@router.get("")
async def list_corpora(db: aiosqlite.Connection = Depends(get_db)):
    return {"corpora": await loader.get_corpus_summary(db)}


@router.get("/{corpus_id}")
async def get_corpus(corpus_id: str, db: aiosqlite.Connection = Depends(get_db)):
    cursor = await db.execute("SELECT * FROM legal_corpus WHERE id = ?", (corpus_id,))
    corpus = await cursor.fetchone()
    if corpus is None:
        raise HTTPException(status_code=404, detail="Corpus not found")
    cursor = await db.execute(
        "SELECT * FROM legal_articles WHERE corpus_id = ? ORDER BY id", (corpus_id,)
    )
    articles = [
        {k: dict(row)[k] for k in ARTICLE_FIELDS}
        for row in await cursor.fetchall()
    ]
    return {"corpus": dict(corpus), "articles": articles}


@router.get("/{corpus_id}/articles/{article_id}")
async def get_corpus_article(
    corpus_id: str, article_id: str, db: aiosqlite.Connection = Depends(get_db)
):
    article = await loader.get_article(article_id, db)
    if article is None or article["corpus_id"] != corpus_id:
        raise HTTPException(status_code=404, detail="Article not found")
    return article
