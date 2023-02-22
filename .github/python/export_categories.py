import financedatabase as fd

equities = fd.Equities()
equities.show_options('countries').to_csv('Database/Categories/equities_countries.csv')
equities.show_options('sectors').to_csv('Database/Categories/equities_sectors.csv')
equities.show_options('industry_groups').to_csv('Database/Categories/equities_industry_groups.csv')
equities.show_options('industries').to_csv('Database/Categories/equities_industries.csv')

etfs = fd.ETFs()
etfs.show_options('category_group').to_csv('Database/Categories/etfs_category_group.csv')
etfs.show_options('category').to_csv('Database/Categories/etfs_category.csv')
etfs.show_options('family').to_csv('Database/Categories/etfs_family.csv')

funds = fd.Funds()
funds.show_options('category_group').to_csv('Database/Categories/funds_category_group.csv')
funds.show_options('category').to_csv('Database/Categories/funds_category.csv')
funds.show_options('family').to_csv('Database/Categories/funds_family.csv')