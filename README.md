# ssc-scrape
requirements:
```pip install requests```
```pip install lxml```
```pip install beautifulsoup4```

If trying to extract ubc_ids:
```pip install selenium```

# How this works
I wrote this code 5 months ago, and didn't expect it to be used again since soon the SSC will be moved to Workday. I will try to document as best as possible. These scripts need to be run using UBC wifi or you get blocked.
There are two parts: 

## Extract UBC ids
First is extracting the ubcid of instructors in an array of courses listed inside `scrape.py` (make sure SESSION_YEAR and SESSION is correct). This outputs a .csv that you will use for the second part.

## Scrape course data
I believe `all_together.py` is the file you want to use, the other files have older portions of this code. It also relies on a file called `Faculty_Rank_Info.csv` which contains a list of Instructors that we keep.
Make sure `filename, sessionYears, sessions` is correct. You should probably test with a subset of ubc ids to make sure the data output format is correct.
