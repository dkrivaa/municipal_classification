import helpers


df = helpers.combine_data()

print(df.columns)
print(df.shape)
print(len(df['StatisticCrimeGroup'].unique().tolist()))



