from django.shortcuts import render,HttpResponse
from django.http import JsonResponse
from app01 import  models
import requests
from bs4 import BeautifulSoup
from utils.es import filter_msg,es,suggest_filter_msg
from utils.pagination import Pagination


def index(request):

    if request.method=="POST":

        search_msg=request.POST.get("search_msg")
        action_type = request.POST.get("action_type")
        current_page = request.POST.get("currentPage")
        res = filter_msg(search_msg,action_type,current_page)
        return JsonResponse(res)


    return render(request,'index.html')


def my_suggest(request):
    if request.method == "POST":
        search_msg = request.POST.get("search_msg")
        # print(search_msg)
        res = suggest_filter_msg(search_msg)
        return JsonResponse({"mySuggest":res})
    return HttpResponse('对不起,403页面错误')


#获取title的url返回对应的结果
def desc(request):
    a_url = request.META['PATH_INFO'].split("/desc/")[-1]
    desc_obj = models.ESTotal.objects.filter(a_url__contains=a_url).first()  #a_url__contains获取包含的url
    return render(request,"desc.html",{"desc_obj":desc_obj})

def spider(request):
    "爬取汽车之家 https://www.autohome.com.cn/news/"
    for i in range(23,33):
        response = requests.get(url="https://www.autohome.com.cn/news/{}/#liststart".format(i))
        soup = BeautifulSoup(response.text,"html.parser")
        div_obj = soup.find(name="div",attrs={"id":"auto-channel-lazyload-article"})
        li_list = div_obj.find_all(name="li")
        for item in li_list:
            title_obj = item.find("h3")
            if not title_obj:continue
            a_url = "https:" + item.find("a").get("href")
            summary = item.find("p").text.split(" ")[-1]
            title = title_obj.text
            action_type = "新闻"
            # print(a_url,summary,title)
            models.ESTotal.objects.create(
                a_url=a_url,
                summary=summary,
                title=title,
                action_type=action_type
            )
            es.index("sf",doc_type="doc",body={
                "a_url":a_url,
                "title":title,
                "summary":summary,
                "action_type":action_type
            })

    return HttpResponse('ok')