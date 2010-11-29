import simplejson

from Products.CMFCore.utils import getToolByName
from zope.publisher.browser import BrowserPage


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
        assert query is not None, "No query"
        limit = int(form.get('limit', 20))
        if limit > 20: limit = 20
        type = form.get('type')

        data = dict(SearchableText=query)
        if type:
            data['portal_type'] = [type.capitalize()]
        else:
            data['portal_type'] = ['Location', 'Name', 'Place']
        if limit:
            data['sort_limit'] = limit
            hits = catalog.searchResults(data)[:limit]
        else:
            hits = catalog.searchResults(data)

        result = [dict(
                    id=self.relPath(m, b.getPath()), 
                    name=b.Title,
                    description=b.Description,
                    type=b.portal_type,
                    uid=b.UID,
                    ) for b in hits]
        self.request.response.setStatus(200)
        self.request.response.setHeader('Content-Type', 'application/json')
        body = simplejson.dumps(dict(result=result)) + "\n"
        return body

