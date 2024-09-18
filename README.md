## General Conference Talks Scraper 

This Python code scrapes content of the General Conference of The Church of Jesus Christ of latter-day Saints, which is publicly available. It's only tested on the global English church site. 

It turns the scraped data and into json and jsonl files. 

"gc_scraper_by_period" will let you scrape a link like this: https://www.churchofjesuschrist.org/study/general-conference/2024/04?lang=eng

"gc_scraper_by_spaker" will let you scrape a link like this: https://www.churchofjesuschrist.org/study/general-conference/speakers/russell-m-nelson?lang=eng

"scrapeby10years" will let you scrape a link like this: https://www.churchofjesuschrist.org/study/general-conference/20102019?lang=eng

The jsonl files conversion uses llm to output synthetic data (i.e., prompts) to fine-tune an llm model. A dataset example can be found here: https://huggingface.co/datasets/zorbalee/generalconference_talks You can also check out the results in the output folder in the project directory. Will add a code that scraps by topics soon. 

If you don't want the jsonl conversion (using llm) but just want the text, use the following codes instead:

1. simple_gcscraper_byperiod.py
2. simple_gcscraper_byspeaker.py
3. simple_scrapeby10years.py

These codes will only output json and txt files. 

This scraper skips "specialty" talks such as church auditing report and sustaining church leaders.
