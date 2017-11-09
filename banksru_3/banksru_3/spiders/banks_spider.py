# -*- coding: utf-8 -*-
import scrapy
import html2text
import pandas as pd
import regex as re
from tqdm import tqdm_notebook
import os
import shutil
import matplotlib.pyplot as plt
import artm
import codecs
from seaborn import heatmap
import time
from math import log
import operator
import numpy as np
from nltk import sent_tokenize
from pymystem3 import Mystem
from tools import *
from preprocess_line import CollocationSyntax, add_collocation, lemmatize
from create_ww_and_pmi_count import main as prepare_vw_wntm_pmi_vocab
import pickle
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


class BanksSpider(scrapy.spider.CrawlSpider):
    name = "banks"
    start_urls = [
        'http://www.banki.ru/services/responses/',
    ]
    
    def parsePage(self, response):

        if response.status != 400:

            h = html2text.HTML2Text()
            h.ignore_links = True
            get_next = response.url.split("=")
            
            if len(get_next) > 1:
                current_number = int(get_next[-1])
            else:
                current_number = 1
                
            for index, item in enumerate(response.xpath('//*[contains(concat( " ", @class, " " ), \
                                                        concat( " ", "responses__item", " " ))]')):
                
                time = item.css("time.display-inline-block::text").extract_first()
                title = item.css("a.font-size-large::text").extract_first()
                rating = h.handle(item.css("div.responses__item__rating").extract_first()).strip()
                bank_response = item.css("div.thread-item__text").extract_first()
                if bank_response:
                    bank_response = h.handle(bank_response).strip()
                text = item.css("div.responses__item__message")
                if len(text) == 2:
                    text = h.handle(text[1].extract()).strip()
                else:
                    text = h.handle(text.extract_first()).strip()
                author = h.handle(item.css("div.responses__item__from").extract_first()).strip()
                comments_n = item.xpath('//a[contains(@href, "comments")]/text()')[index].extract()
                yield {
                    "bank": response.url.split("/")[6],
                    "time": time,
                    "title": title,
                    "rating": rating,
                    "bank_response": bank_response,
                    "text": text,
                    "author": author,
                    "comments_n": comments_n,
                    "comment_page": str(current_number)
                }
   
            if current_number != 1:
                next_number = current_number + 1
                next_page = get_next[0] + "=" + str(next_number)
            else:
                next_page = response.url + "?page=2"
            yield scrapy.Request(next_page, callback=self.parsePage)
    

    def parse(self, response):

        for bank in response.xpath("//script[contains(., 'banksData')]/text()").re(r'"code":"(.*?)"'):
            next_page = "http://www.banki.ru/services/responses/bank/" + bank
            yield scrapy.Request(next_page, callback=self.parsePage)


