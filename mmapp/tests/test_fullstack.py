from django.test import TestCase
from django.test import LiveServerTestCase
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.select import Select
from .. import models
import time
import os

# https://ordinarycoders.com/blog/article/testing-django-selenium
# https://www.selenium.dev/documentation/webdriver/getting_started/install_drivers/
# https://selenium-python.readthedocs.io/locating-elements.html#locating-hyperlinks-by-link-text
# https://stackoverflow.com/questions/33437372/django-test-user-password
# https://www.browserstack.com/guide/find-element-by-text-using-selenium#:~:text=text()%3A%20A%20built%2Din,on%20its%20exact%20text%20value.&text=contains()%3A%20Similar%20to%20the,based%20on%20partial%20text%20match.
# https://stackoverflow.com/questions/52029267/how-to-get-html5-validation-message-with-selenium
# https://www.browserstack.com/guide/get-text-of-an-element-in-selenium#:~:text=Cross%20Browser%20Compatibility-,getText()%20Method%20in%20Selenium,and%20back%20of%20the%20string.
# https://stackoverflow.com/questions/20996392/how-to-get-text-with-selenium-webdriver-in-python
# https://www.geeksforgeeks.org/get_attribute-element-method-selenium-python/
# https://stackoverflow.com/questions/7732125/clear-text-from-textarea-with-selenium
# https://stackoverflow.com/questions/39125633/how-to-click-on-confirmation-button-using-selenium-with-python
# https://www.tutorialspoint.com/how-to-get-all-the-options-in-the-dropdown-in-selenium
# https://www.selenium.dev/documentation/webdriver/support_features/select_lists/
# https://stackoverflow.com/questions/30697991/how-to-access-invisible-unordered-list-element-with-selenium-webdriver-using-jav

class UserAccountTests(LiveServerTestCase): 
    def setUp(self):
        self.service = service = Service(executable_path="./webdrivers/chromedriver")
        self.driver = webdriver.Chrome(service=self.service)
        self.driver.get(self.live_server_url)
        assert self.driver.current_url == self.live_server_url + "/accounts/login/"

    def testValidRegister(self):
        self.driver.find_element(By.LINK_TEXT, "Don't have an account?").click()
        time.sleep(3)
        assert self.driver.current_url == self.live_server_url  + "/register/"
        username = self.driver.find_element(By.ID, "username")
        password = self.driver.find_element(By.ID, "password")
        email = self.driver.find_element(By.ID, "email")
        username.send_keys("end2endTest")
        password.send_keys("mapmind493")
        email.send_keys("end2end@gmail.com")
        submit = self.driver.find_element(By.ID, "submit")
        submit.click()
        time.sleep(3)
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
        self.driver.find_element(By.ID, "register_error").text == "Username is not unique!"

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
        assert self.driver.find_element(By.ID, "register_error").text == "Email is not unique!"

    def testBlankUsernameRegister(self):
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
        assert username.get_attribute("validationMessage") == "Please fill in this field."

    def testBlankPasswordRegister(self):
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
        assert password.get_attribute("validationMessage") == "Please fill in this field."

    def testBlankEmailRegister(self):
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
        assert email.get_attribute("validationMessage") == "Please fill in this field."

    def testInvaildEmailNoAtRegister(self):
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
        assert "Please include an '@' in the email address" in email.get_attribute("validationMessage") 

    def testInvaildEmailNoDomainRegister(self):
        self.driver.find_element(By.LINK_TEXT, "Don't have an account?").click()
        assert self.driver.current_url == self.live_server_url  + "/register/"
        username = self.driver.find_element(By.ID, "username")
        password = self.driver.find_element(By.ID, "password")
        email = self.driver.find_element(By.ID, "email")
        username.send_keys("end2endTest")
        password.send_keys("mapmind493")
        email.send_keys("end2end@")
        submit = self.driver.find_element(By.ID, "submit")
        submit.click()
        assert self.driver.current_url == self.live_server_url + "/register/"
        assert "Please enter a part following '@'" in email.get_attribute("validationMessage") 

    def testShortPasswordRegister(self):
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
        assert  "Please lengthen this text to 8 characters or more" in password.get_attribute("validationMessage")

    def testValidLogin(self):
        self.testValidRegister()
        username = self.driver.find_element(By.ID, "id_username")
        password = self.driver.find_element(By.ID, "id_password")
        username.send_keys("end2endTest")
        password.send_keys("mapmind493")
        submit = self.driver.find_element(By.ID, "submit")
        submit.click()
        assert self.driver.current_url == self.live_server_url + "/"

    def testBlankUserLogin(self):
        self.testValidRegister()
        username = self.driver.find_element(By.ID, "id_username")
        password = self.driver.find_element(By.ID, "id_password")
        submit = self.driver.find_element(By.ID, "submit")
        password.send_keys("mapmind493")
        submit.click()
        assert self.driver.current_url == self.live_server_url + "/accounts/login/"
        assert username.get_attribute("validationMessage") == "Please fill in this field."
    
    def testBlankPasswordLogin(self):
        self.testValidRegister()
        username = self.driver.find_element(By.ID, "id_username")
        password = self.driver.find_element(By.ID, "id_password")
        submit = self.driver.find_element(By.ID, "submit")
        username.send_keys("end2endTest")
        submit.click()
        assert self.driver.current_url == self.live_server_url + "/accounts/login/"
        assert password.get_attribute("validationMessage") == "Please fill in this field."


    def testInvaildUserLogin(self):
        self.testValidRegister()
        username = self.driver.find_element(By.ID, "id_username")
        password = self.driver.find_element(By.ID, "id_password")
        username.send_keys("doesntexist")
        password.send_keys("mapmind493")
        submit = self.driver.find_element(By.ID, "submit")
        submit.click()
        assert self.driver.current_url == self.live_server_url + "/accounts/login/"
        assert self.driver.find_element(By.ID, "login_error").text == "Your username and password didn't match. Please try again."

    def testInvaildPasswordLogin(self):
        self.testValidRegister()
        username = self.driver.find_element(By.ID, "id_username")
        password = self.driver.find_element(By.ID, "id_password")
        username.send_keys("end2endTest")
        password.send_keys("mapmind49111111")
        submit = self.driver.find_element(By.ID, "submit")
        submit.click()
        assert self.driver.current_url == self.live_server_url + "/accounts/login/"
        assert self.driver.find_element(By.ID, "login_error").text == "Your username and password didn't match. Please try again."

    def testResetPassword(self):
        self.testValidRegister()
        self.driver.find_element(By.LINK_TEXT, "Lost password?").click()
        assert self.driver.current_url == self.live_server_url + "/accounts/password_reset/"
        email = self.driver.find_element(By.ID, "id_email")
        email.send_keys("end2end@gmail.com")
        self.driver.find_element(By.ID, "submit").click()
        assert self.driver.current_url == self.live_server_url + "/accounts/password_reset/done/"

    def testResetPasswordInvaildEmailNoAt(self):
        self.testValidRegister()
        self.driver.find_element(By.LINK_TEXT, "Lost password?").click()
        assert self.driver.current_url == self.live_server_url + "/accounts/password_reset/"
        email = self.driver.find_element(By.ID, "id_email")
        email.send_keys("end2end")
        self.driver.find_element(By.ID, "submit").click()
        assert self.driver.current_url == self.live_server_url + "/accounts/password_reset/"
        assert "Please include an '@' in the email address" in email.get_attribute("validationMessage")

    def testResetPasswordInvaildEmailNoDomain(self):
        self.testValidRegister()
        self.driver.find_element(By.LINK_TEXT, "Lost password?").click()
        assert self.driver.current_url == self.live_server_url + "/accounts/password_reset/"
        email = self.driver.find_element(By.ID, "id_email")
        email.send_keys("end2end@")
        self.driver.find_element(By.ID, "submit").click()
        assert self.driver.current_url == self.live_server_url + "/accounts/password_reset/" 
        print(email.get_attribute("validationMessage"))
        assert "Please enter a part following '@'" in email.get_attribute("validationMessage") 

    def testResetPasswordBlankEmail(self):
        self.testValidRegister()
        self.driver.find_element(By.LINK_TEXT, "Lost password?").click()
        assert self.driver.current_url == self.live_server_url + "/accounts/password_reset/"
        email = self.driver.find_element(By.ID, "id_email")
        self.driver.find_element(By.ID, "submit").click()
        assert self.driver.current_url == self.live_server_url + "/accounts/password_reset/"
        assert email.get_attribute("validationMessage") == "Please fill in this field."

    def testResetPasswordFromSettings(self):
        self.testValidLogin()
        self.driver.find_element(By.ID, "settings_nav").click()
        assert self.driver.current_url == self.live_server_url + "/settings"
        self.driver.find_element(By.ID, "reset_password").click()
        time.sleep(5)
        assert self.driver.current_url == self.live_server_url + "/accounts/password_reset/done/"
   
    def testChangeEmail(self):
        self.testValidLogin()
        self.driver.find_element(By.ID, "settings_nav").click()
        assert self.driver.current_url == self.live_server_url + "/settings"
        assert self.driver.find_element(By.ID, "email").get_attribute("value") == "end2end@gmail.com"
        self.driver.find_element(By.ID, "email").clear()
        self.driver.find_element(By.ID, "email").send_keys("end2end2@gmail.com")
        self.driver.find_element(By.ID, "submit_email").click()
        time.sleep(2)
        assert self.driver.current_url == self.live_server_url + "/settings"
        assert self.driver.find_element(By.ID, "email").get_attribute("value") == "end2end2@gmail.com"

    def testChangeUsername(self):
        self.testValidLogin()
        self.driver.find_element(By.ID, "settings_nav").click()
        assert self.driver.current_url == self.live_server_url + "/settings"
        assert self.driver.find_element(By.ID, "username").get_attribute("value") == "end2endTest"
        self.driver.find_element(By.ID, "username").clear()
        self.driver.find_element(By.ID, "username").send_keys("end2end2Test")
        self.driver.find_element(By.ID, "submit_username").click()
        time.sleep(2)
        assert self.driver.current_url == self.live_server_url + "/settings"
        assert self.driver.find_element(By.ID, "username").get_attribute("value") == "end2end2Test"

    def testChangeUsernameDuplicate(self):
        self.testValidLogin()
        self.driver.find_element(By.ID, "settings_nav").click()
        assert self.driver.current_url == self.live_server_url + "/settings"
        assert self.driver.find_element(By.ID, "username").get_attribute("value") == "end2endTest"
        self.driver.find_element(By.ID, "submit_username").click()
        assert self.driver.current_url == self.live_server_url + "/settings"
        assert self.driver.find_element(By.ID, "username").get_attribute("value") == "end2endTest"
        assert self.driver.find_element(By.ID, "username_error").text == "Username is not unique!"
    

    def testChangeEmailDuplicate(self):
        self.testValidLogin()
        self.driver.find_element(By.ID, "settings_nav").click()
        assert self.driver.current_url == self.live_server_url + "/settings"
        assert self.driver.find_element(By.ID, "email").get_attribute("value") == "end2end@gmail.com"
        self.driver.find_element(By.ID, "submit_email").click()
        assert self.driver.current_url == self.live_server_url + "/settings"
        assert self.driver.find_element(By.ID, "email").get_attribute("value") == "end2end@gmail.com"
        assert self.driver.find_element(By.ID, "email_error").text == "Email is not unique!"

    
    def testChangeEmailBlank(self):
        self.testValidLogin()
        self.driver.find_element(By.ID, "settings_nav").click()
        assert self.driver.current_url == self.live_server_url + "/settings"
        assert self.driver.find_element(By.ID, "email").get_attribute("value") == "end2end@gmail.com"
        self.driver.find_element(By.ID, "email").clear()
        self.driver.find_element(By.ID, "submit_email").click()
        assert self.driver.current_url == self.live_server_url + "/settings"
        assert self.driver.find_element(By.ID, "email").get_attribute("validationMessage") == "Please fill in this field."

    
    def testChangeUsernameBlank(self):
        self.testValidLogin()
        self.driver.find_element(By.ID, "settings_nav").click()
        assert self.driver.current_url == self.live_server_url + "/settings"
        assert self.driver.find_element(By.ID, "username").get_attribute("value") == "end2endTest"
        self.driver.find_element(By.ID, "username").clear()
        self.driver.find_element(By.ID, "submit_username").click()
        assert self.driver.current_url == self.live_server_url + "/settings"
        assert self.driver.find_element(By.ID, "username").get_attribute("validationMessage") == "Please fill in this field."

    def testChangeEmailInvaildNoAt(self):
        self.testValidLogin()
        self.driver.find_element(By.ID, "settings_nav").click()
        assert self.driver.current_url == self.live_server_url + "/settings"
        assert self.driver.find_element(By.ID, "email").get_attribute("value") == "end2end@gmail.com"
        self.driver.find_element(By.ID, "email").clear()
        self.driver.find_element(By.ID, "email").send_keys("end2end")
        self.driver.find_element(By.ID, "submit_email").click()
        assert "Please include an '@' in the email address" in self.driver.find_element(By.ID, "email").get_attribute("validationMessage") 

    def testChangeEmailInvaildNoDomain(self):
        self.testValidLogin()
        self.driver.find_element(By.ID, "settings_nav").click()
        assert self.driver.current_url == self.live_server_url + "/settings"
        assert self.driver.find_element(By.ID, "email").get_attribute("value") == "end2end@gmail.com"
        self.driver.find_element(By.ID, "email").clear()
        self.driver.find_element(By.ID, "email").send_keys("end2end@")
        self.driver.find_element(By.ID, "submit_email").click()
        assert "Please enter a part following '@'" in self.driver.find_element(By.ID, "email").get_attribute("validationMessage") 

    def testDeleteAccount(self):
        self.testValidLogin()
        self.driver.find_element(By.ID, "settings_nav").click()
        assert self.driver.current_url == self.live_server_url + "/settings"
        self.driver.find_element(By.ID, "delete_account").click()
        Alert(self.driver).accept()
        time.sleep(5)
        print(self.driver.current_url)
        assert self.driver.current_url == self.live_server_url + "/accounts/login/"

    def testLogout(self):
        self.testValidLogin()
        self.driver.find_element(By.ID, "logout_button").click()
        assert self.driver.current_url == self.live_server_url + "/accounts/logout/"
        
class NotebooksTests(LiveServerTestCase):
    def setUp(self):
        self.service = Service(executable_path="./webdrivers/chromedriver")
        self.driver = webdriver.Chrome(service=self.service)
        self.driver.get(self.live_server_url)
        assert self.driver.current_url == self.live_server_url + "/accounts/login/"
        self.driver.find_element(By.LINK_TEXT, "Don't have an account?").click()
        time.sleep(3)
        assert self.driver.current_url == self.live_server_url  + "/register/"
        username = self.driver.find_element(By.ID, "username")
        password = self.driver.find_element(By.ID, "password")
        email = self.driver.find_element(By.ID, "email")
        username.send_keys("end2endTest")
        password.send_keys("mapmind493")
        email.send_keys("end2end@gmail.com")
        submit = self.driver.find_element(By.ID, "submit")
        submit.click()
        time.sleep(3)
        assert self.driver.current_url == self.live_server_url + "/accounts/login/"
        username = self.driver.find_element(By.ID, "id_username")
        password = self.driver.find_element(By.ID, "id_password")
        username.send_keys("end2endTest")
        password.send_keys("mapmind493")
        submit = self.driver.find_element(By.ID, "submit")
        submit.click()
        assert self.driver.current_url == self.live_server_url + "/"
        self.driver.find_element(By.ID, "notebooks_nav").click()
        time.sleep(2)
        assert self.driver.current_url == self.live_server_url + "/notebooks"

    def testNotebookCreation(self):
        notebook = self.driver.find_element(By.ID, "notebook")
        notebook.send_keys("testnotebook")
        submit = self.driver.find_element(By.ID, "create_submit")
        submit.click()
        assert self.driver.current_url == self.live_server_url + "/notebooks"
        time.sleep(10)
        notebooks_select = Select(self.driver.find_element(By.ID, "notebooks-select"))
        assert len(notebooks_select.options) == 1
        assert notebooks_select.options[0].text == "testnotebook"
        notebook_id = notebooks_select.options[0].get_attribute("value")
        notebook_header = self.driver.find_element(By.ID, "heading-"+str(notebook_id))
        assert "testnotebook" in notebook_header.find_element(By.CLASS_NAME, "accordion-button").text 

    def testUploadNotes(self):
        self.testNotebookCreation()
        notebooks_select = Select(self.driver.find_element(By.ID, "notebooks-select"))
        notebook_id = notebooks_select.options[0].get_attribute("value")
        notebook_header = self.driver.find_element(By.ID, "heading-"+str(notebook_id))
        notebook_header.find_element(By.CSS_SELECTOR, "button.accordion-button").click()
        self.driver.find_element(By.ID, "file-"+str(notebook_id)).send_keys(os.path.abspath("./mmapp/tests/test_note_files/testNotes.txt"))
        self.driver.find_element(By.ID, "submit-"+str(notebook_id)).click()
        assert self.driver.current_url == self.live_server_url + "/notebooks"
        time.sleep(60)
        print(self.driver.find_element(By.ID, "collapse-"+str(notebook_id)).find_element(By.TAG_NAME, "li").text)
        assert "testNotes.txt" in self.driver.find_element(By.ID, "collapse-"+str(notebook_id)).find_element(By.TAG_NAME, "li").text


    def testUploadNotesInvaildFileFormat(self):
        self.testNotebookCreation()
        notebooks_select = Select(self.driver.find_element(By.ID, "notebooks-select"))
        notebook_id = notebooks_select.options[0].get_attribute("value")
        notebook_header = self.driver.find_element(By.ID, "heading-"+str(notebook_id))
        notebook_header.find_element(By.CSS_SELECTOR, "button.accordion-button").click()
        self.driver.find_element(By.ID, "file-"+str(notebook_id)).send_keys(os.path.abspath("./mmapp/tests/test_note_files/testNotes.html"))
        self.driver.find_element(By.ID, "submit-"+str(notebook_id)).click()
        assert self.driver.current_url == self.live_server_url + "/notebooks"
        time.sleep(10)
        assert self.driver.find_element(By.ID, "notebook_error").text == "File is not of correct format"

    def testUploadNotesInvalidFileSize(self):
        self.testNotebookCreation()
        notebooks_select = Select(self.driver.find_element(By.ID, "notebooks-select"))
        notebook_id = notebooks_select.options[0].get_attribute("value")
        notebook_header = self.driver.find_element(By.ID, "heading-"+str(notebook_id))
        notebook_header.find_element(By.CSS_SELECTOR, "button.accordion-button").click()
        self.driver.find_element(By.ID, "file-"+str(notebook_id)).send_keys(os.path.abspath("./mmapp/tests/test_note_files/test_too_large.docx"))
        self.driver.find_element(By.ID, "submit-"+str(notebook_id)).click()
        assert self.driver.current_url == self.live_server_url + "/notebooks"
        time.sleep(10)
        assert self.driver.find_element(By.ID, "notebook_error").text == "File is too large"

#     def testDeleteNotes(self):
#         pass

#     def testNotebookMerging(self):
#         pass

#     def testNotebookDeletion(self):
#         pass


class SearchAndVisualizationTests(LiveServerTestCase):
    def setUp(self):
        self.service = Service(executable_path="./webdrivers/chromedriver")
        self.driver = webdriver.Chrome(service=self.service)
        self.driver.get(self.live_server_url)
        assert self.driver.current_url == self.live_server_url + "/accounts/login/"
        self.driver.find_element(By.LINK_TEXT, "Don't have an account?").click()
        time.sleep(3)
        assert self.driver.current_url == self.live_server_url  + "/register/"
        username = self.driver.find_element(By.ID, "username")
        password = self.driver.find_element(By.ID, "password")
        email = self.driver.find_element(By.ID, "email")
        username.send_keys("end2endTest")
        password.send_keys("mapmind493")
        email.send_keys("end2end@gmail.com")
        submit = self.driver.find_element(By.ID, "submit")
        submit.click()
        time.sleep(3)
        assert self.driver.current_url == self.live_server_url + "/accounts/login/"
        username = self.driver.find_element(By.ID, "id_username")
        password = self.driver.find_element(By.ID, "id_password")
        username.send_keys("end2endTest")
        password.send_keys("mapmind493")
        submit = self.driver.find_element(By.ID, "submit")
        submit.click()
        assert self.driver.current_url == self.live_server_url + "/"
        self.driver.find_element(By.ID, "notebooks_nav").click()
        time.sleep(2)
        assert self.driver.current_url == self.live_server_url + "/notebooks"
        notebook = self.driver.find_element(By.ID, "notebook")
        notebook.send_keys("testnotebook")
        submit = self.driver.find_element(By.ID, "create_submit")
        submit.click()
        assert self.driver.current_url == self.live_server_url + "/notebooks"
        time.sleep(10)
        notebooks_select = Select(self.driver.find_element(By.ID, "notebooks-select"))
        assert len(notebooks_select.options) == 1
        assert notebooks_select.options[0].text == "testnotebook"
        notebook_id = notebooks_select.options[0].get_attribute("value")
        self.notebook_id = notebook_id
        notebook_header = self.driver.find_element(By.ID, "heading-"+str(notebook_id))
        assert "testnotebook" in notebook_header.find_element(By.CLASS_NAME, "accordion-button").text 
        notebooks_select = Select(self.driver.find_element(By.ID, "notebooks-select"))
        notebook_id = notebooks_select.options[0].get_attribute("value")
        notebook_header = self.driver.find_element(By.ID, "heading-"+str(notebook_id))
        notebook_header.find_element(By.CSS_SELECTOR, "button.accordion-button").click()
        self.driver.find_element(By.ID, "file-"+str(notebook_id)).send_keys(os.path.abspath("./mmapp/tests/test_note_files/testNotes.txt"))
        self.driver.find_element(By.ID, "submit-"+str(notebook_id)).click()
        assert self.driver.current_url == self.live_server_url + "/notebooks"
        time.sleep(60)
        print(self.driver.find_element(By.ID, "collapse-"+str(notebook_id)).find_element(By.TAG_NAME, "li").text)
        assert "testNotes.txt" in self.driver.find_element(By.ID, "collapse-"+str(notebook_id)).find_element(By.TAG_NAME, "li").text
        self.driver.find_element(By.ID, "search_nav").click()
        time.sleep(2)
        assert self.driver.current_url == self.live_server_url + "/"

    def testSearch(self):
        self.driver.find_element(By.ID, "search_words").find_keys("cpu thread system")
        self.driver.find_element(By.ID, "submit").click()
        time.sleep(45)
        assert self.driver.current_url == self.live_server_url + "/?search_words=cpu+thread+system&notebook=" + str(self.notebook_id)

    def testEmptySearch(self):
        self.driver.find_element(By.ID, "submit").click()
        assert self.driver.find_element(By.ID, "submit").get_attribute("validationMessage") == "Please fill in this field."


#     def testInspectNode(self):
#         pass
