import fs from 'fs';
import path from 'path';

// Read the allEntries.js file
const filePath = path.resolve('allEntries.js');
const fileContent = fs.readFileSync(filePath, 'utf-8');

// Extract the array by evaluating it
// We need to strip 'export const allEntries = ' and evaluate the rest
const arrayStr = fileContent.replace(/^export const allEntries\s*=\s*/, '');

// Use Function constructor to evaluate (safe here since it's our own file)
const allEntries = new Function(`return ${arrayStr}`)();

console.log(`Total entries: ${allEntries.length}`);

// Find entries with website URLs that have null labels
const entriesWithNullWebsiteLabels = [];
for (const entry of allEntries) {
  if (entry.website && entry.website.length > 0) {
    for (const w of entry.website) {
      if (w.label === null) {
        entriesWithNullWebsiteLabels.push({
          title: entry.title,
          slug: entry.sys?.slug,
          websiteUrl: w.website,
          label: w.label
        });
      }
    }
  }
}

console.log(`\nEntries with website URLs having null labels: ${entriesWithNullWebsiteLabels.length}`);
for (const e of entriesWithNullWebsiteLabels) {
  console.log(`  - ${e.title} (slug: ${e.slug})`);
  console.log(`    URL: ${e.websiteUrl}`);
}

// Now read HTML files and find the link text for each
const htmlDir = '.';
const htmlFiles = fs.readdirSync(htmlDir).filter(f => f.endsWith('.html'));

console.log(`\n--- Looking up labels from HTML files ---\n`);

// Build a map of slug -> possible HTML filenames
// The slug pattern is like 'contact-benefits-section' and HTML is like 'BenefitsSection.html'
// We'll search all HTML files for the matching URL

const fixes = [];

for (const entry of allEntries) {
  if (!entry.website || entry.website.length === 0) continue;
  
  for (let i = 0; i < entry.website.length; i++) {
    const w = entry.website[i];
    if (w.label !== null) continue; // already has a label
    
    const url = w.website;
    if (!url) continue;
    
    // Search all HTML files for this URL
    let foundLabel = null;
    let foundFile = null;
    
    for (const htmlFile of htmlFiles) {
      const htmlContent = fs.readFileSync(path.join(htmlDir, htmlFile), 'utf-8');
      
      // Look for <a> tags containing this URL (not mailto: links)
      // Match: <a ... href="URL" ...>LINK TEXT</a>
      const escapedUrl = url.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const regex = new RegExp(`<a[^>]*href=["']${escapedUrl}[^"']*["'][^>]*>([\\s\\S]*?)<\\/a>`, 'gi');
      
      let match;
      while ((match = regex.exec(htmlContent)) !== null) {
        // Extract text content (strip inner HTML tags)
        let linkText = match[1].replace(/<[^>]*>/g, '').trim();
        // Clean up whitespace
        linkText = linkText.replace(/\s+/g, ' ').trim();
        
        if (linkText) {
          foundLabel = linkText;
          foundFile = htmlFile;
          break;
        }
      }
      
      if (foundLabel) break;
    }
    
    if (foundLabel) {
      console.log(`✅ ${entry.title}`);
      console.log(`   URL: ${url}`);
      console.log(`   Label from ${foundFile}: "${foundLabel}"`);
      fixes.push({
        entryTitle: entry.title,
        websiteIndex: i,
        url: url,
        newLabel: foundLabel,
        htmlFile: foundFile
      });
    } else {
      console.log(`❌ ${entry.title}`);
      console.log(`   URL: ${url}`);
      console.log(`   No matching label found in HTML files`);
    }
  }
}

console.log(`\n--- Summary ---`);
console.log(`Total fixes to apply: ${fixes.length}`);

// Now apply the fixes to the file content
let updatedContent = fileContent;

for (const fix of fixes) {
  // We need to find the specific website entry in the JS and replace label: null
  // Strategy: find the URL in context and replace the nearby label: null
  
  // Find pattern: { label: null, website: 'THE_URL' } or similar  
  const escapedUrl = fix.url.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  
  // Match the object pattern with label: null followed by website: 'url'
  // The pattern in the file looks like:
  //   { label: null, website: 'https://...' }
  // or split across lines:
  //   {
  //     label: null,
  //     website:
  //       'https://...',
  //   }
  
  // Try multi-line pattern first
  const multiLinePattern = new RegExp(
    `(\\{\\s*\\n\\s*label:\\s*)null(,\\s*\\n\\s*website:\\s*\\n\\s*'${escapedUrl}')`,
    'g'
  );
  
  const singleLinePattern = new RegExp(
    `(\\{\\s*label:\\s*)null(,\\s*website:\\s*'${escapedUrl}'\\s*\\})`,
    'g'
  );
  
  const escapedLabel = fix.newLabel.replace(/'/g, "\\'");
  
  let replaced = false;
  const before = updatedContent;
  
  updatedContent = updatedContent.replace(multiLinePattern, `$1'${escapedLabel}'$2`);
  if (updatedContent !== before) {
    replaced = true;
    console.log(`Applied (multi-line): ${fix.entryTitle} -> "${fix.newLabel}"`);
  }
  
  if (!replaced) {
    const before2 = updatedContent;
    updatedContent = updatedContent.replace(singleLinePattern, `$1'${escapedLabel}'$2`);
    if (updatedContent !== before2) {
      replaced = true;
      console.log(`Applied (single-line): ${fix.entryTitle} -> "${fix.newLabel}"`);
    }
  }
  
  if (!replaced) {
    console.log(`⚠️  Could not apply fix for: ${fix.entryTitle} (${fix.url})`);
  }
}

// Write the updated content
fs.writeFileSync(filePath, updatedContent, 'utf-8');
console.log(`\n✅ Updated allEntries.js`);
