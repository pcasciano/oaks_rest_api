from django.conf import settings
import httplib, urllib


def post_node_server(data, token, url):
    """
    Calls node.js server app.
    """
    conn = httplib.HTTPConnection(settings.NODE_HOST, settings.NODE_PORT)
        
    data['outputFile'] = settings.BASE_STORAGE + data['outputFile']
    data['inputFile'] = settings.BASE_STORAGE + data['inputFile']
    
    post_data_encoded = urllib.urlencode(data)
    
    if token is None:
	conn.request("POST", url, post_data_encoded)
    else:
	headers = {"Authorization" : "Token %s" % token}
        conn.request("POST", url, post_data_encoded, headers)	
    """
    if url is '/loadShape': 
      post_data_encoded = urllib.urlencode(data)
    else:
      post_data_encoded = data

    if token is None:
      conn.request("POST", url, post_data_encoded)
    else:
      headers = {"Authorization" : "Token %s" % token}
      conn.request("POST", url, post_data_encoded, headers)
    
    """
   
   
    response = conn.getresponse()
    data = {
      'details': response.read(),
      'status': response.status
      }
    #data = response.read()
    #data = response.getheaders()
    conn.close()   
    return data
