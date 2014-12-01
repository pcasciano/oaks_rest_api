"""API Views for oaks_rest_api application."""
from oaks_rest_api.models import ShapeFile, TripleStore, NodeToken, \
    TGEO_STORE_FORMATS
from oaks_rest_api.serializers import *
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status, generics
from django.http import HttpResponse
from oaks_rest_api.tgeo import rename_params
from django.conf import settings
from oaks_rest_api.utils import *
from django.contrib.auth.models import User
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from oaks_rest_api.node import post_node_server
from oaks_rest_api.git import Git
from os.path import basename, splitext, isdir
from zipfile import BadZipfile


def check_type_params(request):
    """
    checks if request has query "type" params
    """
    if request.QUERY_PARAMS.has_key('type'):
        return request.QUERY_PARAMS['type'].lower()
    else:
        return Response({'type':["This query parameter is required."]},
                           status=status.HTTP_400_BAD_REQUEST)
        
    
def create_zip_archive(file_list, name):
    """
    Creates a zip file resource
    """
    try:
        zip_files(file_list, name)
    except BadZipFile:
        return Response ({'detail': 'Bad Zip file'},
                         status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    file_path = name.replace('/var/www/', '') 
    url = settings.SITEURL+file_path+'.zip'    
    return Response({'file': url}, status=status.HTTP_200_OK)     
    

   
class ShapeList(APIView):
    """
    Shape file resources
    """
    throttle_scope = 'default'
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = (IsAuthenticated, )   
    
    def save_shp(self, shape_file, user):
        """
        Saves a shape file on server
        """
        return ShapeFile.objects.create(shp=shape_file['shp'], 
                                        shx=shape_file['shx'],
                                        dbf=shape_file['dbf'],
                                        prj=shape_file['prj'],
                                        owner=user)
                                         
    def pre_save(self, obj):
        obj.owner = self.request.user                                     
                                     
                                     
    def get(self, request):
        """
        Gets all shape file resources
        """
        shapes = ShapeFile.objects.all().filter(owner=self.request.user.id)
        serializer = ShapeFileSerializer(shapes, many=True)
        return Response(serializer.data)                                     
            
                                     
    def post(self, request):
        """
        uploads a  shape file
        type -- base, all        
        ---    
        omit_serializer: true    
        consumes: ["multipart/form-data"]
        parameters:
            - name: shp
              type: file
              required: true
              paramType: form
            - name: shx
              type: file
              required: true
              paramType: form
            - name: dbf
              type: file
              required: true
              paramType: form
            - name: prj
              type: file
              paramType: form       
            - name: type_wkt
              type: string
              required: false
              paramType: form
            - name: format_file
              type: string
              required: false
              paramType: form    
              defaultValue: rdf
            - name: target_store
              type: string
              required: false
              paramType: form
              defaultValue: 'GeoSparql'
            - name: feature_string
              type: string
              required: false
              paramType: form      
            - name: attribute
              type: string
              required: false
              paramType: form    
            - name: ignore
              type: string
              required: false
              paramType: form    
              defaultValue: 'UNK'
            - name: name
              type: string
              required: false
              paramType: form
            - name: class_store
              type: string
              required: false
              paramType: form    
            - name: ns_URI
              type: string
              required: false
              paramType: form
            - name: ns_prefix
              type: string
              required: false
              paramType: form      
            - name: ontology_NS
              type: string
              required: false
              paramType: form     
            - name: ontology_NS_prefix
              type: string
              required: false
              defaultValue: 'geo'
              paramType: form    
            - name: default_lang
              type: string
              required: false
              paramType: form    
              defaultValue: 'en'
            - name: output_file
              type: string
              required: false
              paramType: form     
            - name: commit_msg
              type: string
              required: false
              paramType: form    
            - name: ckan_api_key
              type: string
              required: false
              paramType: form
            - name: ckan_id
              type: string
              required: false
              paramType: form          
        """
        params = request.DATA.dict()  
        
        def save_ckan_resource(id_shp, params):
            """
            saves a ckan resource
            """
            #check api_key
            #if api_key.is_valid():  
            if params.has_key('ckan_api_key') and params.has_key('ckan_id'):                  
                CkanResource.objects.create(api_key=params['ckan_api_key'], 
                                            id_resource=params['ckan_id'], 
                                            shp_id=id_shp)
                params.pop('ckan_api_key')                  
                params.pop('ckan_id')
                
     
        def process(file_shp, params, store_in_semantic_db=False):   
            #create auth token
            token = NodeToken.objects.create(user=self.request.user)   
            if store_in_semantic_db:
                params['input_file'] = file_shp.shp.name
                pos = params['input_file'].rfind('/')
                params['feature_string'] = params['input_file'][pos+1:-4]
                params['output_file'] = settings.UPLOAD_TRIPLE_STORE+'/'+ \
                params['feature_string']+'.'+params['format_file']
                params['owner'] = self.request.user
                
                triple_store = TripleStore.objects.create(**params)
                triple_store.shp.add(file_shp)
                params = rename_params(params) 
                
                result = post_node_server(data=params, token=token, 
                                          url='/loadShape')
            else:
                result = post_node_server(data={'input-file': file_shp.shp.name},
                                          token=token, url='/loadShpInGeonode')
                
            return Response({'detail': result['details']},
                            status=result['status'])  
                                                                                             
        def process_shp_from_zip(zip, store_type):
            """
            gets a shape file from zip and process it.
            """
            f = get_shp_from_zip(zip, store_in)
            if f:
                file_shape =  self.save_shp(f, self.request.user)
                return process(file_shape, params, 
                               store_in_semantic_db=store_type)
            else:
                return Response(shape_serializer.errors,
                                status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE) 
                                                                                                                
        upload_type = check_type_params(request)
        create_dir(settings.BASE_STORAGE+settings.UPLOAD_SHAPE)
        shape_serializer = ShapeFileSerializer(data=request.FILES)
        
        if isinstance(upload_type, unicode):    
            create_dir(settings.BASE_STORAGE+settings.UPLOAD_SHAPE)
            shape_serializer = ShapeFileSerializer(data=request.FILES) 
                   
            if upload_type == 'base': 
                if shape_serializer.is_valid():
                    file_shp = self.save_shp(request.FILES, self.request.user)
                    save_ckan_resource(file_shp.id, params) 
                elif u'zip' in request.FILES:
                    return process_sho_from_zip(request.FILES['zip'], False)  
                else:
                    return Response(shape_serializer.errors,
                                    status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)  
                
            elif upload_type == 'all':
	        
                if shape_serializer.is_valid():
                    triple_store_serializer = TripleStoreSerializer(data=request.DATA)
                    if triple_store_serializer.is_valid():
                        file_shp = self.save_shp(request.FILES, self.request.user)
                        save_ckan_resource(file_shp.id, params) 
                        
                        return process(file_shp,  params, store_in_semantic_db=True)
                    else:
                        return Response(triple_store_serializer.errors,
                                        status=status.HTTP_400_BAD_REQUEST)
                elif u'zip' in request.FILES:
                    return process_shp_from_zip(request.FILES['zip'], True)   
                else:
                    return Response(shape_serializer.errors,
                                    status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)   
                                                          
            else:
                return Response({'type': ['Select a valid choice!']},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return upload_type
        
        
class ShapeDetail(APIView):
    """
    Shape file resource detail
    """
    throttle_scope = 'default'
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = (IsAuthenticated, )

    def pre_save(self, obj):
        obj.owner = self.request.user        
         
    def get(self, request, pk):
        """
        Downloads a shape file from the server
        """
        try:
            shape = ShapeFile.objects.get(pk=pk)
        except ShapeFile.DoesNotExist:
            return Response({'detail': 'Not found'},
                            status=status.HTTP_404_NOT_FOUND)
                            
        shp_name = basename(shape.shp.name)       
        file_name = splitext(shp_name)[0]
        zip_name = settings.BASE_STORAGE+settings.ZIP_DIR+'/'+file_name
   
        try: 
            zip_files([settings.BASE_STORAGE+str(shape.shp), 
                 settings.BASE_STORAGE+str(shape.dbf),
                 settings.BASE_STORAGE+str(shape.shx), 
                 settings.BASE_STORAGE+str(shape.prj)],
                 zip_name)
        except BadZipfile:
            return Response({'detail': 'Bad Zip file'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return download_file_url(zip_name+'.zip')             
         
    def delete(self, request, pk):
        """
        Deletes a shape file from the server
        """
        try:     
            shape = ShapeFile.objects.get(pk=pk)
        except ShapeFile.DoesNotExist:
            return Response({'detail': 'Not found'},
                            status=status.HTTP_404_NOT_FOUND)
        shape.delete()  
        
        #delete related
        try: 
            ckan_resource = CkanResource.objects.get(shp_id=pk)
            ckan_resource.delete()
        except CkanResource.DoesNotExist:
            pass
     
        try: 
            geonode_resource = GeonodeResource.objects.get(shp_id=pk)
            geonode_resource.delete()
        except GeonodeResource.DoesNotExist:
            pass    
     
        return Response(status=status.HTTP_204_NO_CONTENT)            
                                           
                                     
class ShapeConvert(APIView):
    """
    Converts a shape in a triple store format file(utility)   
    """
    throttle_scope = 'utility'
    parser_classes = (MultiPartParser, FormParser)    
    
    def post(self, request):
        """
        Outputs a triple store format file
        ---
        omit_serializer: true    
        consumes: ["multipart/form-data"]
        parameters:
            - name: shp
              type: file
              required: true
              paramType: form
            - name: shx
              type: file
              required: true
              paramType: form
            - name: dbf
              type: file
              required: true
              paramType: form
            - name: prj  
              type: file
              required: false
              paramType: form
        """      
        shape_serializer = ShapeFileSerializer(data=request.FILES)
        if shape_serializer.is_valid():
            pass
        else:
            return Response(shape_serializer.errors,
                     status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
            
class TripleStoreList(APIView):
    """
    Triple Store resource
    """
    throttle_scope = 'default'
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = (IsAuthenticated, )     
       
    def pre_save(self, obj):
        obj.owner = self.request.user

    def get(self, request):
        """
        gets a list of triple stores files
        """
        triple_stores = TripleStore.objects.all()
        serializer = TripleStoreSerializer(triple_stores, many=True)
        return Response(serializer.data)    
    
    def post(selfself, request):
        """
        Uploads a triple store file on server and store in semantic db
        ---  
        consumes: ["multipart/form-data"]
        parameters:
            - name: triple-store_file
              type: file
              required: true    
              paramType: form    
        """
        create_dir(settings.UPLOAD_TRIPLE_STORE)
        triple_store_file = request.FILES['triple-store_file']
        TripleStore.objects.create(output_file=triple_store_file,
                                   owner=self.request.user)
        #store in semantic db
        token = NodeToken.objects.create(user=self.request.user)
        params = {'filename':str(triple_store_file), 'path': settings.UPLOAD_TRIPLE_STORE }
        result = post_node_server(data=params, token=token, url='/loadTripleStore')
        
        return Response({'detail': result['details']}, status=result['status']) 
        
        
class TripleStoreDetail(APIView):
    """
    Triple Store resource detail
    """
    throttle_scope = 'default'
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = (IsAuthenticated, )

    def pre_save(self, obj):
        obj.owner = self.request.user

    def get(self, request, pk):
        """
        Downloads a triple file from the server
        """    
        try:
            triplestore = TripleStore.objects.get(pk=pk)
        except TripleStore.DoesNotExist:
            return Response({'detail': 'Not found'},
                            status=status.HTTP_404_NOT_FOUND)   
            
        return download_file_url(str(triplestore.output_file))
    
    def delete(selfself, request, pk):
        """
        Deletes a triple store file from the server
        """
        try:     
            triplestore = TripleStore.objects.get(pk=pk)
        except TripleStore.DoesNotExist:
            return Response({'detail': 'Not found'},
                            status=status.HTTP_404_NOT_FOUND)
            
        triplestore.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)      
    
class Data(APIView):
    """
    gets all uploaded data files
    """
    permission_classes = (IsAuthenticated, )
    def get(self, request):
        shapes = ShapeFile.objects.filter(owner_id=self.request.user)
        triple_stores = TripleStore.objects.filter(owner_id=self.request.user)

        shapes_serializer = ShapeFileSerializer(shapes, many=True)
        triple_store_serializer = TripleStoreSerializer(triple_stores, many=True)

        all_data = {'shapes': shapes_serializer.data,
                    'triple-stores': triple_store_serializer.data}
        return Response(all_data)    
        
class DownloadFile(APIView):
    """
    Gets a file resource searched by name

    type -- file format (shp, rdf, nt, n3, all)
    """
    throttle_scope = 'download'
    
    def __search_shape(self, file_name):
        """
        searches a shape file in UPLOAD_SHAPE dir

        returns a ShapeFile object if founds it, HttpResponse otherwise
        """
        try:
            path = settings.UPLOAD_SHAPE+'/'+file_name
            shp = path+'.shp'
            shx = path+'.shx'
            dbf = path+'.dbf'
            prj = path+'.prj'
            return ShapeFile.objects.get(shp=shp, shx=shx, dbf=dbf, prj=prj)
        except ShapeFile.DoesNotExist:
            return Response({'detail': 'File not found!'},
                            status=status.HTTP_404_NOT_FOUND)
        except ShapeFile.MultipleObjectsReturned:
            return Response({'detail': 'Server error, multiple instance file'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)  
            
    def __search_triple_store(self, file_name):
        """
        searches a triple store format file in UPLOAD_TRIPLE_STORE dir.
        returns a TripleStore object if founds it, HttpResponse otherwise
        """          
        try:
            path = settings.UPLOAD_TRIPLE_STORE+'/'+file_name
            
            return TripleStore.objects.get(output_file=path)
        except TripleStore.DoesNotExist:
            return Response({'detail': 'File not found.'},
                            status=status.HTTP_404_NOT_FOUND)
        except TripleStore.MultipleObjectsReturned:
            return Response({'detail': 'Server error, multiple instance file'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR)        

    def get(self, request, name):
        """
        outputs a file resource stored on server in various formats
        """            
        upload_type = check_type_params(request)    
        if isinstance(upload_type, unicode):
            if upload_type == 'shp':
                shape_file_response = self.__search_shape(name)
                if isinstance(shape_file_response, ShapeFile):
                    name = settings.BASE_STORAGE+settings.ZIP_DIR+'/'+name
                    file_list = [
                                 shape_file_response.shp,
                                 shape_file_response.shx,
                                 shape_file_response.prj,
                                 shape_file_response.dbf                                 
                                 ]
                    file_list = [settings.BASE_STORAGE + str(x) for x in file_list]
                    return create_zip_archive(file_list, name)
                else:
                    return shape_file_response
            elif file_format in [v for v, t in TGEO_STORE_FORMATS]:     
                pass 
            elif file_format == 'all':
                pass          
                
        else:
            return upload_type
                                
    
class GitLog(APIView):
    """
    Gets geogit log info
    """
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        geogit = Git(owner=self.request.user)
        return Response(geogit.log())


class UserList(generics.ListAPIView):
    """
    Gets a list of users
    """
    permission_classes = (IsAdminUser, )
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserDetail(generics.RetrieveAPIView):
    """
    Gets user detail by id
    """
    permission_classes = (IsAuthenticated, )
    queryset = User.objects.all()
    serializer_class = UserSerializer


class CurrentUser(APIView):
    """
    Gets current user
    """
    permission_classes = (IsAuthenticated, )
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)    
                               
                                     
                                     
                                     
                                     
                                     
                                     
                                     
                                     
                                     
                                     
                                     