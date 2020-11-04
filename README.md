# pdf_to_extraction

Extract information like author and keywords mentioned from pdfs

'input_pdfs' is the input folder for pdfs

'images' is the input folder for images to be saved, when using OCR

'main_func.py' is the main file to be run (string objects to information)

'utils/data_prep.py' is the data prep file (pdf to text)
'utils/data_prep_image.py' is the data prep images file (pdf to text using images contained)

json files load/dump has also been used for integration across modules

output is a '.csv' file containing filename, author names, institute, companies mentioned
