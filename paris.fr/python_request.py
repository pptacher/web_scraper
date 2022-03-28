import os
import re
import uuid
import sys, traceback, time, datetime

from urllib.request import urlopen, Request
import json
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

# convert cookies in html message to json format.

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

with open("data.json", "r") as file:
    data = json.load(file)

url = "https://teleservices.paris.fr/rdvtitres/jsp/site/Portal.jsp?page=appointmentsearch&view=search&category=titres"

phony_data = {
    "name" : "username",
    "password" : "password"
}
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
poll_period = 0.02 #time between http requests for availability to server in seconds.

while "Merci de renouveler votre demande dans quelques minutes" in html or \
                        "Tous les rendez-vous ont" in  html or \
                        "Aucun rendez-vous n'est actuellement disponible." in  html or \
                        "Ville de Paris pour cette semaine ont tous" in html or \
                        "Le 3975 n’est pas en mesure de vous proposer des rendez-vous" in  html or \
                        "Les  5 600" in html or \
                        "Maintenance" in html or \
                        "Le 3975 n’est pas en mesure de vous proposer des rendez-vous" in  html or \
                        "Les  5 500" in html:

    req = Request(url, data=jsonData, headers={
                        "content-type" : "application/json",
                        "Cookie" : cookies
                        })
    html = urlopen(req).read().decode('utf-8')
    time.sleep(poll_period)

parsed_html = BeautifulSoup(html,features="lxml")
a_element = parsed_html.find('a', id=re.compile("appointment_first_slot$"))
url1 = a_element['href']
date_time = a_element.contents

req1 = Request(url1, data=jsonData, headers={
    "content-type" : "application/json",
    "Cookie" : cookies
})

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

    elem = driver.find_element(By.NAME,"save")
    elem.send_keys(Keys.RETURN)

except NoSuchElementException as e:
    #with open(str(uuid.uuid4()), encoding="utf-8", mode="w") as file:
    #    file.write(driver.page_source)
    print(traceback.format_exc())
    driver.close()
    quit()

title = "Success"
message = f"Slot available on {date_time}."

command = f'''
osascript -e 'display notification "{message}" with title "{title}"'
'''
os.system(command)

command = f'''
osascript sendMessage.scpt {data["phone"]} "Book available slot on {date_time}."
'''
os.system(command)

time.sleep(300) # wait for user to solve captcha.
driver.close()
