import os
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QCheckBox, QScrollArea, QFrame, QLabel, QLineEdit, QHeaderView,
    QMessageBox, QTabWidget, QListWidget, QAbstractItemView, QComboBox, QFormLayout,
    QGraphicsView, QGraphicsScene, QGraphicsTextItem
)
from PyQt6.QtGui import QPainter, QPen, QIntValidator, QFont
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPen
from PyQt6.QtWidgets import QGraphicsScene

# Definiši putanju do baze
DB_PATH = "data/baza.db"


# Custom klasa za unos teksta u velika slova
class UppercaseLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.textChanged.connect(self.to_uppercase)

    def to_uppercase(self):
        self.blockSignals(True)
        self.setText(self.text().upper())
        self.blockSignals(False)


class SimpleApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Turnusi_VV")
        self.resize(1400, 900)
        self.init_database()

        # Promenljive za režim uređivanja
        self.trenutni_broj_za_izmenu = None
        self.trenutni_turnus_za_izmenu = None

        # Inicijalizacija UI
        self.init_ui()

        # Popunjavanje filtera i učitavanje podataka
        self.populate_vozovi_filter()
        self.populate_sekcije_filter()
        self.ucitaj_podatke()

        self.populate_nazivi_filter()
        self.populate_sekcije_turnusi_filter()
        self.ucitaj_turnuse()

        self.populate_grafik_filter()  # Za tab "Grafik"

        # Dodatna podešavanja (ako koristiš QTimer ili druge elemente)
        # Sve je već pokrenuto preko direktnih poziva

    def init_database(self):
        os.makedirs("data", exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Tabela za vozove
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vozovi (
                broj_voza TEXT PRIMARY KEY,
                pocetna_stanica TEXT,
                krajnja_stanica TEXT,
                sat_polaska INTEGER,
                minut_polaska INTEGER,
                sat_dolaska INTEGER,
                minut_dolaska INTEGER,
                status TEXT,
                sekcija TEXT,
                serija_vozila TEXT
            )
        ''')

        # Tabela za turnuse — sa kolonom sekcija
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS turnusi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                naziv TEXT UNIQUE,
                opis TEXT,
                sekcija TEXT
            )
        ''')

        # Proveri da li kolona 'sekcija' postoji u tabeli turnusi
        cursor.execute("PRAGMA table_info(turnusi)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'sekcija' not in columns:
            cursor.execute("ALTER TABLE turnusi ADD COLUMN sekcija TEXT")
            print("✅ Dodata kolona 'sekcija' u tabelu 'turnusi'")

        # Tabela za veze između turnusa i voza
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS turnus_vozovi (
                turnus_id INTEGER,
                broj_voza TEXT,
                redosled INTEGER,
                PRIMARY KEY (turnus_id, broj_voza),
                FOREIGN KEY (turnus_id) REFERENCES turnusi(id),
                FOREIGN KEY (broj_voza) REFERENCES vozovi(broj_voza)
            )
        ''')

        conn.commit()
        conn.close()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Tabovi
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_tab_vozovi(), "Vozovi")
        self.tabs.addTab(self.create_tab_turnusi(), "Turnusi")
        self.tabs.addTab(self.create_tab_grafik(), "Grafik")  # Novi tab!
        main_layout.addWidget(self.tabs)

        self.setLayout(main_layout)

    def create_tab_vozovi(self):
        widget = QWidget()
        layout = QVBoxLayout()

        naslov = QLabel("Unos voza")
        naslov.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(naslov)

        form_layout = QHBoxLayout()
        levo = QVBoxLayout()
        desno = QVBoxLayout()

        self.broj_voza_input = UppercaseLineEdit()
        self.pocetna_input = UppercaseLineEdit()
        self.krajnja_input = UppercaseLineEdit()
        self.sat_p_input = UppercaseLineEdit()
        self.minut_p_input = UppercaseLineEdit()
        self.sat_d_input = UppercaseLineEdit()
        self.minut_d_input = UppercaseLineEdit()
        self.serija_input = UppercaseLineEdit()
        self.status_input = UppercaseLineEdit()
        self.sekcija_input = UppercaseLineEdit()

        # Postavi validator za sat i minut
        self.sat_p_input.setValidator(QIntValidator(0, 23))
        self.minut_p_input.setValidator(QIntValidator(0, 59))
        self.sat_d_input.setValidator(QIntValidator(0, 23))
        self.minut_d_input.setValidator(QIntValidator(0, 59))

        levo.addWidget(QLabel("Broj voza (npr. 4830):"));
        levo.addWidget(self.broj_voza_input)
        levo.addWidget(QLabel("Početna stanica (2-3 slova):"));
        levo.addWidget(self.pocetna_input)
        levo.addWidget(QLabel("Krajnja stanica (2-3 slova):"));
        levo.addWidget(self.krajnja_input)
        levo.addWidget(QLabel("Sat polaska (hh):"));
        levo.addWidget(self.sat_p_input)
        levo.addWidget(QLabel("Minut polaska (mm):"));
        levo.addWidget(self.minut_p_input)

        desno.addWidget(QLabel("Sat dolaska (hh):"));
        desno.addWidget(self.sat_d_input)
        desno.addWidget(QLabel("Minut dolaska (mm):"));
        desno.addWidget(self.minut_d_input)
        desno.addWidget(QLabel("Serija vučnog vozila:"));
        desno.addWidget(self.serija_input)
        desno.addWidget(QLabel("Status (R, L, RE, S, V):"));
        desno.addWidget(self.status_input)
        desno.addWidget(QLabel("Sekcija (npr. KV):"));
        desno.addWidget(self.sekcija_input)

        form_layout.addLayout(levo)
        form_layout.addLayout(desno)
        layout.addLayout(form_layout)

        # Dugme za dodavanje novog voza
        self.btn_dodaj = QPushButton("Dodaj voz")
        self.btn_dodaj.clicked.connect(self.dodaj_voz)
        layout.addWidget(self.btn_dodaj)

        # Dugme za ažuriranje postojećeg voza (skriveno početno)
        self.btn_azuriraj = QPushButton("Ažuriraj voz")
        self.btn_azuriraj.clicked.connect(self.azuriraj_voz)
        self.btn_azuriraj.setVisible(False)
        layout.addWidget(self.btn_azuriraj)

        # Dugme za odustajanje od uredjivanja (skriveno početno)
        self.btn_odustani = QPushButton("Odustani od uredjivanja")
        self.btn_odustani.clicked.connect(self.odustani_od_uredjivanja)
        self.btn_odustani.setVisible(False)
        layout.addWidget(self.btn_odustani)

        # Filteri: VOZOVI (levo) i SEKCIJE (desno)
        filter_main_layout = QHBoxLayout()

        # LEVO: Filter po brojevima voza
        filter_voz_frame = QFrame()
        filter_voz_layout = QVBoxLayout()
        filter_voz_scroll = QScrollArea()
        filter_voz_scroll.setWidgetResizable(True)
        filter_voz_content = QWidget()
        self.voz_filter_layout = QVBoxLayout()
        self.voz_filter_layout.setSpacing(2)

        self.all_vozovi_cb = QCheckBox("Označi sve")
        self.all_vozovi_cb.setChecked(True)
        self.all_vozovi_cb.stateChanged.connect(self.on_all_vozovi_toggled)
        self.voz_filter_layout.addWidget(self.all_vozovi_cb)

        filter_voz_content.setLayout(self.voz_filter_layout)
        filter_voz_scroll.setWidget(filter_voz_content)
        filter_voz_layout.addWidget(QLabel("Filter po vozovima:"))
        filter_voz_layout.addWidget(filter_voz_scroll)
        filter_voz_frame.setLayout(filter_voz_layout)
        filter_voz_frame.setMaximumHeight(120)
        filter_voz_frame.setMaximumWidth(250)

        # DESNO: Filter po sekcijama
        filter_sekcija_frame = QFrame()
        filter_sekcija_layout = QVBoxLayout()
        filter_sekcija_scroll = QScrollArea()
        filter_sekcija_scroll.setWidgetResizable(True)
        filter_sekcija_content = QWidget()
        self.sekcije_filter_layout = QVBoxLayout()
        self.sekcije_filter_layout.setSpacing(2)

        self.all_sekcije_cb = QCheckBox("Označi sve")
        self.all_sekcije_cb.setChecked(True)
        self.all_sekcije_cb.stateChanged.connect(self.on_all_sekcije_toggled)
        self.sekcije_filter_layout.addWidget(self.all_sekcije_cb)

        filter_sekcija_content.setLayout(self.sekcije_filter_layout)
        filter_sekcija_scroll.setWidget(filter_sekcija_content)
        filter_sekcija_layout.addWidget(QLabel("Filter po sekciji:"))
        filter_sekcija_layout.addWidget(filter_sekcija_scroll)
        filter_sekcija_frame.setLayout(filter_sekcija_layout)
        filter_sekcija_frame.setMaximumHeight(120)
        filter_sekcija_frame.setMaximumWidth(250)

        filter_main_layout.addWidget(filter_voz_frame)
        filter_main_layout.addWidget(filter_sekcija_frame)
        filter_main_layout.addStretch()

        layout.addLayout(filter_main_layout)

        # Tabela
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(10)
        self.tabela.setHorizontalHeaderLabels([
            "Broj voza", "Poč. st.", "Kraj. st.", "Polazak", "Dolazak",
            "Serija", "Status", "Sekcija", "Uredi", "Obriši"
        ])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela.setSortingEnabled(True)  # Omogući sortiranje
        self.tabela.sortByColumn(0, Qt.SortOrder.AscendingOrder)  # Sortiraj po broju voza
        layout.addWidget(self.tabela)

        widget.setLayout(layout)
        return widget

    def populate_vozovi_filter(self):
        # Obriši sve osim "Označi sve"
        for i in reversed(range(self.voz_filter_layout.count())):
            item = self.voz_filter_layout.itemAt(i)
            if item and item.widget() != self.all_vozovi_cb:
                widget = item.widget()
                if widget:
                    widget.deleteLater()

        # Učitaj voze iz baze
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT broj_voza FROM vozovi ORDER BY CAST(broj_voza AS INTEGER)")
        brojevi = [str(row[0]) for row in cursor.fetchall()]
        conn.close()

        # Dodaj checkboxove
        for b in brojevi:
            cb = QCheckBox(b)
            cb.setChecked(True)
            cb.stateChanged.connect(self.ucitaj_podatke)
            self.voz_filter_layout.addWidget(cb)

    def populate_sekcije_filter(self):
        # Obriši sve osim "Označi sve"
        for i in reversed(range(self.sekcije_filter_layout.count())):
            item = self.sekcije_filter_layout.itemAt(i)
            if item and item.widget() != self.all_sekcije_cb:
                widget = item.widget()
                if widget:
                    widget.deleteLater()

        # Učitaj sekcije iz baze
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT sekcija FROM vozovi WHERE sekcija IS NOT NULL ORDER BY sekcija")
        sekcije = [str(row[0]) for row in cursor.fetchall() if row[0] is not None]
        conn.close()

        # Dodaj checkboxove
        for s in sekcije:
            cb = QCheckBox(s)
            cb.setChecked(True)
            cb.stateChanged.connect(self.ucitaj_podatke)
            self.sekcije_filter_layout.addWidget(cb)

    def on_all_vozovi_toggled(self, state):
        is_checked = state == Qt.CheckState.Checked.value
        for i in range(self.voz_filter_layout.count()):
            widget = self.voz_filter_layout.itemAt(i).widget()
            if isinstance(widget, QCheckBox) and widget != self.all_vozovi_cb:
                widget.blockSignals(True)
                widget.setChecked(is_checked)
                widget.blockSignals(False)
        self.ucitaj_podatke()

    def on_all_sekcije_toggled(self, state):
        is_checked = state == Qt.CheckState.Checked.value
        for i in range(self.sekcije_filter_layout.count()):
            widget = self.sekcije_filter_layout.itemAt(i).widget()
            if isinstance(widget, QCheckBox) and widget != self.all_sekcije_cb:
                widget.blockSignals(True)
                widget.setChecked(is_checked)
                widget.blockSignals(False)
        self.ucitaj_podatke()

    def ucitaj_podatke(self):
        # Prvo isprazni tabelu
        self.tabela.setRowCount(0)

        # Učitaj sve podatke iz baze
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vozovi ORDER BY CAST(broj_voza AS INTEGER)")
        svi_podaci = cursor.fetchall()
        conn.close()

        # Prikupi selektovane voze iz checkboxova
        selektovani_vozovi = []
        for i in range(self.voz_filter_layout.count()):
            widget = self.voz_filter_layout.itemAt(i).widget()
            if isinstance(widget, QCheckBox) and widget != self.all_vozovi_cb:
                if widget.isChecked():
                    selektovani_vozovi.append(widget.text())

        # Prikupi selektovane sekcije iz checkboxova
        selektovane_sekcije = []
        for i in range(self.sekcije_filter_layout.count()):
            widget = self.sekcije_filter_layout.itemAt(i).widget()
            if isinstance(widget, QCheckBox) and widget != self.all_sekcije_cb:
                if widget.isChecked():
                    selektovane_sekcije.append(widget.text())

        # Ako je "Označi sve" označen, dodaj sve
        if self.all_vozovi_cb.isChecked():
            selektovani_vozovi = list(set(selektovani_vozovi))
        if self.all_sekcije_cb.isChecked():
            selektovane_sekcije = list(set(selektovane_sekcije))

        # Ako nema selektovanih voza ili sekcija, ne prikazuj ništa
        if not selektovani_vozovi or not selektovane_sekcije:
            return

        # Filtriraj podatke
        for red in svi_podaci:
            broj = str(red[0])
            sekcija_val = str(red[8]) if len(red) > 8 and red[8] is not None else ""

            # Proveri da li voz prolazi filtere
            if broj in selektovani_vozovi:
                # Proveri sekciju
                if not selektovane_sekcije or sekcija_val in selektovane_sekcije or (
                        not sekcija_val and '' in selektovane_sekcije):
                    # Dodaj voz u tabelu
                    row_position = self.tabela.rowCount()
                    self.tabela.insertRow(row_position)

                    # MAPIRANJE KOLONA
                    sat_p = red[3]
                    min_p = red[4]
                    sat_d = red[5]
                    min_d = red[6]

                    podaci = [
                        broj,
                        red[1],  # pocetna
                        red[2],  # krajnja
                        f"{sat_p:02}:{min_p:02}",
                        f"{sat_d:02}:{min_d:02}",
                        red[9] or "",  # serija
                        red[7] or "R",  # status
                        red[8] or ""  # sekcija
                    ]

                    # Dodaj podatke u tabelu
                    for col, vrednost in enumerate(podaci):
                        item = QTableWidgetItem(str(vrednost))
                        item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        self.tabela.setItem(row_position, col, item)

                    # Dodaj dugmad
                    btn_uredi = QPushButton("Uredi")
                    btn_uredi.clicked.connect(lambda _, r=red: self.uredi_voz(r))
                    self.tabela.setCellWidget(row_position, 8, btn_uredi)

                    btn_obrisi = QPushButton("Obriši")
                    btn_obrisi.clicked.connect(lambda _, b=broj: self.obrisi_voz(b))
                    self.tabela.setCellWidget(row_position, 9, btn_obrisi)

        # Sortiraj tabelu
        self.tabela.sortByColumn(0, Qt.SortOrder.AscendingOrder)

    def uredi_voz(self, podaci):
        self.broj_voza_input.setText(str(podaci[0]))
        self.pocetna_input.setText(str(podaci[1]))
        self.krajnja_input.setText(str(podaci[2]))
        self.sat_p_input.setText(str(podaci[3]))
        self.minut_p_input.setText(str(podaci[4]))
        self.sat_d_input.setText(str(podaci[5]))
        self.minut_d_input.setText(str(podaci[6]))
        self.serija_input.setText(str(podaci[9] or ""))
        self.status_input.setText(str(podaci[7]))
        self.sekcija_input.setText(str(podaci[8] or ""))
        self.trenutni_broj_za_izmenu = str(podaci[0])

        # Promeni dugmad
        self.btn_dodaj.setVisible(False)
        self.btn_azuriraj.setVisible(True)
        self.btn_odustani.setVisible(True)

        print(f"REŽIM IZMENE: Uređujem voz {podaci[0]}")

    def azuriraj_voz(self):
        self.dodaj_voz()  # Poziva istu logiku kao "Dodaj voz", ali sa trenutnim_brojem_za_izmenu

    def odustani_od_uredjivanja(self):
        # Vrati formu u originalno stanje
        self.ocisti_formu()

        # Vrati dugmad u originalno stanje
        self.btn_dodaj.setVisible(True)
        self.btn_azuriraj.setVisible(False)
        self.btn_odustani.setVisible(False)
        self.trenutni_broj_za_izmenu = None

    def dodaj_voz(self):
        try:
            # Uzmi podatke iz polja
            broj = self.broj_voza_input.text().strip()
            pocetna = self.pocetna_input.text().strip()
            krajnja = self.krajnja_input.text().strip()
            sat_p = self.sat_p_input.text().strip()
            min_p = self.minut_p_input.text().strip()
            sat_d = self.sat_d_input.text().strip()
            min_d = self.minut_d_input.text().strip()
            serija = self.serija_input.text().strip() or None
            status = (self.status_input.text().strip() or 'R').upper()
            sekcija = self.sekcija_input.text().strip()

            # ✅ OBAVEZNA POLJA (mora biti popunjena)
            obavezna_polja = [
                ("Broj voza", broj),
                ("Početna stanica", pocetna),
                ("Krajnja stanica", krajnja),
                ("Sat polaska", sat_p),
                ("Minut polaska", min_p),
                ("Sat dolaska", sat_d),
                ("Minut dolaska", min_d),
                ("Sekcija", sekcija),
            ]

            # Proveri da li su sva obavezna polja popunjena
            nedostajuci = []
            for naziv, vrednost in obavezna_polja:
                if not vrednost:
                    nedostajuci.append(naziv)

            if nedostajuci:
                QMessageBox.critical(
                    self,
                    "Greška u unosu",
                    f"Neophodno je popuniti sledeća polja:\n- " + "\n- ".join(nedostajuci)
                )
                return

            # ✅ Validacija vrednosti
            if not broj.isdigit() or len(broj) < 3 or len(broj) > 5:
                raise ValueError("Broj voza mora imati 3–5 cifara.")
            if not (2 <= len(pocetna) <= 3) or not pocetna.isalpha():
                raise ValueError("Početna stanica: 2–3 slova.")
            if not (2 <= len(krajnja) <= 3) or not krajnja.isalpha():
                raise ValueError("Krajnja stanica: 2–3 slova.")
            if not sat_p.isdigit() or not (0 <= int(sat_p) <= 23):
                raise ValueError("Sat polaska mora biti broj između 0 i 23.")
            if not min_p.isdigit() or not (0 <= int(min_p) <= 59):
                raise ValueError("Minut polaska mora biti broj između 0 i 59.")
            if not sat_d.isdigit() or not (0 <= int(sat_d) <= 23):
                raise ValueError("Sat dolaska mora biti broj između 0 i 23.")
            if not min_d.isdigit() or not (0 <= int(min_d) <= 59):
                raise ValueError("Minut dolaska mora biti broj između 0 i 59.")

            # Pretvori u int
            sat_p = int(sat_p)
            min_p = int(min_p)
            sat_d = int(sat_d)
            min_d = int(min_d)

            conn = None
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                if self.trenutni_broj_za_izmenu is not None:
                    cursor.execute('''
                        UPDATE vozovi SET 
                            broj_voza = ?, pocetna_stanica = ?, krajnja_stanica = ?,
                            sat_polaska = ?, minut_polaska = ?, sat_dolaska = ?, minut_dolaska = ?,
                            serija_vozila = ?, status = ?, sekcija = ?
                        WHERE broj_voza = ?
                    ''', (broj, pocetna, krajnja, sat_p, min_p, sat_d, min_d, serija, status, sekcija, self.trenutni_broj_za_izmenu))
                    poruka = f"Voz {broj} uspešno ažuriran!"
                else:
                    try:
                        cursor.execute('''
                            INSERT INTO vozovi (broj_voza, pocetna_stanica, krajnja_stanica,
                                sat_polaska, minut_polaska, sat_dolaska, minut_dolaska,
                                serija_vozila, status, sekcija)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (broj, pocetna, krajnja, sat_p, min_p, sat_d, min_d, serija, status, sekcija))
                        poruka = f"Voz {broj} uspešno dodat!"
                    except sqlite3.IntegrityError:
                        QMessageBox.critical(self, "Greška", f"Voz broj {broj} već postoji!")
                        return

                conn.commit()
            finally:
                if conn:
                    conn.close()

            # ✅ OSVEŽI FILTERE I TABELU
            self.populate_vozovi_filter()
            self.populate_sekcije_filter()
            self.ucitaj_podatke()

            QMessageBox.information(self, "Uspeh", poruka)
            self.ocisti_formu()

            # ✅ VRAĆANJE FORME U REŽIM DODAVANJA NOVOG VOZA
            self.btn_dodaj.setVisible(True)
            self.btn_azuriraj.setVisible(False)
            self.btn_odustani.setVisible(False)
            self.trenutni_broj_za_izmenu = None

        except ValueError as e:
            QMessageBox.critical(self, "Greška u unosu", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Greška", f"Greška pri čuvanju: {e}")

    def obrisi_voz(self, broj_voza):
        potvrda = QMessageBox.question(self, "Potvrda", f"Obriši voz {broj_voza}?")
        if potvrda == QMessageBox.StandardButton.Yes:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM vozovi WHERE broj_voza = ?", (broj_voza,))
            conn.commit()
            conn.close()

            # OSVEŽI FILTROVE
            self.populate_vozovi_filter()
            self.populate_sekcije_filter()

            # OSVEŽI TABELU
            self.ucitaj_podatke()

            # OČISTI FORMU
            self.ocisti_formu()

            QMessageBox.information(self, "Obrađeno", f"Voz {broj_voza} obrisan.")

    def ocisti_formu(self):
        self.broj_voza_input.clear()
        self.pocetna_input.clear()
        self.krajnja_input.clear()
        self.sat_p_input.clear()
        self.minut_p_input.clear()
        self.sat_d_input.clear()
        self.minut_d_input.clear()
        self.serija_input.clear()
        self.status_input.clear()
        self.sekcija_input.clear()

    def create_tab_turnusi(self):
        widget = QWidget()
        layout = QVBoxLayout()

        # Naslov
        naslov = QLabel("Unos turnusa")
        naslov.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(naslov)

        # Forma za unos
        form_layout = QVBoxLayout()

        # Polje za naziv turnusa
        naziv_layout = QVBoxLayout()
        naziv_layout.addWidget(QLabel("Naziv turnusa:"))
        self.naziv_turnusa_input = QLineEdit()
        self.naziv_turnusa_input.setPlaceholderText("Npr. TUR1")
        naziv_layout.addWidget(self.naziv_turnusa_input)
        form_layout.addLayout(naziv_layout)

        # Polje za opis turnusa
        opis_layout = QVBoxLayout()
        opis_layout.addWidget(QLabel("Opis turnusa:"))
        self.opis_turnusa_input = QLineEdit()
        self.opis_turnusa_input.setPlaceholderText("Npr. Beograd-Niš")
        opis_layout.addWidget(self.opis_turnusa_input)
        form_layout.addLayout(opis_layout)

        # Polje za vozove u turnusu
        vozovi_layout = QVBoxLayout()
        vozovi_layout.addWidget(QLabel("Vozovi u turnusu:"))
        self.vozovi_input = QLineEdit()
        self.vozovi_input.setPlaceholderText("Npr. 4830, 4831, 4832")
        vozovi_layout.addWidget(self.vozovi_input)
        form_layout.addLayout(vozovi_layout)

        # Polje za sekciju
        sekcija_layout = QVBoxLayout()
        sekcija_layout.addWidget(QLabel("Sekcija za vuču vozova:"))
        self.sekcija_voza_input = UppercaseLineEdit()
        self.sekcija_voza_input.setPlaceholderText("Npr. KV, PV")
        sekcija_layout.addWidget(self.sekcija_voza_input)
        form_layout.addLayout(sekcija_layout)

        layout.addLayout(form_layout)

        # Dugme za proveru
        self.btn_proveri = QPushButton("Proveri turnus")
        self.btn_proveri.clicked.connect(self.proveri_turnus)
        layout.addWidget(self.btn_proveri)

        # Dugme za odustajanje (skriveno na početku)
        self.btn_odustani = QPushButton("Odustani")
        self.btn_odustani.clicked.connect(self.odustani_od_uredjivanja_turnusa)
        self.btn_odustani.setVisible(False)
        layout.addWidget(self.btn_odustani)

        # Status provere
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        layout.addWidget(self.status_label)

        # Filteri: NAZIVI i SEKCIJE
        filter_main_layout = QHBoxLayout()

        # LEVO: Filter po nazivima turnusa
        filter_naziv_frame = QFrame()
        filter_naziv_layout = QVBoxLayout()
        filter_naziv_scroll = QScrollArea()
        filter_naziv_scroll.setWidgetResizable(True)
        filter_naziv_content = QWidget()
        self.naziv_filter_layout = QVBoxLayout()
        self.naziv_filter_layout.setSpacing(2)

        self.all_nazivi_cb = QCheckBox("Označi sve")
        self.all_nazivi_cb.setChecked(True)
        self.all_nazivi_cb.stateChanged.connect(self.on_all_nazivi_toggled)
        self.naziv_filter_layout.addWidget(self.all_nazivi_cb)

        filter_naziv_content.setLayout(self.naziv_filter_layout)
        filter_naziv_scroll.setWidget(filter_naziv_content)
        filter_naziv_layout.addWidget(QLabel("Filter po nazivu:"))
        filter_naziv_layout.addWidget(filter_naziv_scroll)
        filter_naziv_frame.setLayout(filter_naziv_layout)
        filter_naziv_frame.setMaximumHeight(120)
        filter_naziv_frame.setMaximumWidth(250)

        # DESNO: Filter po sekcijama
        filter_sekcija_frame = QFrame()
        filter_sekcija_layout = QVBoxLayout()
        filter_sekcija_scroll = QScrollArea()
        filter_sekcija_scroll.setWidgetResizable(True)
        filter_sekcija_content = QWidget()
        self.sekcije_turnusi_filter_layout = QVBoxLayout()
        self.sekcije_turnusi_filter_layout.setSpacing(2)

        self.all_sekcije_turnusi_cb = QCheckBox("Označi sve")
        self.all_sekcije_turnusi_cb.setChecked(True)
        self.all_sekcije_turnusi_cb.stateChanged.connect(self.on_all_sekcije_turnusi_toggled)
        self.sekcije_turnusi_filter_layout.addWidget(self.all_sekcije_turnusi_cb)

        filter_sekcija_content.setLayout(self.sekcije_turnusi_filter_layout)
        filter_sekcija_scroll.setWidget(filter_sekcija_content)
        filter_sekcija_layout.addWidget(QLabel("Filter po sekciji:"))
        filter_sekcija_layout.addWidget(filter_sekcija_scroll)
        filter_sekcija_frame.setLayout(filter_sekcija_layout)
        filter_sekcija_frame.setMaximumHeight(120)
        filter_sekcija_frame.setMaximumWidth(250)

        filter_main_layout.addWidget(filter_naziv_frame)
        filter_main_layout.addWidget(filter_sekcija_frame)
        filter_main_layout.addStretch()

        layout.addLayout(filter_main_layout)

        # Tabela postojećih turnusa
        self.tabela_turnusa = QTableWidget()
        self.tabela_turnusa.setColumnCount(5)
        self.tabela_turnusa.setHorizontalHeaderLabels([
            "Naziv", "Opis", "Vozovi u turnusu", "Sekcija", "Akcije"
        ])
        self.tabela_turnusa.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela_turnusa.setSortingEnabled(True)  # ✅ OMOGUĆENO SORTIRANJE
        layout.addWidget(QLabel("Postojeći turnusi:"))
        layout.addWidget(self.tabela_turnusa)

        widget.setLayout(layout)
        return widget

    def proveri_turnus(self):
        # Resetuj status
        self.status_label.setText("")
        self.status_label.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")

        # Preuzmi podatke
        naziv = self.naziv_turnusa_input.text().strip()
        opis = self.opis_turnusa_input.text().strip()
        vozovi_text = self.vozovi_input.text().strip()

        # Proveri da li je unet naziv
        if not naziv:
            self.status_label.setText("Greška: Naziv turnusa je obavezan!")
            self.status_label.setStyleSheet("padding: 10px; background-color: #ffcccc; border-radius: 5px;")
            return

        # Proveri da li je unet bar jedan voz
        if not vozovi_text:
            self.status_label.setText("Greška: Morate uneti bar jedan voz!")
            self.status_label.setStyleSheet("padding: 10px; background-color: #ffcccc; border-radius: 5px;")
            return

        # Parsiraj vozove
        vozovi = [v.strip() for v in vozovi_text.split(",") if v.strip()]

        # Proveri da li vozovi postoje i da li je redosled ispravan
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Dobavi informacije o svim vozovima
        vozovi_info = {}
        for broj in vozovi:
            cursor.execute("""
                SELECT pocetna_stanica, krajnja_stanica, sat_polaska, minut_polaska, sat_dolaska, minut_dolaska
                FROM vozovi WHERE broj_voza = ?
            """, (broj,))
            info = cursor.fetchone()
            if info:
                vozovi_info[broj] = {
                    "pocetna": info[0],
                    "krajnja": info[1],
                    "polazak": (info[2], info[3]),
                    "dolazak": (info[4], info[5])
                }
            else:
                self.status_label.setText(f"Greška: Voz {broj} ne postoji u bazi!")
                self.status_label.setStyleSheet("padding: 10px; background-color: #ffcccc; border-radius: 5px;")
                conn.close()
                return

        # Proveri redosled
        greske = []
        for i in range(len(vozovi) - 1):
            broj_trenutni = vozovi[i]
            broj_sledeci = vozovi[i + 1]

            # Proveri da li postoji informacija o vozu
            if broj_trenutni not in vozovi_info or broj_sledeci not in vozovi_info:
                continue

            voz_trenutni = vozovi_info[broj_trenutni]
            voz_sledeci = vozovi_info[broj_sledeci]

            # Proveri stanicu
            if voz_trenutni["krajnja"] != voz_sledeci["pocetna"]:
                greske.append(
                    f"Voz {broj_trenutni} i {broj_sledeci}: Stanica {voz_trenutni['krajnja']} ≠ {voz_sledeci['pocetna']}")

            # Proveri vreme
            dolazak_trenutni = voz_trenutni["dolazak"][0] * 60 + voz_trenutni["dolazak"][1]
            polazak_sledeci = voz_sledeci["polazak"][0] * 60 + voz_sledeci["polazak"][1]

            if dolazak_trenutni >= polazak_sledeci:
                greske.append(
                    f"Voz {broj_trenutni} i {broj_sledeci}: Vreme dolaska {dolazak_trenutni // 60}:{dolazak_trenutni % 60} ≥ {polazak_sledeci // 60}:{polazak_sledeci % 60}")

        # Prikazi rezultat
        if greske:
            poruka = "Greške u redosledu:\n" + "\n".join(greske)
            self.status_label.setText(poruka)
            self.status_label.setStyleSheet("padding: 10px; background-color: #ffcccc; border-radius: 5px;")
        else:
            poruka = f"Turnus '{naziv}' je ispravan! Možete ga sačuvati."
            self.status_label.setText(poruka)
            self.status_label.setStyleSheet("padding: 10px; background-color: #ddffdd; border-radius: 5px;")

            # Zameni dugme "Proveri turnus" sa "Sačuvaj turnus"
            self.btn_proveri.setText("Sačuvaj turnus")
            self.btn_proveri.clicked.disconnect()
            self.btn_proveri.clicked.connect(self.sacuvaj_turnus)

        conn.close()

    def sacuvaj_turnus(self):
        # Preuzmi podatke
        naziv = self.naziv_turnusa_input.text().strip()
        opis = self.opis_turnusa_input.text().strip()
        vozovi_text = self.vozovi_input.text().strip()

        # Proveri da li je unet naziv
        if not naziv:
            QMessageBox.critical(self, "Greška", "Naziv turnusa je obavezan!")
            return

        # Parsiraj vozove
        vozovi = [v.strip() for v in vozovi_text.split(",") if v.strip()]
        if not vozovi:
            QMessageBox.critical(self, "Greška", "Morate uneti bar jedan voz!")
            return

        # Sačuvaj u bazu
        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Dodaj turnus
            try:
                cursor.execute("INSERT INTO turnusi (naziv, opis) VALUES (?, ?)", (naziv, opis))
                conn.commit()

                # Dobavi ID novog turnusa
                cursor.execute("SELECT id FROM turnusi WHERE naziv = ?", (naziv,))
                turnus_id = cursor.fetchone()[0]

                # Dodaj voze u turnus
                for redosled, broj_voza in enumerate(vozovi, 1):
                    cursor.execute("""
                        INSERT INTO turnus_vozovi (turnus_id, broj_voza, redosled)
                        VALUES (?, ?, ?)
                    """, (turnus_id, broj_voza, redosled))

                conn.commit()

                QMessageBox.information(self, "Uspeh", f"Turnus '{naziv}' uspešno sačuvan!")

                # Resetuj formu
                self.naziv_turnusa_input.clear()
                self.opis_turnusa_input.clear()
                self.vozovi_input.clear()
                self.status_label.setText("")

                # Vrati dugme na "Proveri turnus"
                self.btn_proveri.setText("Proveri turnus")
                self.btn_proveri.clicked.disconnect()
                self.btn_proveri.clicked.connect(self.proveri_turnus)

                # Ažuriraj prikaz
                self.ucitaj_turnuse()

            except sqlite3.IntegrityError:
                QMessageBox.critical(self, "Greška", f"Turnus '{naziv}' već postoji!")

        finally:
            if conn:
                conn.close()

    def ucitaj_turnuse(self):
        # Isprazni tabelu
        self.tabela_turnusa.setRowCount(0)

        # Prikupi selektovane nazive iz checkboxova
        selektovani_nazivi = []
        for i in range(self.naziv_filter_layout.count()):
            widget = self.naziv_filter_layout.itemAt(i).widget()
            if isinstance(widget, QCheckBox) and widget != self.all_nazivi_cb:
                if widget.isChecked():
                    selektovani_nazivi.append(widget.text())

        # Prikupi selektovane sekcije iz checkboxova
        selektovane_sekcije = []
        for i in range(self.sekcije_turnusi_filter_layout.count()):
            widget = self.sekcije_turnusi_filter_layout.itemAt(i).widget()
            if isinstance(widget, QCheckBox) and widget != self.all_sekcije_turnusi_cb:
                if widget.isChecked():
                    selektovane_sekcije.append(widget.text())

        # Ako je "Označi sve" označen, dodaj sve
        if self.all_nazivi_cb.isChecked():
            selektovani_nazivi = list(set(selektovani_nazivi))
        if self.all_sekcije_turnusi_cb.isChecked():
            selektovane_sekcije = list(set(selektovane_sekcije))

        # Ako nema selektovanih naziva ili sekcija, ne prikazuj ništa
        if not selektovani_nazivi or not selektovane_sekcije:
            return

        # Učitaj sve turnuse iz baze
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT t.id, t.naziv, t.opis, t.sekcija
            FROM turnusi t
            ORDER BY t.naziv
        """)
        svi_turnusi = cursor.fetchall()
        conn.close()

        # Filtriraj i dodaj u tabelu
        for turnus in svi_turnusi:
            naziv = str(turnus[1])
            sekcija_val = str(turnus[3]) if len(turnus) > 3 and turnus[3] is not None else ""

            # Proveri filtere
            if naziv in selektovani_nazivi:
                if not selektovane_sekcije or sekcija_val in selektovane_sekcije:
                    # Dobavi voze za ovaj turnus
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT v.broj_voza
                        FROM turnus_vozovi tv
                        JOIN vozovi v ON tv.broj_voza = v.broj_voza
                        WHERE tv.turnus_id = ?
                        ORDER BY tv.redosled
                    """, (turnus[0],))
                    vozovi = [v[0] for v in cursor.fetchall()]
                    vozovi_str = ", ".join(vozovi)
                    conn.close()

                    # Dodaj red u tabelu
                    row_position = self.tabela_turnusa.rowCount()
                    self.tabela_turnusa.insertRow(row_position)

                    # Popuni kolone
                    self.tabela_turnusa.setItem(row_position, 0, QTableWidgetItem(turnus[1]))
                    self.tabela_turnusa.setItem(row_position, 1, QTableWidgetItem(turnus[2] or ""))
                    self.tabela_turnusa.setItem(row_position, 2, QTableWidgetItem(vozovi_str))
                    self.tabela_turnusa.setItem(row_position, 3, QTableWidgetItem(sekcija_val))

                    # ✅ DODAJ DUGMAD U KOLONU "AKCIJE"
                    akcije_widget = QWidget()
                    akcije_layout = QHBoxLayout()
                    akcije_layout.setContentsMargins(4, 2, 4, 2)  # Manji margine
                    akcije_layout.setSpacing(4)

                    btn_uredi = QPushButton("Uredi")
                    btn_uredi.setFixedWidth(60)
                    btn_uredi.clicked.connect(lambda _, t=turnus: self.uredi_turnus(t))

                    btn_obrisi = QPushButton("Obriši")
                    btn_obrisi.setFixedWidth(60)
                    btn_obrisi.clicked.connect(lambda _, t=turnus: self.obrisi_turnus(t))

                    akcije_layout.addWidget(btn_uredi)
                    akcije_layout.addWidget(btn_obrisi)
                    akcije_widget.setLayout(akcije_layout)  # ✅ KLJUČNO: Postavi layout!

                    self.tabela_turnusa.setCellWidget(row_position, 4, akcije_widget)

    def uredi_turnus(self, turnus):
        # Dobavi voze za ovaj turnus
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT v.broj_voza
            FROM turnus_vozovi tv
            JOIN vozovi v ON tv.broj_voza = v.broj_voza
            WHERE tv.turnus_id = ?
            ORDER BY tv.redosled
        """, (turnus[0],))
        vozovi = [v[0] for v in cursor.fetchall()]
        vozovi_str = ", ".join(vozovi)

        conn.close()

        # Postavi vrednosti u formu
        self.naziv_turnusa_input.setText(turnus[1])
        self.opis_turnusa_input.setText(turnus[2] or "")
        self.vozovi_input.setText(vozovi_str)
        self.trenutni_turnus_za_izmenu = turnus[0]

        # Promeni dugmad
        self.btn_proveri.setText("Proveri i sačuvaj turnus")
        self.btn_proveri.clicked.disconnect()
        self.btn_proveri.clicked.connect(self.proveri_i_sacuvaj_izmene)

        # Dodaj dugme za odustajanje
        if not hasattr(self, 'btn_odustani'):
            self.btn_odustani = QPushButton("Odustani")
            self.btn_odustani.clicked.connect(self.odustani_od_uredjivanja_turnusa)
            self.layout().addWidget(self.btn_odustani)

    def sacuvaj_izmene_turnusa(self, turnus_id):
        # Preuzmi podatke
        naziv = self.naziv_turnusa_input.text().strip()
        opis = self.opis_turnusa_input.text().strip()
        vozovi_text = self.vozovi_input.text().strip()

        # Proveri da li je unet naziv
        if not naziv:
            QMessageBox.critical(self, "Greška", "Naziv turnusa je obavezan!")
            return

        # Parsiraj vozove
        vozovi = [v.strip() for v in vozovi_text.split(",") if v.strip()]
        if not vozovi:
            QMessageBox.critical(self, "Greška", "Morate uneti bar jedan voz!")
            return

        # Sačuvaj izmene u bazu
        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Ažuriraj turnus
            cursor.execute("UPDATE turnusi SET naziv = ?, opis = ? WHERE id = ?", (naziv, opis, turnus_id))

            # Obriši postojeće veze
            cursor.execute("DELETE FROM turnus_vozovi WHERE turnus_id = ?", (turnus_id,))

            # Dodaj nove veze
            for redosled, broj_voza in enumerate(vozovi, 1):
                cursor.execute("""
                    INSERT INTO turnus_vozovi (turnus_id, broj_voza, redosled)
                    VALUES (?, ?, ?)
                """, (turnus_id, broj_voza, redosled))

            conn.commit()

            QMessageBox.information(self, "Uspeh", f"Turnus '{naziv}' uspešno ažuriran!")

            # Resetuj formu
            self.naziv_turnusa_input.clear()
            self.opis_turnusa_input.clear()
            self.vozovi_input.clear()
            self.status_label.setText("")

            # Vrati dugme na "Proveri turnus"
            self.btn_proveri.setText("Proveri turnus")
            self.btn_proveri.clicked.disconnect()
            self.btn_proveri.clicked.connect(self.proveri_turnus)

            # Ukloni dugme za odustajanje
            if hasattr(self, 'btn_odustani') and self.btn_odustani.parent():
                self.btn_odustani.deleteLater()
                del self.btn_odustani

            # Ažuriraj prikaz
            self.ucitaj_turnuse()

            # Resetuj trenutni turnus za izmenu
            self.trenutni_turnus_za_izmenu = None

        finally:
            if conn:
                conn.close()

    def obrisi_turnus(self, turnus):
        potvrda = QMessageBox.question(self, "Potvrda", f"Obriši turnus '{turnus[1]}'?")
        if potvrda == QMessageBox.StandardButton.Yes:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM turnus_vozovi WHERE turnus_id = ?", (turnus[0],))
            cursor.execute("DELETE FROM turnusi WHERE id = ?", (turnus[0],))
            conn.commit()
            conn.close()

            QMessageBox.information(self, "Obrađeno", f"Turnus '{turnus[1]}' obrisan.")
            self.ucitaj_turnuse()

    def proveri_i_sacuvaj_izmene(self):
        # Prvo proveri turnus
        naziv = self.naziv_turnusa_input.text().strip()
        opis = self.opis_turnusa_input.text().strip()
        vozovi_text = self.vozovi_input.text().strip()

        # Proveri da li je unet naziv
        if not naziv:
            self.status_label.setText("Greška: Naziv turnusa je obavezan!")
            self.status_label.setStyleSheet("padding: 10px; background-color: #ffcccc; border-radius: 5px;")
            return

        # Proveri da li je unet bar jedan voz
        if not vozovi_text:
            self.status_label.setText("Greška: Morate uneti bar jedan voz!")
            self.status_label.setStyleSheet("padding: 10px; background-color: #ffcccc; border-radius: 5px;")
            return

        # Parsiraj vozove
        vozovi = [v.strip() for v in vozovi_text.split(",") if v.strip()]

        # Proveri da li vozovi postoje i da li je redosled ispravan
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Dobavi informacije o svim vozovima
        vozovi_info = {}
        for broj in vozovi:
            cursor.execute("""
                SELECT pocetna_stanica, krajnja_stanica, sat_polaska, minut_polaska, sat_dolaska, minut_dolaska
                FROM vozovi WHERE broj_voza = ?
            """, (broj,))
            info = cursor.fetchone()
            if info:
                vozovi_info[broj] = {
                    "pocetna": info[0],
                    "krajnja": info[1],
                    "polazak": (info[2], info[3]),
                    "dolazak": (info[4], info[5])
                }
            else:
                self.status_label.setText(f"Greška: Voz {broj} ne postoji u bazi!")
                self.status_label.setStyleSheet("padding: 10px; background-color: #ffcccc; border-radius: 5px;")
                conn.close()
                return

        # Proveri redosled
        greske = []
        for i in range(len(vozovi) - 1):
            broj_trenutni = vozovi[i]
            broj_sledeci = vozovi[i + 1]

            # Proveri da li postoji informacija o vozu
            if broj_trenutni not in vozovi_info or broj_sledeci not in vozovi_info:
                continue

            voz_trenutni = vozovi_info[broj_trenutni]
            voz_sledeci = vozovi_info[broj_sledeci]

            # Proveri stanicu
            if voz_trenutni["krajnja"] != voz_sledeci["pocetna"]:
                greske.append(
                    f"Voz {broj_trenutni} i {broj_sledeci}: Stanica {voz_trenutni['krajnja']} ≠ {voz_sledeci['pocetna']}")

            # Proveri vreme
            dolazak_trenutni = voz_trenutni["dolazak"][0] * 60 + voz_trenutni["dolazak"][1]
            polazak_sledeci = voz_sledeci["polazak"][0] * 60 + voz_sledeci["polazak"][1]

            if dolazak_trenutni >= polazak_sledeci:
                greske.append(
                    f"Voz {broj_trenutni} i {broj_sledeci}: Vreme dolaska {dolazak_trenutni // 60}:{dolazak_trenutni % 60} ≥ {polazak_sledeci // 60}:{polazak_sledeci % 60}")

        # Ako ima grešaka, prikaži ih
        if greske:
            poruka = "Greške u redosledu:\n" + "\n".join(greske)
            self.status_label.setText(poruka)
            self.status_label.setStyleSheet("padding: 10px; background-color: #ffcccc; border-radius: 5px;")
            return

        # Ako nema grešaka, sačuvaj izmene
        self.sacuvaj_izmene_turnusa(self.trenutni_turnus_za_izmenu)

    def odustani_od_uredjivanja_turnusa(self):
        # Resetuj formu
        self.naziv_turnusa_input.clear()
        self.opis_turnusa_input.clear()
        self.vozovi_input.clear()
        self.status_label.setText("")

        # Vrati dugme na "Proveri turnus"
        self.btn_proveri.setText("Proveri turnus")
        self.btn_proveri.clicked.disconnect()
        self.btn_proveri.clicked.connect(self.proveri_turnus)

        # Ukloni dugme za odustajanje
        if hasattr(self, 'btn_odustani') and self.btn_odustani.parent():
            self.btn_odustani.deleteLater()
            del self.btn_odustani

        # Resetuj trenutni turnus za izmenu
        self.trenutni_turnus_za_izmenu = None

    def proveri_turnus(self):
        # Resetuj status i dugme
        self.status_label.setText("")
        self.status_label.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")

        # Preuzmi podatke
        naziv = self.naziv_turnusa_input.text().strip()
        opis = self.opis_turnusa_input.text().strip()
        vozovi_text = self.vozovi_input.text().strip()
        sekcija = self.sekcija_voza_input.text().strip()

        # ✅ OBAVEZNA POLJA (sva osim "Opis")
        obavezna_polja = [
            ("Naziv turnusa", naziv),
            ("Vozovi u turnusu", vozovi_text),
            ("Sekcija za vuču vozova", sekcija)
        ]

        # Proveri da li su sva obavezna polja popunjena
        nedostajuci = []
        for naziv_p, vrednost in obavezna_polja:
            if not vrednost:
                nedostajuci.append(naziv_p)

        if nedostajuci:
            poruka = "Neophodno je popuniti sledeća polja:\n- " + "\n- ".join(nedostajuci)
            self.status_label.setText(poruka)
            self.status_label.setStyleSheet("padding: 10px; background-color: #ffcccc; border-radius: 5px;")
            return

        # Parsiraj vozove
        vozovi = [v.strip() for v in vozovi_text.split(",") if v.strip()]

        # Proveri da li je unet bar jedan voz
        if not vozovi:
            self.status_label.setText("Greška: Morate uneti bar jedan voz!")
            self.status_label.setStyleSheet("padding: 10px; background-color: #ffcccc; border-radius: 5px;")
            return

        # Proveri da li vozovi postoje i da li je redosled ispravan
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Dobavi informacije o svim vozovima
        vozovi_info = {}
        for broj in vozovi:
            cursor.execute("""
                SELECT pocetna_stanica, krajnja_stanica, sat_polaska, minut_polaska, sat_dolaska, minut_dolaska
                FROM vozovi WHERE broj_voza = ?
            """, (broj,))
            info = cursor.fetchone()
            if info:
                vozovi_info[broj] = {
                    "pocetna": info[0],
                    "krajnja": info[1],
                    "polazak": (info[2], info[3]),
                    "dolazak": (info[4], info[5])
                }
            else:
                self.status_label.setText(f"Greška: Voz {broj} ne postoji u bazi!")
                self.status_label.setStyleSheet("padding: 10px; background-color: #ffcccc; border-radius: 5px;")
                conn.close()
                return

        # Proveri redosled
        greske = []
        for i in range(len(vozovi) - 1):
            broj_trenutni = vozovi[i]
            broj_sledeci = vozovi[i + 1]

            # Proveri da li postoji informacija o vozu
            if broj_trenutni not in vozovi_info or broj_sledeci not in vozovi_info:
                continue

            voz_trenutni = vozovi_info[broj_trenutni]
            voz_sledeci = vozovi_info[broj_sledeci]

            # Proveri stanicu
            if voz_trenutni["krajnja"] != voz_sledeci["pocetna"]:
                greske.append(
                    f"Voz {broj_trenutni} i {broj_sledeci}: Stanica {voz_trenutni['krajnja']} ≠ {voz_sledeci['pocetna']}")

            # Proveri vreme
            dolazak_trenutni = voz_trenutni["dolazak"][0] * 60 + voz_trenutni["dolazak"][1]
            polazak_sledeci = voz_sledeci["polazak"][0] * 60 + voz_sledeci["polazak"][1]

            if dolazak_trenutni >= polazak_sledeci:
                greske.append(
                    f"Voz {broj_trenutni} i {broj_sledeci}: Vreme dolaska {dolazak_trenutni // 60}:{dolazak_trenutni % 60} ≥ {polazak_sledeci // 60}:{polazak_sledeci % 60}")

        # Ako ima grešaka, prikaži ih
        if greske:
            poruka = "Greške u redosledu:\n" + "\n".join(greske)
            self.status_label.setText(poruka)
            self.status_label.setStyleSheet("padding: 10px; background-color: #ffcccc; border-radius: 5px;")
            return

        # Ako nema grešaka → aktiviraj "Sačuvaj ažuriran turnus"
        self.status_label.setText(f"Turnus '{naziv}' je ispravan! Možete ga sačuvati.")
        self.status_label.setStyleSheet("padding: 10px; background-color: #ddffdd; border-radius: 5px;")

        # Zameni dugme
        self.btn_proveri.setText("Sačuvaj ažuriran turnus")
        self.btn_proveri.clicked.disconnect()
        self.btn_proveri.clicked.connect(self.sacuvaj_izmene_turnusa)

        # Prikazi dugme "Odustani"
        self.btn_odustani.setVisible(True)

        # Zapamti ID ako je uređivanje
        self.trenutni_turnus_za_izmenu = getattr(self, 'trenutni_turnus_za_izmenu', None)

        conn.close()

    def sacuvaj_izmene_turnusa(self):
        # Preuzmi podatke
        naziv = self.naziv_turnusa_input.text().strip()
        opis = self.opis_turnusa_input.text().strip()
        vozovi_text = self.vozovi_input.text().strip()
        sekcija = self.sekcija_voza_input.text().strip()

        # Proveri da li je unet naziv
        if not naziv:
            QMessageBox.critical(self, "Greška", "Naziv turnusa je obavezan!")
            return

        # Parsiraj vozove
        vozovi = [v.strip() for v in vozovi_text.split(",") if v.strip()]
        if not vozovi:
            QMessageBox.critical(self, "Greška", "Morate uneti bar jedan voz!")
            return

        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            if self.trenutni_turnus_za_izmenu is not None:
                # AŽURIRANJE POSTOJEĆEG TURNUSA
                cursor.execute("UPDATE turnusi SET naziv = ?, opis = ?, sekcija = ? WHERE id = ?",
                               (naziv, opis, sekcija, self.trenutni_turnus_za_izmenu))

                # Obriši postojeće veze
                cursor.execute("DELETE FROM turnus_vozovi WHERE turnus_id = ?", (self.trenutni_turnus_za_izmenu,))

                # Dodaj nove voze
                for redosled, broj_voza in enumerate(vozovi, 1):
                    cursor.execute("""
                        INSERT INTO turnus_vozovi (turnus_id, broj_voza, redosled)
                        VALUES (?, ?, ?)
                    """, (self.trenutni_turnus_za_izmenu, broj_voza, redosled))

                poruka = f"Turnus '{naziv}' uspešno ažuriran!"
            else:
                # DODAVANJE NOVOG TURNUSA
                cursor.execute("SELECT id FROM turnusi WHERE naziv = ?", (naziv,))
                postoji = cursor.fetchone()
                if postoji:
                    QMessageBox.critical(self, "Greška", f"Turnus '{naziv}' već postoji!")
                    return

                cursor.execute("INSERT INTO turnusi (naziv, opis, sekcija) VALUES (?, ?, ?)",
                               (naziv, opis, sekcija))

                # Dobavi ID novog turnusa
                cursor.execute("SELECT id FROM turnusi WHERE naziv = ?", (naziv,))
                turnus_id = cursor.fetchone()[0]

                # Dodaj voze
                for redosled, broj_voza in enumerate(vozovi, 1):
                    cursor.execute("""
                        INSERT INTO turnus_vozovi (turnus_id, broj_voza, redosled)
                        VALUES (?, ?, ?)
                    """, (turnus_id, broj_voza, redosled))

                poruka = f"Turnus '{naziv}' uspešno dodat!"

            conn.commit()

            # ✅ KLJUČNO: PRVO OSVEŽI FILTERE!
            self.populate_nazivi_filter()
            self.populate_sekcije_turnusi_filter()

            # ✅ ONDA OSVEŽI TABELU - sad filtri znaju za novi turnus
            self.ucitaj_turnuse()

            QMessageBox.information(self, "Uspeh", poruka)

            # Resetuj formu
            self.naziv_turnusa_input.clear()
            self.opis_turnusa_input.clear()
            self.vozovi_input.clear()
            self.sekcija_voza_input.clear()
            self.status_label.setText("")
            self.btn_proveri.setText("Proveri turnus")
            self.btn_proveri.clicked.disconnect()
            self.btn_proveri.clicked.connect(self.proveri_turnus)
            self.btn_odustani.setVisible(False)
            self.trenutni_turnus_za_izmenu = None

        except Exception as e:
            QMessageBox.critical(self, "Greška", f"Greška pri čuvanju: {e}")
        finally:
            if conn:
                conn.close()

    def odustani_od_uredjivanja_turnusa(self):
        # Resetuj formu
        self.naziv_turnusa_input.clear()
        self.opis_turnusa_input.clear()
        self.vozovi_input.clear()
        self.sekcija_voza_input.clear()
        self.status_label.setText("")

        # Vrati dugme na "Proveri turnus"
        self.btn_proveri.setText("Proveri turnus")
        self.btn_proveri.clicked.disconnect()
        self.btn_proveri.clicked.connect(self.proveri_turnus)

        # Skloni dugme "Odustani"
        self.btn_odustani.setVisible(False)

        # Resetuj trenutni turnus
        self.trenutni_turnus_za_izmenu = None

    def uredi_turnus(self, turnus):
        # Dobavi voze za ovaj turnus
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT v.broj_voza
            FROM turnus_vozovi tv
            JOIN vozovi v ON tv.broj_voza = v.broj_voza
            WHERE tv.turnus_id = ?
            ORDER BY tv.redosled
        """, (turnus[0],))
        vozovi = [v[0] for v in cursor.fetchall()]
        vozovi_str = ", ".join(vozovi)

        # Dobavi sekciju
        cursor.execute("SELECT sekcija FROM turnusi WHERE id = ?", (turnus[0],))
        sekcija_val = cursor.fetchone()[0] or ""

        conn.close()

        # Postavi vrednosti u formu
        self.naziv_turnusa_input.setText(turnus[1])
        self.opis_turnusa_input.setText(turnus[2] or "")
        self.vozovi_input.setText(vozovi_str)
        self.sekcija_voza_input.setText(sekcija_val)

        # Postavi trenutni turnus za izmenu
        self.trenutni_turnus_za_izmenu = turnus[0]

        # Promeni dugme i prikaži "Odustani"
        self.btn_proveri.setText("Proveri turnus")
        self.btn_proveri.clicked.disconnect()
        self.btn_proveri.clicked.connect(self.proveri_turnus)
        self.btn_odustani.setVisible(True)

    def populate_nazivi_filter(self):
        # Obriši sve osim "Označi sve"
        for i in reversed(range(self.naziv_filter_layout.count())):
            item = self.naziv_filter_layout.itemAt(i)
            if item and item.widget() != self.all_nazivi_cb:
                widget = item.widget()
                if widget:
                    widget.deleteLater()

        # Učitaj nazive iz baze
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT naziv FROM turnusi WHERE naziv IS NOT NULL ORDER BY naziv")
        nazivi = [str(row[0]) for row in cursor.fetchall() if row[0] is not None]
        conn.close()

        # Dodaj checkboxove
        for n in nazivi:
            cb = QCheckBox(n)
            cb.setChecked(True)
            cb.stateChanged.connect(self.ucitaj_turnuse)
            self.naziv_filter_layout.addWidget(cb)

    def populate_sekcije_turnusi_filter(self):
        # Obriši sve osim "Označi sve"
        for i in reversed(range(self.sekcije_turnusi_filter_layout.count())):
            item = self.sekcije_turnusi_filter_layout.itemAt(i)
            if item and item.widget() != self.all_sekcije_turnusi_cb:
                widget = item.widget()
                if widget:
                    widget.deleteLater()

        # Učitaj sekcije iz baze
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT sekcija FROM turnusi WHERE sekcija IS NOT NULL ORDER BY sekcija")
        sekcije = [str(row[0]) for row in cursor.fetchall() if row[0] is not None]
        conn.close()

        # Dodaj checkboxove
        for s in sekcije:
            cb = QCheckBox(s)
            cb.setChecked(True)
            cb.stateChanged.connect(self.ucitaj_turnuse)
            self.sekcije_turnusi_filter_layout.addWidget(cb)

    def on_all_nazivi_toggled(self, state):
        is_checked = state == Qt.CheckState.Checked.value
        for i in range(self.naziv_filter_layout.count()):
            widget = self.naziv_filter_layout.itemAt(i).widget()
            if isinstance(widget, QCheckBox) and widget != self.all_nazivi_cb:
                widget.blockSignals(True)
                widget.setChecked(is_checked)
                widget.blockSignals(False)
        self.ucitaj_turnuse()

    def on_all_sekcije_turnusi_toggled(self, state):
        is_checked = state == Qt.CheckState.Checked.value
        for i in range(self.sekcije_turnusi_filter_layout.count()):
            widget = self.sekcije_turnusi_filter_layout.itemAt(i).widget()
            if isinstance(widget, QCheckBox) and widget != self.all_sekcije_turnusi_cb:
                widget.blockSignals(True)
                widget.setChecked(is_checked)
                widget.blockSignals(False)
        self.ucitaj_turnuse()

    def create_tab_grafik(self):
        widget = QWidget()
        layout = QVBoxLayout()

        naslov = QLabel("Grafički prikaz turnusa")
        naslov.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(naslov)

        # Filteri za izbor turnusa
        filter_layout = QHBoxLayout()

        self.grafik_filter_layout = QVBoxLayout()
        self.grafik_filter_layout.addWidget(QLabel("Izaberite turnuse za prikaz:"))

        filter_scroll = QScrollArea()
        filter_scroll.setWidgetResizable(True)
        filter_content = QWidget()
        filter_content.setLayout(self.grafik_filter_layout)
        filter_scroll.setWidget(filter_content)

        filter_layout.addWidget(filter_scroll)
        layout.addLayout(filter_layout)

        # QGraphicsView za crtanje grafika
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setFixedHeight(400)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        layout.addWidget(self.view)

        # Dugme za osvežavanje grafika
        self.btn_azuriraj_grafik = QPushButton("Ažuriraj grafik")
        self.btn_azuriraj_grafik.clicked.connect(self.crtaj_grafik)
        layout.addWidget(self.btn_azuriraj_grafik)

        widget.setLayout(layout)
        return widget

    def populate_grafik_filter(self):
        # Obriši sve checkboxove
        for i in reversed(range(self.grafik_filter_layout.count())):
            item = self.grafik_filter_layout.itemAt(i)
            if item and isinstance(item.widget(), QCheckBox):
                item.widget().deleteLater()

        # Učitaj sve turnuse iz baze
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, naziv FROM turnusi ORDER BY naziv")
        turnusi = cursor.fetchall()
        conn.close()

        # Dodaj checkboxove
        for turnus in turnusi:
            cb = QCheckBox(f"{turnus[1]}")
            cb.setChecked(True)
            cb.turnus_id = turnus[0]  # Dodaj ID za kasniju upotrebu
            self.grafik_filter_layout.addWidget(cb)

    def crtaj_grafik(self):
        self.scene.clear()

        # Parametri
        sirina_sata = 60
        ukupna_sirina = 24 * sirina_sata  # 1440 px
        visina_turnusa = 120
        y_pocetak = 50

        # --- 1. GLAVNA VREMENSKA OSA ---

        # ✅ HORIZONTALNA LINIJA [0] od 00 do 24
        self.scene.addLine(0, 0, ukupna_sirina, 0, QPen(Qt.GlobalColor.black, 1.2))  # y=0

        # Sada crtamo vertikalne podelice i brojeve sati
        for h in range(25):
            x = h * sirina_sata
            # Kratka vertikalna podelica: dužina ~9px (≈3mm)
            self.scene.addLine(x, 0, x, 9, QPen(Qt.GlobalColor.black, 0.8))

            # Broj sata iznad podelice
            sat_tekst = f"{h % 24:02d}"
            text = self.scene.addText(sat_tekst)
            text.setFont(QFont("Arial", 8))
            text.setPos(x - 10, -30)

        # --- 1. GLAVNA VREMENSKA OSA ---
        for h in range(25):  # 00 do 24
            x = h * sirina_sata
            # Kratka vertikalna podelica: 9px ≈ 3mm
            # Kratka vertikalna podelica: 9px ≈ 3mm
            self.scene.addLine(x, 0, x, 9, QPen(Qt.GlobalColor.black, 0.8))

            # Broj sata iznad podelice (00, 01, ..., 23, 00)
            sat_tekst = f"{h % 24:02d}"  # Uvek dve cifre: 00, 01...
            text = self.scene.addText(sat_tekst)
            text.setFont(QFont("Arial", 8))  # Mali font za čitljivost
            text.setPos(x - 10, -30)  # Malo više gore od prethodnog

        # Prikupi selektovane turnuse
        selektovani_turnusi = []
        for i in range(self.grafik_filter_layout.count()):
            widget = self.grafik_filter_layout.itemAt(i).widget()
            if isinstance(widget, QCheckBox) and widget.isChecked():
                selektovani_turnusi.append(widget.turnus_id)

        if not selektovani_turnusi:
            return

        # Učitaj podatke
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        placeholders = ','.join('?' * len(selektovani_turnusi))
        cursor.execute(f"""
            SELECT tv.turnus_id, tv.redosled, tv.broj_voza, 
                   v.pocetna_stanica, v.krajnja_stanica,
                   v.sat_polaska, v.minut_polaska, v.sat_dolaska, v.minut_dolaska, v.status
            FROM turnus_vozovi tv
            JOIN vozovi v ON tv.broj_voza = v.broj_voza
            WHERE tv.turnus_id IN ({placeholders})
            ORDER BY tv.turnus_id, tv.redosled
        """, selektovani_turnusi)
        podaci = cursor.fetchall()
        conn.close()

        y_trenutni = y_pocetak
        trenutni_turnus_id = None
        vozovi_u_turnusu = []

        for red in podaci:
            turnus_id, redosled, broj_voza, pocetna, krajnja, sat_p, min_p, sat_d, min_d, status = red

            if turnus_id != trenutni_turnus_id and vozovi_u_turnusu:
                self._crtaj_jedan_turnus(
                    vozovi_u_turnusu, y_trenutni, sirina_sata, visina_turnusa
                )
                y_trenutni += visina_turnusa
                vozovi_u_turnusu = []

            trenutni_turnus_id = turnus_id
            vozovi_u_turnusu.append({
                'broj': broj_voza,
                'pocetna': pocetna,
                'krajnja': krajnja,
                'sat_p': sat_p,
                'min_p': min_p,
                'sat_d': sat_d,
                'min_d': min_d,
                'status': status
            })

        # Nacrtaj poslednji turnus
        if vozovi_u_turnusu:
            self._crtaj_jedan_turnus(vozovi_u_turnusu, y_trenutni, sirina_sata, visina_turnusa)

        # Postavi granice scene
        max_visina = y_trenutni + visina_turnusa + 50
        self.scene.setSceneRect(0, 0, ukupna_sirina, max_visina)

    def _crtaj_jedan_turnus(self, vozovi, y, sirina_sata, visina_turnusa):
        # Koordinate
        gornja_linija_y = y + 30
        donja_linija_y = gornja_linija_y + 20  # Razmak ~20px ≈ 5mm
        tekst_gore_y = gornja_linija_y - 25
        tekst_dole_y = donja_linija_y + 10
        broj_vozila_x = 10
        broj_vozila_y = gornja_linija_y - 5

        # Broj vucnog vozila (1)
        self.scene.addText("1").setPos(broj_vozila_x, broj_vozila_y)

        # Gornja i donja linija puta turnusa
        self.scene.addLine(0, gornja_linija_y, 1440, gornja_linija_y, QPen(Qt.GlobalColor.black, 1.2))
        self.scene.addLine(0, donja_linija_y, 1440, donja_linija_y, QPen(Qt.GlobalColor.black, 1.2))

        # Dodaj kratke vertikalne podelice na [3] i [5]
        for h in range(25):
            x = h * sirina_sata
            # Na [3]: 6px (3mm) ukupno, centrirano
            self.scene.addLine(x, gornja_linija_y - 3, x, gornja_linija_y + 3, QPen(Qt.GlobalColor.black, 0.8))
            # Na [5]: isto
            self.scene.addLine(x, donja_linija_y - 3, x, donja_linija_y + 3, QPen(Qt.GlobalColor.black, 0.8))

        # Stilovi linija
        pen = QPen(Qt.GlobalColor.black, 2)
        style_map = {
            'R': Qt.PenStyle.SolidLine,
            'L': Qt.PenStyle.DashLine,
            'RE': Qt.PenStyle.DotLine,
            'S': Qt.PenStyle.DashDotLine,
            'V': Qt.PenStyle.DashDotDotLine
        }

        for i, voz in enumerate(vozovi):
            x_p = (voz['sat_p'] * 60 + voz['min_p']) / 60 * sirina_sata
            x_d = (voz['sat_d'] * 60 + voz['min_d']) / 60 * sirina_sata

            # ✅ LINIJA VOŽNJE: između [3] i [5], ne preko [3]
            linija_y = gornja_linija_y + 10  # Tačno u sredini prostora
            pen.setStyle(style_map.get(voz['status'], Qt.PenStyle.SolidLine))
            self.scene.addLine(x_p, linija_y, x_d, linija_y, pen)

            # Broj voza (centrirano iznad [3])
            text_broj = self.scene.addText(voz['broj'])
            text_broj.setPos((x_p + x_d) / 2 - 20, tekst_gore_y)

            # Minuti (ispod [5])
            text_min_p = self.scene.addText(f"{voz['min_p']:02}")
            text_min_d = self.scene.addText(f"{voz['min_d']:02}")
            text_min_p.setPos(x_p - 10, tekst_dole_y)
            text_min_d.setPos(x_d - 10, tekst_dole_y)

            # Stanice
            if i == 0:  # Prvi voz
                text_pocetna = self.scene.addText(voz['pocetna'])
                text_pocetna.setPos(x_p - 20, tekst_gore_y - 15)
            if i == len(vozovi) - 1:  # Poslednji voz
                text_krajnja = self.scene.addText(voz['krajnja'])
                text_krajnja.setPos(x_d - 20, tekst_gore_y - 15)
            else:  # Srednji vozi
                if i < len(vozovi) - 1:
                    sledeci = vozovi[i + 1]
                    x_sledeci_p = (sledeci['sat_p'] * 60 + sledeci['min_p']) / 60 * sirina_sata
                    x_sredina = (x_d + x_sledeci_p) / 2
                    text_srednja = self.scene.addText(voz['krajnja'])
                    text_srednja.setPos(x_sredina - 20, tekst_gore_y - 15)


if __name__ == "__main__":
    app = QApplication([])
    window = SimpleApp()
    window.show()
    app.exec()