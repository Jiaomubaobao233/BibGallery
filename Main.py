from Bib import Bib

if __name__ == "__main__":
    bib = Bib(
        inspect_categories=[
            "Additive-Manufacturing",
            "Computational-Origami",
            "Computer-Graphics",
            "Computational-Design",
            "Structural-Design",
            "Self-Forming",
            "Structural-Theory",
            "Discrete-Mathematics",
            "Architectural-History-and-Theory",
            "Architectural-Technology",
            "Theoretical-Computer-Science",
            "Robotics"
        ],
        additional_categories=[
            "TENG"
        ]
    )

    bib.collect(enforce=True)


    # bib.theme_replace("4D-Printing", "4D-Printing-Review")
    # bib.short_code_replace("Wei-2018-Geometry-Partition", "Wei-2018-3DP-Topology")
    # bib.check(show_incomplete=False, update_bibtex="update.bib")
    bib.check(show_incomplete=False)
    bib.generate_html_files()
    # bib.select_from_typst()
    bib.gallery_watch()