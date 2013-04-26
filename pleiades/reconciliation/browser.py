import re

import simplejson

from Products.CMFCore.utils import getToolByName
from zope.publisher.browser import BrowserPage

try:
    import Missing
    mv = Missing.Value
except ImportError:
    mv = None

def catalog_geometry(catalog, brain):
    zg = brain.zgeo_geometry
    if zg in (mv, None):
        return None
    else:
        idx_data = catalog.getIndexDataForRID(brain.getRID())
        precision = idx_data.get('location_precision')
        relation = {}
        if 'rough' in precision:
            relation.update(relation='relates')
        return dict(zg.items() + relation.items())


class ReconciliationEndpoint(BrowserPage):

    def relPath(self, m, path):
        return '/'.join(path.split('/')[m:])

    def __call__(self):
        catalog = getToolByName(self.context, 'portal_catalog')
        url = getToolByName(self.context, 'portal_url')
        portal_path = url.getPortalObject().getPhysicalPath()
        m = len(portal_path)
       
        form = self.request.form
        query = form.get('query')
        limit = int(form.get('limit', 20))
        if limit > 20: limit = 20
        type = form.get('type')
        
        # Experimental spatial search
        spatial = form.get('bbox') # or form.get('near')

        assert (query or spatial) is not None, "No query"

        query = re.sub(r'\([\.\w]+\)', r'*', query)
        query = re.sub(r'^[^"\w*-]', '', query)
        query = re.sub(r'[^"\w*-]$', '', query)
        data = dict(SearchableText=query)

        if type:
            data['portal_type'] = [type.capitalize()]
        else:
            data['portal_type'] = ['Location', 'Name', 'Place']

        if spatial:
            coords = map(float, spatial.split(","))
            if 'bbox' in form.keys():
                qcoords = coords
                qrange = 'intersection'
            # TODO: get bugs out of Pleiades spatial index before we 
            # turn this option back on.
            #elif 'near' in form.keys():
            #    qcoords = (coords, )
            #    qrange = 'nearest'
            data['where'] = {'query': qcoords, 'range': qrange}

        try:
            if limit:
                data['sort_limit'] = limit
                hits = catalog.searchResults(data)[:limit]
            else:
                hits = catalog.searchResults(data)
        except Exception, e:
            self.request.response.setStatus(500)
            self.request.response.setHeader('Content-Type', 'text/plain')
            return str(e) + "\n"
            
        result = [dict(
                    id=self.relPath(m, b.getPath()), 
                    name=b.Title,
                    description=b.Description,
                    type=b.portal_type,
                    geometry=catalog_geometry(catalog, b),
                    ) for b in hits]
        self.request.response.setStatus(200)
        self.request.response.setHeader('Content-Type', 'application/json')
        body = simplejson.dumps(dict(result=result)) + "\n"
        return body

