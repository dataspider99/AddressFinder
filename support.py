from pymongo import MongoClient
from TEXTSearch import TextSearch
from KEAPSearch import KeapSearch
from tld import get_tld
import re,io

def domainFinder(data):
    try:
        domain = get_tld(data["_id"])
    except:
        domain = re.findall("^(?:https?:\/\/)?(?:www\.)?([^\/]+)",data['_id'],re.I)
        if domain:
            domain = domain[0]
    return domain

db = MongoClient(host="23.251.145.225")
db = db['test']['urls']
fil = io.open("level2.urls","w",encoding="utf-8")
data_cur = db.find({"_id":"http://www.advsyscon.com"},{"content":1})
for data in data_cur:
    if data['content']:
        try:
            dom = TextSearch(html_string=data['content'])
        except:
            continue
        urls = dom.get_urls_page(data["_id"])
        if urls['internal']:
            try:
                urls['internal'].remove(data["_id"])
            except:
                print data["_id"]
            fil.write(u'{}\n'.format("\n".join(urls['internal'])))
        
fil.close()
    