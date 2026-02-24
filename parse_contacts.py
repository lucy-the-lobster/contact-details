#!/usr/bin/env python3
import os
import json
import re
from pathlib import Path

def camel_to_title(name):
    """Convert CamelCase to Title Case"""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1 \2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1 \2', s1).title()

def extract_address(lines):
    """Extract address from lines, working backwards from postcode"""
    postcode_pattern = r'\b([Gg][Ii][Rr] 0[Aa]{2})|((([A-Za-z][0-9]{1,2})|(([A-Za-z][A-Ha-hJ-Yj-y][0-9]{1,2})|(([A-Za-z][0-9][A-Za-z])|([A-Za-z][A-Ha-hJ-Yj-y][0-9]?[A-Za-z]))))\s?[0-9][A-Za-z]{2})\b'
    
    postcode = None
    address_lines = []
    
    for i, line in enumerate(reversed(lines)):
        if re.search(postcode_pattern, line):
            postcode = line.strip()
            # Look backwards for address lines
            for j in range(len(lines) - i - 1, -1, -1):
                line_text = lines[j].strip()
                if line_text and not re.match(postcode_pattern, line_text):
                    address_lines.insert(0, line_text)
            break
    
    return address_lines, postcode

def parse_html_file(filepath):
    """Parse a single HTML file for contact information"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract text content (strip HTML tags)
    text_content = re.sub(r'<[^>]+>', ' ', content)
    text_content = re.sub(r'\s+', ' ', text_content).strip()
    
    # Split into lines for address extraction
    lines = text_content.split('\n')
    
    # Extract address
    address_lines, postcode = extract_address(lines)
    
    # Basic structure
    filename = Path(filepath).stem
    entry_title = camel_to_title(filename)
    title = entry_title
    
    address_line01 = address_lines[0] if len(address_lines) > 0 else None
    address_line02 = address_lines[1] if len(address_lines) > 1 else None
    
    # Try to extract city (look for common town names)
    city = None
    county = None
    common_towns = ['Macclesfield', 'Crewe', 'Cheshire']
    for line in address_lines:
        if any(town in line for town in common_towns):
            city = line.strip()
            if 'Cheshire' in line:
                county = None  # Don't include Cheshire as county
            break
    
    # Extract emails
    email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    emails = re.findall(email_pattern, content)
    email_list = [{'label': None, 'email': email} for email in emails]
    
    # Extract telephone numbers
    phone_pattern = r'\b(?:0\d{10}|\+44\d{10}|\(0\d{2}\)\s*\d{3}\s*\d{4}|0\d{4}\s*\d{3}\s*\d{3})\b'
    phones = re.findall(phone_pattern, content)
    phone_list = [{'label': None, 'telephone': phone} for phone in phones]
    
    # Extract website (keep before &pageTitle)
    website_pattern = r'https?://[^\s"\']+(?=&pageTitle|&|$)'
    website = re.search(website_pattern, content)
    website_url = website.group(0) if website else None
    website_list = [{'label': None, 'website': website_url}] if website_url else []
    
    # Create JSON structure
    contact = {
        "entryThumbnail": None,
        "socialLinks": [],
        "website": website_list,
        "address": [{
            "country": None,
            "city": city,
            "county": county,
            "postcode": postcode,
            "addressLine02": address_line02,
            "addressLine01": address_line01,
            "title": title
        }],
        "entryTags": [],
        "entryDescription": None,
        "telephone": phone_list,
        "title": title,
        "text": text_content,
        "entryTitle": entry_title,
        "email": email_list
    }
    
    return contact

def main():
    """Main function to parse all HTML files"""
    html_dir = Path(".")
    html_files = sorted(html_dir.glob("*.html"))
    
    print(f"Processing {len(html_files)} HTML files...")
    
    contacts = []
    for html_file in html_files:
        try:
            contact = parse_html_file(html_file)
            contacts.append(contact)
            print(f"✓ Processed {html_file.name}")
        except Exception as e:
            print(f"✗ Error processing {html_file.name}: {e}")
    
    # Save to JSON
    output_file = "contact_details.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(contacts, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Saved {len(contacts)} records to {output_file}")

if __name__ == "__main__":
    main()