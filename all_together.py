import requests
from bs4 import BeautifulSoup
import csv
import concurrent.futures
import queue

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


def extract_row_data(name, row, session_year, session):
    tds = row.find_all('td')
    data = [name, session_year, session]
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
                url = f"https://courses.students.ubc.ca{course_link['href']}&sessyr={session_year}&sesscd={session}"
                seat_data = extract_course_seat_data_and_other_info(url)
        elif index == 3:
            data.append(session + td.text.strip())
        else:
            data.append(td.text.strip())
            
    data.extend(seat_data)
    return data

def extract_instructor_page_data(name, ubcid, session_year, session):
    url = f'https://courses.students.ubc.ca/cs/courseschedule?pname=inst&ubcid={ubcid}&catano=0&sessyr={session_year}&sesscd={session}&campuscd=UBC'
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'lxml')
    table = soup.find('table', attrs={"class":"section-summary"})
    default_array = [[name, session_year, session, "NO COURSES FOUND", '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', url]]
    try:
        rows = table.find_all('tr')
    except AttributeError:
        return default_array

    all_data = []

    for row in rows[2:]:
        all_data.append(extract_row_data(name, row, session_year, session))

    if len(all_data) == 0:
        return default_array
    
    return all_data

def extract_data_worker(q, name, ubcid, session_year, session):
    data = extract_instructor_page_data(name, ubcid, session_year, session)
    print("DONE FOR", name)
    q.put(data)
                
if __name__ == '__main__':
    sessionYears = ["2022", "2023"]
    sessions = ['W', 'S']
    all_rows = []
    for i in range(len(sessionYears)):
        print("STARTING", sessionYears[i], sessions[i])
        with open('test_ids.csv', 'r') as f:
            heading = next(f) # Skip the header
            reader = csv.reader(f)
            with concurrent.futures.ThreadPoolExecutor() as executor:
                q = queue.Queue()
                for row in reader:
                    executor.submit(extract_data_worker, q, row[0], row[1], sessionYears[i], sessions[i])
                
            # Get the results from the queue
            while not q.empty():
                instructor_row = q.get()
                for row in instructor_row:
                    all_rows.append(row)
                    
    # write the data to a CSV file
    filename = 'ALL TOGETHER_raw.csv'
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Name', 'Year', 'Session', 'Status', 'Course Code', 'Section', 'Activity', 'Term', 'Mode of Delivery', 'Interval', 'Days', 'Start Time', 'End Time', 'Section Comments', 'Requires In-Person Attendance', 'Course Name', 'Credits', 'Location', 'Date Range', 'Instructors', 'TeacherNumber', 'TAs', 'TANumber', 'Total Seats Remaining', 'Currently Registered', 'General Seats Remaining', 'Restricted Seats Remaining', 'Course URL'])
        for row in all_rows:
            writer.writerow(row)
    
    # Cross.py
    print("STARTING CROSS LIST")
    import pandas as pd
    df = pd.read_csv(filename)

    df['Crosslist'] = ""

    def list_same_time(group):
        same_time_list = group['Course Code'].tolist()
        same_time_list = set(same_time_list)
        if len(same_time_list) <= 1:
            return None
        else:
            same_time_list = "/".join([str(item) for item in same_time_list])
            return same_time_list

    grouped = df.groupby(['Name', 'Year', 'Session', 'Term', 'Days', 'Start Time', 'End Time'])

    # Loop through each group
    for name, group in grouped:
        same_time_list = list_same_time(group)
        group['Crosslist'] = same_time_list
        df.update(group)

    # Reorder columns so Course URL is last
    cols = list(df.columns)
    a, b = cols.index('Course URL'), cols.index('Crosslist')
    cols[b], cols[a] = cols[a], cols[b]
    df = df[cols]

    df_copy = df.copy()

    df_copy[['Last', 'First']] = df['Name'].str.split(", ", expand=True)
    df_copy['Last'] = df_copy['Last'].str.split().str[0]
    df_copy['First'] = df_copy['First'].str.split().str[0]
    df_copy = df_copy.reindex(columns=['First', 'Last'] + list(df_copy.columns[:-2]))
    
    df_copy.to_csv(filename, index=False)
    
    # Filter.py
    print("STARTING FILTER LIST")
    
    NAMES_KEEP = 'Faculty_Rank_Info.csv'
    df1 = pd.read_csv(NAMES_KEEP)
    df2 = pd.read_csv(filename)

    valid_names = df1['FirstName'].str.replace(' ', '').str.cat(df1['LastName'].str.replace(' ', ''), sep=' ')
    valid_list = valid_names.str.upper().to_list()

    df2['Full Name'] = df2['First'].str.cat(df2['Last'], sep=' ')

    not_in_df = [name for name in valid_list if name not in df2['Full Name'].tolist()]

    # print names not present in dataframe
    print('Names not present in dataframe:', not_in_df)

    # filter dataframe to keep only rows where Full Name is in valid names array
    df = df2[df2['Full Name'].isin(valid_list)]
    df = df.drop('Full Name', axis=1)

    df.to_csv('filtered ' + filename, index=False)




