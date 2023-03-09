import requests
from bs4 import BeautifulSoup
import csv

def extract_course_seat_data(course_url):
    """ 
    example course_url: https://courses.students.ubc.ca/cs/courseschedule?pname=subjarea&tname=subj-section&dept=GEM&course=530&section=101
    Returns four numbers in the order and also the course url: ['Total Seats Remaining:', 'Currently Registered:', 'General Seats Remaining:', 'Restricted Seats Remaining*:', course_url]
    """
    course_page = requests.get(course_url)
    soup = BeautifulSoup(course_page.text, 'lxml')

    seat_data = soup.find_all('td', string=['Total Seats Remaining:', 'Currently Registered:', 'General Seats Remaining:', 'Restricted Seats Remaining*:'])
    data = []
    for seat_d in seat_data:
        data.append(seat_d.parent.find_all('td')[1].text)
    
    data.append(course_url)
    
    return data


def extract_row_data(name, row):
    tds = row.find_all('td')
    data = [name]
    seat_data = []
    for index, td in enumerate(tds):
        data.append(td.text.strip())
        if index == 1:
            course_link = td.find('a', href=True)
            if course_link:
                url = 'https://courses.students.ubc.ca' + course_link['href']
                seat_data = extract_course_seat_data(url)
    data.extend(seat_data)
    return data

def extract_instructor_page_data(name, ubcid):
    url = f'https://courses.students.ubc.ca/cs/courseschedule?pname=inst&ubcid={ubcid}&catano=0&term=1&sessyr=2022&sesscd=W&campuscd=UBC'
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'lxml')
    table = soup.find('table', attrs={"class":"section-summary"})

    try:
        rows = table.find_all('tr')
    except AttributeError:
        print("NO COURSES FOUND:", url)
        return [[name, "NO COURSES FOUND", url]]

    all_data = []
    extract_row_data.previous_course_link = ""
    for row in rows[2:]:
        all_data.append(extract_row_data(name, row))

    return all_data

if __name__ == '__main__':
    all_rows = []
    with open('ubcid_data.csv', 'r') as f:
        heading = next(f) # Skip the header
        reader = csv.reader(f)
        for row in reader:
            all_rows.append(extract_instructor_page_data(row[0], row[1]))
    
    # write the data to a CSV file
    with open('course_data.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Name', 'Status', 'Section', 'Activity', 'Term', 'Mode of Delivery', 'Interval', 'Days', 'Start Time', 'End Time', 'Section Comments', 'Requires In-Person Attendance', 'Total Seats Remaining', 'Currently Registered', 'General Seats Remaining', 'Restricted Seats Remaining', 'Course URL'])
        for instructor_row in all_rows:
            for row in instructor_row:
                writer.writerow(row)

