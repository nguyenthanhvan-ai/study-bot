"""Memory validation and SQLite migration: decides which memories are safe to store."""
import re, time

CATEGORIES = {"fact":"stable non-sensitive user fact", "preference":"stated preference", "event":"real event explicitly shared", "shared":"mutually established shared fact", "unconfirmed":"uncertain detail; do not treat as fact"}
ALIASES = {"ve_em":"fact", "so_thich":"preference", "su_kien":"event", "hai_dua":"shared", **{k:k for k in CATEGORIES}}

SENSITIVE = re.compile(r"\b(password|passcode|api key|secret key|credit card|bank account|medical|health condition|diagnosis|medication|pregnan|address|street address|lives in|located at|coordinates|phone number|salary|income|sex|sexual|coercion|non-consensual|forced|rape|intimate fantasy)\b", re.I)
ROLEPLAY = re.compile(r"\b(roleplay|fictional|imagine|what if|hypothetical|in this scene|pretend|fantasy)\b", re.I)

def migrate(conn):
    cols={r[1] for r in conn.execute("PRAGMA table_info(ky_uc)")}
    for name,decl in (("confidence","REAL DEFAULT 0.75"),("source","TEXT DEFAULT 'legacy'"),("status","TEXT DEFAULT 'active'"),("updated_at","REAL")):
        if name not in cols: conn.execute(f"ALTER TABLE ky_uc ADD COLUMN {name} {decl}")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_kyuc_status_time ON ky_uc(status, luc DESC)")

def validate(item):
    if not isinstance(item,dict): return None
    text=str(item.get("noi_dung") or item.get("content") or "").strip()
    category=ALIASES.get(str(item.get("loai") or item.get("type") or "fact").strip(), "fact")
    if not 8 <= len(text) <= 240: return None
    if SENSITIVE.search(text) or ROLEPLAY.search(text): return None
    # Avoid first-person / unverifiable narrative fragments as persistent facts.
    if text.lower().startswith(("maybe ","perhaps ","i think ","i guess ","the user might")): return None
    try:
        confidence=float(item.get("confidence",0.8))
    except (TypeError, ValueError):
        confidence=0.0
    confidence=max(0.0,min(1.0,confidence))
    if confidence < 0.65 or category == "unconfirmed": return None
    return {"loai":category,"noi_dung":text,"confidence":confidence}
