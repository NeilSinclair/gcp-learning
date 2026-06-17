from google.cloud import bigquery

PROJECT_ID = "burner-neisincl"

client = bigquery.Client(project=PROJECT_ID)

query = """
SELECT COUNT(*) AS row_count
FROM `burner-neisincl.binary_classification_demo.hotel_clean`
"""

df = client.query(query).to_dataframe()
print(df)