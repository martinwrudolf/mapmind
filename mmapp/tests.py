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
# https://www.browserstack.com/guide/find-element-by-text-using-selenium#:~:text=text()%3A%20A%20built%2Din,on%20its%20exact%20text%20value.&text=contains()%3A%20Similar%20to%20the,based%20on%20partial%20text%20match.

class UserAccountTests(LiveServerTestCase): 
    def setUp(self):
        self.service = service = Service(executable_path="./webdrivers/chromedriver")
        self.driver = webdriver.Chrome(service=self.service)
        self.driver.get(self.live_server_url)
        assert self.driver.current_url == self.live_server_url + "/accounts/login/"

    def testValidRegister(self):
        self.driver.find_element(By.LINK_TEXT, "Don't have an account?").click()
        assert self.driver.current_url == self.live_server_url  + "/register/"
        username = self.driver.find_element(By.ID, "username")
        password = self.driver.find_element(By.ID, "password")
        email = self.driver.find_element(By.ID, "email")
        username.send_keys("end2endTest")
        password.send_keys("mapmind493")
        email.send_keys("end2end@gmail.com")
        submit = self.driver.find_element(By.ID, "submit")
        submit.click()
        assert self.driver.current_url == self.live_server_url + "/accounts/login/"

    def testDupilcateUsernameRegister(self):
        self.testValidRegister()
        self.driver.find_element(By.LINK_TEXT, "Don't have an account?").click()
        assert self.driver.current_url == self.live_server_url  + "/register/"
        username = self.driver.find_element(By.ID, "username")
        password = self.driver.find_element(By.ID, "password")
        email = self.driver.find_element(By.ID, "email")
        username.send_keys("end2endTest")
        password.send_keys("mapmind493")
        email.send_keys("end2end2@gmail.com")
        submit = self.driver.find_element(By.ID, "submit")
        submit.click()
        assert self.driver.current_url == self.live_server_url + "/register/"

    def testDupilcateEmailRegister(self):
        self.testValidRegister()
        self.driver.find_element(By.LINK_TEXT, "Don't have an account?").click()
        assert self.driver.current_url == self.live_server_url  + "/register/"
        username = self.driver.find_element(By.ID, "username")
        password = self.driver.find_element(By.ID, "password")
        email = self.driver.find_element(By.ID, "email")
        username.send_keys("end2endTest2")
        password.send_keys("mapmind493")
        email.send_keys("end2end@gmail.com")
        submit = self.driver.find_element(By.ID, "submit")
        submit.click()
        assert self.driver.current_url == self.live_server_url + "/register/"

    def testBlankUsername(self):
        self.driver.find_element(By.LINK_TEXT, "Don't have an account?").click()
        assert self.driver.current_url == self.live_server_url  + "/register/"
        username = self.driver.find_element(By.ID, "username")
        password = self.driver.find_element(By.ID, "password")
        email = self.driver.find_element(By.ID, "email")
        password.send_keys("mapmind493")
        email.send_keys("end2end@gmail.com")
        submit = self.driver.find_element(By.ID, "submit")
        submit.click()
        assert self.driver.current_url == self.live_server_url + "/register/"


    def testBlankPassword(self):
        self.driver.find_element(By.LINK_TEXT, "Don't have an account?").click()
        assert self.driver.current_url == self.live_server_url  + "/register/"
        username = self.driver.find_element(By.ID, "username")
        password = self.driver.find_element(By.ID, "password")
        email = self.driver.find_element(By.ID, "email")
        username.send_keys("end2endTest")
        email.send_keys("end2end@gmail.com")
        submit = self.driver.find_element(By.ID, "submit")
        submit.click()
        assert self.driver.current_url == self.live_server_url + "/register/"

    def testBlankEmail(self):
        self.driver.find_element(By.LINK_TEXT, "Don't have an account?").click()
        assert self.driver.current_url == self.live_server_url  + "/register/"
        username = self.driver.find_element(By.ID, "username")
        password = self.driver.find_element(By.ID, "password")
        email = self.driver.find_element(By.ID, "email")
        username.send_keys("end2endTest")
        password.send_keys("mapmind493")
        submit = self.driver.find_element(By.ID, "submit")
        submit.click()
        assert self.driver.current_url == self.live_server_url + "/register/"

    def testInvaildEmail(self):
        self.driver.find_element(By.LINK_TEXT, "Don't have an account?").click()
        assert self.driver.current_url == self.live_server_url  + "/register/"
        username = self.driver.find_element(By.ID, "username")
        password = self.driver.find_element(By.ID, "password")
        email = self.driver.find_element(By.ID, "email")
        username.send_keys("end2endTest")
        password.send_keys("mapmind493")
        email.send_keys("end2end")
        submit = self.driver.find_element(By.ID, "submit")
        submit.click()
        assert self.driver.current_url == self.live_server_url + "/register/"


    def testShortPassword(self):
        self.driver.find_element(By.LINK_TEXT, "Don't have an account?").click()
        assert self.driver.current_url == self.live_server_url  + "/register/"
        username = self.driver.find_element(By.ID, "username")
        password = self.driver.find_element(By.ID, "password")
        email = self.driver.find_element(By.ID, "email")
        username.send_keys("end2endTest")
        password.send_keys("mm")
        email.send_keys("end2end@gmail.com")
        submit = self.driver.find_element(By.ID, "submit")
        submit.click()
        assert self.driver.current_url == self.live_server_url + "/register/"

    def testValidLogin(self):
        self.testValidRegister()
        username = self.driver.find_element(By.ID, "id_username")
        password = self.driver.find_element(By.ID, "id_password")
        username.send_keys("end2endTest")
        password.send_keys("mapmind493")
        submit = self.driver.find_element(By.ID, "submit")
        submit.click()
        assert self.driver.current_url == self.live_server_url + "/"

    def testInvaildUser(self):
        self.testValidRegister()
        username = self.driver.find_element(By.ID, "id_username")
        password = self.driver.find_element(By.ID, "id_password")
        username.send_keys("doesntexist")
        password.send_keys("mapmind493")
        submit = self.driver.find_element(By.ID, "submit")
        submit.click()
        assert self.driver.current_url == self.live_server_url + "/accounts/login/"

    def testInvaildPassword(self):
        self.testValidRegister()
        username = self.driver.find_element(By.ID, "id_username")
        password = self.driver.find_element(By.ID, "id_password")
        username.send_keys("end2endTest")
        password.send_keys("mapmind49111111")
        submit = self.driver.find_element(By.ID, "submit")
        submit.click()
        assert self.driver.current_url == self.live_server_url + "/accounts/login/"

    def testResetPassword(self):
        self.testValidRegister()
        self.driver.find_element(By.LINK_TEXT, "Lost password?").click()
        assert self.driver.current_url == self.live_server_url + "/accounts/password_reset/"
        email = self.driver.find_element(By.ID, "id_email")
        email.send_keys("end2end@gmail.com")
        self.driver.find_element(By.ID, "submit").click()
        assert self.driver.current_url == self.live_server_url + "/accounts/password_reset/done/"

    def testResetPasswordInvaildEmail(self):
        self.testValidRegister()
        self.driver.find_element(By.LINK_TEXT, "Lost password?").click()
        assert self.driver.current_url == self.live_server_url + "/accounts/password_reset/"
        email = self.driver.find_element(By.ID, "id_email")
        email.send_keys("end2end")
        self.driver.find_element(By.ID, "submit").click()
        assert self.driver.current_url == self.live_server_url + "/accounts/password_reset/"

    def testResetPasswordBlankEmail(self):
        self.testValidRegister()
        self.driver.find_element(By.LINK_TEXT, "Lost password?").click()
        assert self.driver.current_url == self.live_server_url + "/accounts/password_reset/"
        email = self.driver.find_element(By.ID, "id_email")
        self.driver.find_element(By.ID, "submit").click()
        assert self.driver.current_url == self.live_server_url + "/accounts/password_reset/"

    def testResetPasswordFromSettings(self):
        self.testValidRegister()
        self.testValidLogin()
        self.driver.find_element(By.ID, "settings_nav").click()
        assert self.driver.current_url == self.live_server_url + "/settings"

    def testChangeEmail(self):
        self.testValidRegister()
        self.testValidLogin()
        self.driver.find_element(By.ID, "settings_nav").click()
        assert self.driver.current_url == self.live_server_url + "/settings"
        assert self.driver.find_element(By.ID, "email").getAttribute("value") == "end2end@gmail.com"
        self.driver.find_element(By.ID, "email").send_keys("end2end2@gmail.com")
        self.driver.find_element(By.ID, "submit_email").click()
        assert self.driver.current_url == self.live_server_url + "/settings"
        assert self.driver.find_element(By.ID, "email").getAttribute("value") == "end2end2@gmail.com"

    def testChangeUsername(self):
        self.testValidRegister()
        self.testValidLogin()
        self.driver.find_element(By.ID, "settings_nav").click()
        assert self.driver.current_url == self.live_server_url + "/settings"
        assert self.driver.find_element(By.ID, "username").getAttribute("value") == "end2endTest"
        self.driver.find_element(By.ID, "username").send_keys("end2end2Test")
        self.driver.find_element(By.ID, "submit_username").click()
        assert self.driver.current_url == self.live_server_url + "/settings"
        assert self.driver.find_element(By.ID, "username").getAttribute("value") == "end2endTest2"

    def testChangeEmailDuplicate(self):
        self.testValidRegister()
        self.testValidLogin()
        self.driver.find_element(By.ID, "settings_nav").click()
        self.driver.current_url == self.live_server_url + "/settings"

    def testChangeUsernameDuplicate(self):
        self.testValidRegister()
        self.testValidLogin()
        self.driver.find_element(By.ID, "settings_nav").click()
        self.driver.current_url == self.live_server_url + "/settings"

    
    def testChangeEmailBlank(self):
        self.testValidRegister()
        self.testValidLogin()
        self.driver.find_element(By.ID, "settings_nav").click()
        assert self.driver.current_url == self.live_server_url + "/settings"
        assert self.driver.find_element(By.ID, "email").getAttribute("value") == "end2end@gmail.com"
        self.driver.find_element(By.ID, "email").send_keys("")
        self.driver.find_element(By.ID, "submit_email").click()
        assert self.driver.current_url == self.live_server_url + "/settings"
        assert self.driver.find_element(By.ID, "email").getAttribute("value") == "end2end2@gmail.com"

    
    def testChangeUsernameBlank(self):
        self.testValidRegister()
        self.testValidLogin()
        self.driver.find_element(By.ID, "settings_nav").click()
        self.driver.current_url == self.live_server_url + "/settings"

    def testChangeEmailInvaild(self):
        self.testValidRegister()
        self.testValidLogin()
        self.driver.find_element(By.ID, "settings_nav").click()
        self.driver.current_url == self.live_server_url + "/settings"

    def testDeleteAccount(self):
        self.testValidRegister()
        self.testValidLogin()
        self.driver.find_element(By.ID, "settings_nav").click()
        self.driver.current_url == self.live_server_url + "/settings"
        
class NotebooksTests(LiveServerTestCase):
    def setUp(self):
        self.service = service = Service(executable_path="./webdrivers/chromedriver")
        self.driver = webdriver.Chrome(service=self.service)
        self.driver.get(self.live_server_url)
        assert self.driver.current_url == self.live_server_url + "/accounts/login/"
        self.driver.find_element(By.LINK_TEXT, "Don't have an account?").click()
        assert self.driver.current_url == self.live_server_url  + "/register/"
        username = self.driver.find_element(By.ID, "username")
        password = self.driver.find_element(By.ID, "password")
        email = self.driver.find_element(By.ID, "email")
        username.send_keys("end2endTest")
        password.send_keys("mapmind493")
        email.send_keys("end2end@gmail.com")
        submit = self.driver.find_element(By.ID, "submit")
        submit.click()
        assert self.driver.current_url == self.live_server_url + "/accounts/login/"
        username = self.driver.find_element(By.ID, "id_username")
        password = self.driver.find_element(By.ID, "id_password")
        username.send_keys("end2endTest")
        password.send_keys("mapmind493")
        submit = self.driver.find_element(By.ID, "submit")
        submit.click()
        assert self.driver.current_url == self.live_server_url + "/"
        notebookNav = self.driver.find_element(By.ID, "notebooks_nav")
        notebookNav.click()
        self.driver.current_url == self.live_server_url + "/notebooks"

    def testNotebookCreation(self):
        pass

    def testUpload(self):
        pass

    def testUploadInvaildFileFormat(self):
        pass

    def testUploadInvalidFileSize(self):
        pass

    def testNotebookMerging(self):
        pass

    def testNotebookDeletion(self):
        pass


class SearchAndVisualizationTests(LiveServerTestCase):
    def setUp(self):
        self.service = service = Service(executable_path="./webdrivers/chromedriver")
        self.driver = webdriver.Chrome(service=self.service)
        self.driver.get(self.live_server_url)
        assert self.driver.current_url == self.live_server_url + "/accounts/login/"
        self.driver.find_element(By.LINK_TEXT, "Don't have an account?").click()
        assert self.driver.current_url == self.live_server_url  + "/register/"
        username = self.driver.find_element(By.ID, "username")
        password = self.driver.find_element(By.ID, "password")
        email = self.driver.find_element(By.ID, "email")
        username.send_keys("end2endTest")
        password.send_keys("mapmind493")
        email.send_keys("end2end@gmail.com")
        submit = self.driver.find_element(By.ID, "submit")
        submit.click()
        assert self.driver.current_url == self.live_server_url + "/accounts/login/"
        username = self.driver.find_element(By.ID, "id_username")
        password = self.driver.find_element(By.ID, "id_password")
        username.send_keys("end2endTest")
        password.send_keys("mapmind493")
        submit = self.driver.find_element(By.ID, "submit")
        submit.click()
        assert self.driver.current_url == self.live_server_url + "/"

    def testSearch(self):
        pass

    def testEmptySearch(self):
        pass

    def testSearchWithoutNotebook(self):
        pass

    def testInspectNode(self):
        pass