import requests
import pandas as pd
import json
import openpyxl as xl
import numpy as np
import tensorflow as tf
from keras.models import Sequential
from keras.layers import Dense, Activation
from keras.optimizers import Adam
from keras.metrics import MeanSquaredError, categorical_crossentropy

from sklearn.preprocessing import MinMaxScaler


# Get crime data published by Israel Police
def get_crime_data():
    # FIRST PART OF UPDATE
    # getting the count of records
    url = "https://data.gov.il/api/3/action/datastore_search?resource_id=5fc13c50-b6f3-4712-b831-a75e0f91a17e"

    # Make a GET request to the API endpoint
    response = requests.get(url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the response JSON
        data = json.loads(response.text)

        # Extract the count of records
        count = data["result"]["total"]

    # SECOND PART OF UPDATE
    # doing the actual update of the data file
    url = 'https://data.gov.il/api/3/action/datastore_search'
    resource_id = '5fc13c50-b6f3-4712-b831-a75e0f91a17e'
    limit = 100000  # Number of rows to retrieve per request

    # Initialize an empty list to store the results
    results = []

    # Calculate the total number of requests needed
    total_rows = count
    total_requests = (total_rows // limit) + 1

    # Make multiple requests to retrieve all the rows
    for offset in range(0, total_requests * limit, limit):
        params = {'resource_id': resource_id, 'limit': limit, 'offset': offset}
        response = requests.get(url, params=params).json()
        data = response['result']['records']
        results.extend(data)

    # Create a DataFrame from the combined results
    df = pd.DataFrame(results)

    # THIRD PART OF UPDATE - ADDING VARIABLES TO THE DATAFRAME
    # make 'year' and 'quarter' variable
    df['year'] = df['Quarter'].str[0:4]
    df['quarter'] = df['Quarter'].str[5:]

    #  Making the various "other" statistical crime groups into "אחר"
    other_list = (df['StatisticCrimeGroup'].unique()[9:12])
    df['StatisticCrimeGroup'] = df['StatisticCrimeGroup'].apply(lambda x: 'אחר' if x in other_list else x)

    # Dropping rows with missing values
    df = df.dropna(subset=['Settlement_Council'])

    place_list = ['מקום אחר', 'מקום', 'ישוב פלסטיני']
    df.drop(index=df[df['Settlement_Council'] == 'מקום אחר'].index, inplace=True)
    df.drop(index=df[df['Settlement_Council'] == 'מקום'].index, inplace=True)
    df.drop(index=df[df['Settlement_Council'] == 'ישוב פלסטיני'].index, inplace=True)

    return df


# Getting municipal data from excel file
def muni_data():
    # Read file into panda dataframe:
    workbook = xl.load_workbook('muni_2021.xlsx')
    # Select the sheet you want to read
    sheet = workbook['נתונים פיזיים ונתוני אוכלוסייה ']

    # getting data from the worksheet
    city_list = []
    city_symbol = []
    city_status = []
    city_type = []
    total_pop = []
    young_pop = []
    wage = []
    inequality = []
    bagrut = []
    cars = []
    car_age = []
    socio_econ = []
    unemployment = []
    for i in range(6, 261):
        # city name
        cell1 = sheet[f'A{i}']
        city = cell1.value
        city_list.append(city)
        # city symbol
        cell2 = sheet[f'B{i}']
        symbol = cell2.value
        city_symbol.append(symbol)
        # city status
        cell3 = sheet[f'D{i}']
        status = cell3.value
        if status == 'מועצה אזורית':
            status = 2
        else:
            status = 1
        city_status.append(status)
        # type of city (Jewish, Mixed, Arab)
        cell4 = sheet[f'P{i}']
        ctype = cell4.value
        if ctype == '-':
            ctype = 1
        elif int(ctype) > 79:
            ctype = 3
        elif 21 <= int(ctype) <= 79:
            ctype = 2
        else:
            ctype = 1
        city_type.append(ctype)
        # total population
        cell5 = sheet[f'M{i}']
        pop = cell5.value
        total_pop.append(pop)
        # population aged 15-29 (in %)
        cell6 = sheet[f'Y{i}']
        cell7 = sheet[f'Z{i}']
        young = cell6.value + cell7.value
        young_pop.append(young)
        # Avg wage
        cell8 = sheet[f'DL{i}']
        avg_wage = cell8.value
        wage.append(avg_wage)
        # inequality (gini)
        cell9 = sheet[f'DX{i}']
        ineq = cell9.value
        inequality.append(ineq)
        # bagrut
        cell10 = sheet[f'EW{i}']
        bag = cell10.value
        bagrut.append(bag)
        # cars total
        cell11 = sheet[f'HG{i}']
        car = cell11.value
        cars.append(car)
        # car age
        cell12 = sheet[f'HH{i}']
        carage = cell12.value
        car_age.append(carage)
        # Socio-economic index
        cell13 = sheet[f'HY{i}']
        socio = cell13.value
        socio_econ.append(socio)
        cell14 = sheet[f'CI{i}']
        unem = cell14.value
        unemployment.append(unem)
    # dataframe consisting of the following columns:
    df_muni = pd.DataFrame({'Settlement_Council': city_list, 'city_code': city_symbol,
                           'city_status': city_status, 'city_type': city_type,
                            'population': total_pop, 'youth': young_pop,
                            'wage': wage, 'inequality': inequality,
                            'bagrut': bagrut, "cars": cars, 'car_age': car_age,
                            'socio_econ': socio_econ, 'unemployment': unemployment})

    # Adding 'מועצה אזורית' to the relevant municipalities
    df_muni.loc[df_muni['city_status'] == 2, 'Settlement_Council'] = 'מועצה אזורית' + ' ' + df_muni[
        'Settlement_Council']

    return df_muni


# Function to combine the two dataframes and adding additional calculated columns
def combine_data():
    df = get_crime_data()
    df_muni = muni_data()

    # Adding columns with various characteristics for municipalities
    # making column with city code matching the CBS
    df['city_code'] = (df['Settlement_Council'].map(
        df_muni.set_index('Settlement_Council')['city_code'])).astype(str)
    # making column with city type - 1=jewish, 2=mixed, 3=arab
    df['city_type'] = df['Settlement_Council'].map(
        df_muni.set_index('Settlement_Council')['city_type'])
    # making column with percentage of population aged 15-29
    df['youth'] = df['Settlement_Council'].map(
        df_muni.set_index('Settlement_Council')['youth'])
    df['population'] = df['Settlement_Council'].map(
        df_muni.set_index('Settlement_Council')['population'])
    df['wage'] = df['Settlement_Council'].map(
        df_muni.set_index('Settlement_Council')['wage'])
    df['inequality'] = df['Settlement_Council'].map(
        df_muni.set_index('Settlement_Council')['inequality'])
    df['bagrut'] = df['Settlement_Council'].map(
        df_muni.set_index('Settlement_Council')['bagrut'])
    df['cars'] = df['Settlement_Council'].map(
        df_muni.set_index('Settlement_Council')['cars'])
    df['car_age'] = df['Settlement_Council'].map(
        df_muni.set_index('Settlement_Council')['car_age'])
    df['socio_econ'] = df['Settlement_Council'].map(
        df_muni.set_index('Settlement_Council')['socio_econ'])
    df['unemployment'] = df['Settlement_Council'].map(
        df_muni.set_index('Settlement_Council')['unemployment'])

    # Making dataframe with police city names and CBS city codes - for future use
    df_city_code = df[['city_code', 'Settlement_Council']]

    # Cars per capita in municipality
    df['car_per_capita'] = df['cars'] / df['population']

    # Dropping rows with missing values
    df = df.dropna(subset=['Settlement_Council'])
    df = df.dropna(subset=['StatisticCrimeGroup'])

    return df


def matrix_maker():
    df = combine_data()

    city_list = df['Settlement_Council'].unique().tolist()
    crime_list = df['StatisticCrimeGroup'].unique().tolist()
    quarter_list = df['Quarter'].unique().tolist()
    matrixes_list = []
    y = []
    for city in city_list:
        matrix_list = []
        dfx = df.loc[df['Settlement_Council'] == city]
        y.append(dfx['city_type'].unique())
        for crime in crime_list:
            dfy = dfx.loc[df['StatisticCrimeGroup'] == crime]
            series = dfy.groupby('Quarter')['TikimSum'].sum().reindex(quarter_list).fillna(0)
            series = series.values.reshape(-1, 1)
            matrix_list.append(series)
        matrix = np.hstack(matrix_list)
        matrixes_list.append(matrix)

    X = matrixes_list
    X = np.array(X)
    print(type(X), X.shape)
    print(type(y))
    print(y)

    return X, y


def model_func():
    X, y = matrix_maker()

    y_one_hot_labels = tf.keras.utils.to_categorical(y, num_classes=3)

    model = tf.keras.models.Sequential()
    model.add(Dense(64, input_shape=X.shape, activation='relu'))
    model.add(Dense(32, 'relu'))
    model.add(Dense(3, 'softmax'))

    model.compile(optimizer=Adam(learning_rate=0.001), loss='categorical_crossentropy',
                  metrics=['accuracy'])

    model.summary()
























# # Function to normalize data to be used
# def normalize():
#     df = combine_data()
#
#     norm_list = ['youth', 'population', 'wage','inequality', 'bagrut', 'cars',
#                  'car_age', 'socio_econ', 'unemployment', 'car_per_capita']
#     for var in norm_list:
#         name = 'norm' + '_' + str(var)
#         df[name] = MinMaxScaler.fit_transform(df[[var]])

