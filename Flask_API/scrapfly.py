import json
from typing import Dict
import jmespath
import requests
from bs4 import BeautifulSoup
from parsel import Selector
from nested_lookup import nested_lookup
from playwright.sync_api import sync_playwright

import googleapiclient.discovery
import googleapiclient.errors

import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import re
import emoji

import numpy as np
from PIL import Image
from wordcloud import WordCloud
import matplotlib.pyplot as plt

from prepare_text import clean
from constants import DEVELOPER_KEY_YT
import os

api_service_name = "youtube"
api_version = "v3"
DEVELOPER_KEY = DEVELOPER_KEY_YT

youtube = googleapiclient.discovery.build(api_service_name, api_version, developerKey=DEVELOPER_KEY)


def replace_non_english_python(text):
    # Create a regular expression that matches non-English characters
    regex = '[^A-Za-z0-9:?:@!#$%^&*()_+{}[]:;.,./]'

    # Replace all matches with a random number or symbol
    return re.sub(regex, '', text)


def get_youtube_comments(link, count):
    v_id = link[-11:]
    request = youtube.commentThreads().list(
        part="snippet",
        videoId=v_id,
        maxResults=count)
    response = request.execute()

    return response


def parse_thread(data: Dict) -> Dict:
    """Parse Twitter tweet JSON dataset for the most important fields"""
    result = jmespath.search(
        """{
        textOriginal: post.caption.text,
        publishedAt: post.taken_at,
        id: post.id,
        pk: post.pk,
        code: post.code,
        authorDisplayName: post.user.username,
        user_pic: post.user.profile_pic_url,
        user_verified: post.user.is_verified,
        user_pk: post.user.pk,
        user_id: post.user.id,
        has_audio: post.has_audio,
        reply_count: view_replies_cta_string,
        likeCount: post.like_count,
        images: post.carousel_media[].image_versions2.candidates[1].url,
        image_count: post.carousel_media_count,
        videos: post.video_versions[].url
    }""",
        data,
    )
    result["videos"] = list(set(result["videos"] or []))
    if result["reply_count"]:
        result["reply_count"] = int(re.sub(r"[^\d]", '', result["reply_count"].split(" ")[0]))
    result[
        "url"
    ] = f"https://www.threads.net/@{result['authorDisplayName']}/post/{result['code']}"
    # print(result['textOriginal'])
    if result['textOriginal']:
        result['textOriginal'] = replace_non_english_python(result['textOriginal'])
        result['textOriginal'] = emoji.demojize(result['textOriginal'])
    else:
        result['textOriginal'] = ''
    return result


def scrape_thread(url: str) -> dict:
    """Scrape Threads post and replies from a given URL"""
    with sync_playwright() as pw:
        # start Playwright browser
        browser = pw.chromium.launch()
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        # go to url and wait for the page to load
        page.goto(url)
        # wait for page to finish loading
        page.wait_for_selector("[data-pressable-container=true]")
        # find all hidden datasets
        selector = Selector(page.content())
        hidden_datasets = selector.css('script[type="application/json"][data-sjs]::text').getall()
        # find datasets that contain threads data
        for hidden_dataset in hidden_datasets:
            # skip loading datasets that clearly don't contain threads data
            if '"ScheduledServerJS"' not in hidden_dataset:
                continue
            if "thread_items" not in hidden_dataset:
                continue
            data = json.loads(hidden_dataset)
            # datasets are heavily nested, use nested_lookup to find
            # the thread_items key for thread data
            thread_items = nested_lookup("thread_items", data)
            if not thread_items:
                continue
            # use our jmespath parser to reduce the dataset to the most important fields
            threads = [parse_thread(t) for thread in thread_items for t in thread]
            return {
                # the first parsed thread is the main post:
                "thread": threads[0],
                # other threads are replies:
                "replies": threads[1:],
            }
        raise ValueError("could not find thread data in page")


def get_threads_replies(link):
    scraped = scrape_thread(link)
    return scraped['replies']


def get_yelp_reviews(link):
    r = requests.get(link)
    soup = BeautifulSoup(r.text, 'html.parser')
    regex = re.compile('.*comment.*')
    results = soup.find_all('p', {'class':regex})
    reviews= []
    for i in results:
        reviews.append(i.text)
    return reviews


def get_rating(row):
    tokens = tokenizer.encode(row['Comment'], return_tensors='pt')
    result = model(tokens)
    return int(torch.argmax(result.logits)) + 1


def get_predictions(link) -> pd.DataFrame:
    data = []
    if re.match(r"https://www.youtube.com*", link):
        resp = get_youtube_comments(link, 100)
        for i in resp['items']:
            temp = i['snippet']['topLevelComment']['snippet']
            data.append({
                'Comment': temp['textOriginal'],
                'authorName': temp['authorDisplayName'],
                'likeCount': temp['likeCount'],
                'publishedAt': temp['publishedAt']
            })
    elif re.match(r"https://www.threads.net*", link):
        resp = get_threads_replies(link)
        for i in resp:
            data.append({
                'Comment': i['textOriginal'],
                'authorName': i['authorDisplayName'],
                'likeCount': i['likeCount'],
                'publishedAt': i['publishedAt']
            })

    df = pd.DataFrame(data)

    df['rating'] = df.apply(get_rating, axis=1)
    return df


def make_word_cloud(text):
    background_color = "#fff"
    colormap = 'viridis_r'

    width = 1200
    height = 800

    cleaned_text = clean(text)

    wc = WordCloud(background_color=background_color, colormap=colormap, width=width, height=height).\
        generate(cleaned_text)

    wc.to_file("../Website/public/images/wordc.png")

    # Uncomment to view image
    # plt.axis("off")
    # plt.figure()
    # plt.imshow(wc, interpolation="bilinear")
    # plt.show()


def get_word_cloud(df: pd.DataFrame):
    make_word_cloud(df['Comment'].sum())


# print(get_threads_replies("https://www.threads.net/@zuck/post/CxWMc87galo"))
# resp, comm = get_youtube_comments("https://www.youtube.com/watch?v=v-Ymf_hTbUM", 30)
# resp = get_threads_replies("https://www.threads.net/@zuck/post/CxWMc87galo")


tokenizer = AutoTokenizer.from_pretrained('nlptown/bert-base-multilingual-uncased-sentiment')
model = AutoModelForSequenceClassification.from_pretrained('nlptown/bert-base-multilingual-uncased-sentiment')

if __name__ == '__main__':
    # p_df = get_predictions('https://www.youtube.com/watch?v=NuEgjAMfdIY')
    # get_word_cloud(p_df)
    print(DEVELOPER_KEY_YT)
    # https://www.threads.net/@mrbeast/post/CuXrpemRV3m

