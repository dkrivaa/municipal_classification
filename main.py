
import helpers

df = helpers.combine_data()
df = df.drop('_id', axis=1)
print(type(df))
print(df.shape)
print(df.columns)
print(df)


df = df.groupby(['city_code', 'Quarter']).agg({
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
})
df = df.reset_index()
print(type(df))
print(df)




