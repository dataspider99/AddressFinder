from lxml import html
import io,time
from itertools import chain
from topia.termextract import extract
import re
from requests import Session
import sys

session = Session()

class HTMLSearch():
    extractor = extract.TermExtractor()
    
    def __init__(self,keyword_file_path=None,black_list_path=None):
        
        if not keyword_file_path:
            raise Exception("Please Specify the keyword_file_path for creating class Object")
        if not black_list_path:
            black_list_path = './black_list.txt'
        self.blacklisted = black_list_path
        try:
            self.blacklisted_keywords = map(str.upper.strip,open(self.blacklisted,'r').readlines())
        except:
            self.blacklisted_keywords = []
        self.recommended = keyword_file_path
        #self.recommend_list_keyword = open(self.recommended,'r').readlines()
    
    def index_finder(self,elem):
        child_tag = elem.tag
        parent_elem = elem.getparent()
        childs = parent_elem.getchildren()
        index = 1
        for child in childs:
            if elem == child:
                break
            if child_tag == child.tag:
                index = index + 1
        return index
    
    def get_details_parent_child(self,elements):
        elem_details = []
        for elem in elements:
            """
                @type elements:List of HtmlElement: 
                @type elem:HtmlElement:
                @return: dict
            """
            parent_elem = elem.getparent()
            child_info = self.get_element_details(elem)
            child_info['index'] = self.index_finder(elem)
            parent_info = self.get_element_details(parent_elem)
            parent_info['index'] = self.index_finder(parent_elem)
            elem_details.append({'parent':parent_info,'child':child_info,'parent_elem':parent_elem})
        return elem_details
    
    def get_element_details(self,elem):
        """
        @type elem: HtmlElement
        @return: Dict
        """
        html_id = elem.attrib['id'] if 'id' in elem.attrib else ''
        class_name = elem.attrib['class'] if 'class' in elem.attrib else ''
        alt = elem.attrib['alt'] if 'alt' in elem.attrib else ''
        title = elem.attrib['title'] if 'title' in elem.attrib else ''
        tag_name = elem.tag
        text = elem.text_content().strip()
        node_text = elem.text.strip() if elem.text is not None else ""
        return {
                u'id':unicode(html_id),
                u'class':unicode(class_name),
                u'tag':unicode(tag_name) ,
                u'text': unicode(text),
                u'nodetext':unicode(node_text),
                u'alt': unicode(alt),
                u'title': unicode(title)
            }
        
    def get_priority_key_list(self,dict_data):
        """
        @return: list
        """
        key_list = []
        dict_1 = dict((k, v) for k, v in dict_data.iteritems() if v)
        keys = dict_1.keys()
        priority_key_list = ['id','alt','title','class']
        for key in priority_key_list:
            if key in keys:
                key_list.append(key)
        return key_list
    
    def get_xpath(self,parent,parent_key,child,child_key):
        
        if parent_key and child_key:
            xpath = "//{0}(@{1},'{2}')/{3}(@{4},'{5}')/text()".format(parent['tag'],parent_key,parent[parent_key],child['tag'],child_key,child['child_key'])
        if parent_key and not child_key:
            xpath = "//{0}(@{1},'{2}')/{3}/text()".format(parent['tag'],parent_key,parent[parent_key],child['tag'])
        if not parent_key and child_key:
            xpath = "//{0}/{1}(@{2},'{3}')/text()".format(parent['tag'],child['tag'],child_key,child[child_key])                   
        
        print xpath
        return xpath
    
    def get_grand_keys(self,parent_element,grand_level=2,grand_data = {}):
        grand_info = {}
        grand_level = grand_level-1
        grand_element = parent_element.getparent()
        grand_details = self.get_element_details(grand_element)
        grand_details['index'] = self.index_finder(grand_element)
        grand_keys = self.get_priority_key_list(grand_details)
        grand_info['key'] = grand_keys
        grand_info['element'] = grand_element
        grand_info['details'] = grand_details
        grand_data[grand_level] = grand_info
        if not grand_info['key'] and grand_level and len(grand_element) and not (grand_details['tag']=='html') :
            return self.get_grand_keys(grand_element,grand_level,grand_data) 
        else:
            return grand_data
        
    def xpath_with_probability(self,parent,parent_key,child,child_key):
        if child['nodetext'] and child['text']:
            self.get_xpath(parent,parent_key,child,child_key)
        if child['nodetext'] and not child['text']:
            self.get_xpath(parent,parent_key,child,child_key)
        if not child['nodetext'] and child['text']:
            self.get_xpath(parent,parent_key,child,child_key)
    
    def get_new_xpaths(self,node_infos):
        new_xpaths = []
        print "Total Element Found : ",len(node_infos)
        
        for node_info in node_infos:
            grand_data = []
            parent = node_info['parent']
            child = node_info['child']
            
            parent_keys = self.get_priority_key_list(parent)
            child_keys = self.get_priority_key_list(child)
            
            if not parent_keys:
                print "parent keys not found , Going to upper level for keys"
                grand_data = self.get_grand_keys(node_info['parent_elem'],grand_level=2)
            
            print "Starting Xpath Generator"
            xpaths = self.xpath_generator(child,parent,child_keys,parent_keys,grand_data)    
            new_xpaths.append(xpaths)
        return new_xpaths
    
    def xpath_generator(self,child,parent,child_keys,parent_keys,grand_info):
        xpaths = []
        if grand_info:
            print "Generating Xpath on Grand Node"
            xpaths = self.create_grand_xpaths(grand_info)
        
        if xpaths:
            xpaths = self.extend_xpaths(xpaths,parent,parent_keys)
        else:
            xpaths = self.create_parent_xpaths(parent,parent_keys)
    
        xpaths = self.extend_xpaths(xpaths,child,child_keys)
        if xpaths:
            return xpaths[0]
    
    
    def create_grand_xpaths(self,grand_info):
        new_xpaths = []
        grand_dict_keys = grand_info.keys()
        sorted_keys = sorted(grand_dict_keys)
        counter = 0
        for key_seq in sorted_keys:
            if counter == 0:
                if grand_info[key_seq]['key']:
                    for key in grand_info[key_seq]['key']:
                        new_xpaths.append("//{0}[@{1}='{2}']".format(grand_info[key_seq]['details']['tag'],key,grand_info[key_seq]['details'][key]))
                    counter = counter+1
                else:
                    new_xpaths.append("//{0}[{1}]".format(grand_info[key_seq]['details']['tag'],grand_info[key_seq]['details']['index']))
                    counter = counter+1
            else:
                for xpath in new_xpaths:
                    new_xpaths.append(xpath+"//{0}[{1}]".format(grand_info[key_seq]['details']['tag'],grand_info[key_seq]['details']['index']))
                    new_xpaths.remove(xpath)
                counter = counter+1
        return  new_xpaths
                    
            
    def create_parent_xpaths(self,element,keys):
        new_xpaths = []
        if keys:
            for key in keys:
                if key != 'alt':
                    new_xpaths.append("//{0}[@{1}='{2}']".format(element['tag'],key,element[key]))
                    
        return new_xpaths
    
    def extend_xpaths(self,xpaths,element,keys):
        new_xpaths = []
        for xpath in xpaths:
            if keys:
                for key in keys:
                    if key != 'alt':
                        new_xpaths.append(xpath+"/{0}[@{1}='{2}']".format(element['tag'],key,element[key]))
                    else:
                        new_xpaths.append(xpath+"/{0}[@alt !='']/@alt".format(element['tag']))
            else:
                if 'index' in element.keys():
                    new_xpaths.append(xpath+"/{0}[{1}]".format(element['tag'],element['index']))
                else:
                    new_xpaths.append(xpath+"/{0}".format(element['tag']))
                
        return new_xpaths
            
    def get_the_matches(self,xpaths):
        xpaths = list(set(xpaths))
        data = {}
        for xpath in xpaths:
            if not xpath.endswith('@alt'):
                xpath = xpath+"/text()"
            
            data[xpath] = self.tree2.xpath(xpath)
        return data
    
    def process_the_words(self,keywordList):
        filtered_keyword = []
        extractor = extract.TermExtractor()
        for key_word in keywordList:
            key_word = key_word.strip().encode('utf-8')
            if not len(key_word) > 150:
                filtered_keyword.append(key_word)
            else:
                filter2 = extractor(key_word)
                if filter2:
                    for key_word2 in filter2:
                        filtered_keyword.append("".join(str(key_word2[0])))
        return filtered_keyword
                
            
    def black_list_filter(self,keyword_list,storeResult = True):
        fileObj = open(self.blacklisted,'a+')
        blacklisted_keywords = map(str.strip,fileObj.readlines())
        for key_word in keyword_list:
            if storeResult:
                current_keywords = "\n".join(keyword_list)
            fileObj.close()
            for ignore_word in blacklisted_keywords:
                if re.match('\\b'+key_word+'\\b',ignore_word,flags = re.I):
                    keyword_list.remove(key_word)
        fileObj.write(current_keywords)
        return keyword_list
    
    
    def get_keywords_urls(self,url_list,recommended_keywords_list):
        """
        @type: url_list:list
        @type: recommended_keywords:list
        """
        if not url_list:
            raise Exception("url_list not found")
            sys.exit()
        if isinstance(recommended_keywords_list,list):
            self.recommend_list_keyword = recommended_keywords_list
        url_responses = self.process_urls(url_list)
        detailed_urls = []
        for response in url_responses:
            info = {}
            keywords = ''
            code = response.status_code
            if code == 200:
                keywords = self.start_key_word_finder(response.text,response.url)
            info['response_code']= code
            info['url']=response.url
            info['keywords'] = keywords
            detailed_urls.append(info)
        return detailed_urls
    
    def process_urls(self,url_list,headers={'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36'}):
        counter = 0
        for url in url_list:
            counter = counter + 1
            response = session.get(url,headers = headers)
            if counter % 50 == 0:
                time.sleep(20)
            yield response
    
     
    def get_keywords_html(self,filePath,recommended_keywords):       
        with io.open("input.html","r",encoding="utf-8") as f:
            file_html = f.read()
            self.start_key_word_finder(file_html)
    
    #parser = etree.HTMLParser()
    #tree = etree.parse(StringIO(unicode(file_html)), parser=parser)
    def start_key_word_finder(self,file_html,url=''):
        tree2 = html.fromstring(file_html)
        self.tree2 = tree2
        recommend_list = self.recommend_list_keyword = map(str.upper,self.recommend_list_keyword)
        black_list = self.blacklisted_keywords = map(str.upper,self.blacklisted_keywords)
        
        
        
        patterns = ["text()[contains(translate(.,'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'{{{index}}}')]",
                    "contains(translate(@alt, 'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'), '{{{index}}}')",
                    "contains(translate(@title, 'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'), '{{{index}}}')"
                    ]
        
        keywords = map(str.strip,self.recommend_list_keyword)
        
        xpaths = [pattern.format(index=index) for index, kw in enumerate(keywords) for pattern in patterns]
        conditions = ' or '.join(xpaths).format(*map(str.upper, keywords))
        xpath = "//*[{}]".format(conditions)
        elems = tree2.xpath(xpath)
        node_infos = self.get_details_parent_child(elems)
        xpaths2 = self.get_new_xpaths(node_infos)
        words = self.get_the_matches(xpaths2)
        return list(words)
        
        
        #= print self.black_list_filter(keywords['list2'])            