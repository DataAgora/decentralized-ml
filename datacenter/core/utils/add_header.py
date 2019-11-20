import pandas as pd


def add_header(col_names, filepath):
	"""
	Updates file at 'filepath' with 'cols' (an array of column names) 
	"""
	pd.read_csv(filepath, names=col_names, header=None).to_csv(filepath, index=False)