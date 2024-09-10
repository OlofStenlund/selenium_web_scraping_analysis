# selenium_web_scraping_analysis

Uses Selenium to scrape data from https://arbetsformedlingen.se/platsbanken, and then performas data analysis on the results.

\*\*TODO
~~1: Instead of storing the results in a list and performing anlysis on that list, save everythinG in a csv file, and then further analysis can be done in several stages. This stores the actual data as well. <br>~~
~~2: Get other info, such as location (city, län), experience level, employer, etc.<br>~~
~~3: function "check_next" seems to not be working<br>~~
~~4: Add ID-column<br>~~
~~5: Make sure that the scraper does not fetch URLs that are allready in the dataset. Since URLs are allways in the same order, this can be done by simply taking the last URL added to the continous-DF and break when tha URL is encountered.<br>~~
6: Perform search for specific qualifications in the add texts. This will be handeled in qualification_analysis.py and the results will be stored in a separate DF.<br>
7: Perform analysis using pandas et al.<br>
8: the funtion retrieve_urls_from_page() tried to filter the URLS but does not do this. Remove this attempt and make it so that either 1: the urls are filtered in the function by passing a list of all URLS from the continuous table, or 2: the urls are all fetched and filtered in the main function. The second option is probably preferable, as one might want to get all the URLS in the future. Maybe write a new function for the sorting?<br>~~
