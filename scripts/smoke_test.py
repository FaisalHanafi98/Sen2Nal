"""
Sen2Nal Smoke Test — Phase 5.5.2
Validates core stack: env vars, PostgreSQL, FinBERT, Python 3.14 compatibility.
"""

import os
import sys
import time
import warnings

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Load .env manually (python-dotenv may not be installed yet)
def _load_env(path: str = ".env") -> None:
    env_path = os.path.join(os.path.dirname(__file__), "..", path)
    if not os.path.isfile(env_path):
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

_load_env()

PASS = "[OK]"
WARN = "[WARN]"
FAIL = "[FAIL]"

results = {"passed": 0, "failed": 0, "warnings": 0}


def status(label: str, ok: bool, warn: bool = False) -> None:
    if warn:
        icon = WARN
        results["warnings"] += 1
    elif ok:
        icon = PASS
        results["passed"] += 1
    else:
        icon = FAIL
        results["failed"] += 1
    print(f"  {label} {'.' * (30 - len(label))} {icon}")


def header(num: int, total: int, title: str) -> None:
    print(f"\n[{num}/{total}] {title}")


# ═══════════════════════════════════════════════════════════════
#  Test 1: Environment Variables
# ═══════════════════════════════════════════════════════════════
def test_env() -> None:
    header(1, 4, "Environment Variables")

    db_url = os.getenv("DATABASE_URL")
    db_host = os.getenv("DB_HOST")
    has_db = bool(db_url) or bool(db_host)
    status("DATABASE_URL or DB_HOST", has_db)
    if not has_db:
        results["failed"] += 1  # critical

    for key, required in [
        ("ALPHA_VANTAGE_API_KEY", False),
        ("NEWSAPI_API_KEY", False),
        ("REDDIT_CLIENT_ID", False),
    ]:
        val = os.getenv(key, "")
        is_placeholder = not val or "your_" in val or "here" in val
        if required:
            status(key, not is_placeholder)
        else:
            if is_placeholder:
                status(f"{key} (optional)", False, warn=True)
            else:
                status(key, True)


# ═══════════════════════════════════════════════════════════════
#  Test 2: PostgreSQL Connection
# ═══════════════════════════════════════════════════════════════
def test_postgres() -> None:
    header(2, 4, "PostgreSQL Connection")

    try:
        from sqlalchemy import create_engine, inspect, text

        db_url = os.getenv(
            "DATABASE_URL",
            f"postgresql://{os.getenv('DB_USER', 'sen2nal_user')}:{os.getenv('DB_PASSWORD', 'sen2nal_password')}"
            f"@{os.getenv('DB_HOST', '127.0.0.1')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'sen2nal')}",
        )
        engine = create_engine(db_url)

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        status("Connection", True)

        inspector = inspect(engine)
        tables = inspector.get_table_names()
        expected = {
            "dim_stocks", "dim_calendar", "dim_fear_greed",
            "fact_sentiment", "fact_prices", "fact_predictions", "fact_experiment",
            "stg_news_raw", "stg_reddit_raw", "alembic_version",
        }
        found = expected.intersection(tables)
        status(f"Tables found ({len(found)}/{len(expected)})", len(found) == len(expected))
        if found != expected:
            missing = expected - found
            print(f"    Missing: {missing}")

        # Insert/read/delete test on stg_news_raw (least constrained)
        with engine.connect() as conn:
            conn.execute(text(
                "INSERT INTO stg_news_raw (source, headline) "
                "VALUES ('smoke_test', 'Sen2Nal smoke test row')"
            ))
            row = conn.execute(text(
                "SELECT raw_id FROM stg_news_raw WHERE source = 'smoke_test'"
            )).fetchone()
            assert row is not None, "Insert verification failed"
            conn.execute(text("DELETE FROM stg_news_raw WHERE source = 'smoke_test'"))
            conn.commit()
        status("Insert/Read/Delete", True)

        engine.dispose()
    except Exception as e:
        status(f"PostgreSQL ERROR: {e}", False)


# ═══════════════════════════════════════════════════════════════
#  Test 3: FinBERT Model Load
# ═══════════════════════════════════════════════════════════════
def test_finbert() -> None:
    header(3, 4, "FinBERT Model")

    try:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        t0 = time.time()
        tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
        model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
        model.eval()
        load_time = time.time() - t0
        status(f"Model load time ({load_time:.1f}s)", True)

        headline = "Apple reports record quarterly revenue beating analyst expectations"
        t1 = time.time()
        inputs = tokenizer(headline, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            logits = model(**inputs).logits
        probs = torch.nn.functional.softmax(logits, dim=-1)[0]
        infer_time = time.time() - t1

        labels = ["positive", "negative", "neutral"]
        scores = {labels[i]: round(probs[i].item(), 4) for i in range(3)}
        status(f"Inference ({infer_time:.3f}s)", True)
        print(f"    Scores: pos={scores['positive']}, neg={scores['negative']}, neu={scores['neutral']}")

    except Exception as e:
        status(f"FinBERT ERROR: {e}", False)


# ═══════════════════════════════════════════════════════════════
#  Test 4: Python Compatibility
# ═══════════════════════════════════════════════════════════════
def test_compatibility() -> None:
    header(4, 4, f"Python {sys.version.split()[0]} Compatibility")

    pkgs = {"torch": "torch", "transformers": "transformers", "xgboost": "xgboost", "sqlalchemy": "sqlalchemy"}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        for name, mod in pkgs.items():
            try:
                __import__(mod)
                status(name, True)
            except Exception as e:
                status(f"{name} — {e}", False)

    if caught:
        print("    Deprecation warnings:")
        for w in caught[:5]:
            print(f"      - {w.message}")


# ═══════════════════════════════════════════════════════════════
#  Runner
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\n" + "=" * 47)
    print("  Sen2Nal Smoke Test - Phase 5.5.2")
    print("=" * 47)

    test_env()
    test_postgres()
    test_finbert()
    test_compatibility()

    total = results["passed"] + results["failed"]
    print("\n" + "=" * 47)
    print(f"  RESULT: {results['passed']}/{total} passed | {results['failed']} failed | {results['warnings']} warnings")
    print("=" * 47 + "\n")

    sys.exit(1 if results["failed"] > 0 else 0)
