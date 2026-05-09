"""Inject "Claim on E156" chips into rapidmeta-finerenone/index.html.

For each <a href="X_REVIEW.html"> on the landing page, look up whether that
review has an E156 paper (parsed from C:/E156/students.html ENTRIES) and
add a small green chip linking to
  https://mahmood726-cyber.github.io/e156/students.html?focus=NNN

Idempotent. Safe to re-run.
"""
from __future__ import annotations
import io, json, re, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent
INDEX = REPO / "index.html"
DASHBOARD = REPO / "dashboard.html"
# Other landing/index pages that link to reviews. Discovered by grepping
# for _REVIEW.html across non-review HTML in the repo. Anything matching
# this list also gets the chip injector + style block.
EXTRA_LANDING_PAGES = [
    REPO / "NMA_INDEX.html",
    REPO / "META_DASHBOARD.html",
    REPO / "AutoManuscript.html",
]
STUDENTS = Path(r"C:\E156\students.html")
E156_BASE = "https://mahmood726-cyber.github.io/e156/students.html"
RAPIDMETA_REPO_URL = "rapidmeta-finerenone"  # match against e.code_url

MARKER_BEGIN = "<!-- e156-claim-chips:begin -->"
MARKER_END = "<!-- e156-claim-chips:end -->"
STYLE_BEGIN = "<!-- e156-claim-chips-style:begin -->"
STYLE_END = "<!-- e156-claim-chips-style:end -->"


def parse_entries(students_html: str) -> list[dict]:
    """Pull the JS array `const ENTRIES = [...]` and parse as JSON."""
    m = re.search(r"const\s+ENTRIES\s*=\s*(\[.*?\]);", students_html, re.DOTALL)
    if not m:
        raise RuntimeError("ENTRIES const not found in students.html")
    return json.loads(m.group(1))


def _score_match(review_base: str, title: str) -> int:
    """Heuristic match score between a review filename and an E156 paper title.

    Higher = better. The intent is to pick the most-canonical paper when
    multiple E156 papers reference the same review HTML. Tie-broken by
    lower paper number (older / canonical) at the caller.
    """
    rev_stem = review_base.replace("_REVIEW.html", "").lower()
    tit_norm = (title or "").lower().replace("-", "").replace("/", "").replace(" ", "")
    score = 0
    # Strong: the entire review stem (no underscores) is a substring of the title
    rev_norm = rev_stem.replace("_", "")
    if rev_norm and rev_norm in tit_norm:
        score += 200
    # Per-token matches (drug stems, abbreviations)
    for tok in rev_stem.split("_"):
        tok = tok.replace("-", "")
        if len(tok) >= 3 and tok in tit_norm:
            score += 10 * len(tok)
    # Slight reward for "RapidMeta" branded papers (canonical series)
    if "rapidmeta" in tit_norm:
        score += 5
    return score


def build_map(entries: list[dict]) -> tuple[dict[str, dict], list[dict]]:
    """Map review-file basename → {num, title} for rapidmeta papers.

    On collision (two E156 papers point to the same _REVIEW.html), pick
    the higher-scoring match; tie-break by lower paper-num. Returns
    (mapping, audit) where audit is a list of every collision shown.
    """
    candidates: dict[str, list[dict]] = {}
    for e in entries:
        code_url = e.get("code_url") or ""
        if RAPIDMETA_REPO_URL not in code_url:
            continue
        pages_url = e.get("pages_url") or ""
        if not pages_url.endswith(".html"):
            continue
        basename = pages_url.rsplit("/", 1)[-1]
        if not basename.endswith("_REVIEW.html"):
            continue
        candidates.setdefault(basename, []).append({
            "num": int(e["num"]),
            "title": e.get("title") or "",
        })

    mapping: dict[str, dict] = {}
    audit: list[dict] = []
    for basename, papers in candidates.items():
        if len(papers) == 1:
            mapping[basename] = papers[0]
            continue
        # Collision — score, pick highest, tie-break by lower num
        scored = sorted(
            papers,
            key=lambda p: (-_score_match(basename, p["title"]), p["num"]),
        )
        mapping[basename] = scored[0]
        audit.append({
            "basename": basename,
            "chosen": scored[0],
            "rejected": scored[1:],
            "scores": [(p["num"], _score_match(basename, p["title"])) for p in scored],
        })
    return mapping, audit


def write_audit_csv(mapping: dict[str, dict], landing_hrefs: set[str], audit_path: Path) -> None:
    """Write a CSV showing every landing-page review and what chip (if any)
    was chosen. Helps the user spot bad mappings + uncovered reviews."""
    import csv
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for href in sorted(landing_hrefs):
        if href in mapping:
            rec = mapping[href]
            rows.append([href, "MATCH", rec["num"], rec["title"]])
        else:
            rows.append([href, "UNCOVERED", "", ""])
    with audit_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["review_file", "status", "e156_paper_num", "e156_paper_title"])
        w.writerows(rows)


STYLE_BLOCK = """{begin}
<style>
.card-host {{ position: relative; display: block; }}
.claim-chip {{
  display: inline-block;
  font-family: system-ui,-apple-system,sans-serif;
  font-size: .58rem;
  font-weight: 700;
  letter-spacing: .06em;
  text-transform: uppercase;
  padding: .22rem .5rem;
  border-radius: 4px;
  background: #22c55e;
  color: #fff !important;
  text-decoration: none !important;
  border: 1px solid #16a34a;
  vertical-align: middle;
  white-space: nowrap;
  transition: opacity .15s, transform .15s;
  opacity: .92;
}}
.claim-chip:hover {{ opacity: 1; transform: translateY(-1px); text-decoration: none !important; box-shadow: 0 2px 6px rgba(34,197,94,.25); }}
.card-host {{ position: relative; display: block; }}
/* Give the chip its own space at the top-right of the card so it never
   overlaps long titles. ~108px = the chip width + 6px right margin + 6px left buffer. */
.card-host > .card {{ padding-right: 108px; }}
.card-host .claim-chip {{
  position: absolute;
  top: 6px;
  right: 6px;
  margin: 0;
  z-index: 5;
}}
.inline-claim-chip {{ margin-left: .4rem; }}
@media (max-width: 540px) {{
  .card-host > .card {{ padding-right: 1rem; }}
  .card-host .claim-chip {{
    position: static;
    display: block;
    margin: .4rem 0 0 0;
    width: max-content;
    font-size: .52rem;
    padding: .18rem .4rem;
  }}
}}
</style>
{end}""".format(begin=STYLE_BEGIN, end=STYLE_END)


SCRIPT_TEMPLATE = """__BEGIN__
<script>
(function () {
  var RAPIDMETA_TO_E156 = __JSON__;
  var E156_BASE = "__E156_BASE__";
  function buildClaimLink(num, title, klass) {
    var a = document.createElement("a");
    a.href = E156_BASE + "?focus=" + encodeURIComponent(num);
    a.target = "_blank";
    a.rel = "noopener";
    a.className = "claim-chip" + (klass ? " " + klass : "");
    a.textContent = "📋 Claim on E156";
    a.title = "Open the E156 student board, paper #" + num + (title ? " — " + title : "");
    a.addEventListener("click", function (e) { e.stopPropagation(); });
    return a;
  }
  function inject() {
    var anchors = document.querySelectorAll("a[href$='_REVIEW.html']");
    var injected = 0;
    anchors.forEach(function (a) {
      // Per-anchor idempotency flag — descendant search on parent is unsafe
      // because a single grid/td may contain many sibling anchors and the
      // first-card chip would falsely satisfy the check for all the others.
      if (a.dataset && a.dataset.e156ChipInjected === "1") return;
      var href = a.getAttribute("href") || "";
      var basename = href.split("/").pop();
      var rec = RAPIDMETA_TO_E156[basename];
      if (!rec) return;
      // Card style — wrap in .card-host so the absolute-positioned chip
      // can anchor without nesting <a> inside <a> (invalid HTML).
      if (a.classList && a.classList.contains("card")) {
        if (a.parentNode && a.parentNode.classList.contains("card-host")) {
          a.dataset.e156ChipInjected = "1";
          return;
        }
        var wrap = document.createElement("div");
        wrap.className = "card-host";
        a.parentNode.insertBefore(wrap, a);
        wrap.appendChild(a);
        wrap.appendChild(buildClaimLink(rec.num, rec.title));
        a.dataset.e156ChipInjected = "1";
        injected++;
        return;
      }
      // Inline / table cell — append the chip as a sibling of the <a>.
      var chip = buildClaimLink(rec.num, rec.title, "inline-claim-chip");
      a.insertAdjacentElement("afterend", chip);
      a.dataset.e156ChipInjected = "1";
      injected++;
    });
    return injected;
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inject);
  } else { inject(); }
  // Dashboard renders rows after a JSON fetch — re-run inject on DOM
  // mutations (throttled) so dynamically-added review links also get chips.
  let __scheduled = false;
  const __obs = new MutationObserver(() => {
    if (__scheduled) return;
    __scheduled = true;
    setTimeout(() => { __scheduled = false; inject(); }, 250);
  });
  if (document.body) __obs.observe(document.body, { childList: true, subtree: true });
  else document.addEventListener("DOMContentLoaded", () => __obs.observe(document.body, { childList: true, subtree: true }));
})();
</script>
__END__"""


def remove_block(html: str, begin: str, end: str) -> str:
    pat = re.compile(re.escape(begin) + r".*?" + re.escape(end), re.DOTALL)
    return pat.sub("", html)


def patch_index(index_html: str, mapping: dict[str, dict]) -> tuple[str, int]:
    json_map = json.dumps(mapping, ensure_ascii=False, indent=0).replace("\n", "")
    script_block = (SCRIPT_TEMPLATE
                    .replace("__JSON__", json_map)
                    .replace("__E156_BASE__", E156_BASE)
                    .replace("__BEGIN__", MARKER_BEGIN)
                    .replace("__END__", MARKER_END))
    # Remove any prior version, then insert fresh
    new_html = remove_block(index_html, STYLE_BEGIN, STYLE_END)
    new_html = remove_block(new_html, MARKER_BEGIN, MARKER_END)
    if "</head>" in new_html:
        new_html = new_html.replace("</head>", STYLE_BLOCK + "\n</head>", 1)
    if "</body>" in new_html:
        new_html = new_html.replace("</body>", script_block + "\n</body>", 1)
    return new_html, len(mapping)


def main() -> None:
    if not STUDENTS.exists():
        print("ERROR: students.html not found at", STUDENTS)
        sys.exit(1)
    if not INDEX.exists():
        print("ERROR: index.html not found at", INDEX)
        sys.exit(1)

    students_html = STUDENTS.read_text(encoding="utf-8", errors="replace")
    entries = parse_entries(students_html)
    mapping, audit = build_map(entries)
    print(f"Parsed {len(entries)} ENTRIES; built map with {len(mapping)} review files.")
    if audit:
        print(f"Resolved {len(audit)} collisions:")
        for a in audit:
            print(f"  {a['basename']}")
            print(f"    KEEP  #{a['chosen']['num']:3d}  {a['chosen']['title'][:70]}")
            for r in a["rejected"]:
                print(f"    drop  #{r['num']:3d}  {r['title'][:70]}")

    if not mapping:
        print("ERROR: no rapidmeta entries matched. Aborting.")
        sys.exit(2)

    # Audit CSV: every landing-page review + chip status
    landing_hrefs: set[str] = set()
    if INDEX.exists():
        idx_text = INDEX.read_text(encoding="utf-8", errors="replace")
        landing_hrefs |= set(re.findall(r'href="([A-Z0-9_]+_REVIEW\.html)"', idx_text))
    audit_csv = REPO / "outputs" / "e156_chip_audit.csv"
    write_audit_csv(mapping, landing_hrefs, audit_csv)
    uncovered = sum(1 for h in landing_hrefs if h not in mapping)
    print(f"Audit CSV: {audit_csv.relative_to(REPO)}  "
          f"({len(landing_hrefs)} reviews on landing, {uncovered} UNCOVERED)")

    for target in (INDEX, DASHBOARD, *EXTRA_LANDING_PAGES):
        if not target.exists():
            print(f"  skip (missing): {target.name}")
            continue
        text = target.read_text(encoding="utf-8", errors="replace")
        new_text, n = patch_index(text, mapping)
        if new_text == text:
            print(f"  no-op: {target.name}")
            continue
        target.write_text(new_text, encoding="utf-8")
        print(f"  patched: {target.name} ({n} mappings)")


if __name__ == "__main__":
    main()
