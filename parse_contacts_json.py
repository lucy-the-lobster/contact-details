#!/usr/bin/env python3
"""
Parse contact details from HTML files and output as JSON.
Extracts: Title, Address lines, Postcode, Email, URLs, Telephone, Other info
"""

import os
import re
import json
from pathlib import Path
from urllib.parse import urlparse

def extract_contact_details(html_content, filename):
    """Extract contact details from HTML content."""
    details = {
        "entryTitle": filename,  # filename without .html
        "title": None,
        "address": [{
            "title": None,
            "addressLine01": None,
            "addressLine02": None,
            "city": None,
            "county": None,
            "postcode": None,
            "country": None
        }],
        "email": [],
        "telephone": [],
        "website": [],
        "entryDescription": None,
        "text": None,
        "socialLinks": [],
        "entryTags": [],
        "entryThumbnail": None,
        "other": extract_plain_text(html_content)
    }
    
    # Extract emails - can be multiple
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, html_content)
    for email in emails:
        details["email"].append({
            "label": email,
            "email": email
        })
    
    # Parse telephone numbers - can be multiple
    phone_pattern = r'\b(?:01\d{3,4}|02\d{3,4}|\+44)\s?[\d\s()+-]*\d[\d\s()+-]*\b'
    phones = re.findall(phone_pattern, html_content)
    for phone in phones:
        phone_clean = phone.strip()
        details["telephone"].append({
            "label": phone_clean,
            "telephone": phone_clean,
            "extension": None
        })
    
    # Parse postcodes (UK format)
    postcode_pattern = r'\b[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}\b'
    postcodes = re.findall(postcode_pattern, html_content)
    if postcodes:
        details["address"][0]["postcode"] = postcodes[0].strip()
    
    # Parse URLs from href attributes
    url_pattern = r'href=["\']([^"\']+)["\']'
    url_matches = re.findall(url_pattern, html_content)
    seen_urls = set()
    for url in url_matches:
        if not url.startswith('mailto:'):
            # Remove query strings
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}" if parsed.scheme else url
            base_url = base_url.rstrip('/')
            if base_url and base_url not in seen_urls:
                seen_urls.add(base_url)
                details["website"].append({
                    "label": None,
                    "link": {
                        "id": "",
                        "title": base_url,
                        "uri": base_url
                    }
                })
    
    # Extract address information
    # Look for streetAddress spans
    street_addr_pattern = r'<span[^>]*itemprop=["\']streetAddress["\'][^>]*>(.*?)</span>'
    street_matches = re.findall(street_addr_pattern, html_content, re.DOTALL)
    address_lines = []
    for match in street_matches:
        # Remove nested tags and handle <br>
        text = re.sub(r'<br\s*/?>', '\n', match)
        text = re.sub(r'<[^>]+>', '', text)
        for part in text.split('\n'):
            part = part.strip()
            if part and part not in address_lines:
                address_lines.append(part)
    
    # Look for addressLocality (city)
    locality_pattern = r'<span[^>]*itemprop=["\']addressLocality["\'][^>]*>(.*?)</span>'
    locality_matches = re.findall(locality_pattern, html_content)
    city = None
    if locality_matches:
        city = re.sub(r'<[^>]+>', '', locality_matches[0]).strip()
    
    # Look for addressRegion (county)
    region_pattern = r'<span[^>]*itemprop=["\']addressRegion["\'][^>]*>(.*?)</span>'
    region_matches = re.findall(region_pattern, html_content)
    county = None
    if region_matches:
        county = re.sub(r'<[^>]+>', '', region_matches[0]).strip()
        # Don't include county if it's "Cheshire"
        if county.lower() == "cheshire":
            county = None
    
    # Populate address fields
    if address_lines:
        details["address"][0]["title"] = address_lines[0]
        details["address"][0]["addressLine01"] = address_lines[0] if address_lines else None
        details["address"][0]["addressLine02"] = address_lines[1] if len(address_lines) > 1 else None
    
    if city:
        details["address"][0]["city"] = city
    if county:
        details["address"][0]["county"] = county
    
    # Set title from first line if available
    if address_lines:
        details["title"] = address_lines[0]
    
    return details

def extract_plain_text(html_content):
    """Extract plain text from HTML, removing all tags and extra whitespace."""
    # Remove script tags
    text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Replace multiple whitespace with single space
    text = re.sub(r'\s+', ' ', text)
    # Strip leading/trailing whitespace
    text = text.strip()
    return text if text else None

def parse_html_file(filepath, filename):
    """Parse a single HTML file and extract contact details."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        return extract_contact_details(html_content, filename)
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return None

def process_all_files(directory):
    """Process all HTML files in the directory."""
    results = []
    html_files = sorted(Path(directory).glob('*.html'))
    
    for html_file in html_files:
        if html_file.name in ['.gitignore', 'test.html']:
            continue
        
        filename = html_file.stem
        contacts = parse_html_file(html_file, filename)
        
        if contacts:
            results.append(contacts)
    
    return results

def save_json(results, output_file):
    """Save results to JSON file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved {len(results)} records to {output_file}")

if __name__ == '__main__':
    directory = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(directory, 'contact_details.json')
    
    print(f"Processing HTML files from {directory}...")
    results = process_all_files(directory)
    save_json(results, output_file)
