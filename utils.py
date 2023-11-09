import pandas as pd


def train_test_split(df: pd.DataFrame, test_size: float):
    """Split dataframe into train and test sets.

    Check which students are dropouts with the argument 'dropouts'.
    Keep the same proportion of dropouts in both sets.

    :param df: pandas DataFrame with student's data. first column must be its name,
        and second column must be its classification
        ('positive' = dropout, 'negative' = non-dropout). The first three rows must
        follow Orange's format of header.
    :param test_size: proportion of data to be used as test set
    """
    train, test = df.iloc[:2, :], df.iloc[:2, :]

    # get all rows with dropouts
    rows = df[df.iloc[:, 1] == "positive"]

    test = pd.concat([test, rows[: int(rows.shape[0] * test_size)]])
    train = pd.concat([train, rows[int(rows.shape[0] * test_size) :]])

    non_dropouts = df[df.iloc[:, 1] == "negative"]
    test = pd.concat([test, non_dropouts[: int(non_dropouts.shape[0] * test_size)]])
    train = pd.concat([train, non_dropouts[int(non_dropouts.shape[0] * test_size) :]])
    return train, test
