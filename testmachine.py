from KEAPSearch import KeapSearch
import json
from HTMLSearch import BlankResponse
import urllib.parse
from yahoofinancials import YahooFinancials
import re
from _ast import keyword
import requests
from lxml import html
import twitter
from twitter.api import TwitterError

headers = {
        'user-agent': 'user-agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.79 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'upgrade-insecure-requests': '1',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8'
    }

AMAZON_BASE_URL ="https://www.amazon.co.uk"

def collect_twitter(name):
    api = twitter.Api(consumer_key='a3zVDSqxx3mWleIcBHxxoTZ4f',
                      consumer_secret='6YICcq9UwDA27QLTIj5suj4hCgeSiSM6HWXz5hiNKWxd1kEZMD',
                      access_token_key='65569416-1UbhGclRmQVtA7VYUf1NZbBgLnbsnZrKIki16hxnS',
                      access_token_secret='RORQ5yImEFQ3OqPsi9h448dtHktH6EcPvy1w04dCDYSQ2')
    try:
        return dict( (key,value) for key,value in api.GetUser(screen_name=name).AsDict().items() if not "profile" in key)
    except TwitterError as Ex:
        return {"error":str(Ex)}

def collect_facebook(url="https://www.facebook.com/LoBrosLivingDrinks"):
    response = requests.get(url)
    xpathObj = html.fromstring(response.text)
    try:
        return {"facebook_follower":xpathObj.xpath("//div[@class='_4bl9']/div/text()")[1].split()[0],"facebook_likes": xpathObj.xpath("//span[@id='PagesLikesCountDOMID']/span/text()")[0]}
    except:
        return {"facebook_follower":"","facebook_likes":""}

def collect_instagram(url="http://www.instagram.com/appyfooddrinks"):
    response = requests.get(url)
    xpathObj = html.fromstring(response.text)
    description = " ".join(xpathObj.xpath("//meta[@name='description']/@content"))
    if description:
        splited_description = description.split()
        return {"instagram_follower": splited_description[0],"instagram_following":splited_description[2],"instagram_posts":splited_description[4]}
    return {}

def collect_search_urls_stats(urls,search,keyword = None):
    domain_info = {}
    init_count = 2
    if keyword:
        keyword = keyword.split()
    
    for url in urls:
        domain = search.domain_finder(url)
        if domain and domain not in search.search_engines and 'google' not in domain and 'wikipedia' not in domain:
            for key in keyword: 
                if key in domain:
                    init_count = init_count+3
            if domain_info.get(domain,False):
                domain_info[domain]["urls"].append(url)
                domain_info[domain]["count"]+=1
            else:
                domain_info[domain]={"urls":[url],"count":init_count}
            init_count = 1
    return domain_info

def choose_domain(domain_info):
    maxc = 0
    urls = []
    domain = ""
    for key,value in domain_info.items():
        if value['count'] > maxc:
            maxc = value['count']
            urls = value['urls']
            domain = key
    return maxc,urls,domain
    
def finance_detail(symbol):
    data = {}
    financials = YahooFinancials(symbol.strip())
    try:
        data["Market"] =  financials.get_financial_stmts('quarterly', 'balance')
    except:
        data["Market"] = {}
    try:
        data["MarketCap"] = financials.get_market_cap()
    except:
        data["MarketCap"] = None
    try:
        data["BurnRate"] = financials.get_cost_of_revenue()
    except:
        data["BurnRate"] = None
    try:
        data["Cash"] = list(data["Market"]['balanceSheetHistoryQuarterly'][symbol.strip()][0].values())[0].get("cash",0)
    except:
        data["Cash"] = None
    return data

def create_key(url):
    key = url.split('/')[-1]
    if not key:
        key = url.split('/')[-2]
    key = re.sub("\.[\w]+", "", key)
    return key

def filter_url(url,domain):
    domain_length = len(domain)
    len_url= len(url)
    if len_url - domain_length <=13:
        return url,"about"
    keywords = ["news","contact","about","index","product","headquater","company","leader","partner","location"]
    keywords = ["contact","headquater"]
    key = create_key(url)
    for keyword in keywords:
        if keyword in url: 
            if '#' in url:
                return None,None
            if len(key.replace("-","")) < 15:
                return url,keyword
            continue
    return None,None

def amazon_check(url):
    response = requests.get(url,headers=headers)
    xpathObj = html.fromstring(response.text)
    result = xpathObj.xpath("//*[@id='noResultsTitle']/text()")
    if result:
        return False
    else:
        return True

def ebay_check(url="https://www.ebay.co.uk/sch/i.html?_from=R40&_trksid=m570.l1313&_nkw=vithit"):
    response = requests.get(url,headers=headers)
    xpathObj = html.fromstring(response.text)
    result = xpathObj.xpath("//span[@class='rcnt']/text()| //h1[@class='srp-controls__count-heading']/text()")
    result = "".join(result).strip().replace(",","").replace("results","").replace("result","")
    if int(result):
        return True
    else:
        return False

def ocado_check(url):
    response = requests.get(url,headers=headers)
    xpathObj = html.fromstring(response.text)
    result = xpathObj.xpath("//p[@class='hd-searchTermCorrection__noResultsFoundMessage']")
    if result:
        return False
    else:
        return True

def nyse(company):
    try:
        search = KeapSearch(url='https://www.nasdaq.com/aspx/symbolnamesearch.aspx?q='+company)
        symbol = search.get_text_page().split("\n")[0]
        symbol = symbol.split("|")[0]
        if symbol:
            return symbol,finance_detail(symbol)
    except BlankResponse:
        pass
    return company,{}
        
def main(orikeyword):
    print(collect_twitter(create_key("https://twitter.com/lifehousetonics")))
    keyword= urllib.parse.quote_plus(orikeyword)
    #symbol, finance = nyse(keyword) 
    search = KeapSearch(url="https://www.google.co.uk/search?client=ubuntu&channel=fs&gbv=2&ei=XYLAW67eGYP3rQH1sILwBQ&q="+keyword+"+drinks&oq="+keyword+"+drinks")
    urls = search.get_urls_page()
    domain_info = collect_search_urls_stats(urls, search,re.sub("[^\w\s]+","",orikeyword.lower()))
    
    _,urls,domain = choose_domain(domain_info)
    
    all_urls = []
    detail = {}
    detail["brand"] = orikeyword
    detail["name"] = search.page_title()
    detail["domain"] = domain
    detail["email"] = []
    detail["social"] = {}
    
    for url in set(urls):
        response = search.process_url(url)
        search.update_response(response)
        detail["email"]+=search.get_emails_page()
        all_urls+=search.get_urls_page(url)['internal']
    

    #detail["symbol"] = symbol
    for url in set(all_urls):
        url,keyname = filter_url(url.lower(),domain)
        if not url:
            continue
        try:
            response = search.process_url(url)
        except:
            continue
        
        search.update_response(response)
        detail["email"]+=search.get_emails_page()
        detail["social"] = search.social_sites_url_page()
        if not detail.get(keyname,None):    
            detail[keyname] = [{url:re.sub('<.*?>','',search.page_summary())}]
        else:
            detail[keyname].append({url:re.sub('<.*?>','',search.page_summary())})
    #detail["finance"] = finance
    detail["email"] = "\n".join(list(set(detail["email"])))
    detail["headquater"] = detail.get("contact","")
    twitter = detail["social"].get("twitter.com",None)
    facebook = detail["social"].get("facebook.com",None)
    instagram = detail["social"].get("instagram.com",None)
    if twitter:
        detail.update(collect_twitter(create_key(twitter[0])))
        detail["headquater"] = detail.get("location",detail["headquater"])
    detail["launch"] = detail.get("created_at","")
    if facebook:
        detail.update(collect_facebook(facebook[0]))
    if instagram:
        detail.update(collect_instagram(instagram[0]))
    return detail

if __name__=='__main__':
    companies = [   
            "Aqua Carpatica",
            "Strathmore",
            "Coldpress",
            "Vithit",
            "Little Miracles",
            "Life Tonics",
            "Love Kombucha",
            "Moka Instinct",
            "Monte Rosso",
            "Stur",
            "True Nopal",
            "A Little More",
            "Aloe 24/7",
            "Appy Food & Drinks",
            "Aqua Coco",
            "Aspire Beverages",
            "Aymes",
            "Beanies Flavour Coffee",
            "BEAUTY & GO",
            "Bella Berry",
            "Benefit Drinks",
            "Botonique / Genius",
            "Brew Tea Co",
            "Cafféluxe (Private Level)",
            "Captain Kombucha",
            "ChariTea",
            "Coco Indulgence",
            "CocoPro",
            "CoCos-Pure",
            "Cornish Tea",
            "Cuppanut",
            "Cute",
            "Dalston's",
            "Dandy Lion Tea",
            "Dash Water",
            "Drink Me Chai",
            "Elite Proganic",
            "Erbology",
            "Firefly",
            "Four Sigmatic",
            "Frutree",
            "Fuel 10K",
            "GET MORE",
            "HEY LIKE WOW",
            "I am SuperJuice",
            "Iconiq",
            "J. F. Rabbit's",
            "Jools",
            "Just Bee",
            "Karma Cola / Gingerella",
            "Lemonaid+",
            "Dr. Stuart's",
            "Frozen Bean Frappe Blends",
            "Icelandic Glacial",
            "Jax Coco",
            "Limation",
            "Limitless",
            "Limonitz",
            "Mansi",
            "Matchabar",
            "Meta Matcha",
            "Modern Alkeme",
            "Monfefo",
            "Pure Bio",
            "Muso",
            "Nix and Kix",
            "No Fear",
            "Nood",
            "Nossa!",
            "Nualtra",
            "Nutristrength",
            "Oteas Oteatox",
            "PomeGreat",
            "Purearth",
            "Purition",
            "Qcumber",
            "Royal Chai",
            "Sandow's",
            "Sekforde",
            "Simplee Aloe",
            "Soda Folk",
            "SUNPRIDE",
            "Tåpped",
            "Tea Huggers",
            "TG",
            "Thai Coco",
            "The Little Coffee Bag Co.",
            "The London Essence Co.",
            "The Organic Protein Company",
            "The Protein Works",
            "TrueStart",
            "Turmerlicious",
            "Tymbark Next",
            "Ugly",
            "Vivid Water in a Box",
            "Wow",
            "Wunder Workshop",
            "Yuyo",
            "Califia Farms",
            "Nrich",
            "Trederwen Essence",
            "Moshlings Magic Water",
            "Aartizen Wellness Within",
            "Alfresco",
            "Aloha",
            "Go Splash",
            "Misfit",
            "NUVA",
            "OVIO InFusion",
            "POW",
            "Tassimo",
            "The Bees Knees",
            "V12",
            "Wonjo",
            "Almond Breeze / Blue Diamond",
            "Garant",
            "Smarty",
            "Bloomy Drinks Life",
            "Le Autentiche di Bevi Più Naturale",
            "Caliente",
            "Mana organic",
            "My living water",
            "K-Pop",
            "Black Castle Berry",
            "Three Cents Aegean Tonic",
            "Ekobryggeriet",
            "Hotel Chocolat",
            "AMC - Beauty & go skin",
            "Brämhults Balans",
            "Vegesentials FibreWater",
            "Positivitea",
            "Oshee Vitamin water",
            "Rabenhorst, Rotbäckchen Immunstark",
            "Vitz Drink",
            "Nestle Meritene",
            "Healthy People",
            "Orkla",
            "PHD",
            "Seedlip",
            "Jarr Kombucha",
            "Double Dutch",
            "Daylesford",
            "Elderbrook",
            "Zeo",
            "Stowford Press",
            "Grenade",
            "Easycoffee"
                    ]
    data = {"description":"Not Available",
            "favourites_count": "",
            "followers_count":"",
            "friends_count":"",
            "instagram_follower":"",
            "instagram_following":"",
            "facebook_follower":"","facebook_likes":""}
    csvfile = open("brand2.csv","w")
    csvfile.write("Brand,Name,Domain,Headquater,Emails,Launch,Description,Twitter_Favourite,Twitter_Follower,\
                Twitter_Friend,Instagram_Follower,Instagram_Following,Facebook_Follower,Facebook_Likes,\
                Amazon,Ebay,Ocado\n ")
    for company in companies:
        url = "https://www.ocado.com/search?entry="+company
        data["ocado"] = ocado_check(url)
        
        url = "https://www.ebay.co.uk/sch/i.html?_from=R40&_trksid=m570.l1313&_nkw="+company
        data["ebay"] = ebay_check(url)
        
        url = AMAZON_BASE_URL + '/s/ref=nb_sb_noss_2?url=search-alias%3Daps&field-keywords=' + \
        company + '&rh=i%3Aaps%2Ck%3A' + company
        data["amazon"] = amazon_check(url)
        try:
            data.update(main(company))
            csvfile.write('"{brand}","{name}","{domain}","{headquater}","{email}","{launch}","{description}","{favourites_count}","{followers_count}",\
                    "{friends_count}","{instagram_follower}","{instagram_following}","{facebook_follower}","{facebook_likes}",\
                    "{amazon}","{ebay}","{ocado}"\n'.format(**data))
            open("data/brand.json".format(company.replace("/","")),"a+").write(json.dumps(data)+"\n")
            data = {"description":"Not Available",
                "favourites_count": "",
                "followers_count":"",
                "friends_count":"",
                "instagram_follower":"",
                "instagram_following":"",
                "facebook_follower":"","facebook_likes":""}
        except Exception as Ex:
            print(str(Ex),company)
    csvfile.close()