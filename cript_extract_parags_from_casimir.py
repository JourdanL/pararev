import json
import os
import sys
import re
import argparse
from termcolor import colored, cprint

# I - Utils

def import_data(path,filename):
    with open(path+filename, 'r') as article_file:
        diff_article=[json.loads(line.strip('\n')) for line in article_file]  
    return diff_article

# Function to remove specific tags
def remove_tags(chaine):
    balises = ["[Figure]", "[Equation]", "[Table]"]
    for balise in balises:
        chaine = chaine.replace(balise, "")
    return chaine

def sont_egales_sans_espaces(chaine1, chaine2):
    # Supprimer les espaces des deux chaînes
    chaine1_sans_espaces = re.sub(r'\s', '', chaine1)
    chaine2_sans_espaces = re.sub(r'\s', '', chaine2)

    # Comparer les chaînes sans espaces
    return chaine1_sans_espaces == chaine2_sans_espaces

def enlever_espaces(chaine):
    # Supprimer les espaces des deux chaînes
    chaine_sans_espaces = re.sub(r'\s', '', chaine)

    # Comparer les chaînes sans espaces
    return chaine_sans_espaces


def recollage_parag_nocolor(parag_source,parag_cible):                          
    end_with_space=True
    parag_source_complet=""
    for ligne in parag_source:
        if len(ligne)>0:
            start_with_space=(ligne[0]==' ')
            if end_with_space or start_with_space:
                parag_source_complet+=ligne
            else:
                parag_source_complet+=' '
                parag_source_complet+=ligne
            end_with_space=(ligne[-1]==' ')
    parag_cible_complet=""
    end_with_space=True
    for ligne in parag_cible:
        if len(ligne)>0:
            start_with_space=(ligne[0]==' ')
            if end_with_space or start_with_space:
                parag_cible_complet+=ligne
            else:
                parag_cible_complet+=' '
                parag_cible_complet+=ligne
            end_with_space=(ligne[-1]==' ')
    return  parag_source_complet,parag_cible_complet

# II - Data preparation

def calcul_longeur_modif(phrase,sentence_token_indices):
    debut_sent=0
    fin_sent=0
    if type(sentence_token_indices)==list:
        debut_sent=sentence_token_indices[0]
        fin_sent=sentence_token_indices[1]
        extracted_edit=remove_tags(phrase[debut_sent:fin_sent])
        
        longeur_modif=len(extracted_edit)#fin_sent-debut_sent
    else:
        longeur_modif=0
    
    return longeur_modif

def calcul_pourcentages_modifs(element):
    longeur_modif_1=0
    longeur_modif_2=0
    for idx_elt in range(len(element['edits-combination'])):
        if type(element['edits-combination'][str(idx_elt)]['sentence-1-token-indices'])==list and type(element['edits-combination'][str(idx_elt)]['sentence-2-token-indices'])==list:
            debut_sent1=element['edits-combination'][str(idx_elt)]['sentence-1-token-indices'][0]
            fin_sent1=element['edits-combination'][str(idx_elt)]['sentence-1-token-indices'][1]
            debut_sent2=element['edits-combination'][str(idx_elt)]['sentence-2-token-indices'][0]
            fin_sent2=element['edits-combination'][str(idx_elt)]['sentence-2-token-indices'][1]

            if not(sont_egales_sans_espaces(element['text-sentence-1'][debut_sent1:fin_sent1],element['text-sentence-2'][debut_sent2:fin_sent2])):
                longeur_modif_1+=calcul_longeur_modif(element['text-sentence-1'],element['edits-combination'][str(idx_elt)]['sentence-1-token-indices'])
                longeur_modif_2+=calcul_longeur_modif(element['text-sentence-2'],element['edits-combination'][str(idx_elt)]['sentence-2-token-indices'])
        else:
            longeur_modif_1+=calcul_longeur_modif(element['text-sentence-1'],element['edits-combination'][str(idx_elt)]['sentence-1-token-indices'])
            longeur_modif_2+=calcul_longeur_modif(element['text-sentence-2'],element['edits-combination'][str(idx_elt)]['sentence-2-token-indices'])

    #Calcul des pourcentages modifs
    longueur_phrase_1_ss_balise=len(remove_tags(element['text-sentence-1']))
    longueur_phrase_2_ss_balise=len(remove_tags(element['text-sentence-2']))
    if longueur_phrase_1_ss_balise>0:
        pourcentage_modif_1=longeur_modif_1/longueur_phrase_1_ss_balise
    else:
        pourcentage_modif_1=0
    if longueur_phrase_2_ss_balise>0:
        pourcentage_modif_2=longeur_modif_2/longueur_phrase_2_ss_balise
    else:
        pourcentage_modif_2=0
        
    return pourcentage_modif_1,pourcentage_modif_2,longueur_phrase_1_ss_balise,longueur_phrase_2_ss_balise

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

def get_list_paires_parag(diff_article,seuil_bas=0.5):
    #Initialisations
    old_num_parag_1=-1
    old_num_parag_2=-1
    old_num_section_1=-1
    old_num_section_2=-1
    aggreg_parag_1=[]
    aggreg_parag_2=[]
    
    liste_sections=[]
    liste_paires_parag=[]
    cpt_parag_trop_petits=0
    for element in diff_article:
        
        new_num_section_1,new_num_section_2=get_new_num_section(element)
        
        new_num_parag_1,new_num_parag_2=get_new_num_parag(element)
        
        section_les_deux_changent=(old_num_section_1!=new_num_section_1) and (old_num_section_2!=new_num_section_2)
        section_source_change_cible_vide=(old_num_section_1!=new_num_section_1) and (old_num_section_2+new_num_section_2==-4)
        section_source_vide_cible_change=(old_num_section_1+new_num_section_1==-4) and (old_num_section_2!=new_num_section_2)
        
        parag_les_deux_changent=(old_num_parag_1!=new_num_parag_1) and (old_num_parag_2!=new_num_parag_2)
        parag_source_change_cible_vide=(old_num_parag_1!=new_num_parag_1) and (old_num_parag_2+new_num_parag_2==-4)
        parag_source_vide_cible_change=(old_num_parag_1+new_num_parag_1==-4) and (old_num_parag_2!=new_num_parag_2)
        
        if section_les_deux_changent or section_source_change_cible_vide or section_source_vide_cible_change:
            liste_paires_parag.append((aggreg_parag_1,aggreg_parag_2))

            aggreg_parag_1=[]
            aggreg_parag_2=[]
            liste_sections.append(liste_paires_parag)
            liste_paires_parag=[]
        elif parag_les_deux_changent or parag_source_change_cible_vide or parag_source_vide_cible_change:
            liste_paires_parag.append((aggreg_parag_1,aggreg_parag_2))
            
            aggreg_parag_1=[]
            aggreg_parag_2=[]

        old_num_section_1=new_num_section_1
        old_num_section_2=new_num_section_2  
        
        old_num_parag_1=new_num_parag_1
        old_num_parag_2=new_num_parag_2        
                      
        pourcentage_modif_1,pourcentage_modif_2,longueur_phrase_1,longueur_phrase_2=calcul_pourcentages_modifs(element)
        prct1_round=round(pourcentage_modif_1*100,2)
        prct2_round=round(pourcentage_modif_2*100,2)
        #Cas I vert
        if len(element['edits-combination'])==0:
            #Cas I.1 vert après autre couleur (jaune/rouge)
            aggreg_parag_1.append({"text":str(new_num_parag_1)+"|"+str(len(element['text-sentence-1']))+"-"+str(longueur_phrase_1)+"|","couleur":'black',"sep":'',"flush":True,"longueur":longueur_phrase_1})
            aggreg_parag_2.append({"text":str(new_num_parag_2)+"|"+str(len(element['text-sentence-2']))+"-"+str(longueur_phrase_2)+"|","couleur":'black',"sep":'',"flush":True,"longueur":longueur_phrase_2})
           
            aggreg_parag_1.append({"text":element['text-sentence-1'],"couleur":'green',"sep":'\n',"flush":False})
            aggreg_parag_2.append({"text":element['text-sentence-1'],"couleur":'green',"sep":'\n',"flush":False})

        #Cas II bleu
        elif (pourcentage_modif_1<seuil_bas) and (pourcentage_modif_2<seuil_bas):
            #Imprimer en bleu les zones modifiées et en vert les autres
            fin_prec_1=0
            fin_prec_2=0
            liste_intentions=[]
            for idx_elt in range(len(element['edits-combination'])):
                liste_intentions.append(element['edits-combination'][str(idx_elt)]["intention"])
            liste_intentions=list(set(liste_intentions))
            aggreg_parag_1.append({"list_intentions":liste_intentions,"text":str(new_num_parag_1)+"|"+str(len(element['text-sentence-1']))+"-"+str(longueur_phrase_1)+"|"+str(prct1_round)+" "+str(prct2_round),"couleur":'black',"sep":'',"flush":True,"longueur":longueur_phrase_1,"prct_modif":prct1_round})
            aggreg_parag_2.append({"list_intentions":liste_intentions,"text":str(new_num_parag_2)+"|"+str(len(element['text-sentence-2']))+"-"+str(longueur_phrase_2)+"|"+str(prct1_round)+" "+str(prct2_round),"couleur":'black',"sep":'',"flush":True,"longueur":longueur_phrase_2,"prct_modif":prct2_round})
                  
            for idx_elt in range(len(element['edits-combination'])):
                debut_sent1=0
                fin_sent1=0
                         
                if type(element['edits-combination'][str(idx_elt)]['sentence-1-token-indices'])==list:
                    debut_sent1=element['edits-combination'][str(idx_elt)]['sentence-1-token-indices'][0]
                    fin_sent1=element['edits-combination'][str(idx_elt)]['sentence-1-token-indices'][1]
                    
                    if type(element['edits-combination'][str(idx_elt)]['sentence-2-token-indices'])==list:
                        debut_sent2=element['edits-combination'][str(idx_elt)]['sentence-2-token-indices'][0]
                        fin_sent2=element['edits-combination'][str(idx_elt)]['sentence-2-token-indices'][1]

                        if sont_egales_sans_espaces(element['text-sentence-1'][debut_sent1:fin_sent1],element['text-sentence-2'][debut_sent2:fin_sent2]):
                            aggreg_parag_1.append({"text":element['text-sentence-1'][fin_prec_1:debut_sent1],"couleur":'cyan',"sep":'',"flush":True})
                            aggreg_parag_1.append({"text":element['text-sentence-1'][debut_sent1:fin_sent1],"couleur":'cyan',"sep":'',"flush":True})
                        else:
                            aggreg_parag_1.append({"text":element['text-sentence-1'][fin_prec_1:debut_sent1],"couleur":'cyan',"sep":'',"flush":True})
                            aggreg_parag_1.append({"text":element['text-sentence-1'][debut_sent1:fin_sent1],"couleur":'blue',"sep":'',"flush":True})

                    else:
                        aggreg_parag_1.append({"text":element['text-sentence-1'][fin_prec_1:debut_sent1],"couleur":'cyan',"sep":'',"flush":True})
                        aggreg_parag_1.append({"text":element['text-sentence-1'][debut_sent1:fin_sent1],"couleur":'blue',"sep":'',"flush":True})
                    fin_prec_1=fin_sent1
            aggreg_parag_1.append({"text":element['text-sentence-1'][fin_prec_1:],"couleur":'cyan',"sep":'\n',"flush":False})
                
            for idx_elt in range(len(element['edits-combination'])):
                debut_sent2=0
                fin_sent2=0
                                     
                if type(element['edits-combination'][str(idx_elt)]['sentence-2-token-indices'])==list:
                    debut_sent2=element['edits-combination'][str(idx_elt)]['sentence-2-token-indices'][0]
                    fin_sent2=element['edits-combination'][str(idx_elt)]['sentence-2-token-indices'][1]
                    
                    if type(element['edits-combination'][str(idx_elt)]['sentence-1-token-indices'])==list:
                        debut_sent1=element['edits-combination'][str(idx_elt)]['sentence-1-token-indices'][0]
                        fin_sent1=element['edits-combination'][str(idx_elt)]['sentence-1-token-indices'][1]
                        if sont_egales_sans_espaces(element['text-sentence-1'][debut_sent1:fin_sent1],element['text-sentence-2'][debut_sent2:fin_sent2]):
                            aggreg_parag_2.append({"text":element['text-sentence-2'][fin_prec_2:debut_sent2],"couleur":'cyan',"sep":'',"flush":True})
                            aggreg_parag_2.append({"text":element['text-sentence-2'][debut_sent2:fin_sent2],"couleur":'cyan',"sep":'',"flush":True})
                        else:
                            aggreg_parag_2.append({"text":element['text-sentence-2'][fin_prec_2:debut_sent2],"couleur":'cyan',"sep":'',"flush":True})
                            aggreg_parag_2.append({"text":element['text-sentence-2'][debut_sent2:fin_sent2],"couleur":'blue',"sep":'',"flush":True})
                    else:
                        
                        aggreg_parag_2.append({"text":element['text-sentence-2'][fin_prec_2:debut_sent2],"couleur":'cyan',"sep":'',"flush":True})
                        aggreg_parag_2.append({"text":element['text-sentence-2'][debut_sent2:fin_sent2],"couleur":'blue',"sep":'',"flush":True})
                    fin_prec_2=fin_sent2
            aggreg_parag_2.append({"text":element['text-sentence-2'][fin_prec_2:],"couleur":'cyan',"sep":'\n',"flush":False})
                
            reset=True
        #Cas III: rouge/jaune
        else:
            liste_intentions=[]
            for idx_elt in range(len(element['edits-combination'])):
                liste_intentions.append(element['edits-combination'][str(idx_elt)]["intention"])
            liste_intentions=list(set(liste_intentions))
            aggreg_parag_1.append({"list_intentions":liste_intentions,"text":str(new_num_parag_1)+"|"+str(len(element['text-sentence-1']))+"-"+str(longueur_phrase_1)+"|"+str(prct1_round)+" "+str(prct2_round),"couleur":'black',"sep":'',"flush":True,"longueur":longueur_phrase_1,"prct_modif":prct1_round})
            aggreg_parag_1.append({"text":element['text-sentence-1'],"couleur":'yellow',"sep":'\n',"flush":False})
            
            aggreg_parag_2.append({"list_intentions":liste_intentions,"text":str(new_num_parag_2)+"|"+str(len(element['text-sentence-2']))+"-"+str(longueur_phrase_2)+"|"+str(prct1_round)+" "+str(prct2_round),"couleur":'black',"sep":'',"flush":True,"longueur":longueur_phrase_2,"prct_modif":prct2_round})
            aggreg_parag_2.append({"text":element['text-sentence-2'],"couleur":'red',"sep":'\n',"flush":False})
    
    return liste_sections

# III - Filters

def is_long_enough(paire_parag,longueur_minimum=250):    
    parag_source=[element for element in paire_parag[0] if element['couleur']=="black" ]
    parag_cible=[element for element in paire_parag[1] if element['couleur']=="black" ]
    longeur_parag_1=sum([ligne_source["longueur"] for ligne_source in parag_source])
    longeur_parag_2=sum([ligne_cible["longueur"] for ligne_cible in parag_cible])
    
    return (max(longeur_parag_1,longeur_parag_2)>longueur_minimum)    

def respect_limit_modifs(paire_parag, prct_mini_phrase=25,prct_mini_parag=10, prct_maxi=90, lg_modif_maxi=200,prct_maxi_parag=40):
    parag_source=[element for element in paire_parag[0] if element['couleur']=="black" ]        
    parag_cible=[element for element in paire_parag[1] if element['couleur']=="black" ]
    all_colors=set([ligne_source["couleur"] for ligne_source in paire_parag[0]]+[ligne_cible["couleur"] for ligne_cible in paire_parag[1]])
    prct_modif_max=max([0]+[max(ligne_source["prct_modif"],ligne_cible["prct_modif"]) for (ligne_source, ligne_cible) in zip(parag_source, parag_cible) if "prct_modif" in ligne_source.keys()])
    longueur_plus_maxi_parag1=sum([ligne_source["longueur"] for (ligne_source, ligne_cible) in zip(parag_source, parag_cible) if ("prct_modif" in ligne_source.keys() and max(ligne_source["prct_modif"],ligne_cible["prct_modif"])>prct_maxi) ])
    longueur_plus_maxi_parag2=sum([ligne_cible["longueur"] for (ligne_source, ligne_cible) in zip(parag_source, parag_cible) if ("prct_modif" in ligne_source.keys() and max(ligne_source["prct_modif"],ligne_cible["prct_modif"])>prct_maxi) ])
    longueur_totale_parag1=sum([ligne_source["longueur"] for ligne_source in parag_source])
    longueur_totale_parag2=sum([ligne_cible["longueur"] for ligne_cible in parag_cible])
   
    longueur_modif_parag1=sum([ligne_source["prct_modif"]*ligne_source["longueur"] for (ligne_source, ligne_cible) in zip(parag_source, parag_cible) if "prct_modif" in ligne_source.keys()])
    longueur_modif_parag2=sum([ligne_cible["prct_modif"]*ligne_cible["longueur"] for (ligne_source, ligne_cible) in zip(parag_source, parag_cible) if "prct_modif" in ligne_source.keys()])

    if longueur_totale_parag1>0:
        prct_modif_parag1=longueur_modif_parag1/longueur_totale_parag1
    else:
        prct_modif_parag1=0
    if longueur_totale_parag2>0:
        prct_modif_parag2=longueur_modif_parag2/longueur_totale_parag2
    else:
        prct_modif_parag2=0
        
    if longueur_totale_parag1==0 and longueur_totale_parag2==0:
        return False
    elif longueur_totale_parag1==0:
        trop_de_modif=(longueur_plus_maxi_parag2/longueur_totale_parag2<prct_maxi_parag/100)
    elif longueur_totale_parag2==0:
        trop_de_modif=(longueur_plus_maxi_parag1/longueur_totale_parag1<prct_maxi_parag/100)
    else:
        trop_de_modif=(max(longueur_plus_maxi_parag1/longueur_totale_parag1,longueur_plus_maxi_parag2/longueur_totale_parag2)<prct_maxi_parag/100)
    
    trop_de_modif=trop_de_modif or (max(longueur_plus_maxi_parag1,longueur_plus_maxi_parag2)<lg_modif_maxi)
    
    if len(all_colors.intersection({"yellow","red"}))==0:
        prct_mini_blue_only=20
        longueur_phrases_modif_parag1=sum([ligne_source["longueur"] for ligne_source in parag_source if ("prct_modif" in ligne_source.keys() ) ])
        longueur_phrases_modif_parag2=sum([ligne_cible["longueur"] for ligne_cible in parag_cible if ("prct_modif" in ligne_cible.keys() )])
        if longueur_phrases_modif_parag1>0:
            prct_modif_parag1_blue=longueur_modif_parag1/longueur_phrases_modif_parag1
        else:
            prct_modif_parag1_blue=0
        if longueur_phrases_modif_parag2>0:
            prct_modif_parag2_blue=longueur_modif_parag2/longueur_phrases_modif_parag2
        else:
            prct_modif_parag2_blue=0
        if "green" in all_colors:
            return  prct_modif_max>prct_mini_phrase and trop_de_modif and max(prct_modif_parag1,prct_modif_parag2)> prct_mini_parag and max(prct_modif_parag1_blue,prct_modif_parag2_blue)> prct_mini_blue_only 
        else:
            return  prct_modif_max>prct_mini_phrase and trop_de_modif and max(prct_modif_parag1_blue,prct_modif_parag2_blue)> prct_mini_blue_only 
    else:
        return  prct_modif_max>prct_mini_phrase and trop_de_modif and max(prct_modif_parag1,prct_modif_parag2)> prct_mini_parag        
    
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

def contains_too_many_equations(paire_parag, threshold=11):
    # Extract draft and revised paragraphs from the pair
    draft_paragraph=' '.join([element["text"] for element in paire_parag[0] if (element['couleur']!="black")])
    revised_paragraph=' '.join([element["text"] for element in paire_parag[1] if (element['couleur']!="black")])
    #Extract only the rewritten sentences
    draft_paragraph_no_green=' '.join([element["text"] for element in paire_parag[0] if (element['couleur']!="green" and element['couleur']!="black")])
    revised_paragraph_no_green=' '.join([element["text"] for element in paire_parag[1] if (element['couleur']!="green" and element['couleur']!="black")])

    # Count special characters in each paragraph
    draft_character_counts = count_special_characters(draft_paragraph)
    revised_character_counts = count_special_characters(revised_paragraph)
    # Count special characters in each paragraph only in rewritten sentences
    draft_character_counts_no_green = count_special_characters(draft_paragraph_no_green)
    revised_character_counts_no_green = count_special_characters(revised_paragraph_no_green)

    # Calculate the total count of special characters in each paragraph
    draft_total_count = 2*sum(draft_character_counts.values())+ 7*draft_character_counts["\\(cid:\\d+\\)"]+ 9*draft_character_counts["\\[Equation\\]"]
    revised_total_count = 2*sum(revised_character_counts.values())+ 7*revised_character_counts["\\(cid:\\d+\\)"]+9*revised_character_counts["\\[Equation\\]"]
    draft_total_count_no_green = 2*sum(draft_character_counts_no_green.values())+ 7*draft_character_counts_no_green["\\(cid:\\d+\\)"]+ 9*draft_character_counts_no_green["\\[Equation\\]"]
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
def last_is_problem(phrase_source,phrase_cible):
    #Remove the tags
    phrase_source_no_tag=remove_tags(phrase_source["text"])
    phrase_cible_no_tag=remove_tags(phrase_cible["text"])
    #Remove tags and spaces
    phrase_source_condens=enlever_espaces(remove_tags(phrase_source["text"]))
    phrase_cible_condens=enlever_espaces(remove_tags(phrase_cible["text"]))

    #If the source sentence is not empty, does it have an incorrect ending?
    fin_1_ko= (len(phrase_source["text"])>0) and check_incorrect_ending(phrase_source_no_tag)
    #If the target sentence is not empty, does it have an incorrect ending?
    fin_2_ko= (len(phrase_cible["text"])>0) and check_incorrect_ending(phrase_cible_no_tag)
    #If one of the sentences have an incorrect ending, exit the function with True
    if fin_1_ko or fin_2_ko:
        return True
    
    #Case 1: Heavy change
    if (phrase_source["couleur"]=="yellow") and (phrase_cible["couleur"]=="red"):
    #Est ce quele plus grand est plus petit que 3 fois le plus petit?
        #Case A: The target is longer
        if phrase_source_condens<phrase_cible_condens:
            #Is the source equal to the beginning of the target?
            is_included= (phrase_cible_condens[0:len(phrase_source_condens)]==phrase_source_condens)
            #Is the target more than 3 time the length of the source? (Too much text difference)
            is_too_long=(len(phrase_cible_condens)>3*len(phrase_source_condens))
            return is_included or is_too_long
        #Case B: The source is longer
        else:
            #Is the target equal to the beginning of the source?
            is_included= (phrase_source_condens[0:len(phrase_cible_condens)]==phrase_cible_condens)
            #Is the source more than 3 time the length of the target? (Too much text difference)
            is_too_long=(len(phrase_source_condens)>3*len(phrase_cible_condens))
            return  is_included or is_too_long
    #Case 2: Moderate change or no change, if moderate change, correctness of ending have been checked previously
    else:
        return False
    
#Return true if there is a problem detected in the last sentence
def last_is_problem_extended(phrase_source,phrase_cible):
    #Remove the tags
    phrase_source_no_tag=remove_tags(phrase_source["text"])
    phrase_cible_no_tag=remove_tags(phrase_cible["text"])
    #Remove tags and spaces
    phrase_source_condens=enlever_espaces(remove_tags(phrase_source["text"]))
    phrase_cible_condens=enlever_espaces(remove_tags(phrase_cible["text"]))

    #If the source sentence is not empty, does it have an incorrect ending?
    fin_1_ko= (len(phrase_source["text"])>0) and check_incorrect_ending(phrase_source_no_tag)
    #If the target sentence is not empty, does it have an incorrect ending?
    fin_2_ko= (len(phrase_cible["text"])>0) and check_incorrect_ending(phrase_cible_no_tag)
    #If one of the sentences have an incorrect ending, exit the function with True
    if fin_1_ko or fin_2_ko:
        return True
    
    #Case 1: Deletion of a sentence
    if (phrase_source["couleur"]=="yellow") and ((phrase_cible["couleur"]!="red") or len(phrase_cible["text"])==0):                                                
        return check_incorrect_beginning_ending(phrase_source_no_tag)
    #Case 2: Addition of a sentence
    elif (phrase_cible["couleur"]=="red") and ((phrase_source["couleur"]!="yellow") or len(phrase_source["text"])==0):
        return check_incorrect_beginning_ending(phrase_cible_no_tag)
    #Cas 3: Heavy change
    elif (phrase_source["couleur"]=="yellow") and (phrase_cible["couleur"]=="red"):
    #Est ce quele plus grand est plus petit que 3 fois le plus petit?
        #Case A: The target is longer
        if phrase_source_condens<phrase_cible_condens:
            #Is the source equal to the beginning of the target?
            is_included= (phrase_cible_condens[0:len(phrase_source_condens)]==phrase_source_condens)
            #Is the target more than 3 time the length of the source? (Too much text difference)
            is_too_long=(len(phrase_cible_condens)>3*len(phrase_source_condens))
            return is_included or is_too_long
        #Case B: The source is longer
        else:
            #Is the target equal to the beginning of the source?
            is_included= (phrase_source_condens[0:len(phrase_cible_condens)]==phrase_cible_condens)
            #Is the source more than 3 time the length of the target? (Too much text difference)
            is_too_long=(len(phrase_source_condens)>3*len(phrase_cible_condens))
            return  is_included or is_too_long
    #Case 4: Moderate change or no change, if moderate change, correctness of ending have been checked previously
    else:
        return False
    
def first_is_problem(phrase_source,phrase_cible):
    #Remove the tags
    phrase_source_no_tag=remove_tags(phrase_source["text"])
    phrase_cible_no_tag=remove_tags(phrase_cible["text"])
    #Remove tags and spaces
    phrase_source_condens=enlever_espaces(remove_tags(phrase_source["text"]))
    phrase_cible_condens=enlever_espaces(remove_tags(phrase_cible["text"]))
    
    #Cas que jaune
    if len(phrase_source["text"])>0:
        #Check that the first alphabetical letter is a capital letter
        debut_1_ko= check_incorrect_beginning(phrase_source_no_tag)
    else:
        debut_1_ko=False
    if len(phrase_cible["text"])>0:
        debut_2_ko= check_incorrect_beginning(phrase_cible_no_tag)
    else:
        debut_2_ko=False
    if debut_1_ko or debut_2_ko:
        #Raise a problem in the first sentence is for one of them the first alphabetical letter is NOT a capital letter
        return True
    
    if (phrase_source["couleur"]=="yellow") and (len(phrase_cible["text"])==0):
        return len(phrase_source_condens)>0
    #Cas que rouge
    elif (phrase_cible["couleur"]=="red") and (len(phrase_source["text"])==0):
        return len(phrase_cible_condens)>0
    #Cas jaune et rouge 
    elif (phrase_source["couleur"]=="yellow") and (phrase_cible["couleur"]=="red"):
        #est ce que le plus petit est égal à la fin du plus grand
        if phrase_source_condens<phrase_cible_condens:
            #Is the source equal to the end of the target?
            is_included=phrase_cible_condens[len(phrase_cible_condens)-len(phrase_source_condens):len(phrase_cible_condens)]==phrase_source_condens
            #Is the target more than 3 time the length of the source? (Too much text difference)
            is_too_long=(len(phrase_cible_condens)>3*len(phrase_source_condens))
            return is_too_long or is_included
        else:
            #Is the target equal to the end of the source?
            is_included=phrase_source_condens[len(phrase_source_condens)-len(phrase_cible_condens):len(phrase_source_condens)]==phrase_cible_condens
            #Is the source more than 3 time the length of the target? (Too much text difference)
            is_too_long=(len(phrase_source_condens)>3*len(phrase_cible_condens))
            return  is_too_long or is_included
    #Cas bleu:
    elif (phrase_source["couleur"] in ["blue","cyan"]):
        #Cas bleu modif
        #est ce que le plus petit est égal à la fin du plus grand
        if (phrase_source["couleur"]=="blue") and (phrase_cible["couleur"]=="blue"):
            if phrase_source_condens<phrase_cible_condens:
                #Is the source equal to the end of the target?
                return phrase_cible_condens[len(phrase_cible_condens)-len(phrase_source_condens):len(phrase_cible_condens)]==phrase_source_condens
            else:
                #Is the target equal to the end of the source?
                return phrase_source_condens[len(phrase_source_condens)-len(phrase_cible_condens):len(phrase_source_condens)]==phrase_cible_condens
        #Cas bleu ajout unilatéral
        elif (phrase_source["couleur"]=="blue") and (phrase_cible["couleur"]=="cyan"):
            return len(phrase_source["text"])>10
            
        elif (phrase_source["couleur"]=="cyan") and (phrase_cible["couleur"]=="blue"):
            return len(phrase_cible["text"])>10
    #else: cas vert vert normalement ou bleu sans modif sur le début de phrase
    else:
        return False
    
def ajout_last_or_first(paire_parag):
    parag_source=[element for element in paire_parag[0] if ((len(element['text'])>0 or element["couleur"] in ["yellow","red"]) and element['couleur']!="black")]
    parag_cible=[element for element in paire_parag[1] if  ((len(element['text'])>0 or element["couleur"] in ["yellow","red"]) and element['couleur']!="black")]
    is_last=(parag_source[-1]["couleur"] in ["yellow","red","blue"]) or (parag_cible[-1]["couleur"] in ["yellow","red","blue"])
    is_first=first_is_problem(parag_source[0],parag_cible[0])
    if is_last:
        is_last=last_is_problem(parag_source[-1],parag_cible[-1])
    return is_first or is_last

def verif_balise(liste_text_1, full_text_2):
    baliseok=True
    if len(liste_text_1)>0:
        idx_debut=0
        #We don't consider the tag at the beginning
        while liste_text_1[idx_debut] in ["[Table]","[Figure]","[Equation]"]:
            idx_debut+=1
        idx_fin=len(liste_text_1)
        #We don't consider the tags at the end
        while liste_text_1[idx_fin-1] in ["[Table]","[Figure]","[Equation]"]:
            idx_fin-=1
        
        cropped_liste_text_1=liste_text_1[idx_debut:idx_fin]
        
        #After the tags at the beginning, does the paragraph start correctly?
        if idx_debut!=0:
            baliseok = baliseok and not(check_incorrect_beginning(cropped_liste_text_1[0]))
        #Before the tags at the end, does the paragraph end correctly
        if idx_fin!=len(liste_text_1):
            baliseok = baliseok and not(check_incorrect_ending(cropped_liste_text_1[-1]))
        if not baliseok:
            return baliseok
        else:
            idx_balise=0
            #Was some text incorrectly replaced by a tag?
            while idx_balise<len(cropped_liste_text_1):
                if cropped_liste_text_1[idx_balise] in ["[Table]","[Figure]","[Equation]"]:
                    new_tag_no_replace= (cropped_liste_text_1[idx_balise-1]+cropped_liste_text_1[idx_balise+1] in enlever_espaces(full_text_2))
                    no_change= (cropped_liste_text_1[idx_balise-1]+cropped_liste_text_1[idx_balise]+cropped_liste_text_1[idx_balise+1] in enlever_espaces(full_text_2))
                    baliseok=baliseok and (new_tag_no_replace or no_change)
                idx_balise+=1
    return baliseok


def balise_ok(parag): 
    parag_source=[phrase["text"] for phrase in parag[0] if phrase["couleur"]!="black"]
    parag_cible=[phrase["text"] for phrase in parag[1] if phrase["couleur"]!="black"]

    text_source,text_cible=recollage_parag_nocolor(parag_source,parag_cible)
    liste_text_source=text_source.split(" ")
    liste_text_cible=text_cible.split(" ")
    
    baliseok=True
    if len(liste_text_source)>0:
        baliseok= baliseok and verif_balise(liste_text_source, text_cible)
    if len(parag_cible)>0:
        baliseok= baliseok and verif_balise(liste_text_cible, text_source)
    return baliseok

# IV - Prepare export mini corpus

def remove_tags_avec_espaces(chaine):
# Fonction pour enlever les balises spécifiques
    balises = [" [Figure]", " [Equation]", " [Table]"]
    for balise in balises:
        chaine = chaine.replace(balise, "")
    balises = ["[Figure] ", "[Equation] ", "[Table] "]
    for balise in balises:
        chaine = chaine.replace(balise, "")
    balises = ["[Figure]", "[Equation]", "[Table]"]
    for balise in balises:
        chaine = chaine.replace(balise, "")
    return chaine

def difference_tiret(chaine1, chaine2):
    # Vérifie si les longueurs des chaînes diffèrent exactement de 1
    if abs(len(chaine1) - len(chaine2)) != 1:
        return False
    
    # Identifie la chaîne la plus courte et la plus longue
    courte = min(chaine1, chaine2, key=len)
    longue = max(chaine1, chaine2, key=len)

    # Supprime tous les tirets des deux chaînes
    chaine1_sans_tiret = chaine1.replace("-", "")
    chaine2_sans_tiret = chaine2.replace("-", "")

    # Vérifie si les chaînes sont identiques après suppression des tirets
    if chaine1_sans_tiret == chaine2_sans_tiret:
        return True
    return False

def corrections_espaces_et_tirets(parag):
    source=parag[0]
    cible=parag[1]
    not_end_source=True
    not_end_cible=True
    idx_source=0
    idx_cible=0
    while not_end_source and not_end_cible:
        phrase_source=source[idx_source]['text']
        phrase_cible=cible[idx_cible]['text']
        if (source[idx_source]['couleur']=='cyan') and (cible[idx_cible]['couleur']=='cyan'):
            if len(phrase_source)!=len(phrase_cible) and sont_egales_sans_espaces(phrase_source,phrase_cible):
                if len(phrase_source)>len(phrase_cible):
                    parag[1][idx_cible]['text']=source[idx_source]['text']
                else:
                    parag[0][idx_source]['text']=cible[idx_cible]['text']
            idx_source+=1
            idx_cible+=1
        elif (source[idx_source]['couleur']=='blue') and (cible[idx_cible]['couleur']=='cyan'):
            idx_source+=1
        elif (source[idx_source]['couleur']=='cyan') and (cible[idx_cible]['couleur']=='blue'):
            idx_cible+=1
        elif (source[idx_source]['couleur']=='blue') and (cible[idx_cible]['couleur']=='blue'):
            if difference_tiret(phrase_source,phrase_cible):
                if len(phrase_source)>len(phrase_cible):
                    parag[1][idx_cible]['text']=source[idx_source]['text']                    
                else:
                    parag[0][idx_source]['text']=cible[idx_cible]['text']                    
                parag[1][idx_cible]['couleur']='cyan'
                parag[0][idx_source]['couleur']='cyan'
            idx_source+=1
            idx_cible+=1
        else:
            #cas jr ou v 
            idx_source+=1
            idx_cible+=1
        if (idx_source==len(source)):
            not_end_source=False
        if (idx_cible==len(cible)):
            not_end_cible=False
    return parag

def recollage_sentence(sentence):                          
    end_with_space=True
    sentence_complet=""
    for ligne in sentence:
        if len(ligne)>0:
            start_with_space=(ligne[0]==' ')
            if end_with_space or start_with_space:
                sentence_complet+=ligne
            else:
                sentence_complet+=' '
                sentence_complet+=ligne
            end_with_space=(ligne[-1]==' ')
    return  sentence_complet

def get_list_sentences(parag):
    liste_parag=[]
    wait_for_blue=True
    liste_blue=[]
    for phrase in parag:
        if phrase["couleur"]=="black":
            if not(wait_for_blue):
                liste_parag.append({"text":recollage_sentence(liste_blue)})
                wait_for_blue=True
                liste_blue=[]            
        elif (phrase["couleur"] in ["blue","cyan"]):
            liste_blue.append(remove_tags_avec_espaces(phrase["text"]))
            wait_for_blue=False
        elif (phrase["couleur"] =="green"):
            liste_parag.append({"text":remove_tags_avec_espaces(phrase["text"])})
        else:
            liste_parag.append({"text":remove_tags_avec_espaces(phrase["text"])})
    if not(wait_for_blue):
                liste_parag.append({"text":recollage_sentence(liste_blue)})     
    return liste_parag            

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("--importpath", default='', type=str, required=True,
                        help="Path to the casimir corpus")
    parser.add_argument("--exportpath", default='', type=str, required=False,
                        help="Path to the casimir corpus")

    args = parser.parse_args()

    path_json=args.importpath
    liste_articles=os.listdir(path_json)

    dico_all_parag_select={}

    for filename in liste_articles:
        article=import_data(path_json,filename)
        liste_section=get_list_paires_parag(article)

        liste_parag_valides=[]
        for section in liste_section:
            for parag in section:   
                assez_grand=is_long_enough(parag)            
                if assez_grand:
                    prct_modif_ok=respect_limit_modifs(parag)
                    if prct_modif_ok:
                        equations_ok= not(contains_too_many_equations(parag,threshold=9))
                        if equations_ok:
                            last_first_ok=not(ajout_last_or_first(parag))
                            if last_first_ok:
                                baliseok=balise_ok(parag)
                                if baliseok:
                                    liste_parag_valides.append(parag)                         
   
        if len(liste_parag_valides)>0:
            dico_all_parag_select[filename[:-6]]=liste_parag_valides    

    liste_test_export=list(dico_all_parag_select.keys())

    # Saving 1 : Colorfull, for displaying and easier annotation by humans

    export_path=args.exportpath
    with open(export_path+"gloubiboulga_colorfull.jsonl", 'w') as corpus_file:
        for filename in liste_test_export:
            idx_parag=0        
            for parag in dico_all_parag_select[filename]:
                parag=corrections_espaces_et_tirets(parag)
                source_file, cible_file=filename.split('.')[0], filename.split('.')[1]
                liste_parag1, liste_parag2,list_intentions =[], [], []
                for phrase in parag[0]:
                    if phrase["couleur"]=="black":
                        if "list_intentions" in phrase.keys():
                            list_intentions=phrase["list_intentions"]
                        else:
                            list_intentions=[]
                    else:
                        liste_parag1.append({"color":phrase["couleur"],"text":remove_tags_avec_espaces(phrase["text"])})
                for phrase in parag[1]:
                    if phrase["couleur"]=="black":
                        if "list_intentions" in phrase.keys():
                            list_intentions=phrase["list_intentions"]
                        else:
                            list_intentions=[]
                    else:
                        liste_parag2.append({"color":phrase["couleur"],"text":remove_tags_avec_espaces(phrase["text"])})

                json.dump({'id_source':source_file,"id_cible":cible_file,"index_paragraph":idx_parag,"id_paragraph":filename+'.'+str(idx_parag).zfill(2),
                           "parag-1":liste_parag1,
                           "parag-2":liste_parag2
                          },corpus_file)
                idx_parag+=1
                corpus_file.write('\n')   

    # Saving 2: Full parag and sentence, no color info, for general use    

    export_path=args.exportpath
    with open(export_path+"gloubiboulga.jsonl", 'w', encoding='utf8') as corpus_file:
        for filename in liste_test_export:
            idx_parag=0   
            for parag in dico_all_parag_select[filename]:
                parag=corrections_espaces_et_tirets(parag)
                source_file,cible_file=filename.split('.')[0],filename.split('.')[1]
                liste_sentences_1,liste_sentences_2=get_list_sentences(parag[0]),get_list_sentences(parag[1])
                liste_parag1=[remove_tags_avec_espaces(phrase["text"]) for phrase in parag[0] if phrase["couleur"]!="black"]
                liste_parag2=[remove_tags_avec_espaces(phrase["text"]) for phrase in parag[1] if phrase["couleur"]!="black"]
                parag1,parag2=recollage_parag_nocolor(liste_parag1,liste_parag2)
                json.dump({'id_source':source_file,"id_cible":cible_file,"index_paragraph":idx_parag,"id_paragraph":filename+'.'+str(idx_parag).zfill(2),
                           "parag-1":parag1,
                           "parag-2":parag2,
                           "list-sentences-1": liste_sentences_1,
                           "list-sentences-2": liste_sentences_2
                          },corpus_file, ensure_ascii=False)
                idx_parag+=1
                corpus_file.write('\n')