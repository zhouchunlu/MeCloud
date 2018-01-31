import httplib
import traceback
cookie = 'u="12345678910"'
# base = 'localhost'
base = 'api.videer.net'
path = '/1.0/config/createConfig'
body = '{"id":"59f2de31ca71437b4ee9edbc"}'


try:
    header = {'Cookie': cookie, 'X-MeCloud-Debug': 1}
    print header
    httpClient = httplib.HTTPConnection(base, 80, timeout=30)
    httpClient.request("GET", path,body, header)

    response = httpClient.getresponse()
    print response.status
    print response.reason
    print response.read()
    # print response.msg
    # print response.getheaders()
except Exception, e:
    print e
    msg = traceback.format_exc()
    print msg
finally:
    if httpClient:
        httpClient.close()
