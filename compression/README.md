<img src="https://user-images.githubusercontent.com/46355364/220746807-669cdbc1-ac67-404c-b0bb-4a3d67d9931f.jpg" alt="Logo">
<a href="https://www.buymeacoffee.com/jerbouma">
    <img src="https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Donate-brightgreen?logo=buymeacoffee" alt="Logo">
</a>
<a href="https://github.com/JerBouma/FinanceDatabase/issues">
    <img src="https://img.shields.io/github/issues/jerbouma/financedatabase" alt="Logo">
</a>
    <a href="https://github.com/JerBouma/FinanceDatabase/pulls">
    <img src="https://img.shields.io/github/issues-pr/JerBouma/FinanceDatabase?color=yellow" alt="Logo">
</a>
<a href="https://pypi.org/project/financedatabase/">
    <img src="https://img.shields.io/pypi/v/FinanceDatabase" alt="Logo">
</a>
<a href="https://pypi.org/project/financedatabase/">
    <img src="https://img.shields.io/pypi/dm/FinanceDatabase" alt="Logo">
</a>

This compression notebook figures out what compression techniques are best suited for the database. It tries a variety of methods including csv, pickle and hdf. Based on these findings the compression technique is chosen. Here, the most important thing is **file size** given that every time someone access the database he is required to download the data file (unless stored locally). Therefore, I do not only test how long it takes for the files to get read in locally but also how long it would take to do so remotely.

It uses the methodology as described here: https://towardsdatascience.com/still-saving-your-data-in-csv-try-these-other-options-9abe8b83db3a

___
The conclusion is that **Pickle (xz)** results in the most efficient loading. However, to solve the vulnerability issue that arises with loading with Pickles I've decided to take the next best thing, this is the **CSV BZ2** option which is about the same in terms of loading.
___
