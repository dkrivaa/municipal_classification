import helpers

df = helpers.get_crime_data()
df_muni = helpers.muni_data()

p_list = df['Settlement_Council'].unique().tolist()
CBS_list = df_muni['Settlement_Council'].unique().tolist()

problem1_list = []
problem2_list = []
for city in CBS_list:
    if city in p_list:
        pass
    else:
        problem1_list.append(city)

for city in p_list:
    if city in CBS_list:
        pass
    else:
        if city in problem1_list:
            pass
        else:
            problem2_list.append(city)

print(problem1_list)
print(problem2_list)





