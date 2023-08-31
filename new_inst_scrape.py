import requests
from bs4 import BeautifulSoup
import csv
import concurrent.futures
import queue

SESSION_YEAR = '2023'
SESSION = 'W'

def extract_course_seat_data_and_other_info(course_url):
    """ 
    example course_url: https://courses.students.ubc.ca/cs/courseschedule?pname=subjarea&tname=subj-section&dept=GEM&course=530&section=101
    Returns four numbers in the order and also the course url: ['Course Name', 'Credits', 'Location', 'Date Range', 'Instructors', 'TeacherNumber', 'TAs', 'TANumber', 'Total Seats Remaining:', 'Currently Registered:', 'General Seats Remaining:', 'Restricted Seats Remaining*:', course_url]
    """
    course_page = requests.get(course_url)
    soup = BeautifulSoup(course_page.text, 'lxml')
    data = []
    
    courseName = soup.find('h5')
    data.append(courseName.text)
    # Find the div with id="cdfText" as the <p> with credit info is below it
    cdf_div = soup.find('div', {'id': 'cdfText'})
    credit_p = cdf_div.find_next_sibling('p')
    data.append(credit_p.text.split()[1])
    
    # The next <p> contains Location
    location_p = credit_p.find_next_sibling('p')
    data.append(location_p.text.split()[1])
    
    term_b = location_p.find_next_sibling('b')
    date_range = term_b.next_sibling.strip()
    data.append(date_range)

    potential_instructor_ta_table = cdf_div.find_next_sibling('table').find_next_sibling('table')
    instructor_ta_table = potential_instructor_ta_table.find_next_sibling('table')
    all_rows = instructor_ta_table.find_all('tr')
    teacher_list = []
    ta_list = []
    isTeachers = True
    for row in all_rows:
        tds = row.find_all('td')
        if tds[0].text.strip() == 'TA:':
            isTeachers = False
        teacher_list.append(tds[1].text) if isTeachers else ta_list.append(tds[1].text)
    # print(*teacher_list)
    # print("TA's ARE", *ta_list)
    if teacher_list[0].isdigit(): # This happens when for some reason there is no additional table such as for https://courses.students.ubc.ca/cs/courseschedule?pname=subjarea&tname=subj-section&dept=FRST&course=498&section=944&sessyr=2023&sesscd=S
        all_rows = potential_instructor_ta_table.find_all('tr')
        teacher_list = []
        ta_list = []
        isTeachers = True
        for row in all_rows:
            tds = row.find_all('td')
            if tds[0].text.strip() == 'TA:':
                isTeachers = False
            teacher_list.append(tds[1].text) if isTeachers else ta_list.append(tds[1].text)
        
    data.append(teacher_list)
    data.append(len(teacher_list))
    data.append(ta_list)
    data.append(len(ta_list))
    
    seat_data = soup.find_all('td', string=['Total Seats Remaining:', 'Currently Registered:', 'General Seats Remaining:', 'Restricted Seats Remaining*:'])
    for seat_d in seat_data:
        data.append(seat_d.parent.find_all('td')[1].text)

    if (len(seat_data) < 3):
        data.append('')
        data.append('')
        data.append('')
        data.append('')
    
    data.append(course_url)
    
    return data


def extract_row_data(name, row):
    tds = row.find_all('td')
    data = [name, SESSION_YEAR, SESSION]
    seat_data = []
    for index, td in enumerate(tds):
        if index == 1:
            if td.text.strip() == "":
                data.append("")
                data.append("")
                continue
            course, code, section = td.text.strip().split()
            course_code = course + " " + code
            data.append(course_code)
            data.append(section)
            course_link = td.find('a', href=True)
            if course_link:
                url = f"https://courses.students.ubc.ca{course_link['href']}&sessyr={SESSION_YEAR}&sesscd={SESSION}"
                seat_data = extract_course_seat_data_and_other_info(url)
        elif index == 3:
            data.append(SESSION + td.text.strip())
        else:
            data.append(td.text.strip())
            
    data.extend(seat_data)
    return data

def extract_instructor_page_data(name, ubcid):
    url = f'https://courses.students.ubc.ca/cs/courseschedule?pname=inst&ubcid={ubcid}&catano=0&sessyr={SESSION_YEAR}&sesscd={SESSION}&campuscd=UBC'
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'lxml')
    table = soup.find('table', attrs={"class":"section-summary"})
    default_array = [[name, SESSION_YEAR, SESSION, "NO COURSES FOUND", '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', url]]
    try:
        rows = table.find_all('tr')
    except AttributeError:
        return default_array

    all_data = []

    for row in rows[2:]:
        all_data.append(extract_row_data(name, row))

    if len(all_data) == 0:
        return default_array
    
    return all_data

def extract_data_worker(q, name, ubcid):
    data = extract_instructor_page_data(name, ubcid)
    q.put(data)

# if __name__ == '__main__':
#     print(f"STARTING FOR {SESSION_YEAR} {SESSION} SINGLE THREAD")
#     all_rows = []
#     with open('test_ids.csv', 'r') as f:
#         heading = next(f) # Skip the header
#         reader = csv.reader(f)
#         count = 0
#         for row in reader:
#             all_rows.append(extract_instructor_page_data(row[0], row[1]))
#             count += 1
#             print("FINISHED: " + str(count))
    
#     # write the data to a CSV file
#     with open(f'{SESSION_YEAR}_{SESSION}_raw.csv', 'w', newline='') as file:
#         writer = csv.writer(file)
#         writer.writerow(['Name', 'Year', 'Session', 'Status', 'Course Code', 'Section', 'Activity', 'Term', 'Mode of Delivery', 'Interval', 'Days', 'Start Time', 'End Time', 'Section Comments', 'Requires In-Person Attendance', 'Course Name', 'Credits', 'Location', 'Date Range', 'Instructors', 'TeacherNumber', 'TAs', 'TANumber', 'Total Seats Remaining', 'Currently Registered', 'General Seats Remaining', 'Restricted Seats Remaining', 'Course URL'])
#         for instructor_row in all_rows:
#             for row in instructor_row:
#                 writer.writerow(row)
                
if __name__ == '__main__':
    print(f"STARTING FOR {SESSION_YEAR} {SESSION} THREADED")
    all_rows = []
    with open('test_ids.csv', 'r') as f:
        heading = next(f) # Skip the header
        reader = csv.reader(f)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            q = queue.Queue()
            for row in reader:
                executor.submit(extract_data_worker, q, row[0], row[1])
            
        # Get the results from the queue
        while not q.empty():
            instructor_row = q.get()
            for row in instructor_row:
                all_rows.append(row)
                    
    # write the data to a CSV file
    with open(f'{SESSION_YEAR}_{SESSION}.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Name', 'Year', 'Session', 'Status', 'Course Code', 'Section', 'Activity', 'Term', 'Mode of Delivery', 'Interval', 'Days', 'Start Time', 'End Time', 'Section Comments', 'Requires In-Person Attendance', 'Course Name', 'Credits', 'Location', 'Date Range', 'Instructors', 'TeacherNumber', 'TAs', 'TANumber', 'Total Seats Remaining', 'Currently Registered', 'General Seats Remaining', 'Restricted Seats Remaining', 'Course URL'])
        for row in all_rows:
            writer.writerow(row)




