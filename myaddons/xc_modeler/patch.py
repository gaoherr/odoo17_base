# -*- coding: utf-8 -*-

# before running this script, make sure you have the following files in the same directory:
# and install javascript-obfuscator

import os
import re
from time import time

links = """
# <script type="text/javascript" src="js/modeler/Init.js"></script>
# <script type="text/javascript" src="libs/pk.min.js"></script>
# <script type="text/javascript" src="libs/base64.js"></script>
# <script type="text/javascript" src="js_color/js_color.js"></script>
# <script type="text/javascript" src="libs/sanitizer.min.js"></script>
# <script type="text/javascript" src="libs/jquery.js"></script>
# <script type="text/javascript" src="libs/proper.js"></script>
# <script type="text/javascript" src="libs/tippy.js"></script>
# <script type="text/javascript" src="libs/mxgraph/mxClient.min.js"></script>
# <script type="text/javascript" src="js/modeler/EditorUi.js"></script>
# <script type="text/javascript" src="js/modeler/Editor.js"></script>
# <script type="text/javascript" src="js/modeler/Sidebar.js"></script>
# <script type="text/javascript" src="js/modeler/Graph.js"></script>
# <script type="text/javascript" src="js/modeler/Format.js"></script>
# <script type="text/javascript" src="js/modeler/Shapes.js"></script>
# <script type="text/javascript" src="js/modeler/mxER.js"></script>
# <script type="text/javascript" src="js/modeler/Actions.js"></script>
# <script type="text/javascript" src="js/modeler/Menus.js"></script>
# <script type="text/javascript" src="js/modeler/Toolbar.js"></script>
# <script type="text/javascript" src="js/modeler/Dialogs.js"></script>
# <script type="text/javascript" src="js/XcResourceLoader.js"></script>
# <script type="text/javascript" src="js/modeler/ModelerExtend.js"></script>
# <script type="text/javascript" src="js/modeler/XcCellExtend.js"></script>
# <script type="text/javascript" src="js/modeler/XcField.js"></script>
# <script type="text/javascript" src="js/modeler/XcTable.js"></script>
# <script type="text/javascript" src="js/modeler/XcModeler.js"></script>
# <script type="text/javascript" src="js/XcModelerInitPro.js"></script>
"""

# get current file path
current_path = os.path.dirname(os.path.realpath(__file__))

# user regex to find all the link
regex = r'<script type="text/javascript" src="(.*?)"></script>'
result = re.finditer(regex, links)
urls = []
for match in result:
    link = match.group(1)
    static_dir = current_path + "/static/"
    url = os.path.join(static_dir, link)
    # replace \\ with /
    url = url.replace('\\', '/')
    urls.append(url)

# read all the files
files = []
for url in urls:
    with open(url, 'r') as f:
        files.append(f.read())

# remove files
for url in urls:
    os.remove(url)

# join all the files
content = '\n'.join(files)

write_file = current_path + '/static/js/app.js'
# delete the file if it exists
if os.path.exists(write_file):
    os.remove(write_file)

# write the content to the file
with open(write_file, 'w+') as f:
    f.write(content)

obfuscator_file = current_path + '/static/js/app-obfuscated.js'
# delete the file if it exists
if os.path.exists(obfuscator_file):
    os.remove(obfuscator_file)

# execute the command "javascript-obfuscator write_file"
# to obfuscate the file
os.system("javascript-obfuscator " + write_file)

# change the file name to app-vender.js
vender_file = current_path + '/static/js/app-vender.js'
# delete the file if it exists
if os.path.exists(vender_file):
    os.remove(vender_file)
os.rename(obfuscator_file, vender_file)

# remove write_file
if os.path.exists(write_file):
    os.remove(write_file)

product_html_path = current_path + '/static/product.html'
product_html_path = product_html_path.replace('\\', '/')
# check if the file exists
if os.path.exists(product_html_path):
    with open(product_html_path, 'r+') as f:
        content = f.read()
        # go to the start of the file
        f.seek(0)
        content = content.replace('js/app-vender.js', 'js/app-vender.js?t=' + str(int(time())))
        f.write(content)

index_path = current_path + '/static/index.html'
# delete the file if it exists
if os.path.exists(index_path):
    os.remove(index_path)

# get the file content
with open(product_html_path, 'r') as f:
    content = f.read()
    # write the content to the file
    with open(index_path, 'w') as tmp:
        tmp.write(content)

# remove product.html
os.remove(product_html_path)

# js_files = [
#     'static/XcModelerAction.js',
#     'static/js/XcBaseProjectList.js',
#     'static/js/XcProjectList.js',
#     'static/js/XcChoseDirField.js'
# ]

# # deal the files
# for js_file in js_files:
#     js_file_path = os.path.join(current_path, js_file)
#     # replace \\ with /
#     js_file_path = js_file_path.replace('\\', '/')
#     # execute the command "uglifyjs" and get the result
#     result = os.popen("uglifyjs " + js_file_path + " -c -m reserved=['_super','odoo','define','require']").read()
#     if result:
#         # write result to file
#         with open(js_file_path, 'w+') as f:
#             f.write(result)

# print congratulations
print("Congratulations! You have successfully obfuscated the files.")