from google.cloud import bigquery
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
import joblib

joblib.dump(model, "hotel_cancellation_model.joblib")