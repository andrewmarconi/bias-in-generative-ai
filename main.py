import mlflow

def main():
    print("===== Bias in Generative AI Project =====")
    mlflow.set_tracking_uri("sqlite:///db/mlflow.db")
    mlflow.set_experiment("bias-in-generative-ai")
    with mlflow.start_run():
        mlflow.log_param("test_param", "test_value")
        print("✓ Successfully connected to MLflow!")

if __name__ == "__main__":
    main()
