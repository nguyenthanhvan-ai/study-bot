"""Lightweight local retrieval for memories and conversation snippets (no extra deps)."""
from __future__ import annotations
import math, re, unicodedata, time

STOP = set("a an the and or but if then than of to in on at for with from by is are was were be been being it its this that these those i me my mine you your yours he she we they them their what when where why how do did does can could would should will just very really about into over under again not no yes ok okay uh um hmm la va thi ma co khong ko la em anh toi minh cua voi va mot nhung cac cho nay kia di duoc nhu sao the".split())

def tokenize(text: str) -> list[str]:
    text = unicodedata.normalize("NFD", (text or "").lower()).replace("đ", "d")
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return [t for t in re.findall(r"[a-z0-9]+", text) if len(t) > 1 and t not in STOP]

def score(query: str, document: str, age_seconds: float = 0.0, uses: int = 0) -> float:
    q, d = tokenize(query), tokenize(document)
    if not q or not d: return 0.0
    qset, dset = set(q), set(d)
    overlap = len(qset & dset)
    bigram_q = set(zip(q, q[1:])); bigram_d = set(zip(d, d[1:]))
    phrase = len(bigram_q & bigram_d)
    coverage = overlap / max(1, len(qset))
    density = overlap / max(1, math.sqrt(len(qset) * len(dset)))
    recency = 0.12 * math.exp(-max(0, age_seconds) / (45 * 86400))
    reuse = min(0.08, max(0, uses) * 0.008)
    return coverage * 1.8 + density + phrase * 0.55 + recency + reuse

def rank_memories(query: str, rows, limit: int = 5, threshold: float = 0.48):
    now = time.time(); ranked=[]
    for row in rows:
        age = max(0.0, now - float(row["luc"] or now))
        s = score(query, row["noi_dung"], age, int(row["so_lan_dung"] or 0))
        # Explicit category weighting: stable preferences/facts are more useful than one-off events.
        category = str(row["loai"] or "")
        s *= {"so_thich":1.10,"ve_em":1.08,"fact":1.08,"preference":1.10,"hai_dua":1.04,"shared":1.04,"su_kien":0.96,"event":0.96}.get(category,1.0)
        ranked.append((s,row))
    ranked.sort(key=lambda x:x[0], reverse=True)
    return [r for s,r in ranked[:limit] if s >= threshold]

def rank_conversation(query: str, rows, limit: int = 3, threshold: float = 0.72):
    """Select older chat turns that match the current topic; rows are newest-first SQLite rows."""
    now=time.time(); ranked=[]
    for row in rows:
        content=str(row["noi_dung"] or "").strip()
        if len(content) < 18: continue
        age=max(0.0, now-float(row["luc"] or now))
        s=score(query, content, age)
        ranked.append((s,row))
    ranked.sort(key=lambda x:x[0], reverse=True)
    return [r for s,r in ranked[:limit] if s >= threshold]
