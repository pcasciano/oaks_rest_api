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



def download_file(file, file_name):
    """
    Outputs a file via HttpResponse
    """
    if file:
        if file_name.endswith('.zip'):
            mime = 'application/x-zip-compressed'
        elif file_name.endswith('.rdf'):
            mime = 'application/rdf+xml'
        elif file_name.endswith('.ttl'):
            mime = 'application/x-turtle'
        elif file_name.endswith('.n3'):
            mime = 'text/rdf+n3'
        else:
            mime = 'text/plain'
        response = HttpResponse(file, content_type=mime)
        response['Content-Disposition'] = 'attachment; filename=%s' % file_name
        return response
    else:
        return Response({'detail': 'file not found'},
                        status=status.HTTP_404_NOT_FOUND)

                        
def download_file_url(file_path):
    """
    Creates link url file resource
    """  
    file_path = file_path.replace('/var/www/', '') 
    url = settings.SITEURL+file_path
    return Response({'file': url},
                        status=status.HTTP_200_OK)


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
      
#def save_geonode_resource(id_shp, ):
  

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
	shp = shape_file['shp']
	shx = shape_file['shx']
	dbf = shape_file['dbf']
	prj = shape_file['prj']
	file_saved = ShapeFile.objects.create(shp=shp, shx=shx, dbf=dbf, prj=prj,
					      owner=user)
	return file_saved

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
	serializer: oaks_rest_api.serializers.ShapeFileSerializer	
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
	      required: true	
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
	      required: true
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
        
	def process(file_shp, params, store_in_semantic_db=False):
	   
		    
	    #create auth token
	    token = NodeToken.objects.create(user=self.request.user)
	    
	    
		    
	    if store_in_semantic_db:
	      	#params = request.DATA.dict()
	        params['input_file'] = file_shp.shp.name
	        
		pos = params['input_file'].rfind('/')
		params['feature_string'] = params['input_file'] \
			    [pos+1:-4]

		params['output_file'] = settings.UPLOAD_TRIPLE_STORE+ \
			    '/'+params['feature_string']+'.'+params['format_file']
		params['owner'] = self.request.user

		  #create commit message for geogit
		  #if params.has_key('commit_msg'):
		  #if params['commit_msg'] != '':
		      #commit_msg = params['commit_msg']
		  #else:
		      #commit_msg = 'shape file '+ \
			  #params['feature_string']+' imported.'
		      #params.pop('commit_msg')
		  #else:
		  #return Response({'commit_msg':["This query parameter is required."]},
			      #status=status.HTTP_400_BAD_REQUEST)
		      
		      #TODO:: vedi se possibile togliere triple_store		     
		triple_store = TripleStore.objects.create(**params)
		triple_store.shp.add(file_shp)
		  
		params = rename_params(params)                                                                     

		  #call geogit and commit uploaded shp
		  #geogit = Git(owner=self.request.user)
		  #geogit.push(shp=file_shp.shp.name, commit_msg=commit_msg)



		result = post_node_server(data=params, token=token, url='/loadShape')
	    else:
		result = post_node_server(data={'input_file': file_shp.shp.name
					       },
					       token=token, url='/loadShpInGeonode')
					       
	    return Response({'detail': result['details']}, 
			  status=result['status'])
	      
	    #if result == True:
		#return Response({'detail': result['details'], status=result['status'])
	    #else:
		#return Response({'detail': result}, status=status.HTTP_200_OK)
     
      
        if request.QUERY_PARAMS.has_key('type'):
            upload_type = request.QUERY_PARAMS['type'].lower()
            create_dir(settings.UPLOAD_SHAPE)
            shape_serializer = ShapeFileSerializer(data=request.FILES)
            
            if upload_type == 'base':            
                if shape_serializer.is_valid():
                    file_shp = self.save_shp(request.FILES, self.request.user)
		    save_ckan_resource(file_shp.id, params)  
                    return process(file_shp, params, store_in_semantic_db=False)
                elif u'zip' in request.FILES:
                    f = get_shp_from_zip(request.FILES['zip'])
                    if f:
                        file_shp = self.save_shp(f, self.request.user)                        
                        return process(file_shp, params, store_in_semantic_db=False)
                    else:
                      return Response(shape_serializer.errors,
                                    status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)  
                else:
                    return Response(shape_serializer.errors,
                                    status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
	      
            elif upload_type == 'all':                
                if shape_serializer.is_valid():		  
                    triple_store_serializer = TripleStoreSerializer(
                        data=request.DATA)
                    if triple_store_serializer.is_valid():
                        file_shp = self.save_shp(request.FILES, self.request.user)
                        save_ckan_resource(file_shp.id, params) 
                        return process(file_shp,  params, store_in_semantic_db=True)
                    else:
                        return Response(triple_store_serializer.errors,
                                        status=status.HTTP_400_BAD_REQUEST)
                elif u'zip' in request.FILES:
                    f = get_shp_from_zip(request.FILES['zip'])
                    if f:
                        file_shape =  self.save_shp(f, self.request.user)
                        return process(file_shape, params, store_in_semantic_db=True)
                else:
                    return Response(shape_serializer.errors,
                                    status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
            else:
                return Response({'type': ['Select a valid choice!']},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'type':["This query parameter is required."]},
                            status=status.HTTP_400_BAD_REQUEST)

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
        #return Response({'url':  shape.shp.shp_name}, status=status.HTTP_200_OK)
        
        file_name = splitext(shp_name)[0]
        zip_name = settings.UPLOAD_SHAPE+'/'+file_name
        try: 
	    zip_files([shape.shp.url, 
		     shape.dbf.url,
		     shape.shx.url, 
		     shape.prj.url],
		     zip_name)
	except BadZipfile:
	    return Response({'detail': 'Bad Zip file'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return download_file_url(zip_name+'.zip')        
        
        #return download_file(zip_files([shape.shp.url, shape.dbf.url,
        #        shape.shx.url, shape.prj.url], zip_name), zip_name+'.zip')
              

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

    shp -- .shp file
    dbf -- .dbf file
    shx -- .shx file
    prj -- .prj file
    
    """
    throttle_scope = 'utility'
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        """
        Outputs a triple store format file
        """
        shape_serializer = ShapeFileSerializer(data=request.FILES)
        if shape_serializer.is_valid():
            #create tmp dir
            tmp_dir = save_shape_in_tmp_dir(
                [request.FILES['shp'], request.FILES['shx'],
                 request.FILES['dbf'], request.FILES['prj']])
            request.DATA['input_file'] = tmp_dir+request.FILES['shp'].name
            out_file_path = tmp_dir+request.FILES['shp'].name[:-4]
            out_file_path += '.'+request.DATA['format_file'].lower()
            request.DATA['output_file'] = out_file_path

            triple_store_serializer = TripleStoreSerializer(data=request.DATA)
            if triple_store_serializer.is_valid():
                params = rename_params(request.DATA.dict())
                print post_node_server(data=params, token=None,
                                       url='/convertShape')

                """
                try:
                    f = open(out_file_path)
                    file_content = f.read()
                    f.close()
                    delete_dir(tmp_dir)
                except IOError:
                    return Response({'detail': 'Server error'},
                                        status=
                                        status.HTTP_500_INTERNAL_SERVER_ERROR)
                return file_content
                """
                
                #return Response({'triple-store_url': ''},
                 #                     status=status.HTTP_200_OK)

            else:
                return Response(triple_store_serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST)
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

    def post(self, request):
        """
        Uploads a triple store file on server and store in semantic db
        ---
	#serializer: oaks_rest_api.serializers.TripleStoreSerializer	
	#omit_serializer: true	
	consumes: ["multipart/form-data"]
	parameters:
	    - name: triple-store_file
	      type: file
	      required: true	
	      paramType: form	           
        """
        
        
        create_dir(settings.UPLOAD_TRIPLE_STORE)

        #save file
        triple_store_file = request.FILES['triple-store_file']
        TripleStore.objects.create(output_file=triple_store_file,
                                   owner=self.request.user)
        #store in semantic db
        token = NodeToken.objects.create(user=self.request.user)
        params = {'filename':str(triple_store_file), 'path': settings.UPLOAD_TRIPLE_STORE }
        result = post_node_server(data=params, token=token, url='/loadTripleStore')
        
        #TODO:: handle node.js server responses
        #result = True
        #print result
        if result == True:
	  return Response({'detail':
	    'file stored in semantic db'},
	    status=status.HTTP_201_CREATED)
        else:
          return result


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
        """
        triplestore_filename = settings.UPLOAD_TRIPLE_STORE+'/'+ \
        triplestore.name+'.'+triplestore.format_file
        """
        return download_file_url(str(triplestore.output_file))
        """
        triplestore_filename = triplestore.name+'.'+triplestore.format_file
        triplestore_file = file(settings.UPLOAD_TRIPLE_STORE+'/'+
                                triplestore_filename)
        return download_file(triplestore_file, triplestore_filename)
        """

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
        if request.QUERY_PARAMS.has_key('type'):
            file_format = request.QUERY_PARAMS['type'].lower()

            if file_format == 'shp':
                shape_file_response = self.__search_shape(name)

                if isinstance(shape_file_response, ShapeFile):
                    return download_file(zip_files([
                        shape_file_response.shp.url,
                        shape_file_response.shx.url,
                        shape_file_response.dbf.url,
                        shape_file.response.prj.url],
                        name), name+'.zip')
                else:
                    return shape_file_response

            elif file_format in [v for v, t in TGEO_STORE_FORMATS]:
                file_name = name+'.'+file_format
                triple_store_response = self.__search_triple_store(file_name)
                if isinstance(triple_store_response, TripleStore):
                    try:
                        f = open(unicode(triple_store_response.output_file))
                    except IOError:
                        return Response({'detail':
                                         'File Not found in upload dir!'},
                                        status=status.HTTP_404_NOT_FOUND)
                    file_content = f.read()
                    f.close()
                    return download_file(file_content, file_name)
                else:
                    return triple_store_response

            elif file_format == 'all':
                file_list = []
                shape_file = self.__search_shape(name)
                if isinstance(shape_file, ShapeFile):
                    file_list = [shape_file.shp.url, shape_file.shx.url,
                                 shape_file.dbf.url, shape_file.prj.url]

                for v, t in TGEO_STORE_FORMATS:
                    file_name = name+'.'+v
                    triple_store_file = self.__search_triple_store(file_name)
                    if isinstance(triple_store_file, TripleStore):
                        try:
                            file_list.append(triple_store_file.output_file)
                        except IOError:
                            pass #return Response(status=status.HTTP_404_NOT_FOUND)

                if len(file_list) > 0:
                    return download_file(zip_files(file_list,
                                                          name+'_all.zip'),
                                                name+'_all.zip')
                else:
                    return Response({'detail': 'File not found'},
                                    status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({'type': ['Select a valid choice!']},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'type':["This query parameter is required."]},
                            status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, name):
        if request.QUERY_PARAMS.has_key('type'):
            file_format = request.QUERY_PARAMS['type'].lower()
            if file_format == 'shp':
                shape_file_response = self.__search_shape(name)
                if isinstance(shape_file_response, ShapeFile):
                    shape_file_response.delete()
                    return Response(status=status.HTTP_204_NO_CONTENT)
                else:
                    return shape_file_response

            elif file_format in [v for v, t in TGEO_STORE_FORMATS]:
                file_name = name+'.'+file_format
                triple_store_response = self.__search_triple_store(file_name)
                if isinstance(triple_store_response, TripleStore):
                    triple_store_response.delete()
                    return Response(status=status.HTTP_204_NO_CONTENT)
                else:
                    return triple_store_response

        else:
            return Response({'type':["This query parameter is required."]},
                           status=status.HTTP_400_BAD_REQUEST)


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
