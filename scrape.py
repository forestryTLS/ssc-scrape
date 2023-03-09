from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv

SESSION_YEAR = '2022'
SESSION = 'W'

def add_ids_to_dict(data_dict, subject_area):
        # Create a new instance of the Chrome driver
    driver = webdriver.Chrome('./chromedriver.exe')
    # Navigate to the page
    driver.get(f'https://courses.students.ubc.ca/cs/courseschedule?instSearchName=&sesscd={SESSION}&pname=instsearch&tname=instsearch&sessyr={SESSION_YEAR}')

    subject_area_input = driver.find_element(By.NAME, 'instSearchSubj')
    subject_area_input.send_keys(subject_area)
    
    # Find the Search button and click it
    search_button = driver.find_element(By.NAME, 'submit')
    search_button.click()

    # Extract the search results
    wait = WebDriverWait(driver, 20)
    main_table = wait.until(EC.presence_of_element_located((By.ID, 'mainTable')))


    rows = main_table.find_elements(By.XPATH, ".//tbody/tr")
    # loop through each row and extract the relevant information
    for row in rows:
        # get the full name from the first column
        full_name = row.find_element(By.XPATH, ".//td/a").text
        ubcid = row.find_element(By.XPATH, ".//td/a").get_attribute("href").split("ubcid=")[1].split('&')[0]
        # add the extracted data to the list
        
        print(full_name, ubcid)
        if full_name not in data_dict:
            data_dict[full_name] = ubcid
    
    driver.quit()
    
    return data_dict
    

if __name__ == "__main__":
    data_dict = {}
    
    course_codes = ["FRST", "BEST", "CONS", "FCOR", "FOPE", "FOPR", "GEM", "UFOR", "WOOD"]
    for code in course_codes:
        print(f"{'STARTING TO FIND INSTRUCTORS FOR COURSE ' + code:*^20} ")
        data_dict = add_ids_to_dict(data_dict, code)
    
    # write the data to a CSV file
    with open('data.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['name', 'ubcid'])
        for name, ubcid in data_dict.items():
            writer.writerow([name, ubcid])

