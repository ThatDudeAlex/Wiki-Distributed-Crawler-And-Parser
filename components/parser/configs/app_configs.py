from shared.config import QueueNames

WIKIPEDIA_MAIN_BODY_ID = 'mw-content-text'

IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.svg')

PARSER_QUEUE_CHANNELS = {
    'listen': QueueNames.PARSE.value,
    'savecontent': QueueNames.SAVE_CONTENT.value,
    'processlinks': QueueNames.PROCESS_LINKS.value,
    'failed': QueueNames.FAILED_TASK.value
}


# Specific Wikipedia boilerplate selectors
WIKIPEDIA_BOILERPLATE_SELECTORS = [
    # Invisible anchors next to headings
    ".mw-headline-anchor",

    # Information boxes (sidebars)
    "table.infobox",

    # Metadata tables
    "table.metadata",

    # Ambox templates (e.g., disambiguation, cleanup notices)
    "table.ambox",

    # Hatnotes (e.g., "For other uses, see...")
    "div.hatnote",

    # Rellink templates (e.g., "Related research")
    "div.rellink",

    # Links to Wikimedia sister projects
    "div.sistersitebox",

    # Navigation boxes (often at the bottom)
    "div.navbox",

    # Image containers with captions (often desired to remove if only text is needed)
    "div.thumb",

    # Portal links at the bottom
    "div.portal",

    # Print-specific footer
    "div.printfooter",

    # "edit" links next to headings
    "div.editsection",

    # Table of Contents
    "div#toc",

    # Specific citation markup
    "div.citation",

    # Superscript citation numbers (e.g., [1], [2])
    "sup.reference",

    # Language links
    "li.interlanguage-link",

    # References section, if main_content_div includes it
    "div.mw-references-columns",

    # Reflist for references
    "div.reflist",

    # Ordered list for references
    "ol.references",

    # Categories at the bottom of the page
    "div#catlinks",

    # Left sidebar navigation (though it might be outside main_content_div)
    "div#mw-panel",

    # View history, edit links (usually outside main_content_div)
    "div#p-views",

    # "edit" links next to section titles
    "span.mw-editsection",

    # More specific sections often at the end that might not be 'main article text'
    # For columns of references
    "div.mw-references-columns",

    # External links section, typically by heading but also containers
    "div#External_links",

    # See also section
    "div#See_also",

    # Notes section
    "div#Notes",

    # References section
    "div#References",

    # Further reading section
    "div#Further_reading",

    # Works cited section
    "div#Works_cited",

    # Bibliography section
    "div#Bibliography",

    # Combined refs and notes
    "div#References_and_notes",
]
