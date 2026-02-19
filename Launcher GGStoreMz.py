import customtkinter as ctk
import os
import json
import subprocess
import winreg
import shutil
import tkinter.messagebox

# Configuración visual
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

CONFIG_DIR = os.path.join(os.getenv('APPDATA'), 'GGStoreMz')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'steam_config.json')

class SteamLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SSDAL By GGStoreMz")
        self.geometry("380x288")
        self.resizable(False, False)
        
        # Obtener ruta de Steam del registro
        steam_path = self.get_steam_path()
        if steam_path:
            ico_path = os.path.join(steam_path, 'steam.ico')
            if os.path.exists(ico_path):
                self.iconbitmap(ico_path)

        self.config = self.cargar_config()

        # UI
        self.label = ctk.CTkLabel(self, text="Selector de Instancias Steam", font=("Roboto", 22, "bold"))
        self.label.pack(pady=20)

        # Botón Cuenta 1 (Oficial)
        self.btn1 = ctk.CTkButton(self, text=f"{self.config['cuenta1']['label']}", 
                                   command=lambda: self.lanzar("1"),
                                   height=50, width=280, font=("Roboto", 15))
        self.btn1.pack(pady=10)

        # Botón Cuenta 2 (Lab/LUA)
        self.btn2 = ctk.CTkButton(self, text=f"{self.config['cuenta2']['label']}", 
                                   command=lambda: self.lanzar("2"),
                                   height=50, width=280, fg_color="#1f538d", font=("Roboto", 15))
        self.btn2.pack(pady=10)

        self.status_label = ctk.CTkLabel(self, text="Estado: Listo", text_color="gray")
        self.status_label.pack(pady=5)

        self.btn_edit = ctk.CTkButton(self, text="Configurar IDs de Usuario", command=self.pedir_usuarios,
                                       width=120, height=25, fg_color="transparent", text_color="gray")
        self.btn_edit.pack(pady=10)

    def get_steam_path(self):
        try:
            reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", 0, winreg.KEY_READ)
            steam_path, _ = winreg.QueryValueEx(reg_key, "SteamPath")
            winreg.CloseKey(reg_key)
            return steam_path
        except:
            return None

    def cargar_config(self):
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        return {
            "cuenta1": {"label": "SteamOficial", "path": r"C:\Program Files (x86)\Steam", "user": ""},
            "cuenta2": {"label": "GGStoreMzGames", "path": r"C:\Program Files (x86)\GGStoreMzGames", "user": ""}
        }

    def pedir_usuarios(self):
        u1 = ctk.CTkInputDialog(text="ID Usuario Cuenta Principal de Steam:", title="Setup").get_input()
        u2 = ctk.CTkInputDialog(text="ID Usuario Cuenta Secundaria para GGStoreMz:", title="Setup").get_input()
        if u1 and u2:
            self.config["cuenta1"]["user"] = u1
            self.config["cuenta2"]["user"] = u2
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f)

    def limpiar_evidencia(self, ruta_steam):
        """Elimina telemetría y volcados de memoria para evitar rastreo cruzado."""
        carpetas_criticas = ["logs", "dumps", "appcache"]
        for carpeta in carpetas_criticas:
            path = os.path.join(ruta_steam, carpeta)
            if os.path.exists(path):
                try:
                    shutil.rmtree(path)
                    os.makedirs(path)
                except:
                    pass # Evita errores si un archivo está bloqueado temporalmente

    def lanzar(self, opcion):
        datos = self.config["cuenta1"] if opcion == "1" else self.config["cuenta2"]

        if not datos["user"]:
            self.status_label.configure(text="Error: Configura los IDs primero", text_color="red")
            return

        self.status_label.configure(text="Ejecutando limpieza y cambio...", text_color="yellow")
        self.update()

        # 1. Kill Process (Sanitización de RAM)
        os.system("taskkill /f /im steam.exe >nul 2>&1")

        # 2. Modificación de Registro (Redirección de Identidad)
        try:
            reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(reg_key, "AutoLoginUser", 0, winreg.REG_SZ, datos["user"])
            winreg.SetValueEx(reg_key, "RememberPassword", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(reg_key)
        except Exception as e:
            print(f"Error Registro: {e}")

        # 3. Anti-Forensics (Limpieza de carpetas de telemetría)
        self.limpiar_evidencia(datos["path"])

        # 4. Ejecución Aislada
        exe_path = os.path.join(datos["path"], "steam.exe")
        if os.path.exists(exe_path):
            # Usamos -login para forzar la lectura del registro actualizado
            subprocess.Popen([exe_path, "-login"])
            self.destroy()
        else:
            self.status_label.configure(text="Error: No se halló steam.exe", text_color="red")

if __name__ == "__main__":
    app = SteamLauncher()
    app.mainloop()