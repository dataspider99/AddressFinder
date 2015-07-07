from HTMLSearch import HTMLSearch
from tld import get_tld
import re
from urlparse import urljoin
class TextSearch(HTMLSearch):
    text_xpath = "//text()[not(parent::style) and not(parent::script)]"
    urls_xpath = '//a[@href!="" and not(contains(@href,"javascript:")) and not(starts-with(@href,"#"))]/@href|//iframe/@src|//frame/@src'
    text_url_xpath = '//text()[not(parent::style) and not(parent::script)]|//a[@href!="" and not(contains(@href,"javascript:")) and not(starts-with(@href,"#")) and starts-with(@href,"http")]/@href'
    image_xpath = '//img[@src!="" and not(contains(@src,"javascript:")) and not(starts-with(@src,"#"))]/@src'
    domain = None
    extra_space = re.compile(r"[\s\t\r\n]{2,}")
    social_media = ["google.com","facebook.com","linkedin.com",'twitter.com','tumblr.com','pinterest.com','plus.google.com','reddit.com','instagram.com','stumbleupon.com','flickr.com']
    
    def __init__(self,html_path=None,url=None,html_string=None):
        if url:
            self.domain = self.domain_finder(url)
        super(TextSearch,self).__init__(html_path,url,html_string)
    
    def domain_finder(self,url):
        try:
            domain = get_tld(url)
        except:
            try:
                domain = re.findall("^(?:https?:\/\/)?(?:www\.)?([^\/]+)",url,re.I)[0]
            except:
                return None
        return domain
    
    def get_data_page(self,xpath):
        return self.tree2.xpath(xpath)
    
    def get_text_page_clean(self):
        text = self.get_data_page(self.text_xpath)
        return self.filtered_text(text)
    
    def get_text_page(self):
        return "\n".join(self.get_data_page(self.text_xpath))
    
    def get_urls_page(self,baseurl):
        if not baseurl:
            raise Exception("baseurl not found")
        urls = list(set(self.get_data_page(self.urls_xpath)))
        site_url = baseurl
        domain = self.domain_finder(baseurl)
        if not site_url:
            return {"external":urls,"internal":[]}
        else:
            external = set()
            internal = set()
            for url in urls:
                url = urljoin(site_url,url)
                if not url.startswith("http"):
                    continue
                if domain.lower() in url.lower():
                    internal.add(url)
                else:
                    external.add(url)
            return {"external":list(external),"internal":list(internal)}
            
    
    def get_texturls_page(self):
        return self.get_data_page(self.text_url_xpath)
    
    def get_texturls_page_clean(self):
        text = self.get_data_page(self.text_url_xpath)
        return self.filtered_text(text)
    
    def find_site_url(self,urls):
        for url in urls:
            try:
                if self.domain.upper() in url.upper():
                    domain = self.domain_finder(url)
                    if domain == self.domain:
                        return url
            except:
                pass
        return None
    
    def filtered_text(self,text):
        if isinstance(text,list):
            text = "\n".join(text)
        text = self.extra_space.sub(" ",text)
        return text
    
    def social_sites_url_page(self,sites=[]):
        self.social_media = self.social_media + sites
        urls = list(set(self.get_data_page(self.urls_xpath)))
        return self.domain_maped_urls(urls, self.social_media)
    
    def get_image_urls_page(self,domains=[]):
        urls = list(set(self.get_data_page(self.image_xpath)))
        return self.domain_maped_urls(urls, domains)
    
    def domain_maped_urls(self,urls,domains):    
        site_url = self.find_site_url(urls)
        if not domains:
            return urls
        links ={}
        for url in urls:
            url = urljoin(site_url, url)
            domain = self.domain_finder(url)
            if domain in domains:
                if domain not in links.keys():
                    links[domain] = []
                links[domain].append(url)
        return links
        
    
        
    