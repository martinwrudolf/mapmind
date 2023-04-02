from django.test import TestCase
from django.test import LiveServerTestCase
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from . import models
import time

# https://ordinarycoders.com/blog/article/testing-django-selenium
# https://www.selenium.dev/documentation/webdriver/getting_started/install_drivers/
# https://selenium-python.readthedocs.io/locating-elements.html#locating-hyperlinks-by-link-text
# https://stackoverflow.com/questions/33437372/django-test-user-password

class UserAccountTests(LiveServerTestCase): 
    def testValidRegister(self):
        service = Service(executable_path="./webdrivers/chromedriver")
        driver = webdriver.Chrome(service=service)
        driver.get(self.live_server_url)
        assert driver.current_url == self.live_server_url + "/accounts/login/"
        driver.find_element(By.LINK_TEXT, "Don't have an account?").click()
        assert driver.current_url == self.live_server_url  + "/register/"
        username = driver.find_element(By.ID, "username")
        password = driver.find_element(By.ID, "password")
        email = driver.find_element(By.ID, "email")
        username.send_keys("end2endTest")
        password.send_keys("mapmind493")
        email.send_keys("end2end@gmail.com")
        submit = driver.find_element(By.ID, "submit")
        submit.click()
        user = models.User.objects.get(username="end2endTest")
        assert user.email == "end2end@gmail.com"
        assert user.check_password("mapmind493")
        assert driver.current_url == self.live_server_url + "/accounts/login/"

    def testValidLogin(self):
        self.testValidRegister()

class NotebooksTests(LiveServerTestCase):
    pass

class SearchAndVisualizationTests(LiveServerTestCase):
    pass