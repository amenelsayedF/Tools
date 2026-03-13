
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QScrollArea, QGroupBox, QTextEdit, QFileDialog
)
from PyQt5.QtCore import Qt

from dork_generator import DorkGenerator

class DorkGeneratorGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.dork_generator = DorkGenerator()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Dork Generator Mega')
        self.setGeometry(100, 100, 1000, 700)

        main_layout = QVBoxLayout()

        # --- Target Configuration Group --- #
        target_config_group = QGroupBox('Target Configuration')
        target_config_layout = QGridLayout()

        target_config_layout.addWidget(QLabel('Keyword / File:'), 0, 0)
        self.keyword_file_input = QLineEdit()
        self.keyword_file_input.setPlaceholderText('Enter keywords separated by commas, or path to a keyword file')
        target_config_layout.addWidget(self.keyword_file_input, 0, 1)
        browse_button = QPushButton('Browse')
        browse_button.clicked.connect(self.browse_keyword_file)
        target_config_layout.addWidget(browse_button, 0, 2)

        target_config_layout.addWidget(QLabel('Extra Word:'), 1, 0)
        self.extra_word_input = QLineEdit()
        self.extra_word_input.setPlaceholderText('e.g., confidential, backup')
        target_config_layout.addWidget(self.extra_word_input, 1, 1)

        target_config_layout.addWidget(QLabel('Domain:'), 1, 2)
        self.domain_input = QLineEdit()
        self.domain_input.setPlaceholderText('e.g., example.com')
        target_config_layout.addWidget(self.domain_input, 1, 3)

        target_config_group.setLayout(target_config_layout)
        main_layout.addWidget(target_config_group)

        # --- Generation Settings Group --- #
        gen_settings_group = QGroupBox('Generation Settings')
        gen_settings_layout = QVBoxLayout()

        # Dork Types
        dork_types_label = QLabel('Dork Types:')
        gen_settings_layout.addWidget(dork_types_label)
        dork_types_layout = QHBoxLayout()
        self.dork_type_checkboxes = {}
        dork_types = ['intext', 'inurl', 'intitle', 'filetype', 'site', 'cache', 'link', 'related'] # Simplified for now
        for d_type in dork_types:
            checkbox = QCheckBox(d_type.capitalize())
            self.dork_type_checkboxes[d_type] = checkbox
            dork_types_layout.addWidget(checkbox)
        gen_settings_layout.addLayout(dork_types_layout)

        # File Types
        file_types_label = QLabel('File Types (scroll for more):')
        gen_settings_layout.addWidget(file_types_label)

        file_types_scroll_area = QScrollArea()
        file_types_scroll_area.setWidgetResizable(True)
        file_types_content_widget = QWidget()
        self.file_types_layout = QGridLayout()
        self.file_type_checkboxes = {}

        # Populate file types from DorkGenerator
        for i, ft in enumerate(self.dork_generator.common_file_types):
            checkbox = QCheckBox(ft)
            self.file_type_checkboxes[ft] = checkbox
            self.file_types_layout.addWidget(checkbox, i // 8, i % 8) # 8 columns

        file_types_content_widget.setLayout(self.file_types_layout)
        file_types_scroll_area.setWidget(file_types_content_widget)
        file_types_scroll_area.setFixedHeight(150)
        gen_settings_layout.addWidget(file_types_scroll_area)

        # Quick Select Buttons
        quick_select_layout = QHBoxLayout()
        select_all_button = QPushButton('Select All')
        select_all_button.clicked.connect(self.select_all_file_types)
        quick_select_layout.addWidget(select_all_button)

        deselect_all_button = QPushButton('Deselect All')
        deselect_all_button.clicked.connect(self.deselect_all_file_types)
        quick_select_layout.addWidget(deselect_all_button)

        web_files_button = QPushButton('Web Files')
        web_files_button.clicked.connect(lambda: self.select_file_types_group(['php', 'asp', 'aspx', 'jsp', 'html', 'htm', 'js', 'css', 'xml']))
        quick_select_layout.addWidget(web_files_button)

        documents_button = QPushButton('Documents')
        documents_button.clicked.connect(lambda: self.select_file_types_group(['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt']))
        quick_select_layout.addWidget(documents_button)
        gen_settings_layout.addLayout(quick_select_layout)

        # Options
        options_layout = QHBoxLayout()
        self.randomize_params_checkbox = QCheckBox('Randomize Parameters')
        options_layout.addWidget(self.randomize_params_checkbox)
        self.randomize_output_checkbox = QCheckBox('Randomize Output')
        options_layout.addWidget(self.randomize_output_checkbox)
        gen_settings_layout.addLayout(options_layout)

        gen_settings_group.setLayout(gen_settings_layout)
        main_layout.addWidget(gen_settings_group)

        # --- Generate Dorks Section --- #
        generate_dorks_layout = QHBoxLayout()
        self.generate_button = QPushButton('Generate Dorks')
        self.generate_button.setStyleSheet('background-color: #4CAF50; color: white;')
        self.generate_button.clicked.connect(self.generate_dorks)
        generate_dorks_layout.addWidget(self.generate_button)

        save_results_button = QPushButton('Save Results')
        save_results_button.setStyleSheet('background-color: #008CBA; color: white;')
        save_results_button.clicked.connect(self.save_dorks)
        generate_dorks_layout.addWidget(save_results_button)

        generate_dorks_layout.addWidget(QLabel('Dork Count:'))
        self.dork_count_input = QLineEdit('100')
        self.dork_count_input.setFixedWidth(50)
        generate_dorks_layout.addWidget(self.dork_count_input)

        main_layout.addLayout(generate_dorks_layout)

        # --- Generated Dorks Section --- #
        generated_dorks_group = QGroupBox('Generated Dorks')
        generated_dorks_layout = QVBoxLayout()
        self.generated_dorks_text_edit = QTextEdit()
        self.generated_dorks_text_edit.setReadOnly(True)
        generated_dorks_layout.addWidget(self.generated_dorks_text_edit)

        clear_button = QPushButton('Clear')
        clear_button.clicked.connect(self.generated_dorks_text_edit.clear)
        generated_dorks_layout.addWidget(clear_button, alignment=Qt.AlignRight)

        generated_dorks_group.setLayout(generated_dorks_layout)
        main_layout.addWidget(generated_dorks_group)

        self.setLayout(main_layout)

    def browse_keyword_file(self):
        file_dialog = QFileDialog()
        filepath, _ = file_dialog.getOpenFileName(self, 'Select Keyword File', '', 'Text Files (*.txt);;All Files (*)')
        if filepath:
            self.keyword_file_input.setText(filepath)

    def select_all_file_types(self):
        for checkbox in self.file_type_checkboxes.values():
            checkbox.setChecked(True)

    def deselect_all_file_types(self):
        for checkbox in self.file_type_checkboxes.values():
            checkbox.setChecked(False)

    def select_file_types_group(self, types_to_select):
        self.deselect_all_file_types()
        for ft in types_to_select:
            if ft in self.file_type_checkboxes:
                self.file_type_checkboxes[ft].setChecked(True)

    def generate_dorks(self):
        keywords_input = self.keyword_file_input.text()
        keywords = []
        if keywords_input:
            if '.txt' in keywords_input.lower() and '/' in keywords_input or '\\' in keywords_input:
                try:
                    with open(keywords_input, 'r') as f:
                        keywords = [line.strip() for line in f if line.strip()]
                except FileNotFoundError:
                    self.generated_dorks_text_edit.setText(f"Error: Keyword file not found at {keywords_input}")
                    return
            else:
                keywords = [kw.strip() for kw in keywords_input.split(',') if kw.strip()]

        extra_word = self.extra_word_input.text().strip()
        domain = self.domain_input.text().strip()

        selected_dork_types = [d_type for d_type, checkbox in self.dork_type_checkboxes.items() if checkbox.isChecked()]
        selected_file_types = [ft for ft, checkbox in self.file_type_checkboxes.items() if checkbox.isChecked()]

        randomize_params = self.randomize_params_checkbox.isChecked()
        randomize_output = self.randomize_output_checkbox.isChecked()

        try:
            dork_count = int(self.dork_count_input.text())
        except ValueError:
            self.generated_dorks_text_edit.setText("Error: Dork count must be a number.")
            return

        if not keywords and not extra_word and not domain:
            self.generated_dorks_text_edit.setText("Please provide at least one keyword, extra word, or domain to generate dorks.")
            return

        dorks = self.dork_generator.generate_dorks(
            keywords=keywords,
            dork_types=selected_dork_types,
            file_types=selected_file_types,
            domain=domain,
            extra_word=extra_word,
            randomize_params=randomize_params,
            randomize_output=randomize_output,
            count=dork_count
        )

        self.generated_dorks_text_edit.setText('\n'.join(dorks))
        self.generated_dorks_text_edit.append(f"\nGeneration complete! {len(dorks)} dorks generated.")

    def save_dorks(self):
        dorks_to_save = self.generated_dorks_text_edit.toPlainText()
        if not dorks_to_save:
            return

        file_dialog = QFileDialog()
        filepath, _ = file_dialog.getSaveFileName(self, 'Save Dorks', 'generated_dorks.txt', 'Text Files (*.txt);;All Files (*)')
        if filepath:
            with open(filepath, 'w') as f:
                f.write(dorks_to_save)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = DorkGeneratorGUI()
    gui.show()
    sys.exit(app.exec_())
