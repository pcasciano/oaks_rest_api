Oaks Rest Api
========================


Oaks Rest Api is a Django app to provide rest api for Oaks project.


Requirements
------------

It requires geogit. Install it with:

.. code-block:: bash

  git clone http://github.com/boundlessgeo/GeoGit.git

  cd geogit/src/parent

  mvn clean install


and these python packages:
 
.. code-block:: bash

  pip install djangorestframework

  pip install django-oauth2-provider

  pip install django-rest-swagger

  pip install geogit-py



Settings
--------
- Append required apps to ``INSTALLED_APPS`` var in your **settings.py**:

        
.. code-block:: python

      INSTALLED_APPS = (
        ...
        ...
        ...
        'rest_framework',
        'rest_framework_swagger',
        'provider',
        'provider.oauth2',        
        'oaks_rest_api',
      )
 
- and add these variables in the same file:

.. code-block:: python
  
  #dirs for upload and storing files
  UPLOAD_SHAPE = '/tmp/shapes'
  UPLOAD_TRIPLE_STORE = '/tmp/triple-stores'
  
  #rest_framework config
  REST_FRAMEWORK = {

   'DEFAULT_AUTHENTICATION_CLASSES': (
    'rest_framework.authentication.BasicAuthentication',
    'rest_framework.authentication.SessionAuthentication',
    'rest_framework.authentication.OAuth2Authentication',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.BrowsableAPIRenderer',
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.XMLRenderer',
    ),
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.ScopedRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'default': '10/minute', 
        'download': '50/minute', 
        'utility': '5/minute', 
    }
  }

  #rest swagger config
  SWAGGER_SETTINGS = {
    "exclude_namespaces": [],
    "api_version": '1.0',  
    "api_path": "/",  
    "enabled_methods": [  
        'get',
        'post',
        'put',
        'patch',
        'delete'
    ],
    "api_key": '',
    "is_authenticated": False,  
     authentication,
    "is_superuser": False,  
  }
  
- Create the rest_api db tables:

.. code-block:: bash
    
    python manage.py syncdb
  
  
- Start geogit with:

.. code-block:: bash
    
    geogit-gateway
  
  


  
  
  
  
  
  