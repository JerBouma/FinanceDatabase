import financedatabase as fd
import pandas as pd

equities = fd.Equities()
pd.Series(equities.options('country')).to_csv('Database/Categories/equities_countries.csv', index=False, header=False)
pd.Series(equities.options('sector')).to_csv('Database/Categories/equities_sectors.csv', index=False, header=False)
pd.Series(equities.options('industry_group')).to_csv('Database/Categories/equities_industry_groups.csv', index=False, header=False)
pd.Series(equities.options('industry')).to_csv('Database/Categories/equities_industries.csv', index=False, header=False)

etfs = fd.ETFs()
pd.Series(etfs.options('category_group')).to_csv('Database/Categories/etfs_category_group.csv', index=False, header=False)
pd.Series(etfs.options('category')).to_csv('Database/Categories/etfs_category.csv', index=False, header=False)
pd.Series(etfs.options('family')).to_csv('Database/Categories/etfs_family.csv', index=False, header=False)

funds = fd.Funds()
pd.Series(funds.options('category_group')).to_csv('Database/Categories/funds_category_group.csv', index=False, header=False)
pd.Series(funds.options('category')).to_csv('Database/Categories/funds_category.csv', index=False, header=False)
pd.Series(funds.options('family')).to_csv('Database/Categories/funds_family.csv', index=False, header=False)