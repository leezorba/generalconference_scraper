Readme	


This code is to scrape content from the General Conference of The Church of Jesus Christ of latter-day Saints, that is publicly available. It's only tested on the global English church site. 

It turns the scraped data and turn them into json and jsonl files. Will add a code that turns json into txt or md soon.  

"gc_scraper_by_period" will let you scrape a link like this: https://www.churchofjesuschrist.org/study/general-conference/2024/04?lang=eng

"gc_scraper_by_spaker" will let you scrape a link like this: https://www.churchofjesuschrist.org/study/general-conference/speakers/russell-m-nelson?lang=eng

"scrapeby10years" will let you scrape a link like this: https://www.churchofjesuschrist.org/study/general-conference/20102019?lang=eng

You can check out the results in the output folder. Will add a code that scraps by topics soon. 

A dataset for the conference talks given from April, 2000 to April, 2024 in jsonl (e.g., for fine-tuning an llm model) can be found here: https://huggingface.co/datasets/zorbalee/generalconference_talks

Will add an example notebook on fine-tuning a model soon. 
