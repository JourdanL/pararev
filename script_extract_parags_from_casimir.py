import json
import os
import re
import argparse

# I - Utils

# Function to remove specific tags
def remove_tags(string):
    tags = ["[Figure]", "[Equation]", "[Table]"]
    for tag in tags:
        string = string.replace(tag, "")
    return string

def are_equals_without_space(string1, string2):
    # Delete spaces in the two strings
    string1_without_space = re.sub(r'\s', '', string1)
    string2_without_space = re.sub(r'\s', '', string2)

    # Compare strings without spaces
    return string1_without_space == string2_without_space

def remove_spaces(string):
   # Delete spaces
    string_without_space = re.sub(r'\s', '', string)

    return string_without_space


def assembling_parag_nocolor(parag_source,parag_target):                          
    end_with_space=True
    parag_source_full=""
    for line in parag_source:
        if len(line)>0:
            start_with_space=(line[0]==' ')
            if end_with_space or start_with_space:
                parag_source_full+=line
            else:
                parag_source_full+=' '
                parag_source_full+=line
            end_with_space=(line[-1]==' ')
    parag_target_full=""
    end_with_space=True
    for line in parag_target:
        if len(line)>0:
            start_with_space=(line[0]==' ')
            if end_with_space or start_with_space:
                parag_target_full+=line
            else:
                parag_target_full+=' '
                parag_target_full+=line
            end_with_space=(line[-1]==' ')
    return  parag_source_full,parag_target_full

# II - Data preparation

def calculation_modifications_length(sentence,sentence_token_indices):
    begin_sent=0
    end_sent=0
    if type(sentence_token_indices)==list:
        begin_sent=sentence_token_indices[0]
        end_sent=sentence_token_indices[1]
        extracted_edit=remove_tags(sentence[begin_sent:end_sent])
        
        modifications_length=len(extracted_edit)
    else:
        modifications_length=0
    
    return modifications_length

def calculation_modifications_percentage(element):
    length_modif_1=0
    length_modif_2=0
    for idx_elt in range(len(element['edits-combination'])):
        if type(element['edits-combination'][str(idx_elt)]['sentence-1-token-indices'])==list and type(element['edits-combination'][str(idx_elt)]['sentence-2-token-indices'])==list:
            begin_sent1=element['edits-combination'][str(idx_elt)]['sentence-1-token-indices'][0]
            end_sent1=element['edits-combination'][str(idx_elt)]['sentence-1-token-indices'][1]
            begin_sent2=element['edits-combination'][str(idx_elt)]['sentence-2-token-indices'][0]
            end_sent2=element['edits-combination'][str(idx_elt)]['sentence-2-token-indices'][1]

            if not(are_equals_without_space(element['text-sentence-1'][begin_sent1:end_sent1],element['text-sentence-2'][begin_sent2:end_sent2])):
                length_modif_1+=calculation_modifications_length(element['text-sentence-1'],element['edits-combination'][str(idx_elt)]['sentence-1-token-indices'])
                length_modif_2+=calculation_modifications_length(element['text-sentence-2'],element['edits-combination'][str(idx_elt)]['sentence-2-token-indices'])
        else:
            length_modif_1+=calculation_modifications_length(element['text-sentence-1'],element['edits-combination'][str(idx_elt)]['sentence-1-token-indices'])
            length_modif_2+=calculation_modifications_length(element['text-sentence-2'],element['edits-combination'][str(idx_elt)]['sentence-2-token-indices'])

    #Calculation of modifications percentage
    length_sent_1_without_tags=len(remove_tags(element['text-sentence-1']))
    length_sent_2_without_tags=len(remove_tags(element['text-sentence-2']))
    if length_sent_1_without_tags>0:
        percentage_modif_1=length_modif_1/length_sent_1_without_tags
    else:
        percentage_modif_1=0
    if length_sent_2_without_tags>0:
        percentage_modif_2=length_modif_2/length_sent_2_without_tags
    else:
        percentage_modif_2=0
        
    return percentage_modif_1,percentage_modif_2,length_sent_1_without_tags,length_sent_2_without_tags

def get_new_num_section(element):
    if "num_section-sentence-1" in element:
        new_num_section_1=element["num_section-sentence-1"]
    else:
        new_num_section_1=-2
    if "num_section-sentence-2" in element:
        new_num_section_2=element["num_section-sentence-2"]
    else:
        new_num_section_2=-2
    return new_num_section_1,new_num_section_2         

def get_new_num_parag(element):
    if "num_paragraph-sentence-1" in element:
        new_num_parag_1=element["num_paragraph-sentence-1"]
    else:
        if "id-sentence-1" in element:
            new_num_parag_1=-1
        else:
            new_num_parag_1=-2
    if "num_paragraph-sentence-2" in element:
        new_num_parag_2=element["num_paragraph-sentence-2"]
    else:
        if "id-sentence-2" in element:
            new_num_parag_2=-1
        else:
            new_num_parag_2=-2
    return new_num_parag_1,new_num_parag_2         

def get_list_pairs_parag(diff_article,low_threshold=0.5):
    #Initialisations
    old_num_parag_1=-1
    old_num_parag_2=-1
    old_num_section_1=-1
    old_num_section_2=-1
    aggreg_parag_1=[]
    aggreg_parag_2=[]
    
    list_sections=[]
    list_pairs_parag=[]

    for element in diff_article:
        
        new_num_section_1,new_num_section_2=get_new_num_section(element)
        
        new_num_parag_1,new_num_parag_2=get_new_num_parag(element)
        
        section_both_change=(old_num_section_1!=new_num_section_1) and (old_num_section_2!=new_num_section_2)
        section_source_change_target_empty=(old_num_section_1!=new_num_section_1) and (old_num_section_2+new_num_section_2==-4)
        section_source_empty_target_change=(old_num_section_1+new_num_section_1==-4) and (old_num_section_2!=new_num_section_2)
        
        parag_both_change=(old_num_parag_1!=new_num_parag_1) and (old_num_parag_2!=new_num_parag_2)
        parag_source_change_target_empty=(old_num_parag_1!=new_num_parag_1) and (old_num_parag_2+new_num_parag_2==-4)
        parag_source_empty_target_change=(old_num_parag_1+new_num_parag_1==-4) and (old_num_parag_2!=new_num_parag_2)
        
        if section_both_change or section_source_change_target_empty or section_source_empty_target_change:
            list_pairs_parag.append((aggreg_parag_1,aggreg_parag_2))

            aggreg_parag_1=[]
            aggreg_parag_2=[]
            list_sections.append(list_pairs_parag)
            list_pairs_parag=[]
        elif parag_both_change or parag_source_change_target_empty or parag_source_empty_target_change:
            list_pairs_parag.append((aggreg_parag_1,aggreg_parag_2))
            
            aggreg_parag_1=[]
            aggreg_parag_2=[]

        old_num_section_1=new_num_section_1
        old_num_section_2=new_num_section_2  
        
        old_num_parag_1=new_num_parag_1
        old_num_parag_2=new_num_parag_2        
                      
        percentage_modif_1,percentage_modif_2,length_sent_1,length_sent_2=calculation_modifications_percentage(element)
        prct1_round=round(percentage_modif_1*100,2)
        prct2_round=round(percentage_modif_2*100,2)
        #Case I green
        if len(element['edits-combination'])==0:
            #Case I.1 green after another colour (yellow/red)
            aggreg_parag_1.append({"text":str(new_num_parag_1)+"|"+str(len(element['text-sentence-1']))+"-"+str(length_sent_1)+"|","colour":'black',"sep":'',"flush":True,"length":length_sent_1})
            aggreg_parag_2.append({"text":str(new_num_parag_2)+"|"+str(len(element['text-sentence-2']))+"-"+str(length_sent_2)+"|","colour":'black',"sep":'',"flush":True,"length":length_sent_2})
           
            aggreg_parag_1.append({"text":element['text-sentence-1'],"colour":'green',"sep":'\n',"flush":False})
            aggreg_parag_2.append({"text":element['text-sentence-1'],"colour":'green',"sep":'\n',"flush":False})

        #Case II blue
        elif (percentage_modif_1<low_threshold) and (percentage_modif_2<low_threshold):
            #Blue for modified segment and green for identical ones
            end_previous_1=0
            end_previous_2=0
            list_intentions=[]
            for idx_elt in range(len(element['edits-combination'])):
                list_intentions.append(element['edits-combination'][str(idx_elt)]["intention"])
            list_intentions=list(set(list_intentions))
            aggreg_parag_1.append({"list_intentions":list_intentions,"text":str(new_num_parag_1)+"|"+str(len(element['text-sentence-1']))+"-"+str(length_sent_1)+"|"+str(prct1_round)+" "+str(prct2_round),"colour":'black',"sep":'',"flush":True,"length":length_sent_1,"prct_modif":prct1_round})
            aggreg_parag_2.append({"list_intentions":list_intentions,"text":str(new_num_parag_2)+"|"+str(len(element['text-sentence-2']))+"-"+str(length_sent_2)+"|"+str(prct1_round)+" "+str(prct2_round),"colour":'black',"sep":'',"flush":True,"length":length_sent_2,"prct_modif":prct2_round})
                  
            for idx_elt in range(len(element['edits-combination'])):
                begin_sent1=0
                end_sent1=0
                         
                if type(element['edits-combination'][str(idx_elt)]['sentence-1-token-indices'])==list:
                    begin_sent1=element['edits-combination'][str(idx_elt)]['sentence-1-token-indices'][0]
                    end_sent1=element['edits-combination'][str(idx_elt)]['sentence-1-token-indices'][1]
                    
                    if type(element['edits-combination'][str(idx_elt)]['sentence-2-token-indices'])==list:
                        begin_sent2=element['edits-combination'][str(idx_elt)]['sentence-2-token-indices'][0]
                        end_sent2=element['edits-combination'][str(idx_elt)]['sentence-2-token-indices'][1]

                        if are_equals_without_space(element['text-sentence-1'][begin_sent1:end_sent1],element['text-sentence-2'][begin_sent2:end_sent2]):
                            aggreg_parag_1.append({"text":element['text-sentence-1'][end_previous_1:begin_sent1],"colour":'cyan',"sep":'',"flush":True})
                            aggreg_parag_1.append({"text":element['text-sentence-1'][begin_sent1:end_sent1],"colour":'cyan',"sep":'',"flush":True})
                        else:
                            aggreg_parag_1.append({"text":element['text-sentence-1'][end_previous_1:begin_sent1],"colour":'cyan',"sep":'',"flush":True})
                            aggreg_parag_1.append({"text":element['text-sentence-1'][begin_sent1:end_sent1],"colour":'blue',"sep":'',"flush":True})

                    else:
                        aggreg_parag_1.append({"text":element['text-sentence-1'][end_previous_1:begin_sent1],"colour":'cyan',"sep":'',"flush":True})
                        aggreg_parag_1.append({"text":element['text-sentence-1'][begin_sent1:end_sent1],"colour":'blue',"sep":'',"flush":True})
                    end_previous_1=end_sent1
            aggreg_parag_1.append({"text":element['text-sentence-1'][end_previous_1:],"colour":'cyan',"sep":'\n',"flush":False})
                
            for idx_elt in range(len(element['edits-combination'])):
                begin_sent2=0
                end_sent2=0
                                     
                if type(element['edits-combination'][str(idx_elt)]['sentence-2-token-indices'])==list:
                    begin_sent2=element['edits-combination'][str(idx_elt)]['sentence-2-token-indices'][0]
                    end_sent2=element['edits-combination'][str(idx_elt)]['sentence-2-token-indices'][1]
                    
                    if type(element['edits-combination'][str(idx_elt)]['sentence-1-token-indices'])==list:
                        begin_sent1=element['edits-combination'][str(idx_elt)]['sentence-1-token-indices'][0]
                        end_sent1=element['edits-combination'][str(idx_elt)]['sentence-1-token-indices'][1]
                        if are_equals_without_space(element['text-sentence-1'][begin_sent1:end_sent1],element['text-sentence-2'][begin_sent2:end_sent2]):
                            aggreg_parag_2.append({"text":element['text-sentence-2'][end_previous_2:begin_sent2],"colour":'cyan',"sep":'',"flush":True})
                            aggreg_parag_2.append({"text":element['text-sentence-2'][begin_sent2:end_sent2],"colour":'cyan',"sep":'',"flush":True})
                        else:
                            aggreg_parag_2.append({"text":element['text-sentence-2'][end_previous_2:begin_sent2],"colour":'cyan',"sep":'',"flush":True})
                            aggreg_parag_2.append({"text":element['text-sentence-2'][begin_sent2:end_sent2],"colour":'blue',"sep":'',"flush":True})
                    else:
                        
                        aggreg_parag_2.append({"text":element['text-sentence-2'][end_previous_2:begin_sent2],"colour":'cyan',"sep":'',"flush":True})
                        aggreg_parag_2.append({"text":element['text-sentence-2'][begin_sent2:end_sent2],"colour":'blue',"sep":'',"flush":True})
                    end_previous_2=end_sent2
            aggreg_parag_2.append({"text":element['text-sentence-2'][end_previous_2:],"colour":'cyan',"sep":'\n',"flush":False})
                
        #Case III: red/yellow
        else:
            list_intentions=[]
            for idx_elt in range(len(element['edits-combination'])):
                list_intentions.append(element['edits-combination'][str(idx_elt)]["intention"])
            list_intentions=list(set(list_intentions))
            aggreg_parag_1.append({"list_intentions":list_intentions,"text":str(new_num_parag_1)+"|"+str(len(element['text-sentence-1']))+"-"+str(length_sent_1)+"|"+str(prct1_round)+" "+str(prct2_round),"colour":'black',"sep":'',"flush":True,"length":length_sent_1,"prct_modif":prct1_round})
            aggreg_parag_1.append({"text":element['text-sentence-1'],"colour":'yellow',"sep":'\n',"flush":False})
            
            aggreg_parag_2.append({"list_intentions":list_intentions,"text":str(new_num_parag_2)+"|"+str(len(element['text-sentence-2']))+"-"+str(length_sent_2)+"|"+str(prct1_round)+" "+str(prct2_round),"colour":'black',"sep":'',"flush":True,"length":length_sent_2,"prct_modif":prct2_round})
            aggreg_parag_2.append({"text":element['text-sentence-2'],"colour":'red',"sep":'\n',"flush":False})
    
    return list_sections

# III - Filters

def is_long_enough(pair_parags,minimum_length=250):    
    parag_source=[element for element in pair_parags[0] if element['colour']=="black" ]
    parag_target=[element for element in pair_parags[1] if element['colour']=="black" ]
    length_parag_1=sum([line_source["length"] for line_source in parag_source])
    length_parag_2=sum([line_target["length"] for line_target in parag_target])
    
    return (max(length_parag_1,length_parag_2)>minimum_length)    

def respect_limit_modifs(pair_parags, prct_mini_sent=25,prct_mini_parag=10, prct_max=90, length_modif_max=200,prct_max_parag=40):
    parag_source=[element for element in pair_parags[0] if element['colour']=="black" ]        
    parag_target=[element for element in pair_parags[1] if element['colour']=="black" ]
    all_colors=set([line_source["colour"] for line_source in pair_parags[0]]+[line_target["colour"] for line_target in pair_parags[1]])
    prct_modif_max=max([0]+[max(line_source["prct_modif"],line_target["prct_modif"]) for (line_source, line_target) in zip(parag_source, parag_target) if "prct_modif" in line_source.keys()])
    length_sum_max_parag1=sum([line_source["length"] for (line_source, line_target) in zip(parag_source, parag_target) if ("prct_modif" in line_source.keys() and max(line_source["prct_modif"],line_target["prct_modif"])>prct_max) ])
    length_sum_max_parag2=sum([line_target["length"] for (line_source, line_target) in zip(parag_source, parag_target) if ("prct_modif" in line_source.keys() and max(line_source["prct_modif"],line_target["prct_modif"])>prct_max) ])
    length_total_parag1=sum([line_source["length"] for line_source in parag_source])
    length_total_parag2=sum([line_target["length"] for line_target in parag_target])
   
    length_modif_parag1=sum([line_source["prct_modif"]*line_source["length"] for (line_source, line_target) in zip(parag_source, parag_target) if "prct_modif" in line_source.keys()])
    length_modif_parag2=sum([line_target["prct_modif"]*line_target["length"] for (line_source, line_target) in zip(parag_source, parag_target) if "prct_modif" in line_source.keys()])

    if length_total_parag1>0:
        prct_modif_parag1=length_modif_parag1/length_total_parag1
    else:
        prct_modif_parag1=0
    if length_total_parag2>0:
        prct_modif_parag2=length_modif_parag2/length_total_parag2
    else:
        prct_modif_parag2=0
        
    if length_total_parag1==0 and length_total_parag2==0:
        return False
    elif length_total_parag1==0:
        too_much_modifications=(length_sum_max_parag2/length_total_parag2<prct_max_parag/100)
    elif length_total_parag2==0:
        too_much_modifications=(length_sum_max_parag1/length_total_parag1<prct_max_parag/100)
    else:
        too_much_modifications=(max(length_sum_max_parag1/length_total_parag1,length_sum_max_parag2/length_total_parag2)<prct_max_parag/100)
    
    too_much_modifications=too_much_modifications or (max(length_sum_max_parag1,length_sum_max_parag2)<length_modif_max)
    
    if len(all_colors.intersection({"yellow","red"}))==0:
        prct_mini_blue_only=20
        length_sent_modif_parag1=sum([line_source["length"] for line_source in parag_source if ("prct_modif" in line_source.keys())])
        length_sent_modif_parag2=sum([line_target["length"] for line_target in parag_target if ("prct_modif" in line_target.keys())])
        if length_sent_modif_parag1>0:
            prct_modif_parag1_blue=length_modif_parag1/length_sent_modif_parag1
        else:
            prct_modif_parag1_blue=0
        if length_sent_modif_parag2>0:
            prct_modif_parag2_blue=length_modif_parag2/length_sent_modif_parag2
        else:
            prct_modif_parag2_blue=0
        if "green" in all_colors:
            return  prct_modif_max>prct_mini_sent and too_much_modifications and max(prct_modif_parag1,prct_modif_parag2)> prct_mini_parag and max(prct_modif_parag1_blue,prct_modif_parag2_blue)> prct_mini_blue_only 
        else:
            return  prct_modif_max>prct_mini_sent and too_much_modifications and max(prct_modif_parag1_blue,prct_modif_parag2_blue)> prct_mini_blue_only 
    else:
        return  prct_modif_max>prct_mini_sent and too_much_modifications and max(prct_modif_parag1,prct_modif_parag2)> prct_mini_parag        
    
def count_special_characters(paragraph):
    # Define a list of special characters and patterns to count
    special_patterns = [
        r'\(cid:\d+\)',  # Matches (cid:xx) where x are numbers
        "\[Equation\]",
        r'\s[A-Za-z]\s',  # Matches individual letters surrounded by spaces
        r'\s\(\s', r'\s\)\s', '\=', '\+', '\/'
    ]
    # Count the occurrences of each special character or pattern in the paragraph
    character_counts = {pattern: len(re.findall(pattern, paragraph)) for pattern in special_patterns}

    return character_counts

def contains_too_many_equations(pair_parags, threshold=11):
    # Extract draft and revised paragraphs from the pair
    draft_paragraph  =' '.join([element["text"] for element in pair_parags[0] if (element['colour']!="black")])
    revised_paragraph=' '.join([element["text"] for element in pair_parags[1] if (element['colour']!="black")])
    #Extract only the rewritten sentences
    draft_paragraph_no_green  =' '.join([element["text"] for element in pair_parags[0] if (element['colour']!="green" and element['colour']!="black")])
    revised_paragraph_no_green=' '.join([element["text"] for element in pair_parags[1] if (element['colour']!="green" and element['colour']!="black")])

    # Count special characters in each paragraph
    draft_character_counts   = count_special_characters(draft_paragraph)
    revised_character_counts = count_special_characters(revised_paragraph)
    # Count special characters in each paragraph only in rewritten sentences
    draft_character_counts_no_green   = count_special_characters(draft_paragraph_no_green)
    revised_character_counts_no_green = count_special_characters(revised_paragraph_no_green)

    # Calculate the total count of special characters in each paragraph
    draft_total_count   = 2*sum(draft_character_counts.values())+ 7*draft_character_counts["\\(cid:\\d+\\)"]+ 9*draft_character_counts["\\[Equation\\]"]
    revised_total_count = 2*sum(revised_character_counts.values())+ 7*revised_character_counts["\\(cid:\\d+\\)"]+9*revised_character_counts["\\[Equation\\]"]
    draft_total_count_no_green   = 2*sum(draft_character_counts_no_green.values())+ 7*draft_character_counts_no_green["\\(cid:\\d+\\)"]+ 9*draft_character_counts_no_green["\\[Equation\\]"]
    revised_total_count_no_green = 2*sum(revised_character_counts_no_green.values())+ 7*revised_character_counts_no_green["\\(cid:\\d+\\)"]+ 9*revised_character_counts_no_green["\\[Equation\\]"]

    # Check if either paragraph has too many special characters
    #Case 1: Perfectly identical paragraph, never happen
    if len(draft_paragraph_no_green)==0 and len(revised_paragraph_no_green)==0:
        if len(draft_paragraph)==0:
            return revised_total_count*100/len(revised_paragraph)>threshold
        elif len(revised_paragraph)==0:
            return draft_total_count*100/len(draft_paragraph)>threshold
        else:
            return draft_total_count*100/len(draft_paragraph)>threshold or revised_total_count*100/len(revised_paragraph)>threshold
    #Case 2 : Only additions
    elif len(draft_paragraph_no_green)==0:
        return revised_total_count_no_green*100/len(revised_paragraph_no_green)>threshold
    #Case 3 : Only deletions
    elif len(revised_paragraph_no_green)==0:
        return draft_total_count_no_green*100/len(draft_paragraph_no_green)>threshold
    #Case 4: Both deletions and additions
    else:
        if draft_total_count_no_green*100/len(draft_paragraph_no_green)>threshold or revised_total_count_no_green*100/len(revised_paragraph_no_green)>threshold:
            return True
        else:
            return False


def check_incorrect_beginning(sentence):
    return (re.match(r'^[^a-zA-Z]*[A-Z]', sentence) is None)
# Check if the ending of the sentence is correct. 
# aka Finish with a punctuation mark, spaces and url are accepted after the final punctuation
def check_incorrect_ending(sentence):
    #TODO rajouter un point pour les url avec que des points
    return (re.match(r'.*([\.\?!:]\s*$|\.[a-zA-Z/.]+\s*$)', sentence) is None)
def check_incorrect_beginning_ending(sentence):
    return (re.match(r'^[^a-zA-Z]*[A-Z].*([\.\?!:]\s*$|\.[a-zA-Z/.]+\s*$)', sentence) is None)
    
#Return true if there is a problem detected in the last sentence
def last_is_problem(sentence_source,sentence_target):
    #Remove the tags
    sentence_source_no_tag=remove_tags(sentence_source["text"])
    sentence_target_no_tag=remove_tags(sentence_target["text"])
    #Remove tags and spaces
    sentence_source_condensed=remove_spaces(remove_tags(sentence_source["text"]))
    sentence_target_condensed=remove_spaces(remove_tags(sentence_target["text"]))

    #If the source sentence is not empty, does it have an incorrect ending?
    end_1_ko= (len(sentence_source["text"])>0) and check_incorrect_ending(sentence_source_no_tag)
    #If the target sentence is not empty, does it have an incorrect ending?
    end_2_ko= (len(sentence_target["text"])>0) and check_incorrect_ending(sentence_target_no_tag)
    #If one of the sentences have an incorrect ending, exit the function with True
    if end_1_ko or end_2_ko:
        return True
    
    #Case 1: Heavy change
    if (sentence_source["colour"]=="yellow") and (sentence_target["colour"]=="red"):
    #Is the longer one smaller than 3 times the length of the smallest one?
        #Case A: The target is longer
        if sentence_source_condensed<sentence_target_condensed:
            #Is the source equal to the beginning of the target?
            is_included= (sentence_target_condensed[0:len(sentence_source_condensed)]==sentence_source_condensed)
            #Is the target more than 3 time the length of the source? (Too much text difference)
            is_too_long=(len(sentence_target_condensed)>3*len(sentence_source_condensed))
            return is_included or is_too_long
        #Case B: The source is longer
        else:
            #Is the target equal to the beginning of the source?
            is_included= (sentence_source_condensed[0:len(sentence_target_condensed)]==sentence_target_condensed)
            #Is the source more than 3 time the length of the target? (Too much text difference)
            is_too_long=(len(sentence_source_condensed)>3*len(sentence_target_condensed))
            return  is_included or is_too_long
    #Case 2: Moderate change or no change, if moderate change, correctness of ending have been checked previously
    else:
        return False
    
#Return true if there is a problem detected in the last sentence
def last_is_problem_extended(sentence_source,sentence_target):
    #Remove the tags
    sentence_source_no_tag=remove_tags(sentence_source["text"])
    sentence_target_no_tag=remove_tags(sentence_target["text"])
    #Remove tags and spaces
    sentence_source_condensed=remove_spaces(remove_tags(sentence_source["text"]))
    sentence_target_condensed=remove_spaces(remove_tags(sentence_target["text"]))

    #If the source sentence is not empty, does it have an incorrect ending?
    end_1_ko= (len(sentence_source["text"])>0) and check_incorrect_ending(sentence_source_no_tag)
    #If the target sentence is not empty, does it have an incorrect ending?
    end_2_ko= (len(sentence_target["text"])>0) and check_incorrect_ending(sentence_target_no_tag)
    #If one of the sentences have an incorrect ending, exit the function with True
    if end_1_ko or end_2_ko:
        return True
    
    #Case 1: Deletion of a sentence
    if (sentence_source["colour"]=="yellow") and ((sentence_target["colour"]!="red") or len(sentence_target["text"])==0):                                                
        return check_incorrect_beginning_ending(sentence_source_no_tag)
    #Case 2: Addition of a sentence
    elif (sentence_target["colour"]=="red") and ((sentence_source["colour"]!="yellow") or len(sentence_source["text"])==0):
        return check_incorrect_beginning_ending(sentence_target_no_tag)
    #Cas 3: Heavy change
    elif (sentence_source["colour"]=="yellow") and (sentence_target["colour"]=="red"):
    # Is the longest one smaller than 3 times the smallest one?
        #Case A: The target is longer
        if sentence_source_condensed<sentence_target_condensed:
            #Is the source equal to the beginning of the target?
            is_included= (sentence_target_condensed[0:len(sentence_source_condensed)]==sentence_source_condensed)
            #Is the target more than 3 time the length of the source? (Too much text difference)
            is_too_long=(len(sentence_target_condensed)>3*len(sentence_source_condensed))
            return is_included or is_too_long
        #Case B: The source is longer
        else:
            #Is the target equal to the beginning of the source?
            is_included= (sentence_source_condensed[0:len(sentence_target_condensed)]==sentence_target_condensed)
            #Is the source more than 3 time the length of the target? (Too much text difference)
            is_too_long=(len(sentence_source_condensed)>3*len(sentence_target_condensed))
            return  is_included or is_too_long
    #Case 4: Moderate change or no change, if moderate change, correctness of ending have been checked previously
    else:
        return False
    
def first_is_problem(sentence_source,sentence_target):
    #Remove tags and spaces
    sentence_source_condensed=remove_spaces(remove_tags(sentence_source["text"]))
    sentence_target_condensed=remove_spaces(remove_tags(sentence_target["text"]))
    
    #Case yellow only
    if len(sentence_source["text"])>0:
        #Check that the first alphabetical letter is a capital letter
        debut_1_ko= check_incorrect_beginning(sentence_source["text"])
    else:
        debut_1_ko=False
    if len(sentence_target["text"])>0:
        debut_2_ko= check_incorrect_beginning(sentence_target["text"])
    else:
        debut_2_ko=False
    if debut_1_ko or debut_2_ko:
        #Raise a problem in the first sentence is for one of them the first alphabetical letter is NOT a capital letter
        return True
    
    if (sentence_source["colour"]=="yellow") and (len(sentence_target["text"])==0):
        return len(sentence_source_condensed)>0
    #Case red only
    elif (sentence_target["colour"]=="red") and (len(sentence_source["text"])==0):
        return len(sentence_target_condensed)>0
    #Case yellow and red 
    elif (sentence_source["colour"]=="yellow") and (sentence_target["colour"]=="red"):
        #Is the smallest equal to the end of the longest?
        if sentence_source_condensed<sentence_target_condensed:
            #Is the source equal to the end of the target?
            is_included=sentence_target_condensed[len(sentence_target_condensed)-len(sentence_source_condensed):len(sentence_target_condensed)]==sentence_source_condensed
            #Is the target more than 3 time the length of the source? (Too much text difference)
            is_too_long=(len(sentence_target_condensed)>3*len(sentence_source_condensed))
            return is_too_long or is_included
        else:
            #Is the target equal to the end of the source?
            is_included=sentence_source_condensed[len(sentence_source_condensed)-len(sentence_target_condensed):len(sentence_source_condensed)]==sentence_target_condensed
            #Is the source more than 3 time the length of the target? (Too much text difference)
            is_too_long=(len(sentence_source_condensed)>3*len(sentence_target_condensed))
            return  is_too_long or is_included
    #Case blue
    elif (sentence_source["colour"] in ["blue","cyan"]):
        #Case blue modif
        #Is the smallest equal to the end of the longest?
        if (sentence_source["colour"]=="blue") and (sentence_target["colour"]=="blue"):
            if sentence_source_condensed<sentence_target_condensed:
                #Is the source equal to the end of the target?
                return sentence_target_condensed[len(sentence_target_condensed)-len(sentence_source_condensed):len(sentence_target_condensed)]==sentence_source_condensed
            else:
                #Is the target equal to the end of the source?
                return sentence_source_condensed[len(sentence_source_condensed)-len(sentence_target_condensed):len(sentence_source_condensed)]==sentence_target_condensed
        #Case blue unilateral addition
        elif (sentence_source["colour"]=="blue") and (sentence_target["colour"]=="cyan"):
            return len(sentence_source["text"])>10
            
        elif (sentence_source["colour"]=="cyan") and (sentence_target["colour"]=="blue"):
            return len(sentence_target["text"])>10
    # Case green only or blue without modification on the beginning of the sentence
    else:
        return False
    
def addition_last_or_first(pair_parags):
    parag_source=[element for element in pair_parags[0] if ((len(element['text'])>0 or element["colour"] in ["yellow","red"]) and element['colour']!="black")]
    parag_target=[element for element in pair_parags[1] if  ((len(element['text'])>0 or element["colour"] in ["yellow","red"]) and element['colour']!="black")]
    is_last=(parag_source[-1]["colour"] in ["yellow","red","blue"]) or (parag_target[-1]["colour"] in ["yellow","red","blue"])
    is_first=first_is_problem(parag_source[0],parag_target[0])
    if is_last:
        is_last=last_is_problem(parag_source[-1],parag_target[-1])
    return is_first or is_last

def tag_verification(list_text_1, full_text_2):
    tag_ok=True
    if len(list_text_1)>0:
        idx_beginning=0
        #We don't consider the tag at the beginning
        while list_text_1[idx_beginning] in ["[Table]","[Figure]","[Equation]"]:
            idx_beginning+=1
        idx_end=len(list_text_1)
        #We don't consider the tags at the end
        while list_text_1[idx_end-1] in ["[Table]","[Figure]","[Equation]"]:
            idx_end-=1
        
        cropped_list_text_1=list_text_1[idx_beginning:idx_end]
        
        #After the tags at the beginning, does the paragraph start correctly?
        if idx_beginning!=0:
            tag_ok = tag_ok and not(check_incorrect_beginning(cropped_list_text_1[0]))
        #Before the tags at the end, does the paragraph end correctly
        if idx_end!=len(cropped_list_text_1):
            tag_ok = tag_ok and not(check_incorrect_ending(cropped_list_text_1[-1]))
        if not tag_ok:
            return tag_ok
        else:
            idx_tag=0
            #Was some text incorrectly replaced by a tag?
            while idx_tag<len(cropped_list_text_1):
                if cropped_list_text_1[idx_tag] in ["[Table]","[Figure]","[Equation]"]:
                    new_tag_no_replace= (cropped_list_text_1[idx_tag-1]+cropped_list_text_1[idx_tag+1] in remove_spaces(full_text_2))
                    no_change= (cropped_list_text_1[idx_tag-1]+cropped_list_text_1[idx_tag]+cropped_list_text_1[idx_tag+1] in remove_spaces(full_text_2))
                    tag_ok=tag_ok and (new_tag_no_replace or no_change)
                idx_tag+=1
    return tag_ok


def is_tag_ok(parag): 
    parag_source=[sentence["text"] for sentence in parag[0] if sentence["colour"]!="black"]
    parag_target=[sentence["text"] for sentence in parag[1] if sentence["colour"]!="black"]

    text_source,text_target=assembling_parag_nocolor(parag_source,parag_target)
    list_text_source=text_source.split(" ")
    list_text_target=text_target.split(" ")
    
    tag_ok=True
    if len(list_text_source)>0:
        tag_ok= tag_ok and tag_verification(list_text_source, text_target)
    if len(parag_target)>0:
        tag_ok= tag_ok and tag_verification(list_text_target, text_source)
    return tag_ok

# IV - Prepare export mini corpus

def remove_tags_with_spaces(string):
# Function to remove specific tags
    tags = [" [Figure]", " [Equation]", " [Table]"]
    for tag in tags:
        string = string.replace(tag, "")
    tags = ["[Figure] ", "[Equation] ", "[Table] "]
    for tag in tags:
        string = string.replace(tag, "")
    tags = ["[Figure]", "[Equation]", "[Table]"]
    for tag in tags:
        string = string.replace(tag, "")
    return string

def difference_dash(string1, string2):
    # Checks if string lengths differ by exactly 1
    if abs(len(string1) - len(string2)) != 1:
        return False

    # Supprime tous les tirets des deux chaînes
    string1_without_dash = string1.replace("-", "")
    string2_without_dash = string2.replace("-", "")

    # Vérifie si les chaînes sont identiques après suppression des tirets
    if string1_without_dash == string2_without_dash:
        return True
    return False

def corrections_spaces_and_dash(parag):
    source=parag[0]
    target=parag[1]
    not_end_source=True
    not_end_target=True
    idx_source=0
    idx_target=0
    while not_end_source and not_end_target:
        sentence_source=source[idx_source]['text']
        sentence_target=target[idx_target]['text']
        if (source[idx_source]['colour']=='cyan') and (target[idx_target]['colour']=='cyan'):
            if len(sentence_source)!=len(sentence_target) and are_equals_without_space(sentence_source,sentence_target):
                if len(sentence_source)>len(sentence_target):
                    parag[1][idx_target]['text']=source[idx_source]['text']
                else:
                    parag[0][idx_source]['text']=target[idx_target]['text']
            idx_source+=1
            idx_target+=1
        elif (source[idx_source]['colour']=='blue') and (target[idx_target]['colour']=='cyan'):
            idx_source+=1
        elif (source[idx_source]['colour']=='cyan') and (target[idx_target]['colour']=='blue'):
            idx_target+=1
        elif (source[idx_source]['colour']=='blue') and (target[idx_target]['colour']=='blue'):
            if difference_dash(sentence_source,sentence_target):
                if len(sentence_source)>len(sentence_target):
                    parag[1][idx_target]['text']=source[idx_source]['text']                    
                else:
                    parag[0][idx_source]['text']=target[idx_target]['text']                    
                parag[1][idx_target]['colour']='cyan'
                parag[0][idx_source]['colour']='cyan'
            idx_source+=1
            idx_target+=1
        else:
            # Case yellow/red or green
            idx_source+=1
            idx_target+=1
        if (idx_source==len(source)):
            not_end_source=False
        if (idx_target==len(target)):
            not_end_target=False
    return parag

def assembling_sentence(sentence):                          
    end_with_space=True
    full_sentence=""
    for line in sentence:
        if len(line)>0:
            start_with_space=(line[0]==' ')
            if end_with_space or start_with_space:
                full_sentence+=line
            else:
                full_sentence+=' '
                full_sentence+=line
            end_with_space=(line[-1]==' ')
    return  full_sentence

def get_list_sentences(parag):
    list_parag=[]
    wait_for_blue=True
    list_blue=[]
    for sentence in parag:
        if sentence["colour"]=="black":
            if not(wait_for_blue):
                list_parag.append({"text":assembling_sentence(list_blue)})
                wait_for_blue=True
                list_blue=[]            
        elif (sentence["colour"] in ["blue","cyan"]):
            list_blue.append(remove_tags_with_spaces(sentence["text"]))
            wait_for_blue=False
        elif (sentence["colour"] =="green"):
            list_parag.append({"text":remove_tags_with_spaces(sentence["text"])})
        else:
            list_parag.append({"text":remove_tags_with_spaces(sentence["text"])})
    if not(wait_for_blue):
                list_parag.append({"text":assembling_sentence(list_blue)})     
    return list_parag            

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("--importpath", default='', type=str, required=True,
                        help="Path to the casimir corpus")
    parser.add_argument("--exportpath", default='', type=str, required=False,
                        help="Path to the casimir corpus")

    args = parser.parse_args()

    path_json=args.importpath
    casimir_files=["article_pairs_train.jsonl","article_pairs_dev.jsonl","article_pairs_test.jsonl"]

    dico_all_parag_select={}
    for filename in casimir_files:
        id_pair_source=""
        id_pair_target=""
        current_article=[]
        with open(path_json+"/"+filename, 'r') as article_file:
            for line in article_file:
                current_sentence=json.loads(line.strip('\n'))
                
                if id_pair_source!=current_sentence["id_version_1"]:
                    if len(current_article)>0:
                        list_section=get_list_pairs_parag(current_article)

                        list_parag_valid=[]
                        for section in list_section:
                            for parag in section:   
                                long_enough=is_long_enough(parag)            
                                if long_enough:
                                    prct_modif_ok=respect_limit_modifs(parag)
                                    if prct_modif_ok:
                                        equations_ok= not(contains_too_many_equations(parag,threshold=9))
                                        if equations_ok:
                                            last_first_ok=not(addition_last_or_first(parag))
                                            if last_first_ok:
                                                tag_ok=is_tag_ok(parag)
                                                if tag_ok:
                                                    list_parag_valid.append(parag)                         
            
                        if len(list_parag_valid)>0:
                            dico_all_parag_select[id_pair_source+"."+id_pair_target]=list_parag_valid   

                    current_article=[current_sentence]
                else:
                    current_article.append(current_sentence)

                id_pair_source=current_sentence["id_version_1"]
                id_pair_target=current_sentence["id_version_2"]

            if len(current_article)>0:
                list_section=get_list_pairs_parag(current_article)

                list_parag_valid=[]
                for section in list_section:
                    for parag in section:   
                        long_enough=is_long_enough(parag)            
                        if long_enough:
                            prct_modif_ok=respect_limit_modifs(parag)
                            if prct_modif_ok:
                                equations_ok= not(contains_too_many_equations(parag,threshold=9))
                                if equations_ok:
                                    last_first_ok=not(addition_last_or_first(parag))
                                    if last_first_ok:
                                        tag_ok=is_tag_ok(parag)
                                        if tag_ok:
                                            list_parag_valid.append(parag)                         
            
                if len(list_parag_valid)>0:
                    dico_all_parag_select[id_pair_source+"."+id_pair_target]=list_parag_valid   


    list_test_export=list(dico_all_parag_select.keys())

    # Saving : Full parag and sentences    

    export_path=args.exportpath
    with open(export_path+"/pararev.jsonl", 'w', encoding='utf8') as corpus_file:
        for filename in list_test_export:
            idx_parag=0   
            for parag in dico_all_parag_select[filename]:
                parag=corrections_spaces_and_dash(parag)
                source_file,target_file=filename.split('.')[0],filename.split('.')[1]
                liste_sentences_1,liste_sentences_2=get_list_sentences(parag[0]),get_list_sentences(parag[1])
                list_parag1=[remove_tags_with_spaces(sentence["text"]) for sentence in parag[0] if sentence["colour"]!="black"]
                list_parag2=[remove_tags_with_spaces(sentence["text"]) for sentence in parag[1] if sentence["colour"]!="black"]
                parag1,parag2=assembling_parag_nocolor(list_parag1,list_parag2)
                json.dump({'id_source':source_file,"id_target":target_file,"index_paragraph":idx_parag,"id_paragraph":filename+'.'+str(idx_parag).zfill(2),
                           "parag-1":parag1,
                           "parag-2":parag2,
                           "list-sentences-1": liste_sentences_1,
                           "list-sentences-2": liste_sentences_2
                          },corpus_file, ensure_ascii=False)
                idx_parag+=1
                corpus_file.write('\n')