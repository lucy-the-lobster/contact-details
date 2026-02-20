#!/usr/bin/env python3
"""
Parse contact details from HTML files and output as CSV.
Extracts: Title, Address lines, Postcode, Email, URLs, Telephone, Other info
"""

import os
import re
import csv
from pathlib import Path
from urllib.parse import urlparse

def extract_contact_details(html_content):
    """Extract contact details from HTML content."""
    details = {
        'email': '',
        'telephone': '',
        'address_lines': [],
        'postcode': '',
        'urls': set(),
        'other': []
    }
    
    # Parse emails
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, html_content)
    if emails:
        details['email'] = emails[0]
    
    # Parse telephone numbers
    phone_pattern = r'\b(?:01\d{3,4}|02\d{3,4}|\+44)\s?[\d\s()+-]{8,}\b'
    phones = re.findall(phone_pattern, html_content)
    if phones:
        details['telephone'] = phones[0].strip()
    
    # Parse postcodes (UK format)
    postcode_pattern = r'\b[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}\b'
    postcodes = re.findall(postcode_pattern, html_content)
    if postcodes:
        details['postcode'] = postcodes[0].strip()
    
    # Parse URLs from href attributes
    url_pattern = r'href=["\']([^"\']+)["\']'
    url_matches = re.findall(url_pattern, html_content)
    for url in url_matches:
        if not url.startswith('mailto:'):
            # Remove query strings
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}" if parsed.scheme else url
            base_url = base_url.rstrip('/')
            if base_url:
                details['urls'].add(base_url)
    
    # Extract address information
    # Look for streetAddress spans (can appear on multiple lines)
    street_addr_pattern = r'<span[^>]*itemprop=["\']streetAddress["\'][^>]*>(.*?)</span>'
    street_matches = re.findall(street_addr_pattern, html_content, re.DOTALL)
    for match in street_matches:
        # Remove nested tags and split by <br>
        text = re.sub(r'<[^>]+>', '', match)
        # Split on <br> or newlines
        text = re.sub(r'<br\s*/?>', '\n', text)
        for part in text.split('\n'):
            part = part.strip()
            if part and part not in details['address_lines']:
                details['address_lines'].append(part)
    
    # Look for addressLocality
    locality_pattern = r'<span[^>]*itemprop=["\']addressLocality["\'][^>]*>(.*?)</span>'
    locality_matches = re.findall(locality_pattern, html_content)
    for match in locality_matches:
        text = re.sub(r'<[^>]+>', '', match).strip()
        if text and text not in details['address_lines']:
            details['address_lines'].append(text)
    
    # Look for addressRegion
    region_pattern = r'<span[^>]*itemprop=["\']addressRegion["\'][^>]*>(.*?)</span>'
    region_matches = re.findall(region_pattern, html_content)
    for match in region_matches:
        text = re.sub(r'<[^>]+>', '', match).strip()
        if text and text not in details['address_lines']:
            details['address_lines'].append(text)
    
    # Extract other useful information (department/service names, etc.)
    text_content = html_content
    # Remove script tags
    text_content = re.sub(r'<script[^>]*>.*?</script>', '', text_content, flags=re.DOTALL)
    # Remove HTML tags
    text_content = re.sub(r'<[^>]+>', '', text_content)
    # Remove extra whitespace
    text_content = re.sub(r'\s+', ' ', text_content)
    
    # Extract proper nouns and service names
    other_terms = set()
    # Look for sequences of capitalized words (potential service names)
    for match in re.finditer(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', text_content):
        word = match.group(1)
        # Filter out common words
        if word not in ['Address', 'Service', 'Management', 'Email', 'Phone', 'Cheshire', 'East', 'Council', 'Contact', 'Team', 'Division']:
            other_terms.add(word)
    
    if other_terms:
        details['other'] = sorted(list(other_terms))[:3]
    
    return details

def parse_html_file(filepath):
    """Parse a single HTML file and extract contact details."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        return extract_contact_details(html_content)
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
        
        title = html_file.stem
        contacts = parse_html_file(html_file)
        
        if contacts:
            # Pad address lines to 3
            addr_lines = contacts['address_lines']
            while len(addr_lines) < 3:
                addr_lines.append('')
            
            result = {
                'Title': title,
                'Address Line 1': addr_lines[0] if len(addr_lines) > 0 else '',
                'Address Line 2': addr_lines[1] if len(addr_lines) > 1 else '',
                'Address Line 3': addr_lines[2] if len(addr_lines) > 2 else '',
                'Postcode': contacts['postcode'],
                'Email': contacts['email'],
                'URLs': ', '.join(sorted(contacts['urls'])) if contacts['urls'] else '',
                'Telephone': contacts['telephone'],
                'Other Information': '; '.join(contacts['other']) if contacts['other'] else ''
            }
            results.append(result)
    
    return results

def save_csv(results, output_file):
    """Save results to CSV file."""
    fieldnames = [
        'Title',
        'Address Line 1',
        'Address Line 2',
        'Address Line 3',
        'Postcode',
        'Email',
        'URLs',
        'Telephone',
        'Other Information'
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"✓ Saved {len(results)} records to {output_file}")

if __name__ == '__main__':
    directory = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(directory, 'contact_details.csv')
    
    print(f"Processing HTML files from {directory}...")
    results = process_all_files(directory)
    save_csv(results, output_file)
