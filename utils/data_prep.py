# -*- coding: utf-8 -*-
"""
Created on Wed Nov  4 00:33:49 2020

@author: Shubham
"""

import os

from os import listdir
from os.path import isfile, join

import time

import json

from io import StringIO

#pip install pdfminer.six
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

from pdfminer.high_level import extract_pages

def pdf_to_text(fp,parse_page=[]):
    '''
    Input parameters
    ------
    fp: file path of pdf
    parse_page: page numbers (starting at 0), to conver to text. All pages if empty []
    
    Output returns
    ------
    string_output: String output of contents in pdf
    '''
    
    output_string = StringIO()
    with open(fp, 'rb') as in_file:
        num_pages = len(list(extract_pages(in_file)))
        #print('Number of pages {}'.format(num_pages))
        parser = PDFParser(in_file)
        doc = PDFDocument(parser)
        rsrcmgr = PDFResourceManager()
        device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for i, page in enumerate(PDFPage.create_pages(doc)):            
            if len(parse_page)>0 and i not in parse_page:
                continue
            #print('Processing page number {}'.format(i))
            interpreter.process_page(page)
    
    string_output = output_string.getvalue()
    # Close open handles
    device.close()
    output_string.close()
    
    return string_output


def parse_pdfs(folder_path, n = None):
    # Convert all pdfs in a folder, to text
    '''
    Input parameters
    ------
    folder_path: folder path where your pdfs are stored
    n: limitation on number of files parsed, if specified. default is None
    
    Output returns
    ------
    doc_dict: dictionary containing filepaths as keys and string objects as values
    '''
    
    onlyfiles = [f for f in listdir(folder_path) if isfile(join(folder_path, f))]
    
    #print(onlyfiles)
    
    # If limitation specified on number of files to be read
    if n:
        onlyfiles = onlyfiles[:n]
    
    # Please specify direction of slash accordingly
    #filepaths = [folder_path+'\\'+i for i in onlyfiles]
    #print(filepaths)
    
    counter=0
    doc_dict = {}
    
    for filename in onlyfiles:
        counter+=1  
        
        fp = folder_path+'\\' + filename
        
        s = pdf_to_text(fp)
        print('file processed number',counter)
        
        doc_dict[filename] = s
    
    return doc_dict


# If run
if __name__=='__main__':
    
    print(os.getcwd())
    
    folder_path = 'C:\\Users\Shubham\\Desktop\\pdf_to_information\\'
    
    # Specify any single file path
    fp = folder_path + 'input_pdfs\\' + '[Kotak] Consumer Products (Cautious) Month in review - July 2017- GST-led price cuts underway.pdf'
    
    # Number of pages in file
    with open(fp, 'rb') as in_file:
        num_pages = len(list(extract_pages(in_file)))
    
    print('Number of pages {}'.format(num_pages))
    
    # Load string content of file
    # Calculate time taken
    start = time.time()
    s = pdf_to_text(fp)
    print('Contents of string length {}'.format(len(s)))
    end = time.time()
    
    time_taken = end - start
    
    print('Took time {}'.format(time_taken))
    
    # Load strings for multiple files in pdfs
    
    # If want to try all files, then don't put 'n'
    #doc_dict = parse_pdfs(folder_path)
    doc_dict = parse_pdfs(folder_path + 'input_pdfs', n = 10)
    
    # Dump the content dictionary to a json file, which can then be read to load strings
    with open(folder_path + '\\' + 'doc_dict_tmp.json', 'w') as f:
        json.dump(doc_dict, f)
    
    print('Success')
