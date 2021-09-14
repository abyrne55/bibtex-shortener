from bibtexparser import dumps as bibdumps
from bibtexparser.bparser import BibTexParser
from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.customization import author
import urllib.request
import json 
import sys
import logging


def load_bib_file(file_path):
  parser = BibTexParser(common_strings=True)
  with open(file_path) as f:
    bibliography = parser.parse_file(f)
  return bibliography

def et_al_ify(bib_entry, max_authors=2):
  """
  Truncate an entry to its first author "and others" if it has more than max_authors
  authors. Entries with an author count <= max_authors will be returned mostly 
  untouched (author list will just be standardized into "Last, First and..." format)
  
  @returns the et-al-ified bib entry with author key in string format
  """
  author_list = author(bib_entry)['author']
  if len(author_list) > max_authors:
    author_string = author_list[0] + " and others"
  else:
    author_string = " and ".join(author_list)
  
  bib_entry['author'] = author_string
  return bib_entry

def remove_uuids(bib_entry):
  """
  Removes the following fields: doi, eprint, archiveprefix, isbn
  
  @returns the filtered bib_entry
  """
  for field in ['doi', 'eprint', 'archiveprefix', 'isbn', 'issn', 'arxivid', 'arxivId']:
    bib_entry.pop(field, None)
  
  return bib_entry

def doi_to_short_url(bib_entry):
  """
  If an entry has a DOI, convert it into its corresponding https://doi.org/wxyz URL
  using the official shortDOI service (an API offered by the International DOI
  Foundation).
  
  @returns the bib entry with its url field populated
  @raises KeyError if the provided entry doesn't have a doi field
  """
  api_url = "http://shortdoi.org/{}?format=json".format(bib_entry['doi'])
  shortdoi_api_response = json.loads(urllib.request.urlopen(api_url).read())
  shortdoi_url = "https://doi.org/" + shortdoi_api_response['ShortDOI'].split('/')[-1]
  bib_entry['url'] = shortdoi_url
  return bib_entry

def arxiv_to_url(bib_entry):
  """
  If an entry has an arXiv or eprint ID, populate its url filed with a
  https://arxiv.org/abs/1234.56789 URL
  
  @returns the bib entry with its url field populated
  @raises KeyError if the provided entry doesn't have an arXiv-related field
  """
  try:
    arxiv_id = bib_entry['arxivId']
  except KeyError:
    try:
      arxiv_id = bib_entry['arxivid']
    except KeyError:
      arxiv_id = bib_entry['eprint']
  
  bib_entry['url'] = "https://arxiv.org/abs/" + arxiv_id
  return bib_entry


if __name__ == "__main__":
  bib = load_bib_file(sys.argv[1])
  
  cleaned_bib = BibDatabase()
  for bib_entry in bib.entries:
    try:
      bib_entry = doi_to_short_url(bib_entry)
      no_std_url = False
    except KeyError:
      try:
        bib_entry = arxiv_to_url(bib_entry)
        no_std_url = False
      except KeyError:
        no_std_url = True
      
    if no_std_url and 'url' not in bib_entry:
      logging.warning("%s has no URL", bib_entry['ID'])
    else:
      remove_uuids(bib_entry)
      
    try:
      bib_entry = et_al_ify(bib_entry, max_authors=3)
    except KeyError:
      logging.error("%s has no author!", bib_entry['ID'])
    
    cleaned_bib.entries.append(bib_entry)
    
  print(bibdumps(cleaned_bib))
  
  
  
  
  
  
  
  