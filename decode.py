"""Rebuild fragmented Ollama NDJSON streams from hex-encoded byte chunks.

Usage:
    python decode.py chunks.json > answer.json

chunks.json is the JSON object copied from the exam page:
    {"A": ["7b22...", ...], "B": [...], "C": [...]}
"""
import json
import sys


def decode_stream(chunks):
    # Join the raw BYTES first, so multi-byte UTF-8 characters split across
    # chunk boundaries are reassembled before any decoding happens.
    data = b"".join(bytes.fromhex(c.strip()) for c in chunks)

    # Only newline-terminated lines are complete records; whatever follows the
    # last newline is an incomplete trailing record and is ignored.
    lines = data.split(b"\n")[:-1]

    text = ""
    for raw in lines:
        raw = raw.strip()
        if not raw:
            continue
        try:
            rec = json.loads(raw.decode("utf-8"))
        except Exception:
            continue  # not a valid complete record

        if rec.get("error"):
            # keep earlier text, set the error, stop. Ignore later records.
            return {"text": text, "complete": False, "error": str(rec["error"])}

        text += rec.get("response", "") or ""  # "thinking" is ignored

        if rec.get("done") is True:
            return {"text": text, "complete": True, "error": None}

    # transport EOF without a terminal record
    return {"text": text, "complete": False, "error": None}


def main():
    with open(sys.argv[1], encoding="utf-8") as f:
        streams = json.load(f)
    out = {name: decode_stream(chunks) for name, chunks in streams.items()}
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
