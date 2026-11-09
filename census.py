import pandas as pd



df=pd.read_csv("/storage/emulated/0/kenya project/census_2019_vol_i_22distribution_of_population_by_county.csv")
#inspect

print("rows and columns")
print(df.shape)
print(df.info())
print("column names")
print(df.columns)
print(df.head().to_string())
print(df.dtypes)
#standardize
df.columns = (df.columns.str.strip().str.lower()
              .str.replace(r"[^a-z0-9]+", "_", regex=True)
              .str.strip("_"))
print(df.head())

df = df.drop(index=0).reset_index(drop=True)  # row 0 = national total
print(len(df))
df = df.rename(columns={"national_county": "county","sex_male": "male","sex_female": "female"})
print(df.columns)
df["county"] = df["county"].str.strip()
#to numeric columns
num_cols=["male","female","intersex","total"]
for col in num_cols:

 df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", ""), errors="coerce")
#missing data
print(df[num_cols].isna().sum())

print("duplicates",df.duplicated().sum())#no duplicates
#total =male+female
mismatch = df[df["total"] != df[["male", "female", "intersex"]].sum(axis=1)]


print("Rows where parts != total:", len(mismatch))
print(mismatch)
#export cleaned dataset
df.to_csv("/storage/emulated/0/kenya project/county_population_cleaned_census.csv",index=False)

import sqlite3 
conn=sqlite3.connect("kenya_census.db")
df.to_sql("county_population",conn,if_exists="replace",index=False)

#national totals for males, females, intersex persons and total population, and how many counties are there?

total_males="""SELECT 
sum(male)as total_male
FROM county_population;
"""
males=pd.read_sql(total_males,conn)
print(males)
total_females="""SELECT sum(female) as total_female
FROM county_population;
"""
print(pd.read_sql(total_females,conn))
intersex_total="""
SELECT sum(intersex)as total_intersex
FROM county_population;
"""
print(pd.read_sql(intersex_total,conn))
total_counties="""
SELECT COUNT(county) AS no_counties
FROM county_population;
"""
print(pd.read_sql(total_counties,conn))

total_population="""
SELECT SUM(total) AS total_population
FROM county_population;
"""
print(pd.read_sql(total_population,conn))

#Which 10 counties are the most populous, and what share of the national population does each hold?

pct_share="""
SELECT county, total,
 ROUND(100.0 * total / (SELECT SUM(total) FROM county_population), 2) AS share_pct
FROM county_population
ORDER BY total DESC
LIMIT 10;
"""
print(pd.read_sql(pct_share,conn))

#Which 5 counties are the least populous, and what is their share of the national population?
least_populous="""
SELECT county, total,
 ROUND(100.0 * total / (SELECT SUM(total) FROM county_population), 2) AS share_pct
FROM county_population
ORDER BY total ASC
LIMIT 5;
"""
print(pd.read_sql(least_populous,conn))

#How many counties together account for 50% of Kenya's population? Show a running (cumulative) share.

pop_half="""
WITH shares AS (
 SELECT county, total,
 100.0 * total / SUM(total) OVER () AS share_pct
 FROM county_population
)
SELECT county, total,
 ROUND(share_pct, 2) AS share_pct,
 ROUND(SUM(share_pct) OVER (ORDER BY total DESC), 2) AS cumulative_pct
FROM shares
ORDER BY total DESC;
"""





print(pd.read_sql(pop_half,conn))

#For each county, calculate the female share (%) and males per 100 females. Which sex dominates?

sex_dominates="""
SELECT county, male, female,
 ROUND(100.0 * female / total, 2) AS female_pct,
 ROUND(100.0 * male / female, 1) AS males_per_100_females,
 CASE WHEN male > female THEN 'More males'
 WHEN male < female THEN 'More females'
 ELSE 'Balanced'
  END AS dominant_sex
FROM county_population
ORDER BY males_per_100_females DESC;
"""
print(pd.read_sql(sex_dominates,conn))

#How many counties have more males than females, and how many have more females? What population do each group hold?

counties="""
SELECT CASE WHEN male > female THEN 'More males'
 WHEN male < female THEN 'More females'
 ELSE 'Balanced' END AS dominant_sex,
 COUNT(*) AS no_counties,
 SUM(total) AS population;
"""
print(pd.read_sql(counties ,conn))
conn.close()


