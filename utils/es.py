from elasticsearch import Elasticsearch

es = Elasticsearch()


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


def filter_msg(search_msg,action_type):
    """处理搜索请求"""
    #汽车中字段必须包含汽车,并且文章分类属于问答
    if action_type == "全部":
        action_type = "问答 文章 新闻"
    body = {
        "query": {
            "bool": {
                "must": [
                    {
                        "match":{
                            "title":search_msg
                        }

                    },
                    {
                        "match":{
                            "action_type":action_type
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
    res = es.search(index="sf", body=body, filter_path=["hits.total", "hits.hits"])
    print(res)
    return res


if __name__ == '__main__':
    # create_es()
    while 1:
        res = input(">>>").strip()
        filter_msg(res)
