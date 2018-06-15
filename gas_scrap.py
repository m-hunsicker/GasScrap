#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data fecth from Power next
Created on Thu Jun  7 15:56:10 2018

@author: mitch
"""

#system import
import os
from datetime import date

# Internet data handling imports
from bs4 import BeautifulSoup
import requests

#Plotting
import matplotlib
matplotlib.use('Agg') #This is required at this place to ensure it works when
#launched with no display.
import matplotlib.pyplot as plt

# Intenet site access variables
from private_data import HEADERS, INDEX_LIST, RECEIVERS_EMAIL_LIST, SUPPORT_EMAIL

#Commons
from common import send_email, send_html_email, log_print

#Database
import database_access as da


#File path
FILE_PATH = os.path.dirname(os.path.realpath(__file__))


class Cotation():
    """
    Sert à stocker les cotations A  REFACTORER
    """
    def __init__(self, index, cot_date=None, cotation_set=None):
        self.date = cot_date
        self.index = index
        self.cotation_set = cotation_set

def fetch_cotations(index_list):
    """
    Get cotations
    """
    for index in index_list.keys():
        req = requests.post(index_list[index], HEADERS)
        content = BeautifulSoup(req.json()['html'], 'html.parser')
        cotation_table = content.div.table
        cotation_list = []

        #Product name extraction, we need to scrap the firs header since it the Trading
        #Day
        product_list = []
        for elements in cotation_table.thead.find_all("th"):
            product_list.append(elements.string)
        product_list = product_list[1:]


        #Data extraction
        for row in cotation_table.tbody.find_all('tr'):
            cotation_set = {}
            data_list = []
            for cell in row.find_all('td'):
                data_list.append(cell.string)
            date_component = [int(i) for i in data_list[0].split('-')]
            cot_date = date(date_component[0], date_component[1], date_component[2])
            #print(cot_date)
            for k, data in enumerate(data_list[1:]):
                #print(data)
                price = (lambda x: float(x) if x != None else 'NULL')(data)
                #Cleaning price from erroneous data eg. data < 1€/MWh
                if price != 'NULL':
                    if price < 1:
                        price = 'NULL'
                cotation_set.update({product_list[k]: price})
            cotation_list.append(Cotation(index, cot_date, cotation_set))

        for cotation in cotation_list:
            data = {'trading_day': cotation.date.strftime("%Y-%m-%d"), 'Gas_index':cotation.index}
            data = {**data, **cotation.cotation_set}
            da.insert_data(data)

        log_print("Data inserted")


#Information extraction
def extract_cotations(index_list, previous_date):
    """
    Return the synthetic indexes and associated email
    """

    #If no more recent Trading day then abort
    if previous_date >= da.get_last_date():
        log_print("Pas de nouvelle cotation, arrêt de la procédure")
        #return
    

    #Else compute
    df = da.get_data(index_list)

    #Integration of a synthetic value to compute trends for all indexes

    syn_df = df.groupby('Trading_day', as_index=False, sort=False)['Calendar+1'].mean()

    syn_df['Calendar+2'] = df.groupby('Trading_day',\
          as_index=False, sort=False)['Calendar+2'].mean()['Calendar+2']

    syn_df['Calendar+3'] = df.groupby('Trading_day',\
          as_index=False, sort=False)['Calendar+3'].mean()['Calendar+3']


    syn_df['Synthetic'] = (syn_df['Calendar+1'] + syn_df['Calendar+2'] +\
                          syn_df['Calendar+3'])/3

    #Classement par date descendante utilisée pour les opérations suivantes
    syn_df = syn_df.sort_values('Trading_day', ascending=False)

    log_print("Synthetic index ready")

    #Prix lors de l'appel d'offre
    origin_synthetic = round(syn_df.loc[syn_df['Trading_day'] == '2018-06-06']\
                             ['Synthetic'].item(), 2)
    
    #Dernier prix disponible a priori le closing de la veille.
    last_synthetic = round(syn_df.iloc[0]['Synthetic'].item(), 2) #Since we sorted we can use it
    

    #Evaluation of price evolution trends.
    tendance = 'BAISSE'
    previous_synthetic = round(syn_df.iloc[1]['Synthetic'].item(), 2)
      
    if last_synthetic > previous_synthetic:
        tendance = 'HAUSSE'
    tendance_pct = round((last_synthetic - previous_synthetic)/previous_synthetic*100, 2)

    texte = "\nRappel: L'index de prix synthétique est une moyenne sur les hubs " +\
            "PEG Nord et TTF à partir des produits Cal+1, Cal+2 et Cal+3.\n " +\
            "Les prix sont obtenus via Powernext avec un jour de décalage et l'index est un " +\
            "proxy pour les variations du prix de la molécule des offres fournisseurs.\n" +\
            f"\nIndex du 6 juin : <b>{origin_synthetic} €/MWh</b>\n"+\
            f"Index à date : <b>{last_synthetic} €/MWh</b>\n"+\
            "Ecart de l'index à date vs l'index de l'appel d'offre) du 6 juin : "+\
            f"<b>{round((last_synthetic - origin_synthetic)/origin_synthetic*100,2)}%</b>\n" +\
            f"\nTendance de l'index par rapport à la cotation précédente : {tendance} de " +\
            f"<b>{abs(tendance_pct)}%</b>"

    #Computation of graphics
    fig = plt.figure()
    plt.plot(syn_df['Trading_day'], syn_df['Synthetic'])
    plt.suptitle("Evolution du prix de l'index gazier", fontsize=15)
    plt.xlabel('Date', fontsize=13)
    plt.ylabel('€/MWh', fontsize=13)
    #Size
    fig.set_size_inches(10, 6)
    #Annotate
    plt.annotate("Appel d'offre du 6 juin 2018",
                 xy=(date(2018, 6, 6), origin_synthetic), xycoords='data',
                 xytext=(-90, -50), textcoords='offset points', fontsize=10,
                 arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.2"))

    picture_path = os.path.join(FILE_PATH, 'Data', 'img.png')
    fig.savefig(picture_path)
    #plt.show()

    #Emails sending
    for receiver in RECEIVERS_EMAIL_LIST:
        send_html_email(receiver,
                        f"Evolution prix du gaz: {last_synthetic}€/MWH en {tendance}",
                        texte, picture_path)
    log_print("Emails sent")

if __name__ == "__main__":
    try:
        log_print("Démarrage de la procédure")

        #Get the last Trading day previously inserted
        PREVIOUS_DATE = da.get_last_date()

        #Récupération des données et intégration dans la base
        fetch_cotations(INDEX_LIST)

        extract_cotations(INDEX_LIST, PREVIOUS_DATE)
        log_print("Fin de la procédure")

    except Exception as exception:
        log_print("Erreur dans la  " + str(exception))
        send_email(SUPPORT_EMAIL,
                   "Le processus de récupération des données gaz a planté",
                   "L'erreur est :" + str(exception))
