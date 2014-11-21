"""TGeo code for triplegeo-service utilization"""
from oaks_rest_api.models import TGEO_STORE_FORMATS
import re


def rename_params(params):
    """
    rename triple store params (triplegeo configs)

    all configs are in params dict.
    Available formats are .rdf, .ttl, .nt, .n3.
    """
    def to_camelcase(s):
        """
        matching all alphanumeric characters,
        and making the first alphabet uppercase
        """
        return re.sub(r'(?!^)_([a-zA-Z])', lambda m: m.group(1).upper(), s)


    #change some params names to make them understandable to triplegeo
    for k, v in params.items():
        if '_' in k:
            params[to_camelcase(k)] = v
            params.pop(k)
          
    params['job'] = 'file'
    params['format'] = [t for v, t in TGEO_STORE_FORMATS if
                             v == params['formatFile']][0] #TODO::controllo su formato valido!
    file_extension = '.'+params['formatFile'].lower()
    params.pop('formatFile')
    
    if params.has_key('typeWkt'):
      params['type'] = params['typeWkt']
      params.pop('typeWkt')
    else:
      params['type'] = 'point'
  
    if params.has_key('classStore'):
      params['class'] = params['classStore']
      params.pop('classStore')
    else:
      params['class'] = ''
      
    params['nsPrefix'] = ''

    return params




def get_tgeo_exception(html):
    """
    grabs triplegeo error response
    """
    pos = html.find('Caused by:</h3><pre>')
    pos1 = html.find('\n', pos)
    return html[pos+20: pos1]
