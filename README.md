# Dork Generator Mega

## Project Goal
To develop a powerful and user-friendly Google Dork Generator with a Graphical User Interface (GUI) for penetration testing reconnaissance. The tool will enable users to generate highly specific Google Dorks to discover sensitive information related to a target.

## Key Features
- **GUI Interface**: Intuitive and interactive interface for ease of use.
- **Multiple Dork Types**: Support for various dork types (e.g., `intext`, `inurl`, `filetype`, `site`).
- **Customizable File Types**: Ability to select specific file extensions (e.g., `.pdf`, `.docx`, `.php`, `.asp`).
- **Keyword Management**: Input keywords directly or load from a file.
- **Target Domain Specification**: Option to narrow down searches to a specific domain.
- **Extra Word Inclusion**: Add additional keywords to refine dorks.
- **Output Management**: Display generated dorks and save them to a file.
- **Randomization Options**: Randomize dork parameters and output order.

## Technical Stack
- **Programming Language**: Python
- **GUI Framework**: PyQt5 (chosen for its robustness and rich set of widgets)
- **Core Logic**: Custom Python modules for dork generation.

## Application Architecture (High-Level)
1.  **`main.py`**: Entry point of the application, responsible for initializing the GUI and connecting signals/slots.
2.  **`gui.py`**: Defines the PyQt5 UI elements, layouts, and event handlers.
3.  **`dork_generator.py`**: Contains the core logic for generating Google Dorks based on selected parameters.
4.  **`config.py`**: Stores application-wide configurations, default values, and potentially dork templates.

## Dork Generation Logic (Conceptual)
The `dork_generator.py` module will take inputs such as:
-   `keywords` (list of strings)
-   `extra_word` (string, optional)
-   `domain` (string, optional)
-   `dork_types` (list of selected dork operators, e.g., `intext`, `filetype`)
-   `file_types` (list of selected file extensions, e.g., `pdf`, `docx`)

It will then combine these elements using predefined templates and rules to construct valid Google Dorks. For example:
-   `intext:"keyword" filetype:pdf site:target.com`
-   `inurl:"admin" intitle:"login"`

Randomization will involve shuffling the order of operators, keywords, or selecting a subset of available options.

## Next Steps
1.  Set up a basic PyQt5 application structure.
2.  Implement the core dork generation logic.
3.  Integrate the dork generation logic with the GUI.
4.  Add file input/output functionalities.
5.  Implement randomization features.
6.  Thorough testing and refinement.
