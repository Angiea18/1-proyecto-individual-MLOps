import ast
import pandas as pd
import numpy as np
from fastapi import FastAPI 
from fastapi import FastAPI, HTTPException
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from sklearn.ensemble import BaggingRegressor
from pydantic import BaseModel
from sklearn.decomposition import PCA
import pickle

# Indicamos título y descripción de la API
app = FastAPI(title='PI N°1 (MLOps) -Angie Arango Zapata DTS13')

#Dataset
games = []
with open('steam_games.json') as f: 
    for line in f.readlines():
        games.append(ast.literal_eval(line)) 
df = pd.DataFrame(games) 
df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
df['metascore'] = pd.to_numeric(df['metascore'], errors='coerce')


# Endpoint 1: Géneros más repetidos por año
@app.get('/ Genero')
def genero(año: str):
    # Filtrar el DataFrame por el año proporcionado
    df_filtrado = df[df['release_date'].dt.year == int(año)]
    
    # Obtener una lista con todos los géneros para el año dado
    generos_list = df_filtrado['genres'].explode().tolist()

    # Calcular el conteo de cada género en la lista
    generos_count = pd.Series(generos_list).value_counts()

    # Obtener los 5 géneros más vendidos en orden correspondiente
    generos_mas_repetidos = generos_count.nlargest(5).to_dict()

    return generos_mas_repetidos

# Endpoint 2: Juegos lanzados en un año
@app.get('/ Juegos')
def juegos(año: str):
    # Filtrar los datos por el año especificado
    df_filtrado = df[df['release_date'].dt.year == int(año)]

    # Obtiener la lista de juegos lanzados en el año
    juegos_lanzados = df_filtrado['title'].tolist()

    return juegos_lanzados

# Endpoint 3: Specs más comunes por año
@app.get('/ Specs')
def specs(año: str):
    # Filtrar el DataFrame por el año proporcionado
    df_filtrado = df[df['release_date'].dt.year == int(año)]
    
    # Obtener una lista con todos los Specs para el año dado
    specs_list = df_filtrado['specs'].explode().tolist()

    # Calcular el conteo de cada Spec en la lista
    specs_count = pd.Series(specs_list).value_counts()

    # Obtener los 5 Specs más comunes en orden correspondiente
    top_5_specs = specs_count.nlargest(5).to_dict()

    return top_5_specs

# Endpoint 4: Cantidad de juegos con early access en un año
@app.get('/ Earlyacces')
def earlyacces(año: str):
    #Filtrar los datos por el año especificado y por juegos con early access
    df_filtrado = df[(df['release_date'].dt.year == int(año)) & (df['early_access'] == True)]

    #Contar la cantidad de juegos con early access en el año especificado
    cantidad_juegos_early_access = len(df_filtrado)

    return cantidad_juegos_early_access

# Endpoint 5: Análisis de sentimiento por año
@app.get('/ Sentimient')
def sentiment(año: str):
    # Filtrar los datos por el año especificado
    df_filtrado = df[df['release_date'].dt.year == int(año)]

    # Contar la cantidad de registros que cumplen con cada análisis de sentimiento
    sentimient_counts = df_filtrado['sentiment'].value_counts()

    # Convertir la serie de conteo en un diccionario
    sentimient_dict = sentimient_counts.to_dict()

    # Eliminar sentimientos que no están en la lista mencionada
    sentimient_valid = ["Mixed", "Positive", "Very Positive", "Mostly Positive",
                            "Negative", "Very Negative", "Mostly Negative", "Overwhelmingly Positive"]
    sentimient_dict = {sentimient: count for sentimient, count in sentimient_dict.items() if sentimient in sentimient_valid}

     # Verificar si el diccionario está vacío
    if not sentimient_dict:
        return "Sin registros"

    return sentimient_dict

# Endpoint 6: Top 5 juegos con mayor metascore por año
@app.get('/ Metascore')
def metascore(año: str):
    #Filtrar los datos por el año especificado y ordena por metascore de forma descendente
    df_filtrado = df[df['release_date'].dt.year == int(año)].sort_values(by='metascore', ascending=False)

    #Seleccionar los 5 juegos con mayor metascore y obtiene su información
    top_juegos_metascore = df_filtrado.head(5)[['title', 'metascore']].to_dict(orient='records')

    return top_juegos_metascore


# Cargar el modelo desde el archivo pickle
with open('modelo.pickle', 'rb') as file:
    model = pickle.load(file)

# Cargar el DataFrame preprocesado
df_limpio = pd.read_csv('datos_limpio.csv')

# Definir la ruta para la predicción
@app.get('/predict')
def predict(metascore: str = Query(None, description='Metascore of the game (0 to 100).'),
            year: str = Query(None, description='Release year of the game.'),
            genre: str = Query(None, description='Genre of the game (Action, Adventure, Casual, etc.).')):
    # Verificar que los valores de metascore y year sean números válidos
    if metascore is not None and not metascore.isnumeric():
        raise HTTPException(status_code=422, detail='Invalid metascore. It should be a number.')

    if year is not None and not year.isnumeric():
        raise HTTPException(status_code=422, detail='Invalid year. It should be a number.')

    # Verificar que el valor de genre esté dentro de los géneros disponibles
    available_genres = ['Action', 'Adventure', 'Casual', 'Early Access', 'Free to Play', 'Indie',
                        'Massively Multiplayer', 'RPG', 'Racing', 'Simulation', 'Sports', 'Strategy', 'Video Production']
    if genre is not None and genre not in available_genres:
        raise HTTPException(status_code=422, detail='Invalid genre. It should be one of the available genres.')

    # Crear un diccionario con las características ingresadas
    data = {'metascore': [float(metascore)] if metascore is not None else [0.0],
            'year': [int(year)] if year is not None else [0]}
    for genre in df_limpio['genres'].unique():
        if genre == genre:
            data[genre] = [1]
        else:
            data[genre] = [0]

    # Crear el DataFrame de entrada para la predicción
    input_df = pd.DataFrame(data)

    # Realizar la predicción con el modelo cargado
    precio_predicho = model.predict(input_df)

    # Retornar la predicción de precio en formato JSON
    return {"precio_predicho": precio_predicho[0]}

class Item(BaseModel):
    genres: str
    early_access: bool
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
import pandas as pd
import pickle

# Cargar el modelo desde el archivo pickle
with open('modelo.pickle', 'rb') as file:
    model = pickle.load(file)

# Cargar el DataFrame preprocesado
df_limpio = pd.read_csv('datos_limpio.csv')

app = FastAPI()

# Definir la clase modelo para los datos de entrada
class Item(BaseModel):
    genres: str
    early_access: bool

# Definir la ruta para la predicción
@app.get('/predict')
def predict(item: Item):
    # Verificar que el valor de genre esté dentro de los géneros disponibles
    available_genres = ['Action', 'Adventure', 'Casual', 'Early Access', 'Free to Play', 'Indie',
                        'Massively Multiplayer', 'RPG', 'Racing', 'Simulation', 'Sports', 'Strategy', 'Video Production']
    if item.genres not in available_genres:
        raise HTTPException(status_code=422, detail='Invalid genre. It should be one of the available genres.')

    # Crear un diccionario con las características ingresadas
    data = {'metascore': [0.0],
            'year': [0]}
    for genre in df_limpio['genres'].unique():
        if genre == item.genres:
            data[genre] = [1]
        else:
            data[genre] = [0]

    # Crear el DataFrame de entrada para la predicción
    input_df = pd.DataFrame(data)

    # Realizar la predicción con el modelo cargado
    precio_predicho = model.predict(input_df)

    # Retornar la predicción de precio en formato JSON
    return {"precio_predicho": precio_predicho[0]}
