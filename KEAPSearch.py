#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
from nltk.corpus import gazetteers
import nltk
from TEXTSearch import TextSearch
import re
from PhoneReg import PhoneReg
import json
class KeapSearch(TextSearch):
    """
    Keywords, Email, Address and Xpath Finder
    """
    max_score = 0
    email = re.compile(r"(\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}\b)",re.I)
    coded_email = ""
    general_phone = ""
    address_symptoms = {'TOLL FREE':3,'Headquarter':8,'Global Headquarter':9,
                        'Telefon':3,'contact':4,'contact us':8,
                        'phone':3,'email':4,'go to us':4,'Correspondence':4,
                        'Adresse':7,'postale':6,'address':7,
                        'pin':6,'zip':6,'postal':6,'code':2,'Inc':7,
                        'tel':3,'fax':4,'post':5,'office':5,'mail':1,
                        'CORPORATE':6,'mailing':5,'PO Box':5,'Telèfon':4,
                        'Branch':5,'location':5,'helpdesk':5,'telefoon':4,
                        'offices':5, 'call':2
                        }
    keywords1 = []
    keywords2 = []
    ereg = ""
    classifier = None
    
    def __init__(self,html_path=None,url=None,html_string=None):
        self.email = re.compile(r"(\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}\b)",re.I)
        self.token = r"[\s\n\/\\,;]+|WWW\."
        #self.train_classifier()
        super(KeapSearch,self).__init__(html_path,url,html_string)
        
        
    def get_emails_page(self,reg = None,text = None):
        if not KeapSearch.ereg and reg:
            KeapSearch.ereg = re.compile(reg,re.I)
            self.email = KeapSearch.ereg
        if not text:
            text = self.get_text_page()
        return self.email.findall(text)
    
    def get_site_emails(self,domain = None):
        if domain:
            self.domain = domain
        if not self.domain:
            raise Exception("Domain not found")
        emails = self.get_emails_page()
        e_mail = {'internal':[],'external':[]}
        for email in list(set(emails)):
            if domain.upper() in email.upper():
                e_mail['internal'].append(email)
            else:
                e_mail['external'].append(email)
        return e_mail
    
    def get_phone_numbers_page(self,iso3_country = 'USA',reg = None,text = None):
        if reg and not KeapSearch.preg:
            KeapSearch.preg = re.compile(reg,re.I)
            self.preg = KeapSearch.preg
        elif PhoneReg[iso3_country]:
            self.preg = re.compile(PhoneReg[iso3_country], re.I)
        else:
            self.preg = re.compile(self.general_phone,re.I)
        if not text:
            text = self.get_text_page()
        phone_numbers = set()
        for phone in self.preg.findall(text):
            phone_numbers.add("".join(phone))
        return list(phone_numbers)
    
    
    def match_keywords_page(self,keywords,text=None):
        if not isinstance(keywords,list):
            raise Exception("match_keywords_page requires list of keywords")
        if KeapSearch.keywords != keywords:
            KeapSearch.keywords = keywords
            for keyword in KeapSearch.keywords:
                if " " in keyword:
                    KeapSearch.keywords1.append(keyword.strip().upper())
                else:
                    KeapSearch.keywords2.append(keyword.strip().upper())
        if not text:
            text = self.get_text_page_clean()
        
        tok_text = self.tokenize(text.upper())
        matches = set()
        match2 = set(tok_text).intersection(set(KeapSearch.keywords2))
        for keyword in KeapSearch.keywords1:
            if keyword in text.upper():
                matches.add(keyword)
        matches = matches.union(match2)
        return list(matches)
                
    def tokenize(self,text):
        tokens = filter(None, self.token.split(text))
        return tokens

    def similar_keywords_page(self):
        pass
    
    def find_address_page(self,domain=None):
        if domain:
            self.domain = domain
        if not self.domain:
            raise Exception("find_address_page requires domain of site")
        address1 = self.find_address_text()
        return address1
    
    def normalize_text_in_upper(self,text):
        try:
            text = unicodedata.normalize('NFC',text.upper())
        except:
            text = text.decode("utf-8").upper()
        return text
    def weight_creater(self,keys,weight):
        for key in keys:
            self.address_symptoms[key] = weight
    
    def prepare_addr_symp(self):
        site_name = self.domain.split(".")[0]
        self.address_symptoms[site_name]=10
        for country in gazetteers.words('countries.txt'):
            if country == "US":
                self.address_symptoms[country] = 20
                continue
            self.address_symptoms[country] = 20
        for city in open("cities.txt","r").readlines():
            self.address_symptoms[city.strip()] = 20
        for state in open("states.txt","r").readlines():
            self.address_symptoms[state.strip()] = 20
        emails = self.get_emails_page()
        self.weight_creater(emails,7)
        phones = self.get_phone_numbers_page()
        self.weight_creater(phones,7)
    
    def get_address_by_index(self,indexing):
        raw_add_keys = self.dict_inverter(indexing)
        #raw_add_keys.sort()
        classify = {}
        diff_address = []
        dup_index = []
        
        for raw_key in raw_add_keys:
            if list(raw_key.keys())[0] in dup_index:
                continue
            dup_index.append(list(raw_key.keys())[0])
            if list(raw_key.values())[0] not in classify.keys():
                classify[list(raw_key.values())[0]] = list(raw_key.keys())[0]
            else:
                diff_address.append(classify)
                classify = {}
                classify[list(raw_key.values())[0]]= list(raw_key.keys())[0]
        return diff_address
        
    def find_address_text(self,text=None):
        indexing = {}
        #indexing2 = {}
        self.prepare_addr_symp()
        self.max_score = sum(list(set(self.address_symptoms.values())))
        if not text:
            text = self.get_text_page()
        text = self.filtered_text(text)
        text2 = self.normalize_text_in_upper(text)

        for key in self.address_symptoms.keys():   
            keyU = self.normalize_text_in_upper(key.strip())
            index_match = self.allindices(text2,keyU)
            if index_match:
                indexing[key] = index_match
            
        #self.guess_address(indexing)
        addrs = self.get_address_by_index(indexing)
        pro = self.address_properties(addrs)
        return pro
    
    def guess_address(self,indexing):
        for key, value in indexing.items():
            if len(key) > 2 and len(value)>1:
                for i in xrange(0,len(value)-1):
                    text = self.text[value[i]:value[i+1]]
                    if len(text) < 300:
                        print (text)
                        print ("next address is: \n\n\n")
    
    def address_properties(self,addresses):
        add = []
        with open("feature.json","w") as jsonfile:
            for address in addresses:
                properties = {"weight":0,"distance":0}
                for k in address.keys():
                    properties['weight'] += self.address_symptoms[k]
                mini = min(address.values())
                maxi = max(address.values())
                properties['distance'] = maxi -mini
                properties['start'] = mini
                properties['end'] = maxi
                properties['address'] = self.text[mini-1:maxi-1]
                jsonfile.write(json.dumps((False,properties))+"\n")
                if (maxi-mini) < 20 or (maxi-mini) > 200:
                    continue
                if properties["weight"] > 25 and properties["weight"] < self.max_score:
                    add.append(properties)
        return sorted(add, key=lambda k: k['weight'],reverse=True) 
    
        
    def find_address_xpath(self):
        pass
        
    
    def allindices(self,string, sub, offset=0):
        return [m.start() for m in re.finditer(r"\b"+re.escape(sub)+r"\b", string)]
            
    def dict_inverter(self,dic):
        inverted_dic = []
        for key,values in dic.items():
            for value in values:
                inverted_dic.append({value:key})
        return inverted_dic
                
                