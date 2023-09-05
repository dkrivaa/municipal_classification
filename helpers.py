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
    df = df.drop('_id', axis=1)

    # Making new rows for quarters missing in certain municipalities
    quarter_list = df['Quarter'].unique().tolist()

    new_row_code = []
    new_row_quarter = []
    city_code_list = df['city_code'].unique().tolist()
    for code in city_code_list:
        df_temp = df.loc[df['city_code'] == code]
        city_quarter_list = df_temp['Quarter'].unique().tolist()
        if len(city_quarter_list) == len(quarter_list):
            pass
        else:
            for i in range(0, len(quarter_list)):
                if quarter_list[i] in city_quarter_list:
                    pass
                else:
                    new_row_code.append(code)
                    new_row_quarter.append(quarter_list[i])

    new_rows = pd.DataFrame({'city_code': new_row_code, 'Quarter': new_row_quarter})
    df = pd.concat([df, new_rows], ignore_index=True)

    return df


def city_quarter_generic():
    df = combine_data()

    def first_non_empty(city):
        df_temp = df_new.loc[df_new['city_code'] == city]
        special = df_temp.dropna().iloc[0] if not df_temp.dropna().empty else np.nan
        return special

    df_new = df.groupby(['city_code', 'Quarter']).agg({
        'PoliceDistrict': 'first',
        'PoliceMerhav': 'first',
        'PoliceStation': 'first',
        'Settlement_Council': 'first',
        'population': 'first',
        'youth': 'first',
        'wage': 'first',
        'inequality': 'first',
        'bagrut': 'first',
        'cars': 'first',
        'car_age': 'first',
        'socio_econ': 'first',
        'unemployment': 'first',
        'car_per_capita': 'first',
        'city_type': 'first'
    }).reset_index()

    city_list = df_new['city_code'].unique().tolist()
    for city in city_list:
        special = first_non_empty(city)

        df_new.loc[(df_new['PoliceDistrict'].isnull()) & (df_new['city_code'] == city), 'PoliceDistrict'] = special[2]
        df_new.loc[(df_new['PoliceMerhav'].isnull()) & (df_new['city_code'] == city), 'PoliceMerhav'] = special[3]
        df_new.loc[(df_new['PoliceStation'].isnull()) & (df_new['city_code'] == city), 'PoliceStation'] = special[4]
        df_new.loc[(df_new['Settlement_Council'].isnull()) & (df_new['city_code'] == city), 'Settlement_Council'] = special[5]
        df_new.loc[(df_new['population'].isnull()) & (df_new['city_code'] == city), 'population'] = special[6]
        df_new.loc[(df_new['youth'].isnull()) & (df_new['city_code'] == city), 'youth'] = special[7]
        df_new.loc[(df_new['wage'].isnull()) & (df_new['city_code'] == city), 'wage'] = special[8]
        df_new.loc[(df_new['inequality'].isnull()) & (df_new['city_code'] == city), 'inequality'] = special[9]
        df_new.loc[(df_new['bagrut'].isnull()) & (df_new['city_code'] == city), 'bagrut'] = special[10]
        df_new.loc[(df_new['cars'].isnull()) & (df_new['city_code'] == city), 'cars'] = special[11]
        df_new.loc[(df_new['car_age'].isnull()) & (df_new['city_code'] == city), 'car_age'] = special[12]
        df_new.loc[(df_new['socio_econ'].isnull()) & (df_new['city_code'] == city), 'socio_econ'] = special[13]
        df_new.loc[(df_new['unemployment'].isnull()) & (df_new['city_code'] == city), 'unemployment'] = special[14]
        df_new.loc[(df_new['car_per_capita'].isnull()) & (df_new['city_code'] == city), 'car_per_capita'] = special[15]
        df_new.loc[(df_new['city_type'].isnull()) & (df_new['city_code'] == city), 'city_type'] = special[16]

    df_csv = df_new.to_csv('df.csv')

    return df_new


def city_quarter_crime():
    df = combine_data()

    city_list = df['city_code'].unique().tolist()
    crime_list = df['StatisticCrimeGroup'].unique().tolist()
    quarter_list = df['Quarter'].unique().tolist()
    crime_list.pop(len(crime_list)-1)

    city_code_list = []
    quarter_code_list = []
    crime_code_list = []
    crime_data_list = []

    for crime in crime_list:
        for city in city_list:
            df_temp = df.loc[(df['city_code'] == city) & (df['StatisticCrimeGroup'] == crime)]
            series = df_temp.groupby(['Quarter'])['TikimSum'].sum().reindex(quarter_list).fillna(0)
            city_code_list.append(city)
            quarter_code_list.append(series.index)
            crime_code_list.append(crime)
            crime_data_list.append(series)

    # Flattening quarter and crime lists:
    flat_quarter = [item for sublist in quarter_code_list for item in sublist]
    flat_crime = [item for sublist in crime_data_list for item in sublist]

    # Organizing city_code_list
    temp_city_code = city_code_list[0:251]
    flat_city_code = [item for item in temp_city_code for _ in range(21)]

    df_crime = pd.DataFrame({'city_code': flat_city_code[0:5271],
                             'Quarter': flat_quarter[0:5271],
                             'econ_crime': flat_crime[0:5271],
                             'vice_crime': flat_crime[5271:10542],
                             'property_crime': flat_crime[10542:15813],
                             'sex_crime': flat_crime[15813:21084],
                             'fraud_crime': flat_crime[21084:26355],
                             'body_crime': flat_crime[26355:31626],
                             'public_order_crime': flat_crime[31626:36897],
                             'traffic_crime': flat_crime[36897:42168],
                             'other_crime': flat_crime[42168:47439],
                             'license_crime': flat_crime[47439:52710],
                             'person_crime': flat_crime[52710:57981],
                             'security_crime': flat_crime[57981:63252],
                             'administrative_crime': flat_crime[63252:],
                             })

    # uncomment to get the hebrew titles of crime groups

    # print(crime_code_list[0])
    # print(crime_code_list[251])
    # print(crime_code_list[502])
    # print(crime_code_list[753])
    # print(crime_code_list[1004])
    # print(crime_code_list[1255])
    # print(crime_code_list[1506])
    # print(crime_code_list[1757])
    # print(crime_code_list[2008])
    # print(crime_code_list[2259])
    # print(crime_code_list[2510])
    # print(crime_code_list[2761])
    # print(crime_code_list[3012])


    return df_crime

# Combining the generic and crime dataframes (according to city and quarter)
def final_frame():
    df_generic = city_quarter_generic()
    df_crime = city_quarter_crime()

    df_final = pd.merge(df_generic, df_crime, on=['city_code', 'Quarter'], how='inner')

    # per-capita crimes:
    df_final['econ_per_capita'] = df_final['econ_crime'] / df_final['population']
    df_final['vice_per_capita'] = df_final['vice_crime'] / df_final['population']
    df_final['property_per_capita'] = df_final['property_crime'] / df_final['population']
    df_final['sex_per_capita'] = df_final['sex_crime'] / df_final['population']
    df_final['fraud_per_capita'] = df_final['fraud_crime'] / df_final['population']
    df_final['body_per_capita'] = df_final['body_crime'] / df_final['population']
    df_final['public_order_per_capita'] = df_final['public_order_crime'] / df_final['population']
    df_final['traffic_per_capita'] = df_final['traffic_crime'] / df_final['population']
    df_final['other_per_capita'] = df_final['other_crime'] / df_final['population']
    df_final['license_per_capita'] = df_final['license_crime'] / df_final['population']
    df_final['person_per_capita'] = df_final['person_crime'] / df_final['population']
    df_final['security_per_capita'] = df_final['security_crime'] / df_final['population']
    df_final['administrative_per_capita'] = df_final['administrative_crime'] / df_final['population']

    return df_final


def normalize():

    df = final_frame()

    # Define a function to normalize columns using Min-Max scaling
    def normalize_column(column):
        min_val = column.min()
        max_val = column.max()
        normalized_column = (column - min_val) / (max_val - min_val)
        return normalized_column

    # Normalize specific columns
    columns_to_normalize = df.columns[6:].tolist()
    columns_to_normalize.pop(10)
    df[columns_to_normalize] = df[columns_to_normalize].apply(normalize_column)

    return df


def model_frame():
    df = normalize()

    # Drop unnecessary columns from dataframe - leaving only crimes per capita
    columns_to_drop = ['city_code', 'Quarter', 'PoliceDistrict', 'PoliceMerhav',
                       'PoliceStation', 'Settlement_Council',
                       'econ_crime', 'vice_crime', 'property_crime', 'sex_crime',
                       'fraud_crime', 'body_crime', 'public_order_crime', 'traffic_crime',
                       'other_crime', 'license_crime', 'person_crime', 'security_crime',
                       'administrative_crime', 'population', 'youth', 'wage', 'inequality',
                       'bagrut', 'cars', 'car_age', 'socio_econ', 'unemployment',
                       'car_per_capita']

    df = df.drop(columns=columns_to_drop)

    # Move city_type to be last column
    df['last_city_type'] = df['city_type']
    df = df.drop(columns='city_type')
    # df['city_type'] = df.pop('city_type')

    print(df.columns)

    # Grouping the data back into matrixes for each city
    rows_per_matrix = 21
    columns_per_matrix = 13
    city_matrix = []
    type_list = []
    for start_row in range(0, len(df), rows_per_matrix):
        end_row = start_row + rows_per_matrix
        for start_col in range(0, len(df.columns)-1, columns_per_matrix):
            end_col = start_col + columns_per_matrix
            small_matrix = df.iloc[start_row:end_row, start_col:end_col]
            city_matrix.append(small_matrix)

    for start in range(0, len(df), rows_per_matrix):
        small_matrix = df['last_city_type'].iloc[start]
        type_list.append(small_matrix)

    print(city_matrix)
    print(type_list)

    df_final = pd.DataFrame({'data': city_matrix, 'type': type_list})
    df_final.to_csv('df_final.csv')

    return df









    # city_list = df['city_code'].unique().tolist()
    # crime_list = df['StatisticCrimeGroup'].unique().tolist()
    # quarter_list = df['Quarter'].unique().tolist()
    # matrixes_list = []
    # for city in city_list:
    #     matrix_list = []
    #     dfx = df.loc[df['Settlement_Council'] == city]
    #     for crime in crime_list:
    #         dfy = dfx.loc[df['StatisticCrimeGroup'] == crime]
    #         series = dfy.groupby('Quarter')['TikimSum'].sum().reindex(quarter_list).fillna(0)
    #         series = series.values.reshape(-1, 1)
    #         matrix_list.append(series)
    #     matrix = np.hstack(matrix_list)
    #     matrixes_list.append(matrix)
    #
    # X = matrixes_list
    # X = np.array(X)
    # print(type(X), X.shape)
    #
    #
    # return X, y






def model_func():
    # Define the model
    model = models.Sequential()

    # Convolutional layers
    model.add(layers.Conv2D(32, (3, 3), activation='relu', input_shape=(21, 13, 1)))
    model.add(layers.MaxPooling2D((2, 2)))

    model.add(layers.Conv2D(64, (3, 3), activation='relu'))
    model.add(layers.MaxPooling2D((2, 2)))

    model.add(layers.Conv2D(64, (3, 3), activation='relu'))

    # Flatten layer
    model.add(layers.Flatten())

    # Dense layers
    model.add(layers.Dense(64, activation='relu'))
    model.add(layers.Dense(3, activation='softmax'))  # Three output classes

    # Compile the model
    model.compile(optimizer='adam',
                  loss='categorical_crossentropy',
                  metrics=['accuracy'])

    # Display the model summary
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

