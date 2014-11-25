"""API utils for oaks_rest_api application"""
from zipfile import ZipFile, BadZipfile
import cStringIO
import StringIO
import os
import tempfile
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import shutil
from django.core.files.uploadedfile import InMemoryUploadedFile


def get_shp_from_zip(zip_file):
    """
    extract components file parts of a shapefile from a zip file

    zip_file -- zip file
    """
    try:
        zip_f = ZipFile(zip_file, 'r')
    except BadZipfile:
        return None
    list_names = zip_f.namelist()
    d = {}
    for elem in list_names:
        t = elem.split('.')
        d[t[1].lower()] = t[0]
        ll = d.values()
    #shp name validation (same name)
    if all(x == ll[0] for x in ll):
        k = d.keys()
        #shp file  type validation
        if len(k) == 4 and ('shp' in k and 'dbf' in k and 'shx' in k
                            and 'prj' in k):
            res = {}
        for name in zip_f.namelist():
            io = StringIO.StringIO()
            zo = zip_f.open(name, 'r')
            io.write(zo.read()) #.decode('ISO8859-1').encode('utf-8'))
            zo.close()
            res_file = InMemoryUploadedFile(io, None, name.lower(), 'text', io.len, None)
            res_file.seek(0)
            res[name.split('.')[1].lower()] = res_file
        return res
    else:
        return None

def zip_files(files, zip_name):
    """
    Creates a zip file named zip_name from files list argument.
    Returns a zip file string content

    files -- files list argument
    zip_name -- name of created zip file

    """
   # s = cStringIO.StringIO()
#    zip_file = ZipFile(s, 'w')
    zip_name = zip_name+'.zip'
    zip_file = ZipFile(zip_name, 'w')
    files_len = len(files)
    #counter for not found files in list arg
    file_not_found_count = 0

    #make dir if there are a shape file plus other formats files in files list
    if files_len > 3 and any('shp' in substr for substr in files):
        dir_shp = 'shp/'
    else:
        dir_shp = ''

    #create zip
    for n in files:
        try:
            name = unicode(n)
            f = open(name, 'r')
            if name.endswith('.shp') or name.endswith('.dbf') or name.endswith(
                    '.shx') or name.endswith('prj'):
                zip_file.writestr(dir_shp+os.path.basename(name), f.read())
            else:
                zip_file.writestr(os.path.basename(name), f.read())
            f.close()

        except IOError:
            #file not found
            file_not_found_count += 1
    zip_file.close()
        

    #returns zip files string if there are files in zip,
    #None, otherwise.
    
    if files_len > file_not_found_count:        
	return None
    else:
	delete_file(zip_name)
	raise BadZipfile('Zip file not valid!')
      

def save_shape_in_tmp_dir(shp_file):
    """
    Saves a shape file in a temporary directory.

    shp_file -- shape file list (.shp, .shx, .dbf, .prj)
    """
    tmp_dir = tempfile.mkdtemp()+'/'
    for f in shp_file:
        default_storage.save(tmp_dir+f.name, ContentFile(f.read()))
    return tmp_dir

def delete_file(file_name):
    """
    Deletes a file.

    file_name -- file path name to be deleted
    """
    try:
        os.remove(file_name)
    except OSError:
        pass

def delete_dir(dir):
    """
    Deletes a directory

    dir -- directory to be deleted
    """
    shutil.rmtree(dir)

def create_dir(dir):
    """
    Creates a directory if it doesn't exist
    dir -- directory to be created
    """
    try:
        os.stat(dir)
    except:
        os.mkdir(dir)

def copy_file(src, dest):
    """
    Copy a file from src to dest

    src -- source file path
    dest -- destination file path
    """
    try:
        shutil.move(src, dest)
    #src an dest are same file
    except shutil.Error:
        return False
    #src or dest doesn't exist
    except IOError:
        return False
    return True
