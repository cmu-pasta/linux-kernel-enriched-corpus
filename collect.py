#!/usr/bin/env python3


from bs4 import BeautifulSoup
import os
import requests
import re
import multiprocessing

'''
Query https://syzkaller.appspot.com/upstream for all bugs against upstream kernel and have "C" and "syz" reproducers
Save reproducers to text files
'''

def get_reproducers(bug):
        # get the id from the bug
        bug_id = bug.split("=")[1]
        existing_files = [f for f in os.listdir("files/") if f.startswith(bug_id)]
        if existing_files:
                print(f"Files for bug {bug_id} already exist. Skipping...")
                return
        page = requests.get("https://syzkaller.appspot.com" + bug)
        soup = BeautifulSoup(page.content, 'html.parser')
        # parse last table in page that has class "list_table"
        try:
                table = soup.find_all('table', class_="list_table")[-1]
        except IndexError:
                print("No reproducers for bug : ",bug)
                return
        # find td that has text "syz", only one
        td = table.find_all('td', text="syz")
        for entry in td:
            # get the href of the link
            link = entry.find('a').get('href')
            page = requests.get("https://syzkaller.appspot.com" + link)
            # bug = files/bug?id=17ee94193810ddc5d820094d4e509d47ad5bf6bc
            # link = /text?tag=ReproSyz&x=1789e141d00000
            # get the x from the link
            x = re.search(r'x=(.*)', link).group(1)
            print("Saving bug " + bug_id + " with x " + x)
            with open("files/" + bug_id + "-" + x + ".txt", 'w+') as f:
                f.write(page.text)

def main():
    # Query the page
    bugs = []
    page = requests.get("https://syzkaller.appspot.com/upstream/")
    soup = BeautifulSoup(page.content, 'html.parser')
    # parse table rows
    rows = soup.find_all('tr')
    for row in rows:
        # print row with class as "title" and first "stat"
        title = row.find_all('td', class_="title")
        stat = row.find_all('td', class_="stat")
        # if title and stat exist
        if title and stat:
            # check if stat[0] contains "C" in "td"
            if "C" in stat[0] or "syz" in stat[0]:
                print(title[0].find('a').get('href'))
                bugs.append(title[0].find('a').get('href'))

    # for each bug, get the reproducers from "https://syzkaller.appspot.com/$bug"
    # run the following code in 15 parallel processes to speed up
    pool = multiprocessing.Pool(15)
    pool.map(get_reproducers, bugs)

if __name__ == "__main__":
    main()
