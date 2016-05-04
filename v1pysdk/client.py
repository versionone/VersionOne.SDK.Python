import logging
import urllib2
from urllib2 import Request, HTTPError, HTTPBasicAuthHandler, HTTPCookieProcessor
from urllib import urlencode
from urlparse import urlunparse, urlparse

try:
    from xml.etree import ElementTree
    from xml.etree.ElementTree import Element
except ImportError:
    from elementtree import ElementTree
    from elementtree.ElementTree import Element

AUTH_HANDLERS = [HTTPBasicAuthHandler]

try:
    from ntlm.HTTPNtlmAuthHandler import HTTPNtlmAuthHandler
except ImportError:
    logging.warn("Windows integrated authentication module (ntlm) not found.")
else:
    class CustomHTTPNtlmAuthHandler(HTTPNtlmAuthHandler):
        """ A version of HTTPNtlmAuthHandler that handles errors (better).

            The default version doesn't use `self.parent.open` in it's
            error handler, and completely bypasses the normal `OpenerDirector`
            call chain, most importantly `HTTPErrorProcessor.http_response`,
            which normally raises an error for 'bad' http status codes..
        """

        def http_error_401(self, req, fp, code, msg, hdrs):
            response = HTTPNtlmAuthHandler.http_error_401(self, req, fp, code, msg, hdrs)
            if not (200 <= response.code < 300):
                response = self.parent.error(
                    'http', req, response, response.code, response.msg,
                    response.info)
            return response


    AUTH_HANDLERS.append(CustomHTTPNtlmAuthHandler)


class V1Error(Exception): pass


class V1AssetNotFoundError(V1Error): pass


class V1Server(object):
    "Accesses a V1 HTTP server as a client of the XML API protocol"
    def __init__(self, address="localhost", instance="VersionOne.Web", username='', password='', scheme="http",
                 instance_url=None, logparent=None, loglevel=logging.ERROR):
        if instance_url:
            self.instance_url = instance_url
            parsed = urlparse(instance_url)
            self.address = parsed.netloc
            self.instance = parsed.path.strip('/')
            self.scheme = parsed.scheme
        else:
            self.address = address
            self.instance = instance.strip('/')
            self.scheme = scheme
            self.instance_url = self.build_url('')

        modulelogname = 'v1pysdk.client'
        logname = "%s.%s" % (logparent, modulelogname) if logparent else None
        self.logger = logging.getLogger(logname)
        self.logger.setLevel(loglevel)
        base_url = self.build_url('')
        self.http_client = HttpClient(base_url, username, password)

    def build_url(self, path, query='', fragment='', params=''):
        "So we dont have to interpolate urls ad-hoc"
        path = self.instance + '/' + path.strip('/')
        if isinstance(query, dict):
            query = urlencode(query)
        url = urlunparse((self.scheme, self.address, path, params, query, fragment))
        return url

    def __handle_non_xml_response(self, body, exception, msg, postdata):
        if exception.code >= 500:
            # 5XX error codes mean we won't have an XML response to parse
            self.logger.error("{0} during {1}".format(exception, msg))
            if postdata is not None:
                self.logger.error(postdata)
            raise exception

    def __handle_http_exception(self, exception, document, body):
        if exception:
            exception.xmldoc = document
            if exception.code == 404:
                raise V1AssetNotFoundError(exception)
            elif exception.code == 400:
                raise V1Error('\n' + body)
            else:
                raise V1Error(exception)

    def __parse_xml(self, body, exception):
        if exception:
            self.__handle_non_xml_response(body, exception, '', postdata=None)
        document = ElementTree.fromstring(body)
        self.__handle_http_exception(exception, document, body)
        return document

    def get_asset_xml(self, asset_type_name, oid, moment=None):
        path = '/rest-1.v1/Data/{0}/{1}/{2}'.format(asset_type_name, oid,
                                                    moment) if moment else '/rest-1.v1/Data/{0}/{1}'.format(
            asset_type_name, oid)
        url = self.build_url(path)
        exception, body = self.http_client.get(url)
        return self.__parse_xml(body, exception)

    def get_query_xml(self, asset_type_name, where=None, sel=None):
        path = '/rest-1.v1/Data/{0}'.format(asset_type_name)
        query = {}
        if where is not None:
            query['Where'] = where
        if sel is not None:
            query['sel'] = sel
        url = self.build_url(path, query)
        exception, body = self.http_client.get(url)
        return self.__parse_xml(body, exception)

    def get_meta_xml(self, asset_type_name):
        path = '/meta.v1/{0}'.format(asset_type_name)
        url = self.build_url(path)
        exception, body = self.http_client.get(url)
        return self.__parse_xml(body, exception)

    def execute_operation(self, asset_type_name, oid, opname):
        path = '/rest-1.v1/Data/{0}/{1}'.format(asset_type_name, oid)
        query = {'op': opname}
        url = self.build_url(path, query)
        exception, body = self.http_client.post(url, postdata={})
        return self.__parse_xml(body, exception)

    def get_attr(self, asset_type_name, oid, attrname, moment=None):
        path = '/rest-1.v1/Data/{0}/{1}/{3}/{2}'.format(asset_type_name, oid, attrname,
                                                        moment) if moment else '/rest-1.v1/Data/{0}/{1}/{2}'.format(
            asset_type_name, oid, attrname)
        url = self.build_url(path)
        exception, body = self.http_client.get(url)
        return self.__parse_xml(body, exception)

    def create_asset(self, asset_type_name, xmldata, context_oid=''):
        body = ElementTree.tostring(xmldata, encoding="utf-8")
        query = {}
        if context_oid:
            query = {'ctx': context_oid}
        path = '/rest-1.v1/Data/{0}'.format(asset_type_name)
        url = self.build_url(path, query)
        exception, body = self.http_client.post(url, body)
        return self.__parse_xml(body, exception)

    def update_asset(self, asset_type_name, oid, update_doc):
        newdata = ElementTree.tostring(update_doc, encoding='utf-8')
        path = '/rest-1.v1/Data/{0}/{1}'.format(asset_type_name, oid)
        url = self.build_url(path)
        exception, body = self.http_client.post(url, newdata)
        return self.__parse_xml(body, exception)

    def get_attachment_blob(self, attachment_id, blobdata=None):
        path = '/attachment.v1/{0}'.format(attachment_id)
        #TODO: post or get?
        exception, body = self.__http_get(path)
        if exception:
            raise exception
        return body

    set_attachment_blob = get_attachment_blob


class HttpClient(object):
    def __init__(self, base_url, username, password):
        password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
        password_manager.add_password(None, base_url, username, password)
        handlers = [HandlerClass(password_manager) for HandlerClass in AUTH_HANDLERS]
        self.opener = urllib2.build_opener(*handlers)
        self.opener.add_handler(HTTPCookieProcessor())

    def get(self, url):
        try:
            request = Request(url)
            request.add_header("Content-Type", "text/xml;charset=UTF-8")
            response = self.opener.open(request)
            body = response.read()
            return (None, body)
        except HTTPError, e:
            if e.code == 401:
                raise
            body = e.fp.read()
            return (e, body)

    def post(self, url, postdata):
        try:
            if isinstance(postdata, dict):
                postdata = urlencode(postdata)
            request = Request(url, postdata)
            request.add_header("Content-Type", "text/xml;charset=UTF-8")
            response = self.opener.open(request)
            body = response.read()
            return (None, body)
        except HTTPError, e:
            if e.code == 401:
                raise
            body = e.fp.read()
            return (e, body)
