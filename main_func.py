# -*- coding: utf-8 -*-
"""
Created on Tue Nov  3 08:49:47 2020

@author: Shubham
"""
import os

#import sys
#sys.path.extend(os.path.dirname(os.path.realpath()))

import json

import re

#!pip install spacy
import spacy
#!pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-2.3.1/en_core_web_sm-2.3.1.tar.gz
import spacy
from spacy import displacy
from collections import Counter
import en_core_web_sm

import nltk

from collections import defaultdict

import pandas as pd

import time

from utils import data_prep
from utils.data_prep import pdf_to_text

def extract_small_blocks(s, block_sep = '\n', min_len = 2, max_len = 100):
    '''
    Input parameters
    ------
    s: A string object
    block_sep: How to split string into blocks, separator
    min_len: Minimum length of string in any block. 'ab' as length = 2
    max_len: Minimum length of string in any block. 'abc' has length = 3
    
    Output returns
    ------
    s_blocks: String blocks. A list
    '''
    
    # Block separator is double line-break for now
    
    for i in range(1,6):
        to_replace = '\n'+' '*i + '\n'
        s = s.replace(to_replace,'\n\n')
        
    # Replace some known characters
    s = s.replace(u'\xa0', u' ')
    
    # Remove punctuations
    s = re.sub(r"[,;#?!&$]+\ *", " ", s)
    
    s_split_1 = re.split(block_sep,s)
    
    s_split_2 = re.split('\n\n',s)
    
    #s_small = [i for i in s_split if i!=' ' and len(i)>=min_len and len(i)<=max_len]
    
    s_small_1 = [i for i in s_split_1 if i!=' ' and len(i)>=min_len and len(i)<=max_len]
    
    s_small_2 = [i for i in s_split_2 if i!=' ' and len(i)>=min_len and len(i)<=max_len]
    
    s_small = list(set(s_small_1).union(set(s_small_2)))
    
    # replace linebreaks with one space
    s_space = [i.replace('\n',' ') for i in s_small]
        
    # Strip extra whitespaces
    s_strip = [i.strip(' ') for i in s_space]
        
    # Remove empty blocks
    s_blocks = [i for i in s_strip if i!='']
        
    return s_blocks


def pos_tagger(sent):
    '''
    Input parameters
    ------
    sent: Any sentence string
    
    Output returns
    ------
    sent_pos: Part of Speech Tagging of any sentence
    '''
    
    sent = nltk.word_tokenize(sent)
    sent_pos = nltk.pos_tag(sent)
    
    return sent_pos

def find_emails(s_blocks, email_pattern = '[a-zA-Z0-9-_.]+@[a-zA-Z0-9-_.]+[a-zA-Z]'):
    '''
    Input parameters
    ------
    s_blocks:  is a list of strings, inside pdf
    email_pattern: is regular expression (RegEx) pattern for email identification, supplied
    
    Output returns
    ------
    emails: List of email address found
    '''
    
    # s_blocks is a list of strings, inside pdf
    emails = [re.findall(email_pattern,i) for i in s_blocks]
    emails = [i for i in emails if i!=[]]
    emails = [i for sublist in emails for i in sublist]
    
    return emails


def find_author_institute(s_blocks, author_candidates):
    '''
    Input parameters
    ------
    s_blocks:  is a list of strings, inside pdf
    author_candidates: is list of authors description, including email, or just email
    
    Output returns
    ------
    author_institute: Most probable institute name of author(s)
    '''
    
    # Find word that appears just after '@'
    author_insti_hints = [re.findall('@\w*',str(i)) for i in author_candidates]
    
    # Strip out any extra brackets, and replace @ by empty
    # 0th word because output is usually a list format, tho single item
    author_insti_hints = [i[0].replace('@','').strip('[]') for i in author_insti_hints]
    
    # Convert to lower case, for better matching across cases
    author_insti_hints = [i.lower() for i in author_insti_hints]
    
    # We have multiple hints using @, but for now choose most common out of them
    # As author names will tend to have a single email domain
    try:
        author_insti_hint = Counter(author_insti_hints).most_common(1)[0][0]
    except:
        author_insti_hint = 'unknown'
    
    # Finally find string blocks which contain this hint word
    # Without space
    author_insti_candidates_wospace = [i for i in s_blocks if author_insti_hint in i.lower()]
    
    # Blocks containing hint word but spaces allowed
    # But hint word should be atleast 4 character long
    author_insti_candidates_space = [i for i in s_blocks if (len(author_insti_hint)>=4) and author_insti_hint in i.replace(' ','').lower()]
    
    author_insti_candidates = set(author_insti_candidates_wospace).union(set(author_insti_candidates_space))
    
    # Now, first we can check if any 'ORG' i.e Named entity recognition for Organizations/Institutes present
    # Or, we can output any pattern which contains hint word (in absence of NER)
    
    author_insti_ent = [[(X.text, X.label_) for X in nlp(i).ents] for i in author_insti_candidates]
    
    # NER
    author_insti_org = [i for sublist in author_insti_ent for i in sublist if i[1]=='ORG']
    
    try:
        author_insti_ner = Counter(author_insti_org).most_common(1)[0][0][0]
    except:
        author_insti_ner = 'unknown'
    
    # Any string containing hint word, most common of them
    try:
        author_insti_general = Counter(author_insti_candidates).most_common(1)[0][0]
    except:
        author_insti_general = 'unknown'
    
    if author_insti_ner != 'unknown' and author_insti_general != 'unknown':
        author_institute = author_insti_ner or author_insti_general
    else:
        author_institute = 'Others'
    
    return author_institute

def author_name(author_desc):
    '''
    Input parameters
    ------
    author_desc:  Description of an author
    
    Output returns
    ------
    final_names: Most probable names of author(s). A list, tho usually single length
    '''
    
    # Position of sentence, POS Tagging
    s_pos = pos_tagger(author_desc)
    
    # First create bigrams out of it
    bigrams = [(s_pos[i],s_pos[i+1]) for i in range(len(s_pos)-1)]
    
    # Now filter NNP
    # Inside bigram, both first word and second word tag should be proper nouns. NNP stands for that
    # first index if letter order, 2nd index is for word vs tag
    bigrams_nnp = [i for i in bigrams if i[0][1]=='NNP' and i[1][1]=='NNP']
    
    # Both words should have first letter capitalized, or entire word capital
    #bigrams_capital = [i for i in bigrams_nnp if (i[0][0].istitle() or i[0][0].isupper()) and (i[1][0].istitle() or i[1][0].isupper())]
    bigrams_capital = bigrams_nnp
    
    # Now return only words
    final_names = ['{} {}'.format(i[0][0],i[1][0]) for i in bigrams_capital]
    
    return final_names

def author_names(authors_desc):
    '''
    Input parameters
    ------
    authors_desc:  Descriptions of authors
    
    Output returns
    ------
    authors: Most probable names of author(s). A list
    '''
    
    authors = [author_name(i) for i in authors_desc]
    # Remove empty names
    authors = [i for i in authors if i!=[]]
    # Flatten the list
    authors = [i for sublist in authors for i in sublist]
    
    return authors


def author_names_from_emails(emails):
    '''
    Input parameters
    ------
    emails: List of emails
    
    Output returns
    ------
    author_hints: Best guess hints for author names, from emails supplied 
    '''
    
    # Anything that appears before @ in email
    author_hints = [re.findall('.*@',str(i)) for i in emails]
    author_hints = [i[0].replace('@','').strip('[]') for i in author_hints]

    # Remove digits if any
    author_hints = [''.join([i for i in s if not i.isdigit()]) for s in author_hints]

    # Split on -, _, or .
    # Replacing _ by . because of regex matching flexibility, following will detect - and . by default
    author_hints = [' '.join(re.findall('\w+',i.replace('_','.'))) for i in author_hints]

    # Capitalize first letters of each word
    author_hints = [' '.join(j.capitalize() for j in i.split()) for i in author_hints]
    
    return author_hints

def final_author_names(authors, author_hints):
    '''
    Input parameters
    ------
    authors:  List of candidates for author names, detected using main logic
    author_hints: List of candidate hints for author names, detected using other information, like email etc
    
    Output returns
    ------
    authors_final_cap: Final author names after validating, filtering, removing duplicates.
        Capitalized on first letter each word 
    '''
    
    # First make lowercase both of them, and make individual set of both
    set_authors = set([i.lower() for i in authors])
    set_author_hints = set([i.lower() for i in author_hints])
    
    # Now if authors names, are also in author hints (even partial match), then it gives validation
    # So in authors list, we will see if any word is present in emails hints too, and then return those author names
    author_hints_split = [i.split() for i in set_author_hints]
    author_hints_flat = [i for sublist in author_hints_split for i in sublist]
    author_hints_flat_lower = set([i.lower() for i in author_hints_flat])
    
    set_authors_filtered = set([i for i in set_authors if any(word in i.lower() for word in author_hints_flat_lower)])
    
    # Now final list, will be, if main list present then main, else hint list
    authors_final = set_authors_filtered.union(set_author_hints)
    
    # Set and then capitalize
    set_authors_final = set([i.lower() for i in authors_final])
    
    # Capitalize first letters of each word
    authors_final_cap = [' '.join(j.capitalize() for j in i.split()) for i in set_authors_final]
    
    return authors_final_cap


def author_names_institute(s, email_pattern = '[a-zA-Z0-9-_.]+@[a-zA-Z0-9-_.]+[a-zA-Z]'):
    '''
    Input parameters
    ------
    s:  String object
    email_pattern: is regular expression (RegEx) pattern for email identification, supplied
    
    Output returns
    ------
    final_authors: Final author names. List
    author_institute: Institute that authored this document. A string
    '''
    
    # Extract small blocks
    s_blocks = extract_small_blocks(s)
    #print('Length of small blocks {}'.format(len(s_blocks)))
    
    emails = find_emails(s_blocks,email_pattern)
    
    # Blocks that contain emails
    authors_desc = [i for i in s_blocks if any(word in i.lower() for word in emails)]
    #print('Length of author description blocks {}'.format(len(authors_desc)))
    
    # Main candidates author names
    authors = author_names(authors_desc)
    
    # Hint candidates author name, from emails
    author_hints = author_names_from_emails(emails)
    
    # Final authors
    final_authors = final_author_names(authors,author_hints)
    
    # Final author institute
    author_institute = find_author_institute(s_blocks,authors_desc)
    
    return final_authors, author_institute
  
def find_companies(doc_dict, companies_list):
    # Program to find companies name in a string object
    '''
    Input parameters
    ------
    doc_dict:  Dictionary containing filepaths as keys and string objects as values
    companies_list: list of companies names.
    
    Output returns
    ------
    doc_comp_dict: Dictionary of filenames and companies mentioned
    '''
    
    doc_comp_dict = {}
    
    counter = 0
    for d,s in doc_dict.items():
        counter += 1
        print('Processing document number {}'.format(counter))
        temp_list = []
        for comp in companies_list:
            # Convert both pattern and targets to lower case, just in case
            comp_l = comp.lower()
            # Remove ltd., as it's not generally found in documents
            # And remove extra whitespaces
            comp_clean = comp_l.replace('ltd.','').strip(' ')
            
            # Document smallcase
            s_lower = s.lower()
            
            if comp_clean!='' and s_lower.find(comp_clean)>-1:
                    temp_list.append(comp)
        
        doc_comp_dict[d] = temp_list
    
    return doc_comp_dict

# If run
if __name__=='__main__':
    
    print(os.getcwd())
    
    folder_path = 'C:\\Users\Shubham\\Desktop\\pdf_to_information\\'
    
    # Specify any single file path
    fp = folder_path + 'input_pdfs\\' + '[Kotak] Consumer Products (Cautious) Month in review - July 2017- GST-led price cuts underway.pdf'
    
    # Load string content of file
    s = pdf_to_text(fp)
    
    # Loading spacy corpus
    nlp = en_core_web_sm.load()
    
    email_pattern = '[a-zA-Z0-9-_.]+@[a-zA-Z0-9-_.]+[a-zA-Z]'
    
    print('Testing a document')
    print(author_names_institute(s, email_pattern))
    
    # For multiple files
    # Already converted to string objects. Load from local
    with open(folder_path + 'doc_dict.json') as f:
        doc_dict = json.load(f)
    
    # Images texts in pdfs
    # If already done and saved once, then use this
    with open(folder_path + 'image_dict.json') as f:
        image_dict = json.load(f)
        
    # Append values of these two dictionaries into once
    doc_dict_final = {}
    
    # Assuming all keys are present
    # Strings are to be appended using +
    for fp, s in doc_dict.items():
        doc_dict_final[fp] = image_dict.get(fp,'') + doc_dict[fp]
    
    # Run this code to find author names and institute  
    # Uncomment to run
    info_dict = {}
    
    for fp,s in doc_dict_final.items():
        info_dict[fp] = author_names_institute(s, email_pattern)
        print('Processed {}'.format(fp))
    
    # If already done, then use this    
    '''
    with open(folder_path + 'info_dict.json') as f:
        info_dict = json.load(f)
    '''
    
    # Documents with author names present
    counter = 0
    for fp, v in info_dict.items():
        if v[0]!=[]:
            counter+=1
         
    # Documents with institute name present
    counter2 = 0
    for fp, v in info_dict.items():
        if v[1]!='Others':
            counter2+=1
            
    # Save as json, in local. Uncomment to do so
    '''
    with open(folder_path + 'info_dict.json', 'w') as f:
        json.dump(info_dict, f)
    '''
    # Read companies list
    # UTF-8 was giving UnicodeDecodeError
    companies = pd.read_csv(folder_path + 'bse_companies.csv', encoding='latin-1')
    #print(companies.columns)
    comp_list = companies['Company Name'].dropna().drop_duplicates().to_list()
    
    # Find companies in docs
    start = time.time()

    # Run this line after uncommenting
    #doc_comp_dict = find_companies(doc_dict_final, comp_list)
    
    # If already done and saved once, then use this
    with open(folder_path + 'doc_comp_dict.json') as f:
        doc_comp_dict = json.load(f)
    
    end = time.time()
    
    time_taken = end - start
    
    print('Took time {}'.format(time_taken))
    
    # Non empty companies names in documents
    counter3 = 0
    for fp, v in doc_comp_dict.items():
        if v!=[]:
            counter3+=1
     
    # Save as json, in local. Uncomment to do so
    '''
    with open(folder_path + 'doc_comp_dict_tmp.json', 'w') as f:
        json.dump(doc_comp_dict, f)    
    '''
    
    # Append information for files
    
    # info_dict contains author names and institute, each value is tuple of 2 elements
    # doc_comp_dict contains companies mentioned in a document, value is a list itself
    
    final_dict = {}
    for d in info_dict.keys():
        authors = info_dict[d][0]
        institute = info_dict[d][1]
        
        companies = doc_comp_dict[d]
        
        final_dict[d] = (authors,institute,companies)
        
    # Save as json, in local. Uncomment to do so
    '''
    with open(folder_path + 'final_dict.json', 'w') as f:
        json.dump(final_dict, f)
    '''
    
    df = pd.DataFrame(final_dict).transpose().reset_index()
    df.columns = ['filename','author_names','author_institute','companies_mentioned']
    df.to_csv(folder_path + 'output.csv', index = False)
        
    print('Success')
