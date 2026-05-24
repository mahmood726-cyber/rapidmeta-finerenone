// Extract `realData: { ... }` from every *_FULL_REVIEW.html and parse-eval it
// to verify no Python-isms / typos slipped through.
const fs = require("fs");
const path = require("path");

const dir = process.argv[2] || ".";
const files = fs
  .readdirSync(dir)
  .filter((n) => n.endsWith("_FULL_REVIEW.html"));

let ok = 0,
  bad = 0;
const failures = [];

for (const fn of files) {
  const txt = fs.readFileSync(path.join(dir, fn), "utf8");
  const start = txt.indexOf("realData:");
  if (start === -1) continue;
  const open = txt.indexOf("{", start);
  let depth = 0,
    end = -1;
  for (let i = open; i < txt.length; i++) {
    if (txt[i] === "{") depth++;
    else if (txt[i] === "}") {
      depth--;
      if (depth === 0) {
        end = i;
        break;
      }
    }
  }
  if (end === -1) {
    bad++;
    failures.push([fn, "could not locate realData block"]);
    continue;
  }
  const block = txt.slice(open, end + 1);
  try {
    // Wrap as expression so the literal is evaluated, not declared.
    new Function("return (" + block + ")")();
    ok++;
  } catch (e) {
    bad++;
    failures.push([fn, e.message]);
  }
}

console.log(`OK: ${ok}, BAD: ${bad}`);
for (const [fn, msg] of failures.slice(0, 20)) {
  console.log(`  - ${fn}: ${msg}`);
}
process.exit(bad === 0 ? 0 : 1);
