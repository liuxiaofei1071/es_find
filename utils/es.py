import os
import json
from elasticsearch import helpers  # ES批量写入的helpers
from elasticsearch import Elasticsearch

es = Elasticsearch()

class Pagination:

    def __init__(self, page, all_count, per_num=10, max_show=11):
        # 基本的URL
        # self.base_url = request.path_info
        # 当前页码
        try:
            self.current_page = int(page)
            if self.current_page <= 0:
                self.current_page = 1
        except Exception as e:
            self.current_page = 1
        # 最多显示的页码数
        self.max_show = max_show
        half_show = max_show // 2

        # 每页显示的数据条数
        self.per_num = per_num
        # 总数据量
        self.all_count = all_count

        # 总页码数
        self.total_num, more = divmod(all_count, per_num)
        if more:
            self.total_num += 1

        # 总页码数小于最大显示数：显示总页码数
        if self.total_num <= max_show:
            self.page_start = 1
            self.page_end = self.total_num
        else:
            # 总页码数大于最大显示数：最多显示11个
            if self.current_page <= half_show:
                self.page_start = 1
                self.page_end = max_show
            elif self.current_page + half_show >= self.total_num:
                self.page_end = self.total_num
                self.page_start = self.total_num - max_show + 1
            else:
                self.page_start = self.current_page - half_show
                self.page_end = self.current_page + half_show

    @property
    def start(self):
        return (self.current_page - 1) * self.per_num

    @property
    def end(self):
        return self.current_page * self.per_num

    @property
    def show_li(self):
        # 存放li标签的列表
        html_str = ''

        # first_li = '<li><a href="javascript:;">首页</a></li>'.format(self.base_url)
        # html_list.append(first_li)

        if self.current_page == 1:
            html_str  += '<li class="disabled"><a>&laquo;</a></li>'
        else:
            html_str += '<li><a page="{}"><<</a></li>'.format(self.current_page - 1)
        # html_list.append(prev_li)
        for num in range(self.page_start, self.page_end + 1):
            if self.current_page == num:
                html_str += '<li class="active"><a page="{0}">{0}</a></li>'.format(num)
            else:
                html_str += '<li><a page="{0}">{0}</a></li>'.format(num)
            #html_list.append(li_html)

        if self.current_page == self.total_num:
            html_str += '<li class="disabled"><a href="javascript:;">>></a></li>'
        else:
            html_str += '<li><a page="{0}">>></a></li>'.format(self.current_page + 1)

        # html_list.append(next_li)

        # last_li = '<li><a page="{0}">尾页</a></li>'.format(self.total_num, self.base_url)
        # html_list.append(last_li)

        return html_str

# ES建表用来存储爬取的data
def create_es():
    body = {
        "mappings": {
            "doc": {
                "properties": {
                    "a_url": {
                        "type": "text"
                    },
                    "title": {
                        "type": "text",
                        "analyzer": "ik_max_word"
                    },
                    "summary": {
                        "type": "text"
                    },
                    "action_type": {
                        "type": "text"
                    }
                }
            }
        }
    }

    es.indices.create("sf", body=body)


# 分类筛选数据实现
def filter_msg(search_msg, action_type,current_page):
    """处理搜索请求"""
    # 汽车中字段必须包含汽车,并且文章分类属于问答
    if action_type == "全部":
        action_type = "问答 文章 新闻"
    body = {
        "from":0,
        "size":es.count(index='sf')['count'],
        "query": {
            "bool": {
                "must": [
                    {
                        "match": {
                            "title": search_msg
                        }
                    },
                    {
                        "match": {
                            "action_type": action_type
                        }
                    }
                ]
            }
        },
        "highlight": {
            "pre_tags": "<b style='color:red;font-size:16px;'>",
            "post_tags": "</b>",
            "fields": {
                "title": {}
            }
        }
    }
    d = {}
    res = es.search(index="sf", body=body, filter_path=["hits.total", "hits.hits"])
    page_obj = Pagination(current_page,res['hits']['total'])
    d['total_num']=res['hits']['total']
    d['total_data'] = res['hits']['hits'][page_obj.start:page_obj.end]
    d['page'] = page_obj.show_li
    return d


# 创建词库,清洗数据
def clean_data():
    a_set = set()  # 创建一个新的集合
    # 获取当前目录相对路径 E:/S17/project/es_qd/utils
    base_dir = os.path.dirname(__file__)
    # 拼接指定文件的目录,比如data   E:/S17/project/es_qd/utils\data
    data_path = os.path.join(base_dir, 'data')
    # 获取到每个文件以及文件夹
    lst = os.listdir(data_path)
    # 拼接每一个文件的全路径
    sss = [(os.path.join(data_path, i)) for i in lst]
    for item in sss:
        with open(item, 'r', encoding='utf-8') as f:
            for line in f:
                # 获取到每一行的内容content数据
                file_content = json.loads(line)['content']
                # 创建词库分词结构,获取到分词后所有词组,列表形式
                res = es.indices.analyze(body={"analyzer": "ik_smart", "text": file_content})['tokens']
                # print(res)
                # 循环列表获取每个字典的数据,并通过集合去重
                tmp = {i['token'] for i in res}
                a_set.update(tmp)
    f = open('s.json', 'w', encoding='utf-8')
    json.dump(" ".join(a_set), f)
    f.flush()
    f.close()


# 筛选建议器数据
def suggest_filter_msg(search_msg):
    body = {
        "suggest": {
            "lexicon1": {
                "text": search_msg,
                "completion": {
                    "field": "title",
                    "size":4
                }
            },
            "lexicon2":{
                "text":search_msg,
                "phrase":{
                    "field":"title",
                    "size": 3,
                    "highlight":{
                        "pre_tag":"<b style='color:red'>",
                        "post_tag":"</b>"
                    }
                }
            }
        }

    }

    res = es.search(index="lexicon", body=body)
    # lexicon1 = [i["_source"]["title"] for i in res['suggest']['lexicon1'][0]['options']]
    # lexicon2 = [i["text"].repalce('\x1f','')  for i in res['suggest']['lexicon2'][0]['options']]
    lexicon1 = [i['_source']['title'] for i in res['suggest']['lexicon1'][0]['options']]
    lexicon2 = [i['text'].replace('\x1f', '') for i in res['suggest']['lexicon2'][0]['options']]
    return lexicon1+lexicon2


# 词库索引
def create_lexicon():
    body = {
        "mappings": {
            "doc": {
                "properties": {
                    "title": {
                        "type": "completion"  # 完成建议器
                        # "analyzer":"standard"  # 建议/'ænəlaɪzə/    标准/'stændəd/
                    }
                }
            }
        }
    }

    es.indices.create(index="lexicon", body=body)


# 读取本地json数据录入es词库
def write_json_data_to_es():
    with open('s.json', "r", encoding="utf-8") as f:
        res = json.load(f).split(" ")
        # print(res)
        action = [{
            "_index": "lexicon",
            "_type": "doc",
            "_source": {
                "title": i
            }
        } for i in res]
        print(helpers.bulk(es, action))


if __name__ == '__main__':

    # create_es()
    # clean_data()
    #  create_lexicon()
    #  write_json_data_to_es()
    while 1:
        res = input(">>>").strip()
        filter_msg(res)
