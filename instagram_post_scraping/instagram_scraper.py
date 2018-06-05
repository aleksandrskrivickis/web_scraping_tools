#!/usr/bin/python
# -*- coding: utf-8 -*-
##############################Imports:
import argparse
import selenium
from selenium import webdriver
import time
import pandas as pd
import re
from tqdm import tqdm
import datetime
import dateutil.parser as dparser
from datetime import timedelta
import random

##############################Constants:
    #Scraper delays(s):

DELAY_GETPOSTDATA = 0.1
DELAY_GETALLPOSTDATA = 0.1
DELAY_SCROLLER = 1
DELAY_COMMENT_EXPANDER = 0.1

##############################Global vars:
global URL_TO_SCRAPE, XLSX_OUTPUT_FILE_NAME, VERBOSE
##############################Methods:
def updDelayScroller():
    global DELAY_SCROLLER
    DELAY_SCROLLER = round(random.uniform(1, 2), 2)
    
def scrollRandomUp(driver):
    for a in range(1, random.randint(1, 5)):
        driver.execute_script("window.scrollBy(0," + str(-(random.randint(768, 1055))) + ")")
        time.sleep(round(random.uniform(0.1, 0.5), 2))
    
def scrollPageToBottomAndFindPostLinks():
    time.sleep(5)
    #Get total amount of posts:
    
    try:
        totalPosts = int(driver.find_element_by_xpath("//*[@id=\"react-root\"]/section/main/div/header/section/ul/li[1]/span/span").text.replace(",", ""))
    except Exception as Ex:
        if VERBOSE:
            print(Ex)
            print("Unable to locate amount of posts, using 99999 instead.")
            totalPosts = 9999

    pbar = tqdm(total=totalPosts, desc="Getting links for all the posts")

    def scrl(attempts=0, allPosts=[]):
        if VERBOSE:
            print("Attempt number: " + str(attempts) + "\n AllPosts len is: " + str(len(allPosts)))
        if attempts < (totalPosts / 10):
            prevHeight = 0
            newHeight = 1
            while prevHeight != newHeight:
                prevHeight = int(driver.execute_script("return document.body.scrollHeight;"))
                scrollRandomUp(driver)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(DELAY_SCROLLER)
                updDelayScroller()#Random delay
                allPosts.append(findPostLinks(driver))
                newHeight = int(driver.execute_script("return document.body.scrollHeight;"))
                pbar.update(16) 
            attempts += 1
            return scrl(attempts, allPosts)
        else:
            return allPosts
    
    allPosts = scrl()

    return allPosts
    



def findPostLinks(driver):
    posts = []
    src = driver.page_source
    src_splitted = src.split("</div>")

    for entry in src_splitted:
        postRegex = re.findall("(<a href=\")(.*)(\?taken-by=\w*\">)", entry)
        if len(postRegex) > 0:
            posts.append(postRegex[0][1])
    return posts

def getPostData(driver):
    time.sleep(DELAY_GETPOSTDATA)
    postData = []
    expandAllComments(driver)
    post_link = driver.current_url
    
    try:
        image_link = driver.find_element_by_xpath("//*[@id=\"react-root\"]/section/main/div/div/article/div[1]/div/div/div[2]").text
    except Exception as e:
        try:
            image_link = driver.find_elements_by_tag_name('img')[1].get_attribute('src')
        except Exception as ex:
            image_link = ""
    
    if VERBOSE:
        try:
            authors, comments = getAllCommentsFromArticle(driver)
        except Exception as ex:
            authors = []
            comments = []
            print("Exception in getPostData() - unable to get comments from article: " + str(post_link))
    #Getting likes
    try:
        likes = driver.find_element_by_xpath("//*[@id=\"react-root\"]/section/main/div/div/article/div[2]/section[2]/div/span/span").text#driver.find_element_by_tag_name('span').text.splitlines()[6].replace(" likes", "")
    except Exception as e:
        if VERBOSE:
            print("Unable to get likes from post: " + post_link + "\n Trying different approach...")
        try:
            likes = (len(driver.find_element_by_xpath("//*[@id=\"react-root\"]/section/main/div/div/article/div[2]/section[2]/div").text.split(",")) + 1)
        except Exception as Ex:
            if VERBOSE:
                print("Different approach didn't work. Value of likes field will be \"Exception\"")
            likes = "Exception"
            
    #Getting and processing date
    try:
        date = driver.find_element_by_xpath("//*[@id=\"react-root\"]/section/main/div/div/article/div[2]/div[2]/a/time").text#driver.find_element_by_tag_name('article').text.splitlines()[len(driver.find_element_by_tag_name('article').text.splitlines()) - 2]
    except Exception as e:
        if VERBOSE:
            print("Unable to get date from post: " + post_link)
        date = "Exception"
        
    if ("," not in date):
        if VERBOSE:
            print("Date has a weird format.. " + str(date) + " converting...")
        date = date + ", " + str(datetime.datetime.now().year)
    date = convertDate(date)
    if VERBOSE:
        print(date)
    
    if date == "" or " days ago" in driver.find_element_by_xpath("//*[@id=\"react-root\"]/section/main/div/div/article/div[2]/div[2]/a/time").text.casefold():
        try:
            daysAgo = driver.find_element_by_xpath("//*[@id=\"react-root\"]/section/main/div/div/article/div[2]/div[2]/a/time").text.casefold().replace(" days ago", "").replace(" day ago", "")
        except Exception as ex:
            if VERBOSE:
                print("Exception in getPostData()'s date conversion getting days ago from web page.")
                daysAgo = 0
        try:
            date = datetime.datetime.now() - timedelta(days=int(daysAgo))
        except Exception as ex:
            if VERBOSE:
                print("Exception in getPostData()'s date conversion(daysAgo) part.")

    firstRun = True
    cnt = 0
    for a, c in zip(authors, comments):
        if firstRun:
            firstRun = False
            postData.append({"post_id": str(post_link.split("/")[4]), "post_link" : post_link, "image_link" : image_link, "post_author" : a, "post" : c, "likes": likes, "date": date, "comment": "N/A", "comment_author": "N/A"})
        else:
            postData.append({"post_id": str(post_link.split("/")[4] + "_" + str(cnt)), "post_link" : post_link, "image_link" : image_link, "post_author" : authors[0], "post" : comments[0], "likes": "N/A", "date": date, "comment": c, "comment_author": a})
            cnt += 1
    return postData

def getAllCommentsFromArticle(driver):
    #Posts description and authors name is a very first comment's content and authors name
    authors = []
    comments = []
    article = driver.find_element_by_tag_name("article")
    comment = article.find_elements_by_tag_name("li")
    firstRun = True
    for com in comment:
        #print("\n" + com.find_element_by_tag_name("a").text + ", post: " + com.find_element_by_tag_name("span").text)
        postAuthor = driver.find_element_by_xpath("//*[@id=\"react-root\"]/section/main/div/div/article/header/div[2]/div[1]/div[1]/a").text
        if firstRun:
            if com.find_element_by_tag_name("a").text != postAuthor:
                authors.append("")
                comments.append("")
            firstRun = False
        authors.append(com.find_element_by_tag_name("a").text)
        comments.append(com.find_element_by_tag_name("span").text)
    return authors, comments

def expandAllComments(driver):
    try:
        el = driver.find_element_by_xpath("//*[@id=\"react-root\"]/section/main/div/div/article/div[2]/div[1]/ul/li[2]/a")
        while (el.text == "Load more comments" or "View all" in el.text):
            el = driver.find_element_by_xpath("//*[@id=\"react-root\"]/section/main/div/div/article/div[2]/div[1]/ul/li[2]/a")
            if (el.text == "Load more comments" or "View all" in el.text):
                el.click()
            time.sleep(DELAY_COMMENT_EXPANDER)
    except Exception as e:
        if VERBOSE:
            print("expandAllComments() - expanded")
        
def convertDate(date):
    returnable = []
    try:
        if (str(date) == "NaT" or str(date) == ""):
            currDate = str(date)
            returnable == ""
        else:
            currDate = str(date)
            returnable = dparser.parse(str(date)).date()
    except Exception as e:
        if VERBOSE:
            print("Exception in convertAllDates() " + str(e))
            print("Exception in convertAllDates() caused by " + currDate + " instead of date string...")
        returnable = ""
    return returnable           

def parseArgs():
    parser = argparse.ArgumentParser(description='Instagram scraper allows to dump all the public posts and comments from a specified link to a profile.')
    parser.add_argument('-i', '--input_addr', help='Address of an instagram profile to scrape from', required=True)
    parser.add_argument('-o', '--output_file', help='Output file name', default="./instagram_dump" + "_" + datetime.datetime.now().strftime("%Y_%m_%d_%H_%M") + ".xlsx", required=False)
    parser.add_argument('-v', '--verbose', help='Show additional information or alerts', required=False, default=True, type=bool, choices=[True, False])
    args = vars(parser.parse_args())
    
    VERBOSE = args['verbose']

    if VERBOSE:
        print("Profile address: " + args['input_addr'])
        print("Output file name: " + args['output_file'])

    return args    


##############################Main me
if __name__ == "__main__":
    #Getting global variables from arguments:
    args = parseArgs()
    URL_TO_SCRAPE = args['input_addr']
    XLSX_OUTPUT_FILE_NAME = args['output_file']
    VERBOSE = args['verbose']
    
    #Getting all the post links
    driver = webdriver.Chrome()
    driver.get(URL_TO_SCRAPE)
    #time.sleep(10)
    allPosts = scrollPageToBottomAndFindPostLinks()
    
    #Concatenate all lists in one
    allPosts = sum(allPosts, [])
    #Remove dupes from posts
    allPosts = list(set(allPosts))
    allPosts = ["https://www.instagram.com" + x for x in allPosts]
    if VERBOSE:
        print("Amount of links to posts scraped: " + str(len(allPosts)))
    allPostData = []
    
    #Parsing every post
    #driver = webdriver.Chrome()
    for link in tqdm(allPosts, desc="Parsing post data"):
        driver.get(link)
        time.sleep(DELAY_GETALLPOSTDATA)
        allPostData.append(getPostData(driver))
        
    #Export to file:
    allPostData = sum(allPostData, [])
    df = pd.DataFrame.from_dict(allPostData)
    df = df.reindex(["post_id", 'post_link', "image_link", "date", "post", "post_author", "likes", "comment", "comment_author"], axis=1)
    df.index.name = "entry"
    #Sort by post date, keep post and comment order
    df.reset_index(level=0, inplace=True)
    df['date'] = pd.to_datetime(df.date)
    df_sorted = df.sort_values(['date', 'entry'], ascending=[True, True])
    df_sorted.reset_index(inplace=True)
    df_sorted = df_sorted.iloc[::-1]
    df_sorted.drop(labels=["index", "entry"], axis=1, inplace=True)
    df_sorted.to_excel(XLSX_OUTPUT_FILE_NAME, index=False)
    driver.quit()
    print("Fin!")