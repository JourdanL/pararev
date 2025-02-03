# ParaRev : Building a dataset for Scientific Paragraph Revision annotated with revision instruction

🤗 [Link to Pararev dataset on Hugging Face](https://huggingface.co/datasets/taln-ls2n/pararev)


#### Extract ParaRev from CASIMIR
*script_extract_parags_from_casimir.py* can be used to reproce the work in our paper and extract [ParaRev](https://huggingface.co/datasets/taln-ls2n/pararev) from the [CASIMIR](https://huggingface.co/datasets/taln-ls2n/CASIMIR) dataset.


#### Visualize the data
The code in *print_diff_pair_parag.ipynb* can be used to display the difference between the 2 versions of the paragraphs.


### Citation

You can find the paper associated to this repository on the [ACL Anthology](https://aclanthology.org/2025.wraicogs-1.4/)

Please cite it as:

	@inproceedings{jourdan-etal-2025-pararev,
    		title = "{P}ara{R}ev : Building a dataset for Scientific Paragraph Revision annotated with revision instruction",
    		author = "Jourdan, L{\'e}ane  and
      			Boudin, Florian  and
      			Dufour, Richard  and
      			Hernandez, Nicolas  and
     			 Aizawa, Akiko",
    		editor = "Zock, Michael  and
      			Inui, Kentaro  and
      			Yuan, Zheng",
    		booktitle = "Proceedings of the First Workshop on Writing Aids at the Crossroads of AI, Cognitive Science and NLP (WRAICOGS 2025)",
    		month = jan,
    		year = "2025",
    		address = "Abu Dhabi, UAE",
    		publisher = "International Committee on Computational Linguistics",
    		url = "https://aclanthology.org/2025.wraicogs-1.4/",
    		pages = "35--44",
   
	}

