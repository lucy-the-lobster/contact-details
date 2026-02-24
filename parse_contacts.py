#!/usr/bin/env python3
import os
import json
import re
from pathlib import Path

def camel_to_title(name):
    """Convert CamelCase to Title Case"""
    s1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1 \2', name)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', s1).title()

def extract_address_parts(text):
    """Extract address components from text"""
    # Postcode pattern
    postcode_pattern = r'\b([Gg][Ii][Rr] 0[Aa]{2})|((([A-Za-z][0-9]{1,2})|(([A-Za-z][A-Ha-hJ-Yj-y][0-9]{1,2})|(([A-Za-z][0-9][A-Za-z])|([A-Za-z][A-Ha-hJ-Yj-y][0-9]?[A-Za-z]))))\s?[0-9][A-Za-z]{2})\b'
    
    # Street pattern (contains street/road/court/avenue etc)
    street_pattern = r'\b(?:Street|Road|Way|Close|Avenue|Drive|Crescent|Court|Terrace|Place|Lane|Gardens|Square|Park|Hill|Walk)\b'
    
    # Building pattern (contains House/Building/Centre etc)
    building_pattern = r'\b(?:House|Building|Centre|Office|Suite|Floor|Level)\b'
    
    # Common town names
    common_towns = [r'\bMacclesfield\b', r'\bCrewe\b', r'\bCheshire\b']
    
    postcode = None
    street = None
    building = None
    city = None
    county = None
    
    # Find postcode first
    postcode_match = re.search(postcode_pattern, text)
    if postcode_match:
        postcode = postcode_match.group(0)
        text = text.replace(postcode, '').strip()
    
    # Find street
    street_match = re.search(street_pattern, text)
    if street_match:
        # Extract the street line
        parts = text.split(street_match.group(0))
        if len(parts) > 1:
            street = f"{parts[0].strip()} {street_match.group(0)}".strip()
            text = text.replace(street, '').strip()
    
    # Find building
    building_match = re.search(building_pattern, text)
    if building_match:
        building = f"{text.split(building_match.group(0))[0].strip()} {building_match.group(0)}".strip()
        text = text.replace(building, '').strip()
    
    # Find city (Macclesfield or Crewe)
    for town_pattern in common_towns:
        town_match = re.search(town_pattern, text)
        if town_match:
            city = town_match.group(0)
            text = text.replace(city, '').strip()
            # If Cheshire is found, set county to None
            if 'Cheshire' in text:
                county = None
                text = text.replace('Cheshire', '').strip()
            break
    
    return {
        'postcode': postcode,
        'street': street,
        'building': building,
        'city': city,
        'county': county,
        'remaining': text
    }

def parse_html_file(filepath):
    """Parse a single HTML file for contact information"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract text content (strip HTML tags)
    text_content = re.sub(r'<[^>]+>', ' ', content)
    text_content = re.sub(r'\s+', ' ', text_content).strip()
    
    # Extract address components
    address_parts = extract_address_parts(text_content)
    
    # Basic structure
    filename = Path(filepath).stem
    entry_title = camel_to_title(filename)
    title = entry_title
    
    address_line01 = address_parts['building']
    address_line02 = address_parts['street']
    city = address_parts['city']
    county = address_parts['county']
    postcode = address_parts['postcode']
    
    # Extract emails
    email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'
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