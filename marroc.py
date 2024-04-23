import sys
import requests
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QListWidget, QListWidgetItem, QMessageBox, QComboBox, QDialog
from PyQt5.QtGui import QPixmap
import os


class ModrinthSearchApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Modrinth Mod Search")
        self.setGeometry(100, 100, 500, 400)

        layout = QVBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter mod name...")
        layout.addWidget(self.search_input)

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_mods)
        layout.addWidget(self.search_button)

        self.mods_list = QListWidget()
        layout.addWidget(self.mods_list)

        self.select_button = QPushButton("Select Mod")
        self.select_button.clicked.connect(self.show_mod_details_window)
        layout.addWidget(self.select_button)

        self.selected_mod = None

        self.setLayout(layout)

    def search_mods(self):
        self.mods_list.clear()
        mod_name = self.search_input.text()
        api_url = f"https://api.modrinth.com/v2/search?query={mod_name}&limit=20"
        response = requests.get(api_url)
        if response.status_code == 200:
            mods_data = response.json()['hits']
            for mod in mods_data:
                mod_name = mod['title']
                mod_description = mod['description']
                item = QListWidgetItem(f"Title: {mod_name}\nDescription: {mod_description}")
                item.mod_data = mod
                self.mods_list.addItem(item)
        else:
            self.mods_list.addItem("Failed to fetch mods. Please try again later.")

    def show_mod_details_window(self):
        selected_item = self.mods_list.currentItem()
        if selected_item is not None:
            mod_data = selected_item.mod_data
            mod_slug = mod_data.get('slug')
            if mod_slug:
                api_url = f"https://api.modrinth.com/v2/project/{mod_slug}"
                response = requests.get(api_url)
                if response.status_code == 200:
                    mod_info = response.json()
                    icon_url = mod_info.get('icon_url')
                    mod_versions = self.get_mod_versions(mod_slug)
                    mod_details_window = ModDetailsWindow(mod_data, icon_url, mod_versions)
                    mod_details_window.exec_()
                else:
                    QMessageBox.warning(self, "Failed to Fetch Mod Details", "Failed to fetch mod details. Please try again later.")
            else:
                QMessageBox.warning(self, "No Mod Slug", "Selected mod has no slug.")
        else:
            QMessageBox.warning(self, "No Mod Selected", "Please select a mod first.")

    def get_mod_versions(self, mod_slug):
        api_url = f"https://api.modrinth.com/v2/project/{mod_slug}/version"
        response = requests.get(api_url)
        if response.status_code == 200:
            versions = response.json()
            return [version['name'] for version in versions]
        else:
            return []

class ModDetailsWindow(QDialog):
    def __init__(self, mod_data, icon_url, mod_versions):
        super().__init__()

        self.setWindowTitle("Mod Details")
        self.setGeometry(100, 100, 400, 300)

        self.mod_data = mod_data  # Store mod data

        layout = QVBoxLayout()

        mod_name_label = QLabel(f"Mod Name: {mod_data['title']}")
        layout.addWidget(mod_name_label)

        mod_description_label = QLabel(f"Mod Description: {mod_data['description']}")
        layout.addWidget(mod_description_label)

        icon_pixmap = self.load_icon(icon_url)
        icon_label = QLabel()
        if icon_pixmap:
            icon_label.setPixmap(icon_pixmap.scaled(64, 64))
        else:
            icon_label.setText("Icon not available")
        layout.addWidget(icon_label)

        self.version_dropdown = QComboBox()
        self.version_dropdown.addItems(mod_versions)
        layout.addWidget(self.version_dropdown)

        self.download_button = QPushButton("Download")
        self.download_button.clicked.connect(self.download_mod)  # Connect the button to the method
        layout.addWidget(self.download_button)

        self.download_url_label = QLabel()  # Label to display download URL
        layout.addWidget(self.download_url_label)

        self.setLayout(layout)

    def load_icon(self, icon_url):
        try:
            response = requests.get(icon_url)
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                return pixmap
            else:
                return None
        except Exception as e:
            print("Error loading icon:", e)
            return None

    def download_mod(self):
        selected_version = self.version_dropdown.currentText()
        mod_data = self.mod_data
        files = mod_data.get("files")
        if files:
            for file in files:
                if file.get("primary") and file.get("url").endswith('.jar'):
                    url = file.get("url")
                    filename = os.path.basename(url)
                    if url:
                        try:
                            response = requests.get(url)
                            response.raise_for_status()
                            with open(filename, 'wb') as f:
                                f.write(response.content)
                            QMessageBox.information(self, "Download Mod", f"Downloaded {filename} successfully.")
                            return
                        except Exception as e:
                            print("Error downloading mod:", e)
                            break
        QMessageBox.warning(self, "Download Mod", "Failed to download the mod.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ModrinthSearchApp()
    window.show()
    sys.exit(app.exec_())
