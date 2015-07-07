from pymongo import MongoClient
import io
from tld import get_tld
import re
def domain_finder(self,url):
      try:
          domain = get_tld(url)
      except:
          try:
              domain = re.findall("^(?:https?:\/\/)?(?:www\.)?([^\/]+)",url,re.I)[0]
          except:
              return None
      return domain

db = MongoClient(host='23.251.145.225')
db3 = db['test2']['urls2']
db2 = db['test2']['text']
data1 = set(db3.find({},{"_id":1}))
data2 = set(db2.find({},{"_id":1}))
data3 = list(data1.intersection(data2))
stri = "\n".join(data3)
fil = io.open("file3","w",encoding='utf-8')
data4 = set()
for url in data3:
    data4.add(domain_finder(url))
print len(data4)