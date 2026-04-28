import os
from src.powerbi_client import PowerBIClient
from urllib import request, error

c = PowerBIClient()
print("Refrescando conexión local...")
print(c.refresh_connection())
port = c.local_port
if not port:
    raise SystemExit("No se detectó puerto local XMLA.")
url = f"http://localhost:{port}/xmla"

soap = '''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <Discover xmlns="urn:schemas-microsoft-com:xml-analysis">
      <RequestType>DISCOVER_PROPERTIES</RequestType>
      <Restrictions/>
      <Properties>
        <PropertyList>
        </PropertyList>
      </Properties>
    </Discover>
  </soap:Body>
</soap:Envelope>'''

req = request.Request(url, data=soap.encode('utf-8'), headers={"Content-Type": "text/xml; charset=utf-8"}, method='POST')
try:
    with request.urlopen(req, timeout=10) as resp:
        body = resp.read().decode('utf-8', errors='replace')
        print('--- RESPONSE START ---')
        print(body[:8000])
        print('--- RESPONSE END ---')
except error.HTTPError as he:
    print('HTTPError', he.code, he.reason)
    try:
        print(he.read().decode('utf-8', errors='replace'))
    except Exception:
        pass
except Exception as e:
    print('Error:', e)
