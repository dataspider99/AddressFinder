from HTMLSearch import HTMLSearch
from numpy.core.defchararray import endswith

class XpathSearch(HTMLSearch):
    train_data = {}
    patterns = ["text()[contains(translate(.,'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'{{{index}}}')]",
                    "contains(translate(@alt, 'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'), '{{{index}}}')",
                    "contains(translate(@title, 'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'), '{{{index}}}')"
                    ]
    social_site = ["facebook.com","linkedin.com","plus.google.com ","pinterest.com","twitter.com"\
                   ,"flickr.com","livejournal.com","badoo.com","reddit.com"]
            
    def __init__(self,html_path=None,url=None,html_string=None,training_set= {},**kwrgs):
        
        if (not training_set) and (not kwrgs):
            raise Exception("Require a Dictionary for training")
        if not training_set:
            self.train_data = kwrgs
        else:
            self.train_data = training_set
        self.verify_train_data() 
        super(XpathSearch,self).__init__(html_path,url,html_string)
        
        
    def get_xpath_page(self, attribute_priority_list = None):
        if attribute_priority_list and isinstance(attribute_priority_list,list):
            self.priority_key_list = attribute_priority_list
        accurate_xpaths = []
        xpaths = self.get_xpaths_page()
        for key,values in xpaths.items():
            if "values" in key:
                continue
            total_values = len(values)
                
            for value in values:
                    if not value.endswith("@alt"):
                        value = value+"/text()" 
                    output_data = [field.strip().upper() for field in self.tree2.xpath(value)]
                    matching_nodes = len(output_data)
                    xpaths[key+"_values"] = [field.strip().upper() for field in xpaths[key+"_values"]]
                    
                    if set(xpaths[key+"_values"]).issubset(set(output_data)):
                        if total_values > 1:
                            confidence = (len(xpaths[key+"_values"])*100)/len(set(output_data))
                        else:
                            confidence = 100
                        accurate_xpaths.append({key:value,"confidence":confidence,"nodes":matching_nodes})
                    elif total_values == 1:
                        accurate_xpaths.append({key:value,"confidence":50,"nodes":matching_nodes})
        return accurate_xpaths
    def get_xpaths_page(self):
        xpaths = {}
        for key,values in self.train_data.items():
            elems = self.getsimilar_elem(values)
            node_infos = self.get_details_parent_child(elems)
            xpaths[key] = self.get_new_xpaths(node_infos)
            xpaths[key+"_values"] = values
        return xpaths
    
    def getsimilar_elem(self,keywords):
        patterns = self.patterns
        xpaths = [pattern.format(index=index) for index, kw in enumerate(keywords) for pattern in patterns]
        conditions = ' or '.join(xpaths).format(*map(str.upper, keywords))
        xpath = "//*[{}]".format(conditions)
        elems = self.tree2.xpath(xpath)
        try:
            if not elems:
                raise Exception("NO such words "+str(keywords) + "found on the page")
        except:
            pass
        return elems
    
    def verify_train_data(self):
        for key,value in self.train_data.items():
            if isinstance(value,str) or isinstance(value,int):
                value = str(value).strip()
                value = [value]
            if isinstance(value,list):
                value = [str(val).strip() for val in value]
            self.train_data[key] = value