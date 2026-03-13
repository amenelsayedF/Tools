
import random

class DorkGenerator:
    def __init__(self):
        self.dork_operators = {
            "intext": "intext:",
            "inurl": "inurl:",
            "intitle": "intitle:",
            "filetype": "filetype:",
            "site": "site:",
            "cache": "cache:",
            "link": "link:",
            "related": "related:",
            "AND": " AND ",
            "OR": " OR ",
            "NOT": " NOT "
        }
        self.common_file_types = [
            "php", "asp", "aspx", "jsp", "do", "action", "cfm", "cgi", "pl", "py", "rb",
            "html", "htm", "shtml", "dhtml", "xhtml", "mjs", "js", "css", "scss", "sass", "less",
            "xml", "xsl", "xsd", "json", "txt", "rtf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
            "pdf", "zip", "rar", "7z", "tar", "gz", "sql", "log", "conf", "ini", "env"
        ]

    def generate_dorks(self, keywords, dork_types, file_types, domain=None, extra_word=None, randomize_params=False, randomize_output=False, count=1):
        generated_dorks = []
        selected_file_types = file_types if file_types else self.common_file_types

        for _ in range(count):
            dork_parts = []
            current_keywords = list(keywords)
            if randomize_params:
                random.shuffle(current_keywords)
                random.shuffle(dork_types)
                random.shuffle(selected_file_types)

            # Add main keywords
            if current_keywords:
                dork_parts.append(f'"{current_keywords[0]}"')
                if len(current_keywords) > 1:
                    for kw in current_keywords[1:]:
                        dork_parts.append(f'{self.dork_operators["AND"]}"{kw}"')

            # Add dork operators
            for d_type in dork_types:
                if d_type in self.dork_operators and d_type not in ["AND", "OR", "NOT"]:
                    if d_type == "filetype":
                        if selected_file_types:
                            filetype_dork = " | ".join([f'{self.dork_operators["filetype"]}{ft}' for ft in selected_file_types])
                            dork_parts.append(f'{self.dork_operators["AND"]}({filetype_dork})')
                    elif d_type == "site":
                        if domain:
                            dork_parts.append(f'{self.dork_operators["AND"]}{self.dork_operators["site"]}{domain}')
                    else:
                        # For intext, inurl, intitle, etc., use a keyword or extra_word
                        value = random.choice(current_keywords) if current_keywords else (extra_word if extra_word else "")
                        if value:
                            dork_parts.append(f'{self.dork_operators["AND"]}{self.dork_operators[d_type]}"{value}"')

            # Add extra word
            if extra_word:
                dork_parts.append(f'{self.dork_operators["AND"]}"{extra_word}"')

            # Add domain if not already added by site operator
            if domain and "site" not in dork_types:
                dork_parts.append(f'{self.dork_operators["AND"]}{self.dork_operators["site"]}{domain}')

            dork = "".join(dork_parts).strip()
            if dork.startswith(self.dork_operators["AND"]):
                dork = dork[len(self.dork_operators["AND"]):].strip()
            generated_dorks.append(dork)

        if randomize_output:
            random.shuffle(generated_dorks)

        return [d for d in generated_dorks if d] # Filter out empty dorks

# Example Usage (for testing purposes)
if __name__ == "__main__":
    generator = DorkGenerator()
    keywords = ["netflix", "account", "password"]
    dork_types = ["intext", "filetype", "site"]
    file_types = ["pdf", "txt"]
    domain = "example.com"
    extra_word = "confidential"

    print("\n--- Generating 5 dorks without randomization ---")
    dorks = generator.generate_dorks(keywords, dork_types, file_types, domain, extra_word, count=5)
    for d in dorks:
        print(d)

    print("\n--- Generating 5 dorks with parameter randomization ---")
    dorks_rand_params = generator.generate_dorks(keywords, dork_types, file_types, domain, extra_word, randomize_params=True, count=5)
    for d in dorks_rand_params:
        print(d)

    print("\n--- Generating 5 dorks with output randomization ---")
    dorks_rand_output = generator.generate_dorks(keywords, dork_types, file_types, domain, extra_word, randomize_output=True, count=5)
    for d in dorks_rand_output:
        print(d)

    print("\n--- Generating 5 dorks with all file types and no domain ---")
    dorks_all_files = generator.generate_dorks(["sensitive data"], ["intext", "filetype"], [], count=5)
    for d in dorks_all_files:
        print(d)
