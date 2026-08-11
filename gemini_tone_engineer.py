import io
import json
import os
import re
import sys
import time
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
import mido

KEY_FILE = ".gemini_key"
TARGET_MODEL = "gemini-3.6-flash"

# CORREZIONE HEADER HARDWARE PER EFFETTI MISCATEGORIZZATI
KNOWN_HEADER_CORRECTIONS = {
    "BASSDRIVE": [0x18, 0x21, 0x01, 0x00, 0x06],  # Categoria 3 Distortion
    "BASS_DRIVE": [0x18, 0x21, 0x01, 0x00, 0x06],
    "Z_SYN": [0x00, 0x21, 0x01, 0x00, 0x0E],  # Variante 1 Synth
    "Z-SYN": [0x00, 0x21, 0x01, 0x00, 0x0E],
    "4VOICESYN": [0x64, 0x21, 0x01, 0x00, 0x0E],  # Categoria 14 Synth
    "4VOICE_SYN": [0x64, 0x21, 0x01, 0x00, 0x0E],
    "4VOICE SYN": [0x64, 0x21, 0x01, 0x00, 0x0E],
}

# Tabella Pesi Carico DSP per i 105 Effetti Zoom B1on/B1Xon
DSP_WEIGHTS = {
    # AMPLIFICATORI (Carico Pesante ~38%)
    "SVT": 38,
    "B_MAN": 38,
    "B-MAN": 38,
    "HRT3500": 38,
    "SMR": 38,
    "FLIPTOP": 38,
    "FLIP TOP": 38,
    "ACOUSTIC": 38,
    "AGAMP": 38,
    "AG AMP": 38,
    "MONOTONE": 38,
    "SUPERB": 38,
    "G_KRUEGER": 38,
    "G-KRUEGER": 38,
    "HEAVEN": 38,
    "MARKB": 38,
    "MARK B": 38,
    # RIVERBERI ED ECO COMPLESSI (~28%)
    "HDHALL": 28,
    "HD HALL": 28,
    "PARTICLER": 28,
    "PARTICLE_R": 28,
    "MODREVERB": 28,
    "MOD_REVERB": 28,
    "FILTERDLY": 28,
    "FILTER_DLY": 28,
    "TRGHLDDLY": 28,
    "TRG_HLD_DLY": 28,
    "ARENA": 25,
    "PLATE": 25,
    # SYNTH / DRIVE / PITCH COMPLESSI (~22%)
    "4VOICESYN": 22,
    "4VOICE_SYN": 22,
    "Z_SYN": 22,
    "Z-SYN": 22,
    "HPS": 22,
    "BASSDRIVE": 22,
    "BASS_DRIVE": 22,
    "SLICER": 20,
    "SYN_TLK": 20,
    "SYNTLK": 20,
    "V_SYN": 20,
    # MODULAZIONI E DELAY MEDI (~15%)
    "DELAY": 15,
    "TAPE_ECHO": 15,
    "TAPEECHO": 15,
    "STOMPDLY": 15,
    "STOMP_DLY": 15,
    "STEREODLY": 15,
    "STEREO_DLY": 15,
    "MODDELAY2": 15,
    "MOD_DELAY_2": 15,
    "REVERSEDL": 15,
    "REVERSE_DL": 15,
    "MULTITAPD": 15,
    "MULTI_TAP_D": 15,
    "PITCHDLY": 15,
    "PITCH_DLY": 15,
    "BACHORUS": 12,
    "BA_CHORUS": 12,
    "BADETUNE": 12,
    "BA_DETUNE": 12,
    "STEREOCHO": 12,
    "STEREO_CHO": 12,
    "BAENSMBL": 12,
    "BA_ENSMBL": 12,
    "CORONATRI": 12,
    "CORONA_TRI": 12,
    "BAFLANGER": 12,
    "BA_FLANGER": 12,
    "VINFLNGR": 12,
    "VIN_FLNGR": 12,
    "PHASER": 12,
    "DUOPHASE": 12,
    "DUO_PHASE": 12,
    # EFFETTI LEGGERI (~8%)
    "160COMP": 8,
    "160 COMP": 8,
    "OPTCOMP": 8,
    "DCOMP": 8,
    "D_COMP": 8,
    "MCOMP": 8,
    "M_COMP": 8,
    "DUALCOMP": 8,
    "DUAL_COMP": 8,
    "LIMITER": 8,
    "SLOWATTACK": 8,
    "SLOW_ATTCK": 8,
    "ZNR": 6,
    "BAGEQ": 8,
    "BA_GEQ": 8,
    "BAPEQ": 8,
    "BA_PEQ": 8,
    "BABOOST": 8,
    "BA_BOOST": 8,
    "BASSOD": 10,
    "BASS_OD": 10,
    "BASSMUFF": 10,
    "BASS_MUFF": 10,
    "TSDRY": 10,
    "TS_DRY": 10,
    "BADIST1": 10,
    "BA_DIST_1": 10,
    "BASQUEAK": 10,
    "BA_SQUEAK": 10,
    "BAFZSMILE": 10,
    "BA_FZ_SMILE": 10,
    "BAMETAL": 10,
    "BA_METAL": 10,
    "BASSBB": 10,
    "BASS_BB": 10,
    "DI5": 8,
    "BASSPRE": 10,
    "BASS_PRE": 10,
    "ACBSPRE": 10,
    "AC_BS_PRE": 10,
    "ROOM": 12,
    "TILEDROOM": 12,
    "TILED_ROOM": 12,
    "HALL": 12,
    "AIR": 10,
    "EARLYREF": 10,
    "EARLY_REF": 10,
    "SLAPBACK": 12,
    "SLAP_BACK": 12,
}


def get_base_dir():
    return os.path.dirname(os.path.abspath(__file__))


def load_master_db():
    base_dir = get_base_dir()
    candidates = [
        "master_fx_db_final.json",
        "master_fx_db_v2.json",
        "pure_105_effects_master.json",
        "exact_105_effects_master.json",
    ]

    for filename in candidates:
        file_path = os.path.join(base_dir, filename)
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    print(
                        f"✅ Caricato database master: '{filename}' ({len(data)} voci)"
                    )
                    return data
            except Exception as e:
                print(f"❌ Errore durante il caricamento di {filename}: {e}")

    print(
        "⚠️ Nessun database master JSON trovato nella directory dell'applicazione!"
    )
    return {}


def load_param_db():
    base_dir = get_base_dir()
    file_path = os.path.join(base_dir, "fx_params_db.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                print(f"✅ Caricato fx_params_db.json ({len(data)} schemi)")
                return data
        except Exception as e:
            print(f"❌ ERRORE caricamento fx_params_db.json: {e}")
    else:
        print(f"⚠️ FILE MANCANTE: {file_path}")
    return {}


def generate_bank_names():
    banks = []
    for letter in "ABCDEFGHIJ":
        for num in range(10):
            banks.append(f"{letter}{num}")
    return banks


def find_best_db_key(requested_key, master_db):
    if not requested_key:
        return None

    if requested_key in master_db:
        return requested_key

    for k in master_db.keys():
        if k.upper() == requested_key.upper():
            return k

    req_clean = (
        requested_key.replace("_", "").replace("-", "").replace(" ", "").upper()
    )
    for k in master_db.keys():
        k_clean = k.replace("_", "").replace("-", "").replace(" ", "").upper()
        if req_clean == k_clean:
            return k

    return None


def convert_knob_val_to_int(val_raw, param_schema=None):
    """Converte i valori umani nel byte per il registro del payload 0x28."""
    if not param_schema:
        try:
            v = float(val_raw)
            return int(round(max(0, min(127, v)))) & 0x7F
        except (ValueError, TypeError):
            return 0

    p_type = param_schema.get("type", "range")

    if p_type == "enum":
        options = param_schema.get("options", [])
        if isinstance(val_raw, str) and not str(val_raw).isdigit():
            val_str = str(val_raw).strip().lower()
            for idx, opt in enumerate(options):
                if str(opt).lower() == val_str:
                    return idx & 0x7F
            for idx, opt in enumerate(options):
                if str(opt).lower() in val_str or val_str in str(opt).lower():
                    return idx & 0x7F
        try:
            idx_val = int(val_raw)
            return max(0, min(len(options) - 1, idx_val)) & 0x7F
        except (ValueError, TypeError):
            return 0

    try:
        val = float(val_raw)
        min_v = param_schema.get("min", 0)
        max_v = param_schema.get("max", 100)

        if max_v == min_v:
            return 0

        val_clamped = max(min_v, min(max_v, val))

        if max_v > 127 or min_v < 0:
            norm = (val_clamped - min_v) / (max_v - min_v)
            byte_val = int(round(norm * 127.0))
        else:
            byte_val = int(round(val_clamped))

        return max(0, min(127, byte_val)) & 0x7F
    except (ValueError, TypeError):
        return 0


def convert_human_val_to_0x31_int(val_raw, param_schema=None):
    """Calcola il valore intero diretto ad alta risoluzione (14-bit) per il comando SysEx 0x31."""
    if not param_schema:
        try:
            return int(round(float(val_raw)))
        except (ValueError, TypeError):
            return 0

    p_type = param_schema.get("type", "range")

    if p_type == "enum":
        options = param_schema.get("options", [])
        if isinstance(val_raw, str) and not str(val_raw).isdigit():
            val_str = str(val_raw).strip().lower()
            for idx, opt in enumerate(options):
                if str(opt).lower() == val_str:
                    return idx
            for idx, opt in enumerate(options):
                if str(opt).lower() in val_str or val_str in str(opt).lower():
                    return idx
        try:
            return int(val_raw)
        except (ValueError, TypeError):
            return 0

    try:
        val = float(val_raw)
        min_v = param_schema.get("min", 0)
        max_v = param_schema.get("max", 100)

        val_clamped = max(min_v, min(max_v, val))

        if min_v < 0:
            return int(round(val_clamped - min_v))
        else:
            return int(round(val_clamped))
    except (ValueError, TypeError):
        return 0


def manual_160COMP_mapping(param_name, human_value):
    try:
        if param_name == "THRSH":
            val = float(human_value)
            val_clamped = max(-60, min(0, val))
            return int(round((val_clamped + 60.0) / 4.0)) & 0x7F
        elif param_name == "Ratio":
            val = float(human_value)
            val_clamped = max(1.0, min(10.0, val))
            internal_ratio = int(round((val_clamped - 1.0) / 9.0 * 336.0))
            return (internal_ratio // 8) * 8 & 0x7F
        elif param_name == "Gain":
            val = float(human_value)
            val_clamped = max(0, min(20, val))
            return int(round(val_clamped)) & 0x7F
        elif param_name == "Knee":
            return 32 if str(human_value).lower() == "soft" else 0
        elif param_name == "Level":
            val = float(human_value)
            val_clamped = max(0, min(150, val))
            return int(round(val_clamped * 18.0 / 150.0)) & 0x7F
    except (ValueError, TypeError):
        pass
    return None


# --- ALGORITMO DI SCRAMBLING HARDWARE ZOOM ---
def swap_bits(e, mask, shift, indexfrom, indexto):
    if e:
        tmpfrom = e[indexfrom] & mask
        e[indexfrom] &= 0xFF ^ mask
        if shift > 0:
            mask <<= shift
        elif shift < 0:
            mask >>= -shift
        tmpto = e[indexto] & mask
        e[indexto] &= 0xFF ^ mask
        if shift > 0:
            tmpfrom <<= shift
            tmpto >>= shift
        elif shift < 0:
            tmpfrom >>= -shift
            tmpto <<= -shift
        e[indexfrom] |= tmpfrom
        e[indexto] |= tmpto


def exchange_bits(ea, eb, mask, shift, indexfrom, indexto):
    if ea and eb:
        tmpa = ea[indexfrom] & mask
        ea[indexfrom] &= 0xFF ^ mask
        if shift > 0:
            mask <<= shift
        elif shift < 0:
            mask >>= -shift
        tmpb = eb[indexto] & mask
        eb[indexto] &= 0xFF ^ mask
        if shift > 0:
            tmpa <<= shift
            tmpb >>= shift
        elif shift < 0:
            tmpa >>= -shift
            tmpb <<= -shift
        ea[indexfrom] |= tmpb
        eb[indexto] |= tmpa


def move_byte(e, indexfrom, indexto):
    if e:
        tmp = e[indexfrom]
        del e[indexfrom]
        e.insert(indexto, tmp)


def scramble_effects(e1, e2, e3, e4, e5):
    e1, e2, e3, e4, e5 = list(e1), list(e2), list(e3), list(e4), list(e5)

    if e5[0] & 0x40:
        exchange_bits(e5, e4, 0x40, -2, 0, 17)
    if e4[0] & 0x40:
        exchange_bits(e4, e3, 0x40, -5, 0, 16)
    if e3[0] & 0x40:
        exchange_bits(e3, e2, 0x40, -1, 0, 17)
    if e2[0] & 0x40:
        exchange_bits(e2, e1, 0x40, -4, 0, 16)

    exchange_bits(e5, e4, 0x0C, -2, 0, 17)
    swap_bits(e5, 0x02, 5, 8, 16)
    swap_bits(e5, 0x20, -2, 16, 16)
    swap_bits(e5, 0x7C, -2, 8, 8)
    swap_bits(e5, 0x02, 5, 0, 8)

    swap_bits(e4, 0x20, -5, 16, 16)
    swap_bits(e4, 0x1E, 2, 8, 16)
    swap_bits(e4, 0x60, -5, 8, 8)
    swap_bits(e4, 0x0E, 2, 0, 8)

    exchange_bits(e3, e2, 0x0E, -1, 0, 17)
    swap_bits(e3, 0x20, -1, 16, 16)
    swap_bits(e3, 0x7E, -1, 8, 8)

    swap_bits(e2, 0x20, -4, 16, 16)
    swap_bits(e2, 0x0E, 3, 8, 16)
    swap_bits(e2, 0x70, -4, 8, 8)
    swap_bits(e2, 0x0E, 3, 0, 8)

    move_byte(e5, 8, 6)
    move_byte(e5, 16, 14)
    move_byte(e4, 19, 20)
    move_byte(e4, 17, 19)
    move_byte(e4, 16, 11)
    move_byte(e4, 8, 3)
    move_byte(e3, 16, 15)
    move_byte(e3, 8, 7)
    move_byte(e2, 20, 19)
    move_byte(e2, 17, 20)
    move_byte(e2, 16, 12)
    move_byte(e2, 8, 4)

    return e1, e2, e3, e4, e5


def build_logical_bypass():
    return [0] * 21


def send_param_change_0x31(
    outport, dev_id, slot_idx, param_idx, human_value_int
):
    """Invia il comando SysEx 0x31 per ruotare una singola manopola in tempo reale."""
    val_lsb = human_value_int % 128
    val_msb = human_value_int // 128

    sysex_msg = [
        0xF0,
        0x52,
        0x00,
        dev_id,
        0x31,
        slot_idx & 0x7F,
        param_idx & 0x7F,
        val_lsb & 0x7F,
        val_msb & 0x7F,
        0xF7,
    ]

    outport.send(mido.Message.from_bytes(sysex_msg))


class ZoomToneEngineerGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("🎸 Zoom B1on / B1Xon - Master AI Sound Engineer")
        self.root.geometry("720x680")
        self.root.resizable(False, False)

        self.api_key = self.load_or_ask_api_key()
        self.last_sysex_buffer = None
        self.last_ai_response = None

        self.model_var = tk.StringVar(value="B1on")
        self.bank_list = generate_bank_names()
        self.selected_bank_var = tk.StringVar(value="A0")

        self.master_db = load_master_db()
        self.params_db = load_param_db()

        self.setup_ui()
        self.check_hardware_status()

    def load_or_ask_api_key(self):
        if os.path.exists(KEY_FILE):
            with open(KEY_FILE) as f:
                key = f.read().strip()
                if key:
                    return key

        key = simpledialog.askstring(
            "Gemini API Key",
            "Inserisci la tua API Key di Google AI Studio:",
            show="*",
        )
        if key:
            with open(KEY_FILE, "w") as f:
                f.write(key.strip())
            return key.strip()
        else:
            messagebox.showerror("Errore", "API Key necessaria per proseguire!")
            sys.exit(1)

    def get_selected_model_info(self):
        if self.model_var.get() == "B1on":
            return 0x65, "101", ".B1on", "Zoom B1on (Model 0x65)"
        else:
            return 0x66, "102", ".B1Xon", "Zoom B1Xon (Model 0x66)"

    def setup_ui(self):
        header = ttk.Label(
            self.root,
            text="Zoom B1on / B1Xon - AI Tone Generator & Patch Manager",
            font=("Helvetica", 13, "bold"),
        )
        header.pack(pady=6)

        frame_hw = ttk.LabelFrame(
            self.root, text=" Impostazioni Hardware & Banco Pedale "
        )
        frame_hw.pack(fill="x", padx=15, pady=3)

        rb_b1on = ttk.Radiobutton(
            frame_hw,
            text="Zoom B1on (0x65)",
            value="B1on",
            variable=self.model_var,
            command=self.on_model_change,
        )
        rb_b1on.pack(side="left", padx=10, pady=5)

        rb_b1xon = ttk.Radiobutton(
            frame_hw,
            text="Zoom B1Xon (0x66)",
            value="B1Xon",
            variable=self.model_var,
            command=self.on_model_change,
        )
        rb_b1xon.pack(side="left", padx=10, pady=5)

        lbl_bank = ttk.Label(frame_hw, text="Banco Target:")
        lbl_bank.pack(side="left", padx=(20, 2), pady=5)

        self.combo_bank = ttk.Combobox(
            frame_hw,
            textvariable=self.selected_bank_var,
            values=self.bank_list,
            width=5,
            state="readonly",
        )
        self.combo_bank.pack(side="left", padx=2, pady=5)

        btn_switch_bank = ttk.Button(
            frame_hw, text="🎯 Vai al Banco", command=self.switch_physical_bank
        )
        btn_switch_bank.pack(side="left", padx=10, pady=5)

        self.status_label = ttk.Label(
            self.root,
            text="🔌 Controllo Hardware USB...",
            font=("Helvetica", 10, "italic"),
            foreground="#0066cc",
        )
        self.status_label.pack(pady=2)

        frame_input = ttk.LabelFrame(
            self.root, text=" Descrivi il suono di basso che desideri "
        )
        frame_input.pack(fill="x", padx=15, pady=5)

        self.prompt_entry = tk.Text(frame_input, height=3, width=70)
        self.prompt_entry.pack(padx=10, pady=8)
        self.prompt_entry.insert("1.0", "")

        self.prompt_entry.bind(
            "<Control-a>",
            lambda e: (
                self.prompt_entry.tag_add("sel", "1.0", "end"),
                "break",
            )[1],
        )
        self.prompt_entry.bind(
            "<Control-A>",
            lambda e: (
                self.prompt_entry.tag_add("sel", "1.0", "end"),
                "break",
            )[1],
        )

        frame_btn = ttk.Frame(self.root)
        frame_btn.pack(pady=6)

        self.btn_generate = ttk.Button(
            frame_btn,
            text="🚀 Genera & Invia Live",
            command=self.process_sound_generation,
        )
        self.btn_generate.grid(row=0, column=0, padx=4)

        self.btn_open = ttk.Button(
            frame_btn, text="📂 Apri File Patch", command=self.open_patch_file
        )
        self.btn_open.grid(row=0, column=1, padx=4)

        self.btn_save = ttk.Button(
            frame_btn,
            text="💾 Salva File Patch",
            command=self.save_patch_file,
            state="disabled",
        )
        self.btn_save.grid(row=0, column=2, padx=4)

        self.btn_rekey = ttk.Button(
            frame_btn, text="🔑 API Key", command=self.reset_api_key
        )
        self.btn_rekey.grid(row=0, column=3, padx=4)

        frame_log = ttk.LabelFrame(self.root, text=" Console Log Operazioni ")
        frame_log.pack(fill="both", expand=True, padx=15, pady=6)

        self.log_text = tk.Text(
            frame_log, height=13, state="disabled", bg="#1e1e1e", fg="#00ff00"
        )
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)

    def log(self, text):
        self.log_text.config(state="normal")
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")
        self.root.update()

    def on_model_change(self):
        dev_id, dev_str, ext, display_name = self.get_selected_model_info()
        self.log(
            f"🔄 Selezionato modello: {display_name} (Estensione {ext}, SysEx ID 0x{dev_id:02X})"
        )
        self.check_hardware_status()

    def find_zoom_port(self):
        outputs = mido.get_output_names()
        return next(
            (
                p
                for p in outputs
                if "ZOOM" in p
                or "B1on" in p
                or "B1Xon" in p
                or "VirMIDI" in p
            ),
            None,
        )

    def check_hardware_status(self):
        port_name = self.find_zoom_port()
        dev_id, dev_str, ext, display_name = self.get_selected_model_info()

        if port_name:
            self.status_label.config(
                text=f"🟢 Connesso: {port_name} | Target: {display_name}",
                foreground="#008000",
            )
        else:
            self.status_label.config(
                text="🔴 Nessuna pedaliera Zoom rilevata su USB MIDI",
                foreground="#cc0000",
            )

    def switch_physical_bank(self):
        port_name = self.find_zoom_port()
        if not port_name:
            messagebox.showwarning(
                "Attenzione", "Pedaliera non connessa su USB!"
            )
            return

        bank_name = self.selected_bank_var.get()
        letter = bank_name[0]
        number = int(bank_name[1])
        program_index = (ord(letter) - ord("A")) * 10 + number

        outport = mido.open_output(port_name)
        outport.send(mido.Message("program_change", program=program_index))
        self.log(
            f"🎯 Cambiato Banco sulla pedaliera a [{bank_name}] (Program Change #{program_index})"
        )

    def reset_api_key(self):
        if os.path.exists(KEY_FILE):
            os.remove(KEY_FILE)
        self.api_key = self.load_or_ask_api_key()
        self.log("🔑 API Key aggiornata con successo!")

    def open_patch_file(self):
        filename = filedialog.askopenfilename(
            filetypes=[
                (
                    "ToneLib Zoom Patch",
                    "*.B1on *.B1Xon *.b1on *.b1xon",
                ),
                ("Tutti i file", "*.*"),
            ]
        )

        if not filename:
            return

        try:
            with open(filename, "rb") as f:
                content = f.read()

            zip_offset = content.find(b"PK\x03\x04")

            if zip_offset != -1:
                zip_bytes = content[zip_offset:]
                with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
                    xml_bytes = z.read("ToneLib.data")
                    xml_str = xml_bytes.decode("utf-8", errors="ignore")
            else:
                xml_str = content.decode("utf-8", errors="ignore")

            xml_str = xml_str.replace("\x00", "").strip()

            end_tag = "</Patches>"
            if end_tag in xml_str:
                xml_str = xml_str[: xml_str.find(end_tag) + len(end_tag)]

            xml_str_clean = re.sub(
                r"&(?!amp;|lt;|gt;|apos;|quot;)", "&amp;", xml_str
            )

            root = ET.fromstring(xml_str_clean)
            patch_elem = root.find(".//patch")
            if patch_elem is None:
                patch_elem = root.find("patch")

            patch_name = patch_elem.get("name", "IMPORTED")
            desc = patch_elem.get("desc", "")

            data_elem = patch_elem.find("data")
            dump_hex_str = data_elem.get("dump")

            buffer = [int(x, 16) for x in dump_hex_str.split(",")]

            self.last_sysex_buffer = buffer
            self.last_ai_response = {
                "patch_name": patch_name,
                "description": desc,
            }

            self.btn_save.config(state="normal")
            self.log(
                f"📂 File caricato con successo: [{patch_name}] da {os.path.basename(filename)}"
            )

            if messagebox.askyesno(
                "Caricamento",
                f"Patch '{patch_name}' caricata!\nVuoi inviarla subito alla pedaliera USB?",
            ):
                dev_id, dev_str, ext, display_name = (
                    self.get_selected_model_info()
                )
                port_name = self.find_zoom_port()

                self.switch_physical_bank()
                time.sleep(0.05)

                buffer[3] = dev_id
                self.send_sysex_usb(buffer, port_name, dev_id, None)

        except Exception as e:
            self.log(f"❌ Errore durante l'apertura del file: {e}")
            messagebox.showerror(
                "Errore File", f"Impossibile aprire il file:\n{e}"
            )

    def call_gemini_api_rest(self, system_instruction, user_prompt):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{TARGET_MODEL}:generateContent?key={self.api_key}"

        payload = {
            "system_instruction": {"parts": [{"text": system_instruction}]},
            "contents": [{"parts": [{"text": user_prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"},
        }

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=data_bytes, headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req) as response:
                res_body = response.read().decode("utf-8")
                res_json = json.loads(res_body)
                raw_text = res_json["candidates"][0]["content"]["parts"][0][
                    "text"
                ]
                return json.loads(raw_text)
        except urllib.error.HTTPError as e:
            error_msg = e.read().decode("utf-8")
            raise RuntimeError(f"Errore API Google HTTP {e.code}: {error_msg}")

    def process_sound_generation(self):
        prompt = self.prompt_entry.get("1.0", "end").strip()
        if not prompt:
            messagebox.showwarning("Attenzione", "Inserisci una descrizione!")
            return

        dev_id, dev_str, ext, display_name = self.get_selected_model_info()
        port_name = self.find_zoom_port()

        self.log(
            f"\n🤖 Analisi AI Gemini 3.6 Flash per {display_name}: '{prompt}'..."
        )

        try:
            available_fx_with_knobs = {}
            for fx_k in self.master_db.keys():
                clean_k = (
                    fx_k.replace("SLOT_FILE_", "")
                    .replace("_S1", "")
                    .replace("_S2", "")
                    .replace("_S3", "")
                    .replace("_S4", "")
                    .replace("_S5", "")
                    .upper()
                )
                knob_schema_list = self.params_db.get(clean_k, [])
                available_fx_with_knobs[fx_k] = {
                    "dsp_weight_percent": DSP_WEIGHTS.get(clean_k, 15),
                    "parameters": knob_schema_list,
                }

            system_instruction = f"""
Sei un Master Sound Engineer per Basso esperto della Zoom B1on / B1Xon.
Puoi scegliere gli effetti dal seguente catalogo hardware con la lista ufficiale dei loro parametri dal PDF e il loro peso DSP %:
{json.dumps(available_fx_with_knobs, indent=2)}

REGOLE HARDWARE & MANOPOLE:
1. SE L'UTENTE CHIEDE EFFETTI SPECIFICI, DEVI inserire ESCLUSIVAMENTE gli effetti richiesti senza aggiungerne di extra.
2. REGOLA DSP GUARD: La somma dei dsp_weight_percent dei 5 slot DEVE ESSERE MINORE O UGUALE A 95%. Se scegli un Amplificatore (es. SVT, B_MAN, MARKB), usa solo effetti leggeri negli slot rimanenti per NON causare il blocco PROCESS LIMIT del pedale.
3. Per OGNI effetto scelto, imposta le manopole fornendo un array 'knob_values' con i valori numerici o le stringhe 'enum' desiderati rispettando i range e le opzioni ufficiali del manuale.
4. Rispondi ESCLUSIVAMENTE in JSON valido con questa struttura:
{{
    "patch_name": "NOME_MAX10",
    "description": "Spiegazione del suono",
    "effects": [
        {{
            "effect_key": "NOME_EFFETTO_ESATTO",
            "knob_values": [valore1, valore2, valore3, ...]
        }}
    ]
}}
"""
            ai_data = self.call_gemini_api_rest(system_instruction, prompt)
            self.last_ai_response = ai_data

            patch_name = (
                ai_data.get("patch_name", "AI TONE").upper().ljust(10)[:10]
            )
            chosen_effects_data = ai_data.get("effects", [])
            desc = ai_data.get("description", "")

            self.log(f"✨ Patch Creata dall'AI: [{patch_name}]")
            self.log(f"📝 Descrizione: {desc}")

            logical_slots = [build_logical_bypass() for _ in range(5)]
            param_updates_list = []
            total_dsp = 0

            for idx, fx_item in enumerate(chosen_effects_data[:5]):
                fx_key = fx_item.get("effect_key", "").strip().upper()
                knob_vals = fx_item.get("knob_values", [])

                real_db_key = find_best_db_key(fx_key, self.master_db)

                if real_db_key and real_db_key in self.master_db:
                    clean_param_key = (
                        real_db_key.replace("SLOT_FILE_", "")
                        .replace("_S1", "")
                        .replace("_S2", "")
                        .replace("_S3", "")
                        .replace("_S4", "")
                        .replace("_S5", "")
                        .upper()
                    )

                    fx_dsp_cost = DSP_WEIGHTS.get(clean_param_key, 15)

                    if total_dsp + fx_dsp_cost > 95:
                        self.log(
                            f"  ⚠️ DSP GUARD: '{clean_param_key}' (peso {fx_dsp_cost}%) evitato per non superare il 95% total DSP! Slot {idx+1} lasciato in Bypass."
                        )
                        continue

                    total_dsp += fx_dsp_cost

                    fx_entry = self.master_db[real_db_key]

                    if isinstance(fx_entry, dict):
                        base_slot = list(
                            fx_entry.get(
                                "raw_slot_bytes",
                                fx_entry.get("clean_header_5bytes", [0] * 5)
                                + [0] * 16,
                            )
                        )
                    else:
                        base_slot = list(fx_entry)

                    while len(base_slot) < 21:
                        base_slot.append(0)

                    # CORREZIONE HEADER SE PRESENTE NEL DIZIONARIO
                    if clean_param_key in KNOWN_HEADER_CORRECTIONS:
                        base_slot[0:5] = KNOWN_HEADER_CORRECTIONS[
                            clean_param_key
                        ]

                    # FLAG HARDWARE DI POSIZIONE DEGLI SLOT
                    if idx == 1:
                        base_slot[0] |= 0x08  # Slot 2 Flag
                    elif idx == 3:
                        base_slot[4] |= 0x40  # Slot 4 Flag
                    elif idx == 4:
                        base_slot[0] |= 0x08  # Slot 5 Flag

                    # MAPPATURA E CONVERSIONE MANOPOLE PER SYSEX 0x31 REAL-TIME
                    param_key = find_best_db_key(
                        clean_param_key, self.params_db
                    )
                    effect_param_schema_list = (
                        self.params_db.get(param_key, []) if param_key else []
                    )

                    for k_idx, raw_val in enumerate(knob_vals):
                        if 5 + k_idx < 20:
                            p_schema = (
                                effect_param_schema_list[k_idx]
                                if k_idx < len(effect_param_schema_list)
                                else None
                            )

                            if clean_param_key == "160COMP" and p_schema:
                                param_name = p_schema.get("name", "")
                                manual_byte = manual_160COMP_mapping(
                                    param_name, raw_val
                                )
                                converted_byte = (
                                    manual_byte
                                    if manual_byte is not None
                                    else convert_knob_val_to_int(
                                        raw_val, p_schema
                                    )
                                )
                            else:
                                converted_byte = convert_knob_val_to_int(
                                    raw_val, p_schema
                                )

                            base_slot[5 + k_idx] = converted_byte & 0x7F

                            # Calcola il valore intero diretto ad alta risoluzione 14-bit per il comando 0x31
                            human_0x31_val = convert_human_val_to_0x31_int(
                                raw_val, p_schema
                            )

                            param_updates_list.append(
                                (
                                    idx,
                                    k_idx + 2,
                                    human_0x31_val,
                                    (
                                        p_schema.get("name", f"P{k_idx+1}")
                                        if p_schema
                                        else f"P{k_idx+1}"
                                    ),
                                )
                            )

                    logical_slots[idx] = base_slot
                    self.log(
                        f"  ✔️ Slot {idx+1}: Inserito '{real_db_key}' (DSP: {fx_dsp_cost}%) | Manopole: {knob_vals}"
                    )

            self.log(f"📊 Carico DSP Totale Calcolato: {total_dsp}% / 100%")

            # CIFRATURA SCRAMBLING HARDWARE
            se1, se2, se3, se4, se5 = scramble_effects(
                logical_slots[0],
                logical_slots[1],
                logical_slots[2],
                logical_slots[3],
                logical_slots[4],
            )

            patch_payload = [0] * 128
            patch_payload[0:20] = se1[:20]
            patch_payload[20:41] = se2[:21]
            patch_payload[41:61] = se3[:20]
            patch_payload[61:82] = se4[:21]
            patch_payload[82:102] = se5[:20]

            patch_payload[96] |= 0x01
            patch_payload[103] = 0x20
            patch_payload[105] = 85

            for i, char in enumerate(patch_name):
                offset = i + 1 if i >= 4 else i
                patch_payload[116 + offset] = ord(char)

            patch_payload = [b & 0x7F for b in patch_payload]

            buffer = [0xF0, 0x52, 0x00, dev_id, 0x28] + patch_payload + [0xF7]

            self.last_sysex_buffer = buffer

            self.switch_physical_bank()
            time.sleep(0.05)

            # Invia la Patch e poi applica le manopole con SysEx 0x31
            self.send_sysex_usb(
                buffer, port_name, dev_id, param_updates_list=param_updates_list
            )
            self.btn_save.config(state="normal")

        except Exception as e:
            self.log(f"❌ Errore durante la generazione: {e}")
            messagebox.showerror("Errore AI", str(e))

    def send_sysex_usb(
        self, buffer, port_name, dev_id, param_updates_list=None
    ):
        if not port_name:
            self.log(
                "⚠️ Pedaliera non collegata via USB. Patch pronta ma non inviata live."
            )
            return

        outport = mido.open_output(port_name)

        # 1. Invia Handshake Remote Editor (0x50)
        handshake_msg = [0xF0, 0x52, 0x00, dev_id, 0x50, 0xF7]
        outport.send(mido.Message.from_bytes(handshake_msg))
        time.sleep(0.1)

        # 2. Invia la Patch Completa (0x28)
        outport.send(mido.Message.from_bytes(buffer))
        self.log(
            f"🚀 PATCH INVIATA LIVE SU USB (Model ID: 0x{dev_id:02X})! Caricati gli slot."
        )

        # 3. STADIO 2: INVIA I COMANDI SYSEX 0x31 PER RUOTARE LE MANOPOLE IN TEMPO REALE CON I VALORI UMANI DIRETTI
        if param_updates_list:
            time.sleep(0.1)
            self.log(
                "🎛️ Regolazione fine manopole in tempo reale via SysEx 0x31..."
            )
            for slot_idx, param_idx, val_int, p_name in param_updates_list:
                send_param_change_0x31(
                    outport, dev_id, slot_idx, param_idx, val_int
                )
                time.sleep(0.02)
            self.log(
                "✨ MANOPOLE REGOLATE E RUOTATE CON SUCCESSO SENZA MAI USARE IL MOUSE!"
            )

    def save_patch_file(self):
        if not self.last_sysex_buffer or not self.last_ai_response:
            return

        dev_id, dev_str, ext, display_name = self.get_selected_model_info()
        patch_name = self.last_ai_response.get("patch_name", "AI_TONE")

        filename = filedialog.asksaveasfilename(
            defaultextension=ext,
            initialfile=f"{patch_name}{ext}",
            filetypes=[
                (f"ToneLib Zoom Patch (*{ext})", f"*{ext}"),
                ("Tutti i file", "*.*"),
            ],
        )

        if not filename:
            return

        hex_dump_str = ",".join(f"{b:02x}" for b in self.last_sysex_buffer)

        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<Patches ver="1">
  <patch devId="{dev_str}" devCode="1" ver="1.30" idx="0" name="{patch_name}" desc="{self.last_ai_response.get('description','')}">
    <data size="134" hash="d11403e2" dump="{hex_dump_str}"/>
  </patch>
</Patches>"""

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(
            zip_buffer, "w", zipfile.ZIP_DEFLATED
        ) as zip_file:
            zip_file.writestr("ToneLib.data", xml_content)

        header_bytes = bytes([dev_id, 0x00, 0x00, 0x00])

        with open(filename, "wb") as f:
            f.write(header_bytes)
            f.write(zip_buffer.getvalue())

        self.log(
            f"💾 File patch salvato con successo per {display_name}: {filename}"
        )
        messagebox.showinfo("Successo", f"File salvato:\n{filename}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ZoomToneEngineerGUI(root)
    root.mainloop()
