// build-css.js — compiles src/input.css -> dist/output.css using the
// already-installed @tailwindcss/postcss + postcss packages.
//
// WHY THIS EXISTS: package.json only lists @tailwindcss/postcss (the
// PostCSS plugin), not @tailwindcss/cli (the standalone CLI) or
// postcss-cli. There's no `npm run build` script either. Rather than add
// new dependencies mid-hackathon, this drives the plugin programmatically
// with what's already installed. Tailwind v4 auto-detects template files
// (sidepanel.html, sidepanel.js) from the project root — no content[]
// array needed, unlike v3.
//
// Run: node build-css.js
// Re-run this any time you add new Tailwind/daisyUI classes to sidepanel.html
// or sidepanel.js — dist/output.css is a build artifact, not hand-edited.

const fs = require("fs");
const path = require("path");
const postcss = require("postcss");
const tailwindcss = require("@tailwindcss/postcss");

const inputPath = path.join(__dirname, "src", "input.css");
const outputPath = path.join(__dirname, "dist", "output.css");

const css = fs.readFileSync(inputPath, "utf8");

postcss([tailwindcss()])
  .process(css, { from: inputPath, to: outputPath })
  .then((result) => {
    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
    fs.writeFileSync(outputPath, result.css);
    if (result.map) fs.writeFileSync(outputPath + ".map", result.map.toString());
    console.log(`Built ${outputPath} (${(result.css.length / 1024).toFixed(1)} KB)`);
  })
  .catch((err) => {
    console.error("Tailwind build failed:", err);
    process.exit(1);
  });
