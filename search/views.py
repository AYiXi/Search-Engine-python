import time
import datetime
import json

from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic.base import View
from elasticsearch_dsl import connections

from elasticsearch import Elasticsearch

es = Elasticsearch()


# Create your views here.
class SearchSuggest(View):
    def get(self, request):
        keywords = request.GET.get('s', '')
        re_data = []
        if keywords:
            suggestions = es.search(index='jobbole', body={
                "suggest": {
                    "my_suggest": {
                        "text": keywords,
                        "completion": {
                            "field": "suggest",
                            "fuzzy": {
                                "fuzziness": 1
                            }
                        }
                    }
                },
                "_source": "title",
                "size": 10
            })
            for match in suggestions['suggest']['my_suggest'][0]['options']:
                # print(match)
                re_data.append(match['_source']['title'])

        return HttpResponse(json.dumps(re_data), content_type='application/json')


class Search(View):
    def get(self, request):
        keywords = request.GET.get('q', '')
        page = int(request.GET.get('p', 1))
        start_time = datetime.datetime.now()
        response = es.search(
            index='jobbole',
            body={
                'query': {
                    'multi_match': {
                        'query': keywords,
                        'fields': ['tags', 'title', 'html']
                    }
                },
                'from': (page - 1) * 10,
                'size': 10,
                'highlight': {
                    'pre_tags': ['<span class="keyWord>"'],
                    'post_tags': ['</span>'],
                    'fields': {
                        'title': {},
                        'content': {},
                    }
                }
            }
        )
        total_nums = response['hits']['total']  # 34

        if (page % 10) > 0:
            page_num = int(total_nums / 10) + 1
        else:
            page_num = int(total_nums / 10)

        hit_list = []
        for hit in response['hits']['hits']:
            hit_dict = {}
            # hit_dict['title'] = hit['highlight']['title'][0] \
            #     if 'title' in hit['highlight'] else hit['_source']['title']
            #
            # hit_dict['html'] = hit['highlight']['html'][:500] \
            #     if 'html' in hit['highlight'] else hit['_source']['html'][:500]
            # if 'title' in hit['highlight']:
            # hit_dict['title'] = hit['highlight']['title']
            # else:
            hit_dict['title'] = hit['_source']['title']
            #
            # if 'html' in hit['highlight']:
            # hit_dict['html'] = hit['highlight']['html'][:500]
            # else:
            hit_dict['html'] = hit['_source']['html'][:500]  # TODO:highlight

            hit_dict['create_date'] = hit['_source']['create_date']
            hit_dict['url'] = hit['_source']['url']
            hit_dict['score'] = hit['_score']

            hit_list.append(hit_dict)

        end_time = datetime.datetime.now()
        last_time = (end_time - start_time).total_seconds()

        return render(request=request, template_name='result.html', context={
            'all_hits': hit_list,
            'key_words': keywords,
            'page': page,
            'total_nums': total_nums,
            'page_num': page_num,
            'time': last_time,
        })
