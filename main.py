import numpy as np
import pandas as pd

import helpers

df = helpers.combine_data()


# Make dataframe grouped by city_code and quarter
def first_non_empty(series):
    return series.dropna().iloc[0] if not series.dropna().empty else np.nan


df_new = (df.groupby(['city_code', 'Quarter'])[['PoliceDistrict',
                                                'PoliceMerhav',
                                                'PoliceStation',
                                                'Settlement_Council',
                                                'population',
                                                'youth',
                                                'wage',
                                                'inequality',
                                                'bagrut',
                                                'cars',
                                                'car_age',
                                                'socio_econ',
                                                'unemployment',
                                                'car_per_capita',
                                                'city_type']]
            .agg(first_non_empty).reset_index())

print(df_new)

#####################################################

# city_list = df_new['city_code'].unique().tolist()
# crime_list = df['StatisticCrimeGroup'].unique().tolist()
# quarter_list = df['Quarter'].unique().tolist()
# matrix_list = []
#
# for crime in crime_list:
#     dfx = df.loc[df['StatisticCrimeGroup'] == crime]
#     for city in city_list:
#         dfy = dfx.loc[df['city_code'] == city]
#         series = dfy.groupby(['Quarter'])['TikimSum'].sum().reindex(quarter_list).fillna(0)
#         series = series.values.reshape(-1, 1).flatten()
#         # print(city)
#         # print(crime)
#         # print(series)
#         matrix_list.append(series)
#     crime_column = [element for array in matrix_list for element in array]
#     print(crime)
#     print(type(crime_column))
#     print(len(crime_column))
#     print(crime_column)
#     # matrix = np.hstack(matrix_list)
#     # print(matrix)



