from google.cloud import bigquery, storage
import os
import joblib

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import BaggingClassifier
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

PROJECT_ID = "burner-neisincl"
TABLE = "burner-neisincl.binary_classification_demo.hotel_clean"

MODEL_BUCKET = os.getenv("MODEL_BUCKET", "burner-neisincl-ml-pipeline-artefacts")
MODEL_PREFIX = os.getenv("MODEL_PREFIX", "models/hotel-cancellation-vertex-training")

client = bigquery.Client(project=PROJECT_ID)

print(f" --- Training model ---")
print("Loading data...")
query = f"""
SELECT *
FROM `{TABLE}`
"""

df = client.query(query).to_dataframe()

target = "is_canceled"
X = df.drop(columns=[target, "company"])
y = df[target]

numeric_features = X.select_dtypes(include=["int64", "float64"]).columns.tolist()
categorical_features = X.select_dtypes(include=["object"]).columns.tolist()

numeric_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler()),
])

categorical_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("onehot", OneHotEncoder(handle_unknown="ignore")),
])

preprocessor = ColumnTransformer([
    ("num", numeric_pipeline, numeric_features),
    ("cat", categorical_pipeline, categorical_features),
])

# model = Pipeline([
#     ("preprocessor", preprocessor),
#     ("classifier", LogisticRegression(max_iter=1000)),
# ])

model = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", BaggingClassifier(n_estimators=10)),
])


X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"Fitting model")
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)[:, 1]

print(classification_report(y_test, y_pred))
print("ROC AUC:", roc_auc_score(y_test, y_proba))

print("Saving model...")

local_model_path = "/tmp/model.joblib"
joblib.dump(model, local_model_path)

# Upload to GCS

storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(MODEL_BUCKET)
blob = bucket.blob(f"{MODEL_PREFIX}/model.joblib")
blob.upload_from_filename(local_model_path)
print(f"Uploaded model to gs://{MODEL_BUCKET}/{MODEL_PREFIX}/model.joblib")