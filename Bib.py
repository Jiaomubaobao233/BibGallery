__author__ = "Yefan Zhi"

import os
import pandas as pd
from doi2bib import crossref
import shutil
import fitz
import re
import codecs
import bibtexparser
import bibtexparser.middlewares as bm


def analyse_short_code(string):
    string = string.split("::")[-1]
    pattern = r"-(\d{4})-"  # regex pattern to match four-digit numbers
    match = re.search(pattern, string)
    if match:
        year = match.group()[1:-1]
        index = match.start()  # position where the year starts
        author = string[:index]
        theme = string[index + len(year) + 2:]
        if theme.rsplit("-", 1)[-1].isdecimal():
            theme, suffix = theme.rsplit("-", 1)
            suffix = "-" + suffix
        else:
            suffix = ""
        return author, year, theme, suffix
    else:
        return None, None, None, None


def compress_string(string):
    if len(string) <= 63:
        return string
    else:
        return string[:40] + "..." + string[-20:]


def write_to_end_of_file(file_path, content):
    with codecs.open(file_path, 'a', "utf8") as file:
        file.write(content)


def find_substring_locations_regex(A, B):
    pattern = re.compile(f'(?=({re.escape(B)}))')
    return [match.start() for match in pattern.finditer(A)]


def main_parser(bibtex_string):
    # https://github.com/sciunto-org/python-bibtexparser
    # https://bibtexparser.readthedocs.io/en/main/
    # https://stackoverflow.com/questions/491921/unicode-utf-8-reading-and-writing-to-files-in-python
    # https://bibtexparser.readthedocs.io/en/main/customize.html
    bibtex_string = bibtex_string.replace("\&", "&").replace("&", "\&")
    bib_database = bibtexparser.parse_string(
        bibtex_string, append_middleware=[bm.LatexDecodingMiddleware(),
                                          bm.SortBlocksByTypeAndKeyMiddleware()])
    return bibtexparser.write_string(bib_database).replace("https://doi.org/", "")


def latex_encode(bibtex_string):
    bib_database = bibtexparser.parse_string(
        bibtex_string, append_middleware=[bm.LatexEncodingMiddleware()])
    return bibtexparser.write_string(bib_database)


class Bib():
    def __init__(self, inspect_category,
                 root_folder_path="",
                 additional_categories=[],
                 bibtex_folder="bib",
                 bibtex_latex_folder="bib_latex",
                 pdf_folder="PDF",
                 html_folder="Gallery",
                 pdf_collect_folder="to_collect",
                 io_folder=""):
        self.root_folder_path = root_folder_path
        self.inspect_category = inspect_category
        self.additional_categories = additional_categories
        self.bibtex_path = os.path.join(root_folder_path, bibtex_folder)
        self.bibtex_latex_path = os.path.join(root_folder_path, bibtex_latex_folder)
        self.pdf_path = os.path.join(root_folder_path, pdf_folder)
        self.html_path = os.path.join(root_folder_path, html_folder)
        self.pdf_collect_path = os.path.join(root_folder_path, pdf_collect_folder)
        self.io_path = os.path.join(root_folder_path, io_folder)

    def check(self, show_incomplete=True, check_books=False):

        def new_short_code(df, category, string):
            if debug_switch: print("short_code: ", string)
            _, _, theme, _ = analyse_short_code(string)
            df = pd.concat([df, pd.DataFrame({"Category": [category],
                                              "Theme": [theme],
                                              "Title": [""],
                                              "t": [""],
                                              "Type": [""],
                                              "B": [0],
                                              "P": [0],
                                              "Link": [""]}, index=[string])])
            return df

        print("[CHECK]")
        df = pd.DataFrame(columns=["Category", "Theme", "Type", "t", "B", "P", "Title", "Link"])
        debug_switch = False

        for category_file in os.listdir(self.bibtex_path):
            bibtex_file_path = os.path.join(self.bibtex_path, category_file)
            if os.path.isfile(bibtex_file_path):
                category_name = category_file[:-4]
                if category_name not in self.inspect_category: continue
                # print("- Inspecting category: ", category_name)

                # 1. Import, format and sort the BibTeX entries
                with codecs.open(bibtex_file_path, "r", "utf-8") as file:
                    bibtex_string = file.read()
                bibtex_string = main_parser(bibtex_string)

                # 3. Write the sorted BibTeX entries to a new file
                with codecs.open(bibtex_file_path, 'w', "utf-8") as file:
                    file.write(bibtex_string)

                # 4. Import literature from pdf/image files into DataFrame
                category_path = os.path.join(self.pdf_path, category_name)
                for file_name in os.listdir(category_path):
                    if os.path.isfile(os.path.join(category_path, file_name)):
                        name, file_type = file_name.rsplit(".", 1)
                        short_code, title = name.split(" ", 1)
                        short_code = category_name + "::" + short_code

                        if short_code not in df.index:
                            df = new_short_code(df, category_name, short_code)
                            df.loc[short_code]["Title"] = title
                        if file_type.lower() == "pdf":
                            df.loc[short_code]["Link"] = "[](<" + os.path.join(category_path,
                                                                               file_name) + ">)"
                        if file_type.lower() in ["jpg", "png"]: df.loc[short_code]["P"] += 1

                # 5. Import literature from bibtex files into DataFrame
                with codecs.open(bibtex_file_path, "r", "utf-8") as file:
                    bibtex_string = file.read()
                entries = bibtex_string.split('\n\n\n')
                for entry in entries:
                    bib_type, short_code = entry.split("{", 1)
                    short_code = short_code.split(",", 1)[0]
                    short_code = category_name + "::" + short_code
                    # if short_code not in skip_bib:
                    if short_code not in df.index:
                        df = new_short_code(df, category_name, short_code)
                    df.loc[short_code]["Type"] = bib_type[1:]
                    df.loc[short_code]["B"] += 1

        print("√ Bib/PDF/Image imported into the DataFrame")
        print("√ Bibtex files updated in", self.bibtex_path)

        # df display options
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_colwidth', None)
        pd.set_option('display.expand_frame_repr', False)

        # df['Type'] = df['Type'].apply(lambda x: x[:7])

        # Inspect DataFrame
        def reindex_function(x):
            return x.split("::")[-1]

        df_backup = df
        df.index = df.index.map(reindex_function)
        if df[df.index.duplicated(keep=False)].index.empty:
            print("√ No short code collisions in the DataFrame")
        else:
            print("Colliding indices:")
            print(df_backup[df.index.duplicated(keep=False)])
            raise NameError("Above short code collision detected in the DataFrame")

        df = df.sort_values(by=['Category', 'Theme'], ascending=[True, True])
        df.loc[(df["B"] > 0) & (df["Link"] != "") & (df["P"] > 0), "t"] = "t"

        df['Title'] = df['Title'].apply(lambda x: x[:50])
        max_link_len = max(df['Link'].apply(lambda x: len(x)))
        df['Link'] = df['Link'].apply(lambda x: x.ljust(max_link_len))

        # if not show_only_problematic:
        #     print("Bibtex entries:")
        #     print(df)
        #     print()

        # Print results to Markdown
        print(df, file=codecs.open(os.path.join(self.io_path, 'BibCheckResultAll.md'), 'w', 'utf-8'))
        print(df[df["Type"] != "book"],
              file=codecs.open(os.path.join(self.io_path, 'BibCheckResultNonBooks.md'), 'w', 'utf-8'))
        print('√ DataFrame updated as', os.path.join(self.io_path, 'BibCheckResultAll.md'))

        problem_non_book_df = df[
            ((df["B"] != 1) | (df["Link"] == "") | (df["P"] == 0)) & (df["Type"] != "misc") & (
                    df["Type"] != "book")]
        if show_incomplete:
            print("Incomplete non-book bibtex entries:")
            print(problem_non_book_df.drop(columns=['Link']))

        problem_book_df = df[
            ((df["B"] != 1) | (df["Link"] == "") | (df["P"] == 0)) & (df["Type"] != "misc") & (
                    df["Type"] == "book")]

        if show_incomplete and check_books:
            print("Incomplete book bibtex entries:")
            print(problem_book_df.drop(columns=['Link']))

        print("√ Number of all entries:", len(df))
        print("√ Number of incomplete entries:", len(problem_non_book_df), "non-books and", len(problem_book_df),
              "books")
        print()
        # unique_values = df['Category'].unique()

    def update_latex(self):
        print("[UPDATE LATEX]")
        if not os.path.exists(self.bibtex_latex_path):
            os.makedirs(self.bibtex_latex_path)
        for category_file in os.listdir(self.bibtex_path):
            bibtex_file_path = os.path.join(self.bibtex_path, category_file)
            if os.path.isfile(bibtex_file_path):
                if category_file[-4:] != ".bib": continue
                category_name = category_file[:-4]
                if not (category_name in self.inspect_category or category_name in self.additional_categories): continue

                with codecs.open(bibtex_file_path, "r", "utf-8") as file:
                    bibtex_string = file.read()
                bibtex_string = latex_encode(bibtex_string)

                # 3. Write the sorted BibTeX entries to a new file
                bibtex_latex_file_path = os.path.join(self.bibtex_latex_path, category_name + "_latex.bib")
                with codecs.open(bibtex_latex_file_path, 'w', "utf-8") as file:
                    file.write(bibtex_string)

        print("√ Bibtex (latex) files updated in", self.bibtex_latex_path)
        print()

    def generate_html_files(self):

        def fetch_images(folder_path):
            image_extensions = ['.png', '.jpg']
            images = []
            for file in os.listdir(folder_path):
                if file.lower().endswith(tuple(image_extensions)):
                    images.append(file)
            return images

        def generate_html(image_list, folder_path):
            def sort_key(image_string):
                # Extract the required parts from the image filename
                filename = os.path.splitext(image_string)[0]
                [shortcode, title] = filename.split(' ', 1)
                pattern = r"-[0-9]{4}-"

                match = re.search(pattern, shortcode)
                start_index = match.start()
                author = shortcode[:start_index]
                year = shortcode[start_index + 1:start_index + 5]
                category = shortcode[start_index + 6:]
                # Sort the parts based on the required order
                return category, -int(year), author, title

            image_list.sort(key=sort_key)

            html = '''
            <html>
            <head>
            <style>
            .image {
                display: inline-block;
                margin: 15px 10px;
                padding: 5px 0px;
                height: 200px;
                text-align: center;
                <!--border: 1px solid #000;-->
            }
            .image img {
                max-height: 100%;
            }
            </style>
            </head>
            <body>
            '''
            themes = [analyse_short_code(x.split(" ", 1)[0])[2] for x in image_list]
            for i, image in enumerate(image_list):
                # Create the hyperlink to the corresponding PDF file

                if themes[i] != themes[i - 1]:
                    html += '<h1>{}</h1>'.format(themes[i])
                image_name = image.split(" ", 1)[0]
                pdf_file = None
                for file in os.listdir(folder_path):
                    if file.startswith(image_name) and file.lower().endswith('.pdf'):
                        pdf_file = file
                        break
                if pdf_file:
                    hyperlink = '<a href="{}/{}"><img src="file:///{}/{}" alt="{}"></a>'.format(
                        folder_path.replace('\\', '/'), pdf_file.replace('\\', '/'), folder_path.replace('\\', '/'),
                        image,
                        image
                    )
                else:
                    hyperlink = '<img src="file:///{}/{}" alt="{}">'.format(
                        folder_path.replace('\\', '/'), image, image
                    )

                html += '<div class="image">{}</div>'.format(hyperlink)
            html += '''
            </body>
            </html>
            '''
            return html

        print("[GENERATE HTML FILES]")
        if not os.path.exists(self.html_path): os.makedirs(self.html_path)
        # Generate html galleries
        for category_name in self.inspect_category:
            folder_path = os.path.join(self.pdf_path, category_name)

            # Fetch the images in the folder
            image_list = fetch_images(folder_path)

            # Generate the HTML code
            html_code = generate_html(image_list, folder_path)

            # Save the HTML code to a file
            html_file_path = os.path.join(self.html_path, "Gallery - " + category_name + '.html')
            with codecs.open(html_file_path, 'w', "utf-8") as html_file:
                html_file.write(html_code)

        print("√ HTML files saved in", self.html_path)
        print()

    def collect(self):

        def make_valid_filename(filename):
            valid_filename = re.sub(r'[\\/:"*?<>|]', '', filename)
            valid_filename = valid_filename.strip()
            return valid_filename

        def get_metadata_from_pdf(pdf_path):
            try:
                # print(pdf_path)
                doc = fitz.open(pdf_path)
                got_metadata = doc.metadata
                # print(got_metadata)
                doc.close()
                return got_metadata
            except Exception as e:
                return f"Error: {str(e)}"

        def get_bibtex_from_doi(doi_str):
            try:
                _, bib_str = crossref.get_bib(doi_str)
                return main_parser(bib_str)
            except Exception as e:
                return f"Error: {str(e)}"

        def get_short_codes_from_bib_str(bib_str):
            short_codes_set = set()
            entries = main_parser(bib_str).split('\n\n\n')
            for i in range(len(entries)):
                short_codes_set.add(entries[i].split("{", 1)[1].split(",", 1)[0])
            return short_codes_set

        def move_file(source_path, destination_path):
            try:
                shutil.move(source_path, destination_path)
                # print(f"File moved to '{destination_path}'.")
            except FileNotFoundError:
                raise NameError(f"File '{source_path}' not found.")
            except Exception as e:
                raise NameError(f"Error: {str(e)}")

        print("[COLLECT]")
        count_collected = 0
        for category in os.listdir(self.pdf_collect_path):
            if category not in self.inspect_category: continue
            # print("- Collecting category: ", category)
            category_folder_path = os.path.join(self.pdf_collect_path, category)

            with codecs.open(os.path.join(self.bibtex_path, category + ".bib"), 'r', "utf-8") as file:
                bibtex_data = file.read()
            short_codes = get_short_codes_from_bib_str(bibtex_data)
            for pdf_file in os.listdir(category_folder_path):
                if pdf_file[-4:] != ".pdf": continue
                count_collected += 1
                # print("-Processing:", pdf_file)
                theme = pdf_file[:-4].strip()
                # print(theme)
                metadata_dict = get_metadata_from_pdf(os.path.join(category_folder_path, pdf_file))
                author = metadata_dict["author"]
                if "," in author: author = author.split(",")[0]
                if author == "":
                    raise NameError("Failed to decode " + pdf_file)
                author = author.split(" ")[-1]
                title = metadata_dict["title"]
                doi = metadata_dict["subject"].split(" ")[-1]
                year = metadata_dict["subject"].split("(")[1].split(")")[0]
                short_code = author.capitalize() + "-" + year + "-" + theme
                if short_code in short_codes:
                    raise NameError("Short code collision " + short_code)
                new_file_name = make_valid_filename(short_code + " " + title + ".pdf")
                # print(new_file_name)
                bib = get_bibtex_from_doi(doi)
                left = bib.split("{")[0]
                right = bib.split(",", 1)[1]
                bib = left + "{" + short_code + "," + right
                os.rename(os.path.join(category_folder_path, pdf_file),
                          os.path.join(category_folder_path, new_file_name))
                print("√ Updated", pdf_file, "as", new_file_name)
                move_file(os.path.join(category_folder_path, new_file_name),
                          os.path.join(os.path.join(self.root_folder_path, category), new_file_name))
                write_to_end_of_file(os.path.join(self.bibtex_path, category + ".bib"), "\n\n" + bib + "\n")
                print("√ Added Bibtex of length", len(bib), "to", os.path.join(self.bibtex_path, category + ".bib"))
                print("√ Moved the PDF from", category_folder_path, "to", os.path.join(self.root_folder_path, category))
        if count_collected == 0:
            print("√ Nothing to collect")
        else:
            print("√ Collected", count_collected, "sources")
        print()

    def theme_replace(self, old, new):
        print("[THEME REPLACE]")
        categories = self.inspect_category
        # print("- Theme replacing  old:", old, " new:", new, " categories:", categories)

        # modify bibtex file
        for category in os.listdir(self.bibtex_path):
            bibtex_file_path = os.path.join(self.bibtex_path, category)
            if os.path.isfile(bibtex_file_path):
                category = category[:-4]
                if category not in categories: continue
                # print("- Updating bibtex of category: ", category_name)
                with codecs.open(bibtex_file_path, 'r', "utf-8") as file:
                    bibtex_data = file.read()
                bibtex_data = main_parser(bibtex_data)
                # Split the BibTeX entries
                entries = bibtex_data.split('\n\n\n')
                for i in range(len(entries)):
                    left, right = entries[i].split("{", 1)
                    short_code, right = right.split(",", 1)

                    author, year, theme, suffix = analyse_short_code(short_code)
                    if theme == old:
                        short_code_new = author + "-" + year + "-" + new + suffix
                        print("√ Bibtex short code updated from", short_code, "to",
                              short_code_new)
                        entries[i] = left.lower() + "{" + short_code_new + "," + right
                sorted_entries = sorted(entries, key=lambda x: x.split('{')[1].split(',')[0].strip())
                new_bibtex = '\n\n\n'.join(sorted_entries)
                with codecs.open(bibtex_file_path, 'w', "utf-8") as file:
                    file.write(new_bibtex)

        # modify file
        for category in os.listdir(self.pdf_path):
            if category not in categories: continue
            # print("- Updating files of category:", category_name)
            category_path = os.path.join(self.pdf_path, category)
            for file_name in os.listdir(category_path):
                if os.path.isfile(os.path.join(category_path, file_name)):
                    short_code, title = file_name.split(" ", 1)
                    author, year, theme, suffix = analyse_short_code(short_code)
                    if theme == old:
                        # print("- Modifying file:", file_name)

                        short_code_new = author + "-" + year + "-" + new + suffix
                        file_name_new = short_code_new + " " + title
                        print("√ File short code from", short_code, "to",
                              short_code_new, "(" + compress_string(file_name) + ")")
                        os.rename(os.path.join(category_path, file_name),
                                  os.path.join(category_path, file_name_new))
        print()

    def short_code_replace(self, old, new, category=None):
        categories = self.inspect_category if category is None else [category]
        print("[SHORT CODE REPLACE]")
        # print("- Short code replacing  old:", old, " new:", new, " categories:", categories)

        # modify bibtex file
        for category in os.listdir(self.bibtex_path):
            bibtex_file_path = os.path.join(self.bibtex_path, category)
            if os.path.isfile(bibtex_file_path):
                category_name = category[:-4]
                if category_name not in categories: continue
                # print("- Updating bibtex of category: ", category_name)
                with codecs.open(bibtex_file_path, 'r', 'utf-8') as file:
                    bibtex_data = file.read()
                bibtex_data = main_parser(bibtex_data)
                # Split the BibTeX entries
                entries = bibtex_data.split('\n\n\n')
                for i in range(len(entries)):
                    left, right = entries[i].split("{", 1)
                    short_code, right = right.split(",", 1)
                    if short_code == old:
                        # print("- Modifying bibtex:", short_code)
                        print("√ Bibtex short code updated from", old, "to", new)
                        entries[i] = left.lower() + "{" + new + "," + right
                sorted_entries = sorted(entries, key=lambda x: x.split('{')[1].split(',')[0].strip())
                new_bibtex = '\n\n\n'.join(sorted_entries)
                with codecs.open(bibtex_file_path, 'w', 'utf-8') as file:
                    file.write(new_bibtex)

        # modify file
        for category in os.listdir(self.pdf_path):
            if category not in categories: continue
            # print("- Updating files of category:", category_name)
            category_path = os.path.join(self.pdf_path, category)
            for file_name in os.listdir(category_path):
                if os.path.isfile(os.path.join(category_path, file_name)):
                    short_code, title = file_name.split(" ", 1)
                    if short_code == old:
                        print("√ File short code from", old, "to",
                              new, "(" + compress_string(file_name) + ")")
                        file_name_new = new + " " + title
                        os.rename(os.path.join(category_path, file_name),
                                  os.path.join(category_path, file_name_new))
        print()

    def select_from_typst(self, input="input.typ", output="selected.bib"):
        legal_characters = "abcdefghijklmnopqrstuvwxyz"
        legal_characters = legal_characters.upper() + legal_characters + "0123456789" + "-"

        def contains_year(input_string):
            match = re.search(re.compile(r'\b[a-zA-Z-]*\d{4}[a-zA-Z-]*\b'), input_string)
            if match:
                return True
            else:
                return False

        def get_front_shortcode(input_string):
            i = 0
            while i < len(input_string) and input_string[i] in legal_characters: i += 1
            if contains_year(input_string[:i]):
                return input_string[:i]

        def collect_short_code_from_typst(input_data):
            short_code_entries = [get_front_shortcode(x) for x in input_data.split("@")[1:]] + \
                                 [x[1:-1] for x in re.findall(r'<[A-Za-z0-9\-]+-\d{4}-[A-Za-z0-9\-]+>', input_data)]

            # print(short_code_entries)
            short_code_entries = set(short_code_entries)
            short_code_entries.remove(None)
            return short_code_entries

        # extract used shortcodes
        with codecs.open(os.path.join(self.io_path, input), 'r', 'utf-8') as file:
            input_data = file.read()

        short_code_entries = collect_short_code_from_typst(input_data)
        print("√ Number of references in input:", len(short_code_entries))
        # print(short_code_entries)
        collected_bib = []
        bibtex_path = self.bibtex_path
        for category_file in os.listdir(bibtex_path):
            bibtex_file_path = os.path.join(bibtex_path, category_file)
            if os.path.isfile(bibtex_file_path):
                category_name = category_file[:-4]
                # print(category_name)
                if not (category_name in self.inspect_category or category_name in self.additional_categories): continue

                # if category_name not in inspect_category: continue
                count = 0
                # Format and sort the BibTeX entries
                with codecs.open(bibtex_file_path, 'r', 'utf-8') as file:
                    bibtex_data = file.read()
                if category_name in self.additional_categories:
                    bibtex_data = main_parser(bibtex_data)
                entries = bibtex_data.split('\n\n\n')
                for entry in entries:
                    bib_type, short_code = entry.split("{", 1)
                    short_code = short_code.split(",", 1)[0]
                    # print(short_code)
                    if short_code in short_code_entries:
                        count += 1
                        collected_bib.append(entry)
                        short_code_entries.remove(short_code)
                if count > 0:
                    print("√ Collected", count, "entries from category: ", category_name)
        print("√ In total, collected", len(collected_bib), "entries")
        if short_code_entries:
            print("× Remaining references:", short_code_entries)
        # Write the selected BibTeX entries to a new file
        new_bibtex = main_parser('\n\n\n'.join(collected_bib))
        with codecs.open(os.path.join(self.io_path, output), 'w', "utf-8") as file:
            file.write(new_bibtex)

        with codecs.open(os.path.join(self.io_path, output[:-4] + "_latex.bib"), 'w', 'utf-8') as file:
            file.write(latex_encode(new_bibtex))
