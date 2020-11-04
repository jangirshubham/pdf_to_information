# -*- coding: utf-8 -*-
"""
Created on Wed Nov  4 00:33:49 2020

@author: Shubham
"""

import os
from os import listdir
from os.path import isfile, join

#pip install PyMuPDF
import fitz # This is same as PyMuPDF

import io

import time

import json

#pip install pillow
try:
    from PIL import Image, ImageFile
except ImportError:
    import Image, ImageFile
    
# For fixing broken images
import imageio
ImageFile.LOAD_TRUNCATED_IMAGES = True
imageio.plugins.freeimage.download()

#pip install opencv-python
import cv2
import numpy as np

# OCR library
#pip install pytesseract
import pytesseract

# -----------------------------
# Download excecutable from here
# -----------------------------
#https://digi.bib.uni-mannheim.de/tesseract/
# And put executable file path here (remember the path when installing)
# If you don't have tesseract executable in your PATH, include the following:
pytesseract.pytesseract.tesseract_cmd =r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def image_to_text(fp):
    '''
    Input parameters
    ------
    fp:  Image file path. For example some folder/test.png
    
    Output returns
    ------
    image_text: image converted to text
    '''
    
    # Open the image for text conversion
    #img = Image.open(fp)
                    
    img = Image.open(fp).convert('L')  
                    
    # Thresholding to clear noise
    # parameters (img, thresh_value, maxVal, style)
    # if pixel < max value, then it convets to max value
    # if pixel less than threshold, then it converts it to 0
                    
    # change threshold as necessary
    ret,img = cv2.threshold(np.array(img), 128, 255, cv2.THRESH_BINARY)
                    
    # Convert using OCR
    image_text = pytesseract.image_to_string(img, config='') # config setting is expensive
    
    return image_text


def pdf_image_to_text(fp, parse_pages = 'all'):
    '''
    Input parameters
    ------
    fp:  Pdf file path. For example some folder/test.pdf
    range_pages: 'all' for all pages. 'first_last' for first and last page only.
    
    Output returns
    ------
    text_list: pdf images converted to text. list of image texts inside file
    '''
    
    # opens doc using PyMuPDF
    doc = fitz.Document(fp)
    
    # Converted text to go here
    text_list = []
    
    try:
        if parse_pages == 'first_last':
            # default is first_last        
            if doc.pageCount == 1:
                list_pages = [0]
            else:
                list_pages = [0, doc.pageCount-1]
        else:
            # if taking all pages
            list_pages = range(0, doc.pageCount)
        
        # Now parge over pages
        for i in list_pages:
            # Load i'th page
            page = doc.loadPage(i)
            
            # If atleast 1 image found, then iterate            
            len_images = len(page.getImageList())
                        
            if len_images > 0:
                # Take all images in the page                
                
                # List of all images
                xref = page.getImageList()
                
                # Loop over all images                
                for j in range(0,len_images):    
                    # Get image reference id, for current image in loop
                    xref_j = xref[j][0]
                
                    # Gets the image as a dict, check docs under extractImage 
                    baseImage = doc.extractImage(xref_j)
                
                    #gets the raw string image data from the dictionary
                    # and wraps it in a BytesIO object before using PIL to open it
                    image = Image.open(io.BytesIO(baseImage['image']))
                
                    # Remove last characters
                    filename_s = filename.replace('.pdf','')
                    
                    # Where to save the image
                    # filename_pagenum_imagenum.png
                    img_fp = image_download_path + '/' + filename_s + '_' + str(i) + '_' + str(j) + '.png'
                    
                    # Save the image
                    image.convert('RGBA').save(img_fp)
                
                    # Image to text
                    image_text = image_to_text(img_fp)
                
                    # Append the result text of current image, to overall file text
                    text_list.append(image_text)
    
    # Images can be tricky. Pass the logic if decode errors.
    except:
        pass
    
    return text_list
    
def parse_pdfs_images(pdf_folder_path, image_download_path, n = None, parse_pages = 'all'):
    # Convert all pdfs in a folder, to text, specifically for images contained
    '''
    Input parameters
    ------
    pdf_folder_path: folder path where your pdfs are stored
    image_download_path: images to saved in this folder
    n: limitation on number of files parsed, if specified. default is None
    parge_pages: 'first_last' if only first and last pages are to be parase. default 'all' for all.
    
    Output returns
    ------
    image_dict: dictionary containing filepaths as keys and string objects as values
    '''
    
    onlyfiles = [f for f in listdir(pdf_folder_path) if isfile(join(pdf_folder_path, f))]
    
    # If limitation specified on number of files to be read
    if n:
        onlyfiles = onlyfiles[:n]
    
    # Please specify direction of slash accordingly
    #filepaths = [folder_path+'\\'+i for i in onlyfiles]
    #print(filepaths)
    
    # Counter for number of files processed
    counter = 0
    image_dict = {}
    # Iterate over all files in the folder
    for filename in onlyfiles:
        counter+=1
        print('processed filenumber {}'.format(counter))
    
        fp = pdf_folder_path + '/' + filename
    
        text_list = pdf_image_to_text(fp, parse_pages = parse_pages)
        
        # Combine text lists, using combiner
        combiner = '\n\n'
        
        text = combiner.join(text_list)
    
        # Filename (which is pdf file), and its text obtained from images only
        image_dict[filename] = text
    
    return image_dict
    

# If run
if __name__=='__main__':
    
    print(os.getcwd())
    
    # Test a sample image
    # Simple image to string
    folder_path = '/users/Shubham/Desktop/pdf_to_information'
    
    fp = folder_path +'/' + 'test.png'
    
    image_text = image_to_text(fp)
    
    # Parse images from pdfs
    pdf_folder_path = folder_path + '/input_pdfs'
    
    # Images are to be downloaded in this
    image_download_path = folder_path +'/images'

    # Measure time taken
    start = time.time()
    
    # Image strings to be saved in this dict
    image_dict = parse_pdfs_images(pdf_folder_path, image_download_path,
                                   n = 10, parse_pages = 'first_last')
    
    end = time.time()

    time_taken = end - start
    print('Time taken {}'.format(time_taken))
    
    # Non empty texts in dictionary
    counter = 0
    for fp, v in image_dict.items():
        if v.replace('\n','').strip(' ')!='':
            counter+=1
        
    # Save as json, in local. Uncomment to do so
    '''
    with open(folder_path + '/' + 'image_dict_tmp.json', 'w') as f:
        json.dump(image_dict, f)
    '''
    
    # If already done and saved once, then use this
    '''
    with open(folder_path + '/' + 'image_dict.json') as f:
        image_dict = json.load(f)
    '''    
        
    print('Success')
    
            
        
             
