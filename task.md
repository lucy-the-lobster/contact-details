# Contact details parsing

- go through each of the files in this directory
- they all contain some contact information
- Create some JSON. Each contact needs to be like the example in test.json
- take extra care with the addresses - if you find a postcode, work back and see if the previous lines look like an address.

    - entryTitle - use the file name (without the html extension), but change it from Camel case to title case (joining words like "and" can start with lowercase)
    - title - the same as the entryTitle
    - addressLine01 - eg "Delamere House"
    - addressLine02 - eg "Delamere Street"
    - city - likely to be a town (Macclesfield or Crewe often)
    - county - don't include this if it is "Cheshire"
    - postcode
    - Email - there might be more than one, create an array. Each element is an object with fields label and email:
    email: [
    label: null,
    email: ''
    ]
    Make the label null 
    - website (if there is a query string, keep anything before "&pageTitle"
    - the "label" field should be null
    - example URL
    - https://digital-core.cheshireeast.gov.uk/w/webpage/request?form=contact_us&Service=DTC0001982GBFRF1&pageTitle=Household%20waste%20permit%20scheme&pagePath=https%3A%2F%2Fwww.cheshireeast.gov.uk%2Fwaste_and_recycling%2Fusing-household-waste-recycling-centres%2Fhousehold-waste-permit-scheme.aspx

    - "text" field other information - anything else. If in doubt put it here. All the information must be saved - do not include the <feff> character
    - telephone - an array of objects. Make the label field null


- you can ignore any schema structured data, html attributes, classes etc

save an array of json objects in a json file


