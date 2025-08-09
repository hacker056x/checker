import sys
import re
import requests
from datetime import datetime
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QStackedLayout, QProgressBar, QMessageBox
)
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPalette, QColor, QBrush


def formatear_fecha(timestamp):
    try:
        dt = datetime.fromtimestamp(int(timestamp))
        return dt.strftime("%d/%m/%Y %H:%M:%S")
    except:
        return "Fecha inválida"


class VerificadorThread(QThread):
    resultado_signal = pyqtSignal(str)

    def __init__(self, host, username, password):
        super().__init__()
        self.host = host
        self.username = username
        self.password = password

    def contar_items(self, accion):
        try:
            url = f"http://{self.host}/player_api.php?username={self.username}&password={self.password}&action={accion}"
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            data = r.json()
            if isinstance(data, list):
                return len(data)
            if isinstance(data, dict):
                if data.get("error"):
                    return 0
                return len(data.keys())
            return 0
        except:
            return 0

    def run(self):
        api_url = f"http://{self.host}/player_api.php?username={self.username}&password={self.password}"
        try:
            r = requests.get(api_url, timeout=10)
            r.raise_for_status()
            data = r.json()

            if not data.get("user_info"):
                raise Exception("Datos inválidos")

            info = data["user_info"]

            canales = self.contar_items("get_live_streams")
            peliculas = self.contar_items("get_vod_streams")
            series = self.contar_items("get_series")

            output = [
                f"✅ Estado: {info.get('status', 'Desconocido')}",
                f"👤 Usuario: {info.get('username')}",
                f"🔑 Contraseña: {self.password}",
                f"🆔 Tipo de línea: {info.get('line_type')}",
                f"🗓️ Fecha de creación: {formatear_fecha(info.get('created_at', '0'))}",
                f"⏳ Expira: {formatear_fecha(info.get('exp_date', '0'))}",
                f"📺 Conexiones activas: {info.get('active_cons', '0')}",
                f"📡 Máximo de conexiones: {info.get('max_connections', '0')}",
                f"📁 Salida permitida: {info.get('output_formats', 'N/A')}",
                f"🕒 Hora del servidor: {info.get('server_time', 'N/A')}",
                f"🌐 Servidor: http://{self.host}",
                f"🎯 Canales en vivo: {canales}",
                f"🎬 Películas: {peliculas}",
                f"📺 Series: {series}",
                f"🚀 Powered by @hacker056"
            ]
            self.resultado_signal.emit("\n".join(output))
        except requests.exceptions.RequestException as e:
            if "HTTPSConnectionPool" in str(e) or "SSL" in str(e):
                self.resultado_signal.emit("⚠️ Error SSL: Usa http en lugar de https.")
            elif "404" in str(e):
                self.resultado_signal.emit("❌ Usuario o contraseña incorrectos.")
            else:
                self.resultado_signal.emit(f"❌ Error al verificar la cuenta IPTV.\n{e}")
        except Exception:
            self.resultado_signal.emit("❌ Usuario o contraseña incorrectos.")


class IPTVChecker(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Verificador IPTV Premium by @hacker056 v3.0")
        self.setFixedSize(600, 550)
        self.setWindowIcon(QIcon("icono.ico"))

        # Fondo personalizado
        self.setAutoFillBackground(True)
        p = self.palette()
        fondo = QPixmap("fondo.png")
        p.setBrush(QPalette.Window, QBrush(fondo))
        self.setPalette(p)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        titulo = QLabel("🔍 Verificador IPTV")
        titulo.setFont(QFont("Segoe UI", 24, QFont.Bold))
        titulo.setStyleSheet("color: #00aaff;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)

        botones_modo = QHBoxLayout()
        self.boton_manual = QPushButton(" Modo Manual")
        self.boton_manual.setIcon(QIcon("icon_manual.png"))
        self.boton_url = QPushButton(" Modo M3U URL")
        self.boton_url.setIcon(QIcon("icon_m3u.png"))
        for btn in (self.boton_manual, self.boton_url):
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                background-color: #121212;
                color: #00aaff;
                font-weight: bold;
                padding: 8px 12px;
                border-radius: 8px;
            """)
        self.boton_manual.clicked.connect(lambda: self.pila.setCurrentIndex(0))
        self.boton_url.clicked.connect(lambda: self.pila.setCurrentIndex(1))
        botones_modo.addWidget(self.boton_manual)
        botones_modo.addWidget(self.boton_url)
        layout.addLayout(botones_modo)

        self.pila = QStackedLayout()

        manual = QWidget()
        layout_manual = QVBoxLayout(manual)
        self.host_input = QLineEdit()
        self.user_input = QLineEdit()
        self.pass_input = QLineEdit()
        for campo, texto in [(self.host_input, "Host (sin http/s)"), (self.user_input, "Usuario"), (self.pass_input, "Contraseña")]:
            campo.setPlaceholderText(texto)
            campo.setStyleSheet("""
                padding: 8px;
                background-color: #1e1e1e;
                color: #00aaff;
                border: 2px solid #00aaff;
                border-radius: 8px;
                font-size: 14px;
            """)
        layout_manual.addWidget(self.host_input)
        layout_manual.addWidget(self.user_input)
        layout_manual.addWidget(self.pass_input)
        self.pila.addWidget(manual)

        url_mode = QWidget()
        layout_url = QVBoxLayout(url_mode)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Pega tu URL M3U aquí")
        self.url_input.setStyleSheet("""
            padding: 8px;
            background-color: #1e1e1e;
            color: #00ff99;
            border: 2px solid #00ff99;
            border-radius: 8px;
            font-size: 14px;
        """)
        layout_url.addWidget(self.url_input)
        self.pila.addWidget(url_mode)

        layout.addLayout(self.pila)

        self.boton_verificar = QPushButton("✅ Verificar Cuenta IPTV")
        self.boton_verificar.setCursor(Qt.PointingHandCursor)
        self.boton_verificar.setStyleSheet("""
            background-color: #00cc00;
            color: white;
            font-weight: bold;
            padding: 12px;
            border-radius: 10px;
            font-size: 16px;
        """)
        self.boton_verificar.clicked.connect(self.verificar)
        layout.addWidget(self.boton_verificar)

        self.barra = QProgressBar()
        self.barra.setValue(0)
        self.barra.setStyleSheet("""
            QProgressBar {
                border: 2px solid #555;
                border-radius: 8px;
                text-align: center;
                background-color: #2c2c2c;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #00cc00;
                width: 20px;
            }
        """)
        layout.addWidget(self.barra)

        self.resultado = QTextEdit()
        self.resultado.setReadOnly(True)
        self.resultado.setStyleSheet("""
            background-color: rgba(30,30,30,0.8);
            color: #ffffff;
            font-size: 14px;
            padding: 12px;
            border-radius: 8px;
        """)
        layout.addWidget(self.resultado)

    def verificar(self):
        self.resultado.clear()
        self.boton_verificar.setEnabled(False)
        self.barra.setValue(10)

        if self.pila.currentIndex() == 0:
            host = self.host_input.text().strip().replace("http://", "").replace("https://", "").rstrip("/")
            if host.startswith("https"):
                self.resultado.setText("⚠️ Quita la 's' del http (usa solo http://)")
                self.boton_verificar.setEnabled(True)
                return
            username = self.user_input.text().strip()
            password = self.pass_input.text().strip()
            if not host or not username or not password:
                self.resultado.setText("⚠️ Todos los campos son obligatorios.")
                self.boton_verificar.setEnabled(True)
                return
        else:
            url = self.url_input.text().strip()
            match = re.search(r"(http[s]?://[^/]+)/get\.php\?username=([^&]+)&password=([^&]+)", url)
            if not match:
                self.resultado.setText("⚠️ URL M3U inválida.")
                self.boton_verificar.setEnabled(True)
                return
            if url.startswith("https"):
                self.resultado.setText("⚠️ Quita la 's' del http (usa solo http://)")
                self.boton_verificar.setEnabled(True)
                return
            host = match.group(1).replace("https://", "").replace("http://", "")
            username = match.group(2)
            password = match.group(3)

        self.hilo = VerificadorThread(host, username, password)
        self.hilo.resultado_signal.connect(self.mostrar_resultado)
        self.hilo.start()
        self.barra.setValue(50)

    def mostrar_resultado(self, texto):
        self.resultado.setText(texto)
        self.barra.setValue(100)
        self.boton_verificar.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = IPTVChecker()
    ventana.show()
    sys.exit(app.exec_())
