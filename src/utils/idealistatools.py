# -*- coding: utf-8 -*-

import glob
import json
import os
import requests
from requests.auth import HTTPBasicAuth
import urllib.request
from bs4 import BeautifulSoup
from math import sin, cos, sqrt, atan2, radians

import numpy as np
import pandas as pd

import seaborn as sns
import matplotlib.pyplot as plt

from sklearn import preprocessing
from sklearn.feature_extraction import FeatureHasher

# https://developers.idealista.com/access-request
class Idealista:
    '''
    Clase que permite obtener información del portal Idealista a partir de su API.
    '''
    
    __url_token = "https://api.idealista.com/oauth/token"
    __url_search = "http://api.idealista.com/3.5/es/search?"
    __token = None
    
    def __init__(self, debug = False):
        '''
        Constructor
        Parametros:
            debug: si vale True muestra mensajes de debug
        '''
        self.__debug = debug
    
    def generate_token(self, api_key=None, api_secret=None):
        '''
        Genera un token necesario para usar las funciones ofrecidas por la API de Idealista.
        Este token es necesario para invocar al método 'search'.
        
        Argumentos:
        * api_key: api_key
        * api_secret: api_secret
        
        Resultado:
        * El token
        '''
        basic_auth = HTTPBasicAuth(api_key, api_secret)
            
        r = requests.post(self.__url_token,
                          auth=basic_auth,
                          data={"grant_type": "client_credentials"})

        token_response = json.loads(r.text)
        if self.__debug:
            print("r.text:", r.text)
        self.__token = token_response["access_token"]
        if self.__debug:
            print("Token:", self.__token)
    
    def set_token(self, token):
        '''
        Establece un token de la API de Idealista.
        Este token es necesario para invocar al método 'search'.
        
        Argumentos:
        * token: token de la API de Idealista.
        '''
        self.__token = token
        
    def search(self, center, country='es', numPage='1', maxItems='50', distance='1000', propertyType='homes', operation='sale', maxSize='100'):
        '''
        Realiza búsquedas de propiedades en Idealista.
        
        Argumentos:
        * center: centro del radio de búsqueda en longitud/latitud
        * country: código de país, que puede tomar uno de estos valores:
            es - idealista.com
            it - idealista.it
            pt - idealista.pt
        * numPage: número de página (para paginación)
        * maxItems: número de lementos por página (para paginación)
        * distance: radio de búsqueda en metros
        * propertyType: tipo de propiedad a buscar. Posibles valores: homes, offices, premises, garages, bedrooms
        * operation: tipo de operación. Posibles valores: sale, rent
        * maxSize: tamaño máximo de la vivienda en m2
        
        Resultado:
        * JSON con el resultado de la invocación a la función search de la API de Idealista
        '''
        api_url = self.__url_search + \
            'country=' + country +\
            '&center=' + center +\
            '&numPage=' + numPage +\
            '&maxItems=' + maxItems +\
            '&distance=' + distance +\
            '&propertyType=' + propertyType +\
            '&operation=' + operation +\
            '&maxSize=' + maxSize        
        if self.__debug:
            print(api_url)
        
        headers = {"Authorization": "Bearer " + self.__token}
        r = requests.post(api_url, headers = headers)
        result = None
        try:
            result = json.loads(r.text)
        except Exception as ex:
            print("Error:", ex)
            print("r.text:", r.text)            
            
        return result
    
    def summary_result(self, result):
        
        summary = {
            "total": result["total"],
            "totalPages": result["totalPages"],
            "actualPage": result["actualPage"],
            "itemsPerPage": result["itemsPerPage"]
        }
        
        return summary
    
    def elementlist_tojson(self, result, file):
        '''
        Graba en un fichero el elemento "elementList" del resultado de una invocación a la función search de la API de Idealista.
        Argumentos:
        * result: resultado de una invocación a la función search de la API de Idealista
        * file: path del fichero donde graba el elemento "elementList"     
        '''
        with open(file, 'w') as outfile:
            json.dump(result["elementList"], outfile)
    
    def read_json(self, file, type='frame'):
        '''
        Genera un DataFrame a partir de un fichero con el JSON que contiene el elemento "elementList" del resultado de una invocación
        a la función search de la API de Idealista.
        Parametros:
        * file: fichero con el JSON
        * type: 'frame', 'series'
        Resultado:
        * El DataFrame
        '''
        return pd.read_json(file, orient='records', typ=type)
    
    def read_jsons(self, directory='', type='frame'):
        '''
        Lee los ficheros con el JSON que contiene el elemento "elementList" del resultado de una invocación a la función search
        de la API de Idealista y los concatena en un DataFrame de Pandas.
        
        Parametros:
        * directory: directorio donde se encuantra los ficheros
        * type: 'frame', 'series'
        Resultado:
        * El DataFrame
        '''
        list_ficheros_json = glob.glob(os.path.join(directory,'*.json'))
        if self.__debug:
            print(list_ficheros_json)

        #list_df = [self.read_json(fich_json) for fich_json in list_ficheros_json]
        list_df = []
        for fich_json in list_ficheros_json:
            try:
                df_aux = self.read_json(fich_json)
                if self.__debug:
                    print(fich_json," procesado con",df_aux.shape[0]," filas")
                list_df.append(df_aux)
            except Exception as ex:
                print("Error al procesar el fichero", fich_json, ":", ex)
       
        if self.__debug:
            print(len(list_df),"ficheros convertidos a DataFrame")
        
        idealista_df = None
        if len(list_df) == 1:
            idealista_df = list_df[0].copy()
        elif len(list_df) > 1:
            idealista_df = list_df[0].copy()
            for ind in range(1,len(list_df)):
                idealista_df = idealista_df.append(list_df[ind])
            
            idealista_df.reset_index(drop=True,inplace=True)

        return idealista_df
