import numpy as np
import pandas as pd

import helpers

dfx = helpers.city_quarter_frame()
city_code_x = dfx['city_code'].unique().tolist()

df = pd.read_csv('df.csv')
city_code_list = df['city_code'].unique().tolist()

print(city_code_x)
print(city_code_list)






