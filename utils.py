import pandas as pd


def train_test_split(df: pd.DataFrame, test_size: float, dropouts: list):
    """Split dataframe into train and test sets.

    Check which students are dropouts with the argument 'dropouts'.
    Keep the same proportion of dropouts in both sets.

    :param df: pandas DataFrame with student's data. first column must be its name,
        and second column must be its classification
        ('positive' = dropout, 'negative' = non-dropout)
    :param test_size: proportion of data to be used as test set
    :param dropouts: list of students' names that are dropouts
    """
    # Split data into train and test sets
    test = df.sample(frac=test_size, random_state=0)
    train = df.drop(test.index)

    # Check which students are dropouts
    test_dropouts = test[test.iloc[:, 1] == "positive"]
    train_dropouts = train[train.iloc[:, 1] == "positive"]

    # Keep the same proportion of dropouts in both sets
    test = test.drop(test_dropouts.index)
    train = train.drop(train_dropouts.index)

    # Add dropouts to the sets
    test = pd.concat([test, test_dropouts], ignore_index=True)
    train = pd.concat([train, train_dropouts], ignore_index=True)

    return train, test
