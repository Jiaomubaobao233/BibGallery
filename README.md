# BibGallery

BibGallery is a light, simple literature management library that organizes BibTeX, PDF, and image files. It generates
HTML files to display the saved images for the researcher to browse.

You can benefit from BibGallery if

- You use [LaTeX](https://www.latex-project.org/) or [Typst](https://typst.app/) to write and thus save and cite your
  literature using BibTeX.
- You use screenshots to take notes of your literature.

I wrote BibGallery since my notes are essentially screenshots and I would like to review them efficiently.

## Preparations

BibGallery relies
on [pdf2bib](https://github.com/MicheleCotrufo/pdf2bib), [BibtexParser](https://bibtexparser.readthedocs.io/en/main/), [PyMuPDF](https://pymupdf.readthedocs.io/en/latest/index.html), [watchdog](https://github.com/gorakhargosh/watchdog), and [Pandas](https://pandas.pydata.org/).

BibGallery works best in [Visual Studio Code](https://code.visualstudio.com/) where you can easily navigate between
files.

Literatures have to be organized into **categories** and assigned **themes**. Each category uses one BibTeX file.

Short codes (also known as citation keys) in BibTeX files should be formulated as `Author-Year-Theme`, for
example, `Akbarzadeh-2020-Graphic-Statics-Table`. In case of short code collisions, add `-Number` to the end, for
example, `Akbarzadeh-2020-Graphic-Statics-Table-1` and `Akbarzadeh-2020-Graphic-Statics-Table-2`.

Your file structure should be:

```
root
├ Bib.py
├ Main.py
├ bib
│ ├ Category1.bib
│ └ Category2.bib
└ PDF
  ├ Category1
  │ ├ Author-Year-Theme Name of Publication.pdf
  │ ├ Author-Year-Theme Name of Publication.jpg
  │ └ Author-Year-Theme Name of Publication2.png
  └ Category2
    └ ...
```

## Initialization

Set up by specifying the categories to inspect. The root folder and subfolders can be configured if necessary.

```
from Bib import Bib
bib = Bib(inspect_category=["Category1", "Category2"])
```

## Methods

### `Bib.check(self)`

Parse the BibTeX. If encoded for LaTeX, decode as Unicode plain text. Check if BibTeX/PDF/images are missing for any
entry. Only if all three are present, an entry will be considered complete. Incomplete entries will be listed in the
terminal. All results will be saved in `BibCheckResultAll.md` and `BibCheckResultNonBooks.md`. Only complete entries
will be marked `t` in the results. Reviewing the results in Visual Studio Code allows you to click the links to go to
the PDF files easily.

### `Bib.update_latex(self)`

Encode the BibTeX for LaTeX and save them as separate files.

### `Bib.generate_html_files(self)`

Generate HTML galleries using the pictures. Pictures are grouped by theme and titles link to the PDF files. Uses the .csv results saved in `Bib.check(self)`.

### `Bib.gallery_watch(self)`

Update HTML galleries automatically each time a new screenshot is saved.

### `Bib.collect(self)`

Create new entries based on PDF files. Rename and move them into the main folders and extract BibTeX based on the PDF
metadata. The pdf should be renamed as its theme.

The category of the PDF is specified by its parent folder. By default, the PDF to collect should be put as:

```
root
└ to_collect
  └ Category
    └ Theme.pdf
```

If themes collide, simply leave additional spaces at the end.

### `Bib.select_from_typst(self, input, output)`

Inspect the entries cited in the Typst file and extract only the BibTeX used. Save both the plain text and LaTeX
version.

### `Bib.theme_replace(self, old, new)`

Rename a theme from old to new. Affects BibTeX, PDFs and images.

### `Bib.short_code_replace(self, old, new)`

Rename a short code from old to new. Affects BibTeX, PDFs and images.
