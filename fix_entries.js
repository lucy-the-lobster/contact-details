#!/usr/bin/env node
/**
 * fix_entries.js
 * Scans HTML files, extracts anchor URLs + labels,
 * and syncs them into allEntries.js website arrays.
 */

const fs = require('fs');
const path = require('path');

const DIR = __dirname;
const ENTRIES_FILE = path.join(DIR, 'allEntries.js');

// ── 1. Read & parse allEntries.js ────────────────────────────────────
let raw = fs.readFileSync(ENTRIES_FILE, 'utf8');
// Strip the "export const allEntries = " prefix and trailing semicolon
let jsonStr = raw
  .replace(/^export\s+const\s+allEntries\s*=\s*/, '')
  .replace(/;\s*$/, '');

let entries;
try {
  entries = eval('(' + jsonStr + ')');  // safe here – we own the file
} catch (e) {
  console.error('Failed to parse allEntries.js:', e.message);
  process.exit(1);
}

// ── 2. Build a lookup: slug → entry index ────────────────────────────
const slugIndex = {};
entries.forEach((entry, i) => {
  if (entry.sys && entry.sys.slug) {
    slugIndex[entry.sys.slug] = i;
  }
});

// Also build title-based lookup (lowercase, trimmed)
const titleIndex = {};
entries.forEach((entry, i) => {
  if (entry.title) {
    titleIndex[entry.title.toLowerCase().trim()] = i;
  }
});

// ── 3. Scan HTML files ───────────────────────────────────────────────
const htmlFiles = fs.readdirSync(DIR).filter(f => f.endsWith('.html') && f !== 'test.html');

// Simple regex to extract <a href="URL">LABEL</a> (non-mailto)
const anchorRegex = /<a\b[^>]*href\s*=\s*["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi;
const tagStripper = /<[^>]+>/g;

let totalAdded = 0;
let totalLabelFixed = 0;
let unmatchedFiles = [];

for (const htmlFile of htmlFiles) {
  const htmlPath = path.join(DIR, htmlFile);
  const html = fs.readFileSync(htmlPath, 'utf8');

  // Extract all non-mailto anchor links
  const links = [];
  let match;
  while ((match = anchorRegex.exec(html)) !== null) {
    const url = match[1].trim();
    const rawLabel = match[2].replace(tagStripper, '').trim();
    // Skip mailto: links and empty URLs
    if (url.startsWith('mailto:') || !url) continue;
    // Skip anchors that are just "#"
    if (url === '#') continue;
    links.push({ url, label: rawLabel || null });
  }

  if (links.length === 0) continue;

  // ── 4. Match HTML file to an entry ──────────────────────────────
  // Try multiple matching strategies
  const baseName = path.basename(htmlFile, '.html');

  // Strategy 1: Convert filename to slug format and look up
  // e.g. "BenefitsSection" → "contact-benefits-section"
  const slugFromFile = 'contact-' + baseName
    .replace(/([a-z])([A-Z])/g, '$1-$2')   // camelCase → kebab
    .replace(/\s+/g, '-')                   // spaces → hyphens
    .toLowerCase();

  // Strategy 2: Try with hyphens already in filename
  const slugFromFileAlt = 'contact-' + baseName.toLowerCase();

  let entryIdx = slugIndex[slugFromFile];
  if (entryIdx === undefined) entryIdx = slugIndex[slugFromFileAlt];
  if (entryIdx === undefined) entryIdx = slugIndex[baseName.toLowerCase()];

  // Strategy 3: Try matching by title keywords
  if (entryIdx === undefined) {
    // Build search terms from filename
    const searchTerms = baseName
      .replace(/([a-z])([A-Z])/g, '$1 $2')
      .replace(/-/g, ' ')
      .toLowerCase()
      .trim();

    for (const [title, idx] of Object.entries(titleIndex)) {
      // Check if the title (minus "contact ") contains the search terms
      const titleClean = title.replace(/^contact\s+/, '');
      if (titleClean === searchTerms || title.includes(searchTerms)) {
        entryIdx = idx;
        break;
      }
    }
  }

  if (entryIdx === undefined) {
    unmatchedFiles.push(htmlFile);
    continue;
  }

  const entry = entries[entryIdx];

  // ── 5. Sync website URLs ────────────────────────────────────────
  for (const link of links) {
    const existingIdx = entry.website.findIndex(
      w => w.website === link.url
    );

    if (existingIdx === -1) {
      // URL missing – add it
      entry.website.push({ label: link.label, website: link.url });
      totalAdded++;
      console.log(`  ADD  [${entry.title}] → ${link.label || '(no label)'} | ${link.url}`);
    } else {
      // URL exists – fix label if null/empty and we have one
      const existing = entry.website[existingIdx];
      if ((existing.label === null || existing.label === '') && link.label) {
        existing.label = link.label;
        totalLabelFixed++;
        console.log(`  FIX  [${entry.title}] label → "${link.label}" for ${link.url}`);
      }
    }
  }
}

// ── 6. Write updated allEntries.js ───────────────────────────────────
// We need to serialize back to the original format
function serializeEntries(entries) {
  // Use JSON.stringify with indentation, then convert to JS object literal style
  let json = JSON.stringify(entries, null, 2);

  // Convert JSON keys to unquoted JS keys where safe
  json = json.replace(/"(\w+)":/g, '$1:');

  // Fix string values that got double-escaped
  // Re-wrap the output
  return `export const allEntries = ${json};\n`;
}

const output = serializeEntries(entries);
fs.writeFileSync(ENTRIES_FILE, output, 'utf8');

// ── 7. Report ────────────────────────────────────────────────────────
console.log('\n=== Summary ===');
console.log(`HTML files scanned:  ${htmlFiles.length}`);
console.log(`URLs added:          ${totalAdded}`);
console.log(`Labels fixed:        ${totalLabelFixed}`);
console.log(`Unmatched HTML files: ${unmatchedFiles.length}`);
if (unmatchedFiles.length > 0) {
  console.log('  Unmatched:', unmatchedFiles.join(', '));
}
console.log('allEntries.js updated ✅');
