#!/usr/bin/env python
# -*- coding: utf-8 -*-
from HTMLSearch import HTMLSearch
from tld import get_tld
import re 
from readability import Document
from urllib.parse import urljoin

class TextSearch(HTMLSearch):
    """
    Search Text, Url, Image  Data From HTML Page
    """
    text_xpath = "//text()[not(parent::style) and not(parent::script)]"   
    urls_xpath = '//a[@href!="" and not(contains(@href,"javascript:")) and not(starts-with(@href,"#"))]/@href|//iframe/@src|//frame/@src'
    text_url_xpath = '//text()[not(parent::style) and not(parent::script)]|//a[@href!="" and not(contains(@href,"javascript:")) and not(starts-with(@href,"#")) and starts-with(@href,"http")]/@href'
    image_xpath = '//img[@src!="" and not(contains(@src,"javascript:")) and not(starts-with(@src,"#"))]/@src'
    
    extra_space = re.compile(r"[\s\t\r\n]{2,}")
    specialcharacter = re.compile(r"[^\w]+")
    
    social_media = ["youtube.com","facebook.com","linkedin.com",'twitter.com','tumblr.com','pinterest.com','plus.google.com','reddit.com','instagram.com','stumbleupon.com','flickr.com']
    search_engines = ["amazon.com","amazon.in","bigbasket.com","google.co.in","google.co.uk","googleusercontent.com","google.com","youtube.com","bing.com"]
    
    text = None
    domain = None
    url_pattern = re.compile("^(?:https?:\/\/)?(?:www\.)?([^\/]+)")
    
    def __init__(self,html_path=None,url=None,html_string=None):
        super(TextSearch,self).__init__(html_path,url,html_string)
    
    def domain_finder(self,url):
        try:
            domain = get_tld(url)
        except:
            try:
                domain = self.url_pattern.findall(url,re.I)[0]
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
    
    def get_urls_page(self,baseurl=None):
        _urls = list(set(self.get_data_page(self.urls_xpath)))
        _urls2 = [url.replace('/url?q=','').split("&")[0] for url in _urls if url.startswith('/url?q=')]
        urls = _urls + _urls2
        if not baseurl:
            return urls
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
                if domain.lower() == self.domain_finder(url):
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
            text = "\n".join(str(text))
        self.text = self.extra_space.sub(" ",str(text))
        #self.text = self.specialcharacter.sub(" ",text)
        return self.text
    
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
        
    def page_summary(self):
        doc = Document(self.respone_html)
        return doc.summary(html_partial=True)
    
    def page_title(self):
        doc = Document(self.respone_html)
        return doc.title()
        
    