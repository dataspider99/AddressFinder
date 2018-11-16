import requests
from lxml import html
from urllib.parse import urljoin
from flask import Flask
from testmachine import main
from ProductTrials import main as productdetail
from flask import jsonify
from flask_caching import Cache
from flask_cors import CORS

def search_term(term="NCT02633111",url=None):
    urlr = url if url else "https://clinicaltrials.gov/ct2/results?cond=&term="+term
    url = urljoin("https://clinicaltrials.gov/ct2/results",urlr)
    response = requests.get(url)
    if response.status_code not in [200,302]:
        raise Exception("Got a response code which is not handled: {}".format(response.status_code))
    return response.text

def get_term_list(text):
    htmlobj = html.fromstring(text)
    all_products = htmlobj.xpath("//table[@id='theDataTable']//td/a[@title]/@href")
    return all_products

def clean_details(item):
    for key,value in item.items():
        item[key] = ", ".join([detail.strip() for detail in value if detail.strip()]).strip()
    print(item)
    return item

def get_product_details(text):
    item = {}
    htmlobj = html.fromstring(text)
    item["Name"] = htmlobj.xpath("//h1/text()")
    item["NCT"] = htmlobj.xpath("(//td/a[@class='study-link']/text())[1]")
    item["StydyType"] = htmlobj.xpath("//*[contains(text(),'Study Type')]/../..//td[@headers='studyInfoColData']/text()")
    item["Sponsor"] = htmlobj.xpath("//*[@id='sponsor']/text()")
    item["Collabrators"] = htmlobj.xpath("//div[contains(text(),'Collaborator')]/following-sibling::div[contains(@id,'sponsor')]/text()")
    item["Status"] = htmlobj.xpath("//div[contains(@class,'recruiting-status')]/text()")
    item["TID"] = htmlobj.xpath("//span[contains(text(),'Study Start')]/../following-sibling::td/text()")
    item["PCD"] = htmlobj.xpath("//span[contains(text(),'Primary Completion Date')]/../following-sibling::td/text()")
    item["TCD"] = htmlobj.xpath("//span[contains(text(),'Study Completion Date')]/../following-sibling::td/text()")
    item["Enrollment"] = htmlobj.xpath("//span[contains(text(),'Enrollment')]/../following-sibling::td/text()")
    item["Institute"] = htmlobj.xpath("//div[@id='responsibleparty']/text()")
    item["Indication"] = htmlobj.xpath("//td[@class='body3'][1]/span/text()")
    return item

def main(term):
    result = []
    response = search_term(term=term)
    all_products = get_term_list(response)
    for product in all_products:
        response = search_term(url=product)
        item = clean_details(get_product_details(response))
        item["url"] = product
        result.append(item)
    return result
        
app = Flask(__name__)
cache = Cache(app,config={'CACHE_TYPE': 'simple'})
cache.init_app(app)
CORS(app)
@app.route('/')
def hello_world():
    return 'Hello, World!'

        
@app.route('/trial/<name>')
@cache.cached(timeout=50000)
def product(name):
    try:    
        return jsonify(main(name))
    except Exception as Ex:
        return jsonify({"error":str(Ex)})
        
if  __name__=='__main__':
    app.run(port=5555,threaded=True)