# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/utils.ipynb (unless otherwise specified).

__all__ = ['hierarchize']

# Cell
from itertools import chain
from typing import Callable, List

import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder

# Cell
def _to_summing_matrix(S_df: pd.DataFrame):
    """Transforms the DataFrame `df` of hierarchies to a summing matrix S."""
    categories = [S_df[col].unique() for col in S_df.columns]
    cat_sizes = [len(cats) for cats in categories]
    idx_bottom = np.argmax(cat_sizes)
    cats_bottom = categories[idx_bottom]
    encoder = OneHotEncoder(categories=categories, sparse=False, dtype=np.float32)
    S = encoder.fit_transform(S_df).T
    S = pd.DataFrame(S, index=chain(*categories), columns=cats_bottom)
    tags = dict(zip(S_df.columns, categories))
    return S, tags

# Cell
def hierarchize(df: pd.DataFrame, hiers: List[List[str]], agg_fn: Callable = np.sum):
    """Aggregates `df` according to `hiers` using `agg_fn`.

        Parameters
        ----------

        df: pd.DataFrame
            Frame with columns ['ds', 'y'] and
            columns to hierarchize.
        hiers: List[List[str]]
            List of hierarchies.
            Each element of the list contains
            a list of columns of `df` to
            hierarchize.
        agg_fn: Callable
            Function used to aggregate 'y'.
    """
    max_len_idx = np.argmax([len(hier) for hier in hiers])
    bottom_comb = hiers[max_len_idx]
    orig_cols = df.drop(labels=['ds', 'y'], axis=1).columns.to_list()
    df_hiers = []
    for hier in hiers:
        df_hier = df.groupby(hier + ['ds'])['y'].apply(agg_fn).reset_index()
        df_hier['unique_id'] = df_hier[hier].agg('/'.join, axis=1)
        if hier == bottom_comb:
            bottom_hier = df_hier['unique_id'].unique()
        df_hiers.append(df_hier)
    df_hiers = pd.concat(df_hiers)
    S_df = df_hiers[['unique_id'] + bottom_comb].drop_duplicates().reset_index(drop=True)
    S_df = S_df.set_index('unique_id')
    S_df = S_df.fillna('agg')
    hiers_cols = []
    for hier in hiers:
        hier_col = '/'.join(hier)
        S_df[hier_col] = S_df[hier].agg('/'.join, axis=1)
        hiers_cols.append(hier_col)
    y_df = df_hiers[['unique_id', 'ds', 'y']].set_index('unique_id')
    #S definition
    S, tags = _to_summing_matrix(S_df.loc[bottom_hier, hiers_cols])
    return y_df, S, tags