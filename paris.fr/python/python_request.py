import os
import re
import uuid
import sys, traceback, time, datetime

from urllib.request import urlopen, Request
from urllib.parse import urlparse, parse_qs, urlencode
import json
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

# convert cookies in html response message to json format as described in RFC6265. TO DO: handle multiple cookies.
def parse_dict_cookies(cookies):
    result = {}
    for index, item in enumerate(cookies.split(';')):
        if index == 0:
            name, value = item.split('=', 1)
            result['name'] = name
            result['value'] = value
            continue
        item = item.strip()
        if not item:
            continue
        if '=' not in item:
            result[item] = True
            continue
        name, value = item.split('=', 1)
        result[name] = value
    return result

def processing_flush(n, index=10):
    sys.stdout.write(f"\r\033[1mPolling the server\033[0m %s" % (index * " "))
    sys.stdout.write(f"\r\033[1mPolling the server\033[0m %s" % ((n % index)* "."))
    sys.stdout.flush()

with open("data.json", "r") as file:
    data = json.load(file)

url = "https://teleservices.paris.fr/rdvtitres/jsp/site/Portal.jsp?page=appointmentsearch&view=search&category=titres"

phony_data = {
    "name" : "username",
    "password" : "password"
}

while True:

    jsonData = json.dumps(phony_data).encode('utf-8')
    req = Request(url, data=jsonData, headers={
                    'content-type': 'application/json'
                    })
    with urlopen(req) as response:
        html = response.read().decode('utf-8')
        cookies = response.getheader("Set-Cookie")
    parsed_cookies = parse_dict_cookies(cookies)
    driver = webdriver.Safari()
    driver.add_cookie(parsed_cookies)
    poll_period = 0.5 #time before sending new http request for availability to server in seconds.
    #print(f"\033[1mPolling the server...\033[0m")
    i = 0

    while "Merci de renouveler votre demande dans quelques minutes" in html or \
                        "Tous les rendez-vous ont" in  html or \
                        "Veuillez en choisir un autre." in html or \
                        "Aucun rendez-vous n'est actuellement disponible." in  html or \
                        "Ville de Paris pour cette semaine ont tous" in html or \
                        "Le 3975 n???est pas en mesure de vous proposer des rendez-vous" in  html or \
                        "Les  5 600" in html or \
                        "Maintenance" in html or \
                        "Le 3975 n???est pas en mesure de vous proposer des rendez-vous" in  html or \
                        "Les  5 500" in html:
        processing_flush(i)
        time.sleep(poll_period)
        req = Request(url, data=jsonData, headers={
                        "content-type" : "application/json",
                        "Cookie" : cookies
                        })
        html = urlopen(req).read().decode('utf-8')
        i = i + 1
    print('\n')
    parsed_html = BeautifulSoup(html,features="lxml")
    a_element = parsed_html.find('a', id=re.compile("appointment_first_slot$"))
    o = urlparse(a_element['href'])
    dict = parse_qs(o.query)
    dict.pop('anchor',None)
    dict['anchor'] = ''
    url1 = o._replace(query=urlencode(dict,doseq=True)).geturl() + "#step3"
    #print(url1)

    #url1 = a_element['href'] + "&anchor=#step3"
    #date_time = re.sub("[\[\]']",'',str(a_element.contents))
    date_time = a_element.text

    driver.get(url1)
    WebDriverWait(driver, 10).until(
        lambda wd: wd.execute_script("return document.readyState") == "complete"
        )

    try:

        elem = driver.find_element(By.XPATH,"//input[@size='10'][@type='text']")
        elem.clear()
        elem.send_keys(data["phone"])

        elem = driver.find_element(By.XPATH,"//input[@size='5'][@type='text']")
        elem.clear()
        elem.send_keys(data["postal_code"])

        elem = driver.find_element(By.NAME,"lastname")
        elem.clear()
        elem.send_keys(data["last_name"])

        elem = driver.find_element(By.NAME,"firstname")
        elem.clear()
        elem.send_keys(data["first_name"])

        elem = driver.find_element(By.NAME,"email")
        elem.clear()
        elem.send_keys(data["email"])

        elem = driver.find_element(By.NAME,"emailConfirm")
        elem.clear()
        elem.send_keys(data["email"])

        old_url = driver.current_url
        elem = driver.find_element(By.NAME,"save")
        elem.send_keys(Keys.RETURN)

        time.sleep(0.5)
        parsed_html = BeautifulSoup(driver.page_source,features="lxml")
        #input_element = parsed_html.find('h2', class_="current stepTitle")
        #if input_element is not None and input_element['id'] == "step4":
            #break#

        o = urlparse(driver.current_url)
        if o.fragment == 'step4':
            break

    except NoSuchElementException as e:
        #with open(str(uuid.uuid4()), encoding="utf-8", mode="w") as file:
            #file.write(driver.page_source)
        print(traceback.format_exc())

    h_element = parsed_html.find('div', class_="alert alert-danger")
    if h_element is not None:
        print('\033[93m' + h_element.text + '\033[0m')

    driver.close()
    #quit()
    print(f"\033[1mRetrying...\033[0m")


title = "Success"
message = "Slot available."

command = f'''
osascript -e 'display notification "{message}" with title "{title}"'
'''
os.system(command)

message = f'''
Book available slot on {date_time}.
'''
command = f'''
osascript sendMessage.scpt {data["phone"]} "{message}"
'''
os.system(command)
input("Press Enter after solving CAPTCHA.")   # wait for user to solve captcha.

try:
    driver.close()
except:
    pass
