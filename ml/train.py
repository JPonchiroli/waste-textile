from ml.model import generate_synthetic_training_data, train_and_save_model, TRAINING_DATA_PATH


def main():
    df = generate_synthetic_training_data(samples=60, start_date='2022-01')
    df.to_csv(TRAINING_DATA_PATH, index=False)
    model, scaler = train_and_save_model(df)

    print('Treinamento concluido.')
    print(f'Modelo salvo em: {model}')
    print(f'Escalonador salvo em: {scaler}')
    print(f'Dados de treinamento gerados em: {TRAINING_DATA_PATH}')


if __name__ == '__main__':
    main()
