import FinanceDatabase as fd
import matplotlib.pyplot as plt

# Obtain all countries from the database
equities_countries = fd.show_options('equities', 'countries')

# Obtain all sectors from the database
equities_sectors = fd.show_options('equities', 'sectors')

# Obtain all industries from the database
equities_industries = fd.show_options('equities', 'industries')

# Obtain all industries from the database
equities_all_categories = fd.show_options('equities')

equities_per_sector_netherlands = {}

for sector in equities_sectors[1:]:  # I skip the first sector since it means 'No Category'
    try:
        equities_per_sector_netherlands[sector] = len(fd.select_equities(country='Netherlands', sector=sector))
    except ValueError as error:
        print(error)

legend, values = zip(*equities_per_sector_netherlands.items())

colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'tab:blue', 'tab:orange', 'tab:gray',
          'lightcoral', 'yellow', 'saddlebrown', 'lightblue', 'olive']
plt.pie(values, labels=legend, colors=colors,
        wedgeprops={'linewidth': 0.5, 'edgecolor': 'white'})
plt.title('Companies per sector in the Netherlands')
plt.tight_layout()

plt.show()
