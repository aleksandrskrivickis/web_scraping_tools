#!/usr/bin/python
# -*- coding: utf-8 -*-
##############################Imports:
import argparse
from FlaskWebProject2 import settings
import selenium
from selenium import webdriver
import time
import pandas as pd
import re
import tqdm
import datetime
import dateutil.parser as dparser
from datetime import timedelta
import random
import threading

class Repository(object):

	##############################Methods:

	def __init__(self, settings):
		print("Initialising variables")
		global DELAY_GETPOSTDATA, DELAY_GETALLPOSTDATA, DELAY_SCROLLER, DELAY_COMMENT_EXPANDER, THREAD_NUMBER, URL_TO_SCRAPE, XLSX_OUTPUT_FILE_NAME, VERBOSE, allPosts
		"""Initializes the repository. Note that settings are not used."""
		DELAY_GETPOSTDATA = 0.1
		DELAY_GETALLPOSTDATA = 0.1
		DELAY_SCROLLER = 1
		DELAY_COMMENT_EXPANDER = 0.1
		THREAD_NUMBER = 4
		URL_TO_SCRAPE = ""#args['input_addr']
		XLSX_OUTPUT_FILE_NAME = ("./instagram_dump" + "_" + datetime.datetime.now().strftime("%Y_%m_%d_%H_%M") + ".xlsx")#, required=Falseargs['output_file']
		VERBOSE = True#args['verbose']
		allPosts = []

	def setUrlToScrape(self, x):
		global URL_TO_SCRAPE
		#print("Setting URL_TO_SCRAPE to: " + str(x))
		URL_TO_SCRAPE = str(x)
		#print("URL_TO_SCRAPE is: " + str(URL_TO_SCRAPE))

	def pprint(self, txt_pri = "\n"):
		if VERBOSE:
			print(str(txt_pri))
		else:
			pass

	def exportData(self, lst_pst_dat):
		#Export to file:
		lst_pst_dat = sum(lst_pst_dat, [])
		df = pd.DataFrame.from_dict(lst_pst_dat)
		df = df.astype(str)
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
		self.pprint("Finished!")
		return df_sorted

	def getDataFromPostList_Multithread(self, lst_lnk):
		threads = []

		#posts = list(range(1, 1000))
		tmp = allPosts.copy()
		posts_ = splitListToSublists(lst_lnk, THREAD_NUMBER)

		for a in range(0,THREAD_NUMBER):
			threads.append("threading.Thread(target=getDataFromPostList, args=(" + str(posts_[a]) + ",)).start()")  

		for a in threads:
			exec(a)

		global allPostData
		return allPostData



	def getLinks(self):
		global allPosts

		#Testing bit
		return ["https://www.instagram.com/p/BgjNecQl1nz/",
"https://www.instagram.com/p/BgjbbCXFEFe/",
"https://www.instagram.com/p/BegBPChgQ-5/",
"https://www.instagram.com/p/BgmD8qKF46r/",
"https://www.instagram.com/p/BgoW8eJAiJH/",
"https://www.instagram.com/p/BjFgn-bHktO/",
"https://www.instagram.com/p/Bh34sPgnqtI/",
"https://www.instagram.com/p/Bgn_0D8A6Nd/",
"https://www.instagram.com/p/Bgd_dIrlDU8/",
"https://www.instagram.com/p/BhEWGH8AHAH/",
"https://www.instagram.com/p/BgmR59ilE_i/",
"https://www.instagram.com/p/Bf9JtCTASWU/"]

		if len(URL_TO_SCRAPE) < 2:
			return None
		else:
			if len(allPosts) < 2:#Get post links
				#Getting all the post links
				driver = webdriver.Chrome("C:\\Work\\Projects\\Python\\web_scraping_tools\\instagram_post_scraping\\chromedriver.exe")
				driver.get(URL_TO_SCRAPE)
				#time.sleep(10)
				allPosts = self.scrollPageToBottomAndFindPostLinks(driver)

				#Concatenate all lists in one
				allPosts = sum(allPosts, [])
				#Remove dupes from posts
				allPosts = list(set(allPosts))
				allPosts = ["https://www.instagram.com" + x for x in allPosts]
				self.pprint("Amount of links to posts scraped: " + str(len(allPosts)))
				driver.close()
				print("Returning allPosts: " + str(allPosts))
				return allPosts
			else:
				return allPosts

	def getDataFromPostList(post_links):
		global allPostData
		allPostData = []
		#Parsing every post
		driver = webdriver.Chrome("C:\\Work\\Projects\\Python\\web_scraping_tools\\instagram_post_scraping\\chromedriver.exe")
		for link in tqdm.tqdm_notebook(post_links, desc="Parsing post data"):
			driver.get(link)
			time.sleep(DELAY_GETALLPOSTDATA)
			allPostData.append(getPostData(driver))

		driver.close()
		return allPostData

	def splitListToSublists(posts = [], split_parts = 4):
		if split_parts == 0 or split_parts == 1:
			return posts
		else:
			returnable = []
			self.pprint("Splitting " + str(len(posts)) + " posts")
			step = int(len(posts) / split_parts)
			splitted = 0
			for a in range(0, split_parts):
				temp = []
				if splitted < split_parts - 1:
					for i in range(0, step):
						temp.append(posts.pop(i))
					splitted += 1
				else:#Last fraction of a list
					for b in posts:
						temp.append(b)
				returnable.append(temp)
			return returnable


	def updDelayScroller(self):
		global DELAY_SCROLLER
		DELAY_SCROLLER = round(random.uniform(1, 2), 2)

	def scrollRandomUp(self, driver):
		for a in range(1, random.randint(1, 5)):
			driver.execute_script("window.scrollBy(0," + str(-(random.randint(768, 1055))) + ")")
			time.sleep(round(random.uniform(0.1, 0.5), 2))

	def scrollPageToBottomAndFindPostLinks(self, driver):
		time.sleep(5)
		#Get total amount of posts:

		try:
			totalPosts = int(driver.find_element_by_xpath("//*[@id=\"react-root\"]/section/main/div/header/section/ul/li[1]/span/span").text.replace(",", ""))
		except Exception as Ex:
			self.pprint(Ex)
			self.pprint("Unable to locate amount of posts, using 99999 instead.")
			totalPosts = 9999

		pbar = tqdm.tqdm_notebook(total=totalPosts, desc="Getting links for all the posts")

		def scrl(attempts=0, allPosts=[]):
			self.pprint("Attempt number: " + str(attempts) + " / " + str(totalPosts / 8) + "\n AllPosts len is: " + str(len(allPosts)))
			if attempts < (totalPosts / 8):
				prevHeight = 0
				newHeight = 1
				while prevHeight != newHeight:
					prevHeight = int(driver.execute_script("return document.body.scrollHeight;"))
					self.scrollRandomUp(driver)
					driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
					time.sleep(DELAY_SCROLLER)
					self.updDelayScroller()#Random delay
					allPosts.append(self.findPostLinks(driver))
					newHeight = int(driver.execute_script("return document.body.scrollHeight;"))
					pbar.update(16) 
				attempts += 1
				return scrl(attempts, allPosts)
			else:
				return allPosts

		allPosts = scrl()
		return allPosts



	def findPostLinks(self, driver):
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

		#Getting comments
		try:
			authors, comments = getAllCommentsFromArticle(driver)
		except Exception as ex:
			authors = []
			comments = []
			self.pprint("Exception in getPostData() - unable to get comments from article: " + str(post_link))
		#Getting likes
		try:
			likes = driver.find_element_by_xpath("//*[@id=\"react-root\"]/section/main/div/div/article/div[2]/section[2]/div/span/span").text#driver.find_element_by_tag_name('span').text.splitlines()[6].replace(" likes", "")
		except Exception as e:
			self.pprint("Unable to get likes from post: " + post_link + "\n Trying different approach...")
			try:
				likes = (len(driver.find_element_by_xpath("//*[@id=\"react-root\"]/section/main/div/div/article/div[2]/section[2]/div").text.split(",")) + 1)
			except Exception as Ex:
				self.pprint("Different approach didn't work. Value of likes field will be \"Exception\"")
				likes = "Exception"

		#Getting and processing date
		try:
			date = driver.find_element_by_xpath("//*[@id=\"react-root\"]/section/main/div/div/article/div[2]/div[2]/a/time").text#driver.find_element_by_tag_name('article').text.splitlines()[len(driver.find_element_by_tag_name('article').text.splitlines()) - 2]
		except Exception as e:
			self.pprint("Unable to get date from post: " + post_link)
			date = "Exception"

		if ("," not in date):
			self.pprint("Date has a weird format.. " + str(date) + " converting...")
			date = date + ", " + str(datetime.datetime.now().year)
		date = convertDate(date)
		self.pprint(date)

		if date == "" or " days ago" in driver.find_element_by_xpath("//*[@id=\"react-root\"]/section/main/div/div/article/div[2]/div[2]/a/time").text.casefold():
			try:
				daysAgo = driver.find_element_by_xpath("//*[@id=\"react-root\"]/section/main/div/div/article/div[2]/div[2]/a/time").text.casefold().replace(" days ago", "").replace(" day ago", "")
			except Exception as ex:
				self.pprint("Exception in getPostData()'s date conversion getting days ago from web page.")
				daysAgo = 0
			try:
				date = datetime.datetime.now() - timedelta(days=int(daysAgo))
			except Exception as ex:
				self.pprint("Exception in getPostData()'s date conversion(daysAgo) part.")
		######################            
		try:
			post_id = str((driver.execute_script("return window._sharedData;"))["entry_data"]["PostPage"][0]["graphql"]["shortcode_media"]["id"])
		except Exception as ex:
			self.pprint("Exception in getPostData()'s post_id part.")   
			post_id = "00000000"

		firstRun = True
		cnt = 0
		for a, c in zip(authors, comments):
			if firstRun:
				firstRun = False
				postData.append({"post_id": post_id, "post_link" : post_link, "image_link" : image_link, "post_author" : a, "post" : c, "likes": likes, "date": date, "comment": "N/A", "comment_author": "N/A"})
			else:
				postData.append({"post_id": str(post_id + "_" + str(cnt)), "post_link" : post_link, "image_link" : image_link, "post_author" : authors[0], "post" : comments[0], "likes": "N/A", "date": date, "comment": c, "comment_author": a})
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
		oldCommentAmount = 0
		newCommentAmount = 0
		timeoutCounter = 10
		try:
			el = driver.find_element_by_xpath("//*[@id=\"react-root\"]/section/main/div/div/article/div[2]/div[1]/ul/li[2]/a")
			while (el.text == "Load more comments" or "View all" in el.text):
				el = driver.find_element_by_xpath("//*[@id=\"react-root\"]/section/main/div/div/article/div[2]/div[1]/ul/li[2]/a")
				if (el.text == "Load more comments" or "View all" in el.text or timeoutCounter > 0):
					oldCommentAmount = len(driver.find_element_by_tag_name("article").find_elements_by_tag_name("li"))
					el.click()
				time.sleep(DELAY_COMMENT_EXPANDER)
				newCommentAmount = len(driver.find_element_by_tag_name("article").find_elements_by_tag_name("li"))
				if (oldCommentAmount == newCommentAmount and timeoutCounter > 0):
					timeoutCounter -= 1
					print("expandAllComments() timed out. Attempts left: " + str(timeoutCounter))

		except Exception as e:
			self.pprint("expandAllComments() - expanded")

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
			self.pprint("Exception in convertAllDates() " + str(e))
			self.pprint("Exception in convertAllDates() caused by " + currDate + " instead of date string...")
			returnable = ""
		return returnable           

	def parseArgs():
		parser = argparse.ArgumentParser(description='Instagram scraper allows to dump all the public posts and comments from a specified link to a profile.')
		parser.add_argument('-i', '--input_addr', help='Address of an instagram profile to scrape from', required=True)
		parser.add_argument('-o', '--output_file', help='Output file name', default="./instagram_dump" + "_" + datetime.datetime.now().strftime("%Y_%m_%d_%H_%M") + ".xlsx", required=False)
		parser.add_argument('-v', '--verbose', help='Show additional information or alerts', required=False, default=True, type=bool, choices=[True, False])
		args = vars(parser.parse_args())

		VERBOSE = args['verbose']

		self.pprint("Profile address: " + args['input_addr'])
		self.pprint("Output file name: " + args['output_file'])

		return args    

	##############################Main me
	#if __name__ == "__main__":
	#    #args = parseArgs()
	#    links = getLinks()
	#    #data = getDataFromPostList(links)#Single thread
	#    data = getDataFromPostList_Multithread(links)
	#    exportData(allPostData)