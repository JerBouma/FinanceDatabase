<img src="https://user-images.githubusercontent.com/46355364/220746807-669cdbc1-ac67-404c-b0bb-4a3d67d9931f.jpg" alt="Logo">

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor_this_Project-grey?logo=github)](https://github.com/sponsors/JerBouma)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy_Me_a_Coffee-grey?logo=buymeacoffee)](https://www.buymeacoffee.com/jerbouma)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-grey?logo=Linkedin&logoColor=white)](https://www.linkedin.com/in/boumajeroen/)
[![Documentation](https://img.shields.io/badge/Documentation-grey?logo=readme)](https://www.jeroenbouma.com/projects/financedatabase)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/financedatabase)](https://pypi.org/project/financedatabase/)
[![PYPI Version](https://img.shields.io/pypi/v/financedatabase)](https://pypi.org/project/financedatabase/)
[![PYPI Downloads](https://static.pepy.tech/badge/financedatabase/month)](https://pepy.tech/project/financedatabase)

This compression notebook figures out what compression techniques are best suited for the database. It tries a variety of methods including csv, pickle and hdf. Based on these findings the compression technique is chosen. Here, the most important thing is **file size** given that every time someone access the database he is required to download the data file (unless stored locally). Therefore, I do not only test how long it takes for the files to get read in locally but also how long it would take to do so remotely.

It uses the methodology as described here: https://towardsdatascience.com/still-saving-your-data-in-csv-try-these-other-options-9abe8b83db3a

___
The conclusion is that **Pickle (xz)** results in the most efficient loading. However, to solve the vulnerability issue that arises with loading with Pickles I've decided to take the next best thing, this is the **CSV BZ2** option which is about the same in terms of loading.
___
