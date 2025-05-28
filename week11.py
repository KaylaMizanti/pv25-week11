import sys, sqlite3, csv
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QMessageBox, QFileDialog, QDockWidget, QScrollArea, QStatusBar, QTextEdit
)
from PyQt5.QtCore import Qt, QEvent

class BukuApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Manajemen Buku - Week 11")
        self.setGeometry(100, 100, 900, 600)

        self.conn = sqlite3.connect("katalog.db")
        self.c = self.conn.cursor()
        self.create_table()

        self.last_focused_input = None

        self.init_ui()
        self.load_data()

    def create_table(self):
        self.c.execute('''CREATE TABLE IF NOT EXISTS buku (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            judul TEXT,
            pengarang TEXT,
            tahun INTEGER
        )''')
        self.conn.commit()

    def init_ui(self):
        self.central_widget = QWidget()
        layout = QVBoxLayout()

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Cari judul buku...")
        self.search_input.textChanged.connect(self.search_data)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        input_layout = QHBoxLayout()
        self.judul_input = QLineEdit()
        self.judul_input.setPlaceholderText("📘 Judul Buku")
        self.judul_input.installEventFilter(self)

        self.pengarang_input = QLineEdit()
        self.pengarang_input.setPlaceholderText("✍️ Pengarang")
        self.pengarang_input.installEventFilter(self)

        self.tahun_input = QLineEdit()
        self.tahun_input.setPlaceholderText("📅 Tahun")
        self.tahun_input.installEventFilter(self)

        self.paste_button = QPushButton("📋 Paste")
        self.paste_button.clicked.connect(self.universal_paste)

        input_layout.addWidget(self.judul_input)
        input_layout.addWidget(self.pengarang_input)
        input_layout.addWidget(self.tahun_input)
        input_layout.addWidget(self.paste_button)

        layout.addLayout(input_layout)

        pink_style = """
        QPushButton {
            background-color: #d63384;
            color: white;
            border-radius: 5px;
            padding: 6px 12px;
        }
        QPushButton:hover {
            background-color: #e83e8c;
        }
        """
        self.save_button = QPushButton("📂 Simpan")
        self.save_button.setStyleSheet(pink_style)
        self.save_button.clicked.connect(self.save_data)

        self.delete_button = QPushButton("🗑️ Hapus")
        self.delete_button.setStyleSheet(pink_style)
        self.delete_button.clicked.connect(self.delete_data)

        self.export_button = QPushButton("📄 Export CSV")
        self.export_button.setStyleSheet(pink_style)
        self.export_button.clicked.connect(self.export_csv)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.save_button)
        btn_layout.addWidget(self.delete_button)
        btn_layout.addWidget(self.export_button)
        layout.addLayout(btn_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Judul", "Pengarang", "Tahun"])
        self.table.cellChanged.connect(self.update_data)
        self.table.itemDoubleClicked.connect(self.edit_mode)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.table)
        layout.addWidget(scroll)

        self.central_widget.setLayout(layout)
        self.setCentralWidget(self.central_widget)

        info_dock = QDockWidget("ℹ️ Info Aplikasi", self)
        info_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)
        info_widget = QTextEdit()
        info_widget.setReadOnly(True)
        info_widget.setHtml("""
        <h3>Manajemen Buku</h3>
        <p>Aplikasi ini digunakan untuk mencatat dan mengelola data buku.</p>
        <ul>
            <li>Gunakan tombol 📋 untuk menempel data dari clipboard.</li>
            <li>Gunakan fitur pencarian untuk mencari buku berdasarkan judul.</li>
            <li>Data dapat diekspor ke dalam format CSV.</li>
        </ul>""")
        info_dock.setWidget(info_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, info_dock)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Nama: Kayla Mizanti | NIM: F1D022127")

    def eventFilter(self, source, event):
        if event.type() == QEvent.FocusIn and isinstance(source, QLineEdit):
            self.last_focused_input = source
        return super().eventFilter(source, event)

    def universal_paste(self):
        clipboard = QApplication.clipboard()
        if self.last_focused_input:
            self.last_focused_input.insert(clipboard.text())
        else:
            QMessageBox.information(self, "Info", "Klik dulu kolom input yang ingin ditempeli.")

    def save_data(self):
        judul = self.judul_input.text()
        pengarang = self.pengarang_input.text()
        tahun = self.tahun_input.text()

        if not judul or not pengarang or not tahun:
            QMessageBox.warning(self, "Input Error", "Semua field harus diisi.")
            return

        try:
            tahun_int = int(tahun)
            self.c.execute("INSERT INTO buku (judul, pengarang, tahun) VALUES (?, ?, ?)",
                           (judul, pengarang, tahun_int))
            self.conn.commit()
            self.clear_inputs()
            self.load_data()
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Tahun harus berupa angka.")

    def load_data(self):
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        self.c.execute("SELECT * FROM buku")
        for row_idx, row_data in enumerate(self.c.fetchall()):
            self.table.insertRow(row_idx)
            for col_idx, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                self.table.setItem(row_idx, col_idx, item)
        self.table.blockSignals(False)

    def update_data(self, row, col):
        id_item = self.table.item(row, 0)
        if id_item is None:
            return
        record_id = int(id_item.text())
        new_value = self.table.item(row, col).text()
        column = ["id", "judul", "pengarang", "tahun"][col]

        try:
            if column == "tahun":
                new_value = int(new_value)
            self.c.execute(f"UPDATE buku SET {column} = ? WHERE id = ?", (new_value, record_id))
            self.conn.commit()
        except Exception as e:
            QMessageBox.critical(self, "Update Error", str(e))

    def edit_mode(self, item):
        self.table.editItem(item)

    def delete_data(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.information(self, "Hapus", "Pilih baris yang ingin dihapus.")
            return
        id_item = self.table.item(selected, 0)
        if id_item:
            record_id = int(id_item.text())
            self.c.execute("DELETE FROM buku WHERE id = ?", (record_id,))
            self.conn.commit()
            self.load_data()

    def search_data(self, text):
        self.table.setRowCount(0)
        self.c.execute("SELECT * FROM buku WHERE judul LIKE ?", ('%' + text + '%',))
        for row_idx, row_data in enumerate(self.c.fetchall()):
            self.table.insertRow(row_idx)
            for col_idx, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                self.table.setItem(row_idx, col_idx, item)

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Simpan CSV", "", "CSV Files (*.csv)")
        if path:
            self.c.execute("SELECT * FROM buku")
            rows = self.c.fetchall()
            with open(path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["ID", "Judul", "Pengarang", "Tahun"])
                writer.writerows(rows)
            QMessageBox.information(self, "Export Berhasil", "Data berhasil diekspor ke CSV.")

    def clear_inputs(self):
        self.judul_input.clear()
        self.pengarang_input.clear()
        self.tahun_input.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BukuApp()
    window.show()
    sys.exit(app.exec_())
