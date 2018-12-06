# step 1
import requests # HTTP 요청을 보내는 모듈
# step 2
import urllib.robotparser # answers questions about whether or not a particular user agent can fetch a URL on the Web site that published the robots.txt file
# step 3
from pymongo import MongoClient
# step 4
import time
from bs4 import BeautifulSoup
from selenium import webdriver # Chrome Driver를 사용하게끔 하기 위함
from selenium.webdriver.common.by import By # Set of supported locator strategies
from selenium.webdriver.support.ui import WebDriverWait # selenium.webdriver.support.select
from selenium.webdriver.support import expected_conditions as EC # 예외 처리를 위함


# step 1: 퍼머링크 접속 과정 및 http 응답 상태 확인
try:
    driver = webdriver.Chrome("C:/driver/chromedriver.exe")
    driver.get("http://ticket.interpark.com") # Loads a web page in the current browser session

    s2 = BeautifulSoup(driver.page_source, "html.parser")
    s3 = s2.find("a", class_ = "btn_ranking")["href"]

    driver.get(s3) # Loads a web page in the current browser session
    driver.implicitly_wait(5) # Sets a sticky timeout to implicitly wait for an element to be found, or a command to complete

    driver.execute_script("fnRankingMore(this, '01003', 'D')") # 랭킹 더보기 click
    driver.implicitly_wait(5)

    driver.find_element_by_xpath('/html/body/div[6]/div[3]/div/div[3]/ul/li[3]/a').click() # 월간 click
    driver.implicitly_wait(5)
    
    url = "http://ticket.interpark.com/contents/Ranking/RankList?pKind=01003&pCate=01003&pType=M&pDate="
    r = requests.get(s3)

except Exception as e:
    print("****** step 1 error:", e)

print("####### step 1 #######")
print("http 응답 상태 확인 여부:", r.status_code)
print("incoding 정보 확인:", r.encoding)
print("HTTP 헤더의 값:", r.headers['content-type'])


# step 2: crawling 가능 여부 확인
print("\n####### step 2 #######")
rp = urllib.robotparser.RobotFileParser()
rp.set_url("http://ticket.interpark.com/contents/Ranking/RankList?pKind=01003&pCate=01003&pType=M&pDate=/robots.txt")
rp.read()
data = rp.can_fetch("mybot", url)
print("crawling 가능 여부:", data)


# step 3: pymongo
print("\n####### step 3 #######")
try:
    client = MongoClient('localhost', 27017)
    db = client.project
    collection = db.crawling12
except Exception as e:
    print('****** mongoDB error:', e)


# step 4: crawler & scraper
print("\n####### step 4 #######")
driver.get(url)
driver.implicitly_wait(5) 

try:
    soup = BeautifulSoup(driver.page_source, "html.parser")
    boxItems = soup.select(".rankBody")
    count = 0 # insert 횟수를 파악하기 위함

    for boxItem in boxItems:
        # scraping 후 data 정제
        title = boxItem.select(".prdInfo > a > b")[0].string
        title = str(title).strip(" ")
        place = boxItem.select(".prdInfo > a > b")[0]
        place = str(place.next_sibling).replace("\n", "").replace("\t", "").strip(" ")
        duration = boxItem.select(".prdDuration")[0].text
        duration = duration.replace("\n", "").replace("\t", "").replace(" ", "")
        marketShare = boxItem.select("td > b")[0].string

        title = str(title)
        place = str(place)
        duration = str(duration)
        marketShare = str(marketShare)

        count += 1
        print("count 횟수: ", count)    

        # 정제된 데이터 dictionary화
        info = {
            '공연 제목' : title,
            '공연 장소' : place,
            '공연 기간' : duration,
            '판매 점유율' : marketShare
        }
        # mongoDB에 insert
        collection.insert(info)

except Exception as e:
    print("****** page parsing or crawler error", e)

finally:
    for i in collection.find({},{"공연 제목":1,"공연 장소":1,"공연 기간":1,"판매 점유율":1}):
        # if i[5]==1 and i[6]==2:
        if i['공연 기간'][5]=='1' and i['공연 기간'][6]=='2':
            print("제목:",i["공연 제목"], end="\n")
            print("장소:",i["공연 장소"], end="\n")
            print("기간:",i["공연 기간"], end="\n")
            print("판매 점유율:",i["판매 점유율"], end="\n\n")

    time.sleep(5)
    driver.close() # webdrvier
    client.close() # mongoDB