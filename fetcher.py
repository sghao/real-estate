import sys
import httplib
import urllib

request_header = {
    "Host": "210.75.213.188",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:36.0) Gecko/20100101 Firefox/36.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Referer": "http://210.75.213.188/shh/portal/bjjs2016/audit_house_list.aspx",
    "Cookie": "ASP.NET_SessionId=ibvv4p45gxtnws45xtrqcufh",
    "Connection": "keep-alive",
    "Content-Type": "multipart/form-data; boundary=---------------------------11651551972007502633981174814",
    "Content-Length": "1589",
}
with open("request_body_data", "r") as f:
    data = f.read()
request_body = data

# url = "http://210.75.213.188/shh/portal/bjjs2016/audit_house_list.aspx"
host = "210.75.213.188:80"
path = "/shh/portal/bjjs2016/audit_house_list.aspx"
conn = httplib.HTTPConnection(host)
conn.request("POST", path, request_body, request_header)
response = conn.getresponse()
print response.status, response.reason
data = response.read()
print data
conn.close()
