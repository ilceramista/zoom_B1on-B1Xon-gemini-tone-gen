# zoom_B1on-B1Xon-gemini-tone-gen
let Gemini Ai help you to build a zoom pathces, prompt to Ai and check and edit sounds if you need

# 📖  Mini Manuale Utente (Per Uso da Parte di Chiunque)

---

# 🎸 Zoom B1Xon / B1on - AI Sound Engineer
> **Trasforma le tue idee in suoni reali sulla pedaliera Zoom usando l'Intelligenza Artificiale Gemini.**

L'applicazione **Zoom AI Sound Engineer** permette di programmare la pedaliera multieffetto Zoom B1Xon / B1on semplicemente descrivendo il suono desiderato  (es. *"Voglio un suono distorto per basso tipo Muse Hysteria"*).

L'AI analizza la richiesta, consulta il catalogo hardware dei 105 algoritmi disponibili, regola le manopole quasi sempre perfettamente, in questo ho avuto difficoltà e **programma istantaneamente la pedaliera via USB** oppure genera un file `.B1Xon` pronto da salvare.C'è da tener presente che qualora l'app non riuscisse al 100% a immettere i parametri giusti sul device fisico, l'app ci restituisce sempre al nostro prompt un prompt di risposta con inclusi i valori che ha scelto,e questi vengono scelti usano apputo l'immensa conoscenza che ha il modello di linguaggio gemini,al massimo basta quindi un rapido controllo ed un editing manuale dei pochi che ha fallito.In ogni caso l'Ai ci fornisce uno schema ed una chain fx interessante.

---

## 🔑 2. Come Ottenere la propria Gemini API Key (GRATIS)

L'applicazione utilizza il modello di intelligenza artificiale di Google **Gemini 3.6 Flash**. L'uso è **completamente gratuito** e richiede solo una chiave personale (API Key):

1. Vai sul sito ufficiale **[Google AI Studio](https://aistudio.google.com/)**.
2. Accedi con un qualsiasi account Google (Gmail).
3. Fai clic sul pulsante **`Get API key`** (o *Crea chiave API*).
4. Fai clic su **`Create API key`** in a new project.
5. Copia la stringa di testo alfanumerica generata (es. `AIzaSyD...`).

> **Nota:** La chiave ti verrà chiesta **solo al primo avvio** dell'applicazione. Verrà salvata in modo sicuro nel file locale `.gemini_key` e non dovrai mai più digitarla.

---

## 🚀 3. Avvio e Utilizzo dell'Applicazione

1. Collegare la pedaliera Zoom B1Xon al computer tramite il cavo USB ed accenderla.
2. Aprire il terminale nella cartella del programma ed eseguire:
   ```bash
   python3 gemini_tone_engineer.py
   ```
3. **Al primo avvio:** Inserire la propria Gemini API Key nella finestra popup e fare clic su OK. 
**Scegliere il proprio pedale su checkbox B1on oppure B1Xon**
5. **Usare nell'interfaccia grafica l'apposito selettore e bottone "vai al banco" per confermare.**
4. **Inserimento Prompt:** Nel riquadro di testo, descrivere il suono desiderato.
   * *Esempi di prompt efficaci:*
     * `"Suono slap pulito, brillante e compresso stile Marcus Miller"`
     * `"Distorsione pesante e fuzz per synth bass alla Muse Hysteria"`
     * `"Basso caldo jazz fretless con leggero chorus ed equalizzatore morbido"`
5. Fai clic su **`🚀 Genera & Invia Live a Pedaliera USB`**:
   * L'AI elaborerà la patch in 1-2 secondi.
   * La pedaliera Zoom si sbloccherà automaticamente e **caricherà il nuovo suono in tempo reale**!
   * Vedrai il nome della nuova patch e gli effetti caricati direttamente sul display LCD della Zoom.
6. **Salvataggio File (Opzionale):**
   * Fai clic su **`💾 Salva File .B1Xon`** per salvare la patch sul computer,potrai importarla su ToneLib o riutilizzarla in seguito con l'applicazione iniettandola direttamente nello zoom qualora l'avessi sovrascritta o persa per errore.E' possibile anche caricare sullo zoom delle patch precedentemente salvate, usare apposito selettore "apri file patch" e ricordare che verrà scritta nel banco che abbiamo scelto sulla gui.

---

## 🎛️ 4. Funzionalità Avanzate di Sicurezza Hardware

* **Prevenzione Errore `DSP FULL`:** L'Ingegnere AI conosce i limiti di calcolo del processore Zoom. Se selezioni un amplificatore pesante (es. Ampeg SVT), eviterà automaticamente di aggiungere riverberi o sintetizzatori troppo complessi per non mandare in blocco il pedale.
In questo senso quasi sempre il calcolo dsp limits funziona, ma se avviene un errore dovrai corregerlo a mano.
* **Pulsante Cambia API Key:** Se desideri aggiornare la tua chiave API, basta fare clic sul pulsante **`🔑 Cambia API Key`** nell'interfaccia.

---
## ⚙️ 1. Requisiti di Sistema

* **Hardware:** Pedaliera **Zoom B1Xon** o **Zoom B1on** collegata al PC via cavo **USB**.
* **Sistema Operativo:** Linux (Ubuntu/Debian) o qualsiasi OS con Python 3.8+.
* **Librerie Python Richieste:**
  ```bash
  pip3 install mido python-rtmidi
  ```

---


Su Linux (Ubuntu/Debian), affinché Python e `mido` riescano a comunicare via USB MIDI con la pedaliera Zoom senza blocchi di permessi o mancati rilevamenti dell'interfaccia, servono proprio **2 configurazioni di sistema** legate ai moduli del kernel Linux (`modprobe`) e ai permessi utente.

---
### 🐧 Sezione `TROUBLESHOOTING`:



```markdown
---

## 🐧 Configurazione Sistema Linux & Troubleshooting USB/MIDI

Se la pedaliera Zoom non viene rilevata o se si ottiene un errore di permessi all'avvio dell'applicazione, seguire questi passaggi di configurazione del sistema Linux:

### 1. Abilitare i Permessi Utente per i Dispositivi Audio/MIDI
Per consentire a Python di inviare messaggi SysEx alla pedaliera senza usare `sudo`:
```bash
sudo usermod -aG audio $USER
```
*(Dopo aver eseguito il comando, effettuare il log-out ed il log-in dal sistema per applicare i permessi).*

---

### 2. Gestione Moduli del Kernel Linux (`modprobe`)

La Zoom B1Xon utilizza il driver audio/MIDI USB ALSA standard del kernel Linux (`snd-usb-audio`).

#### A. Verificare che la pedaliera sia vista dal sistema:
Nel terminale, digitare uno di questi comandi con la pedaliera collegata via USB:
```bash
amidi -l
```
oppure:
```bash
lsusb | grep -i Zoom
```
Dovresti vedere la pedaliera elencata come `ZOOM B1Xon` o `ZOOM B1 Series`.

#### B. Reset del Modulo USB MIDI se la pedaliera "si incastra" o non risponde:
Se la pedaliera è collegata ma l'applicazione non riesce ad aprirla, è possibile riavviare il driver USB MIDI di Linux con il comando `modprobe`:

```bash
# Riavvia il driver audio/MIDI USB di Linux
sudo modprobe -r snd-usb-audio && sudo modprobe snd-usb-audio
```

#### C. Abilitare la Porta MIDI Virtuale (Opzionale per Testing):
Se si desidera fare test con porte MIDI virtuali senza collegare il pedale fisico:
```bash
sudo modprobe snd-virmidi
```
```

---

### 🎯 Perché queste istruzioni salvano la vita all'utente:
1. **`usermod -aG audio $USER`**: Risolve il $90\%$ dei casi in cui Python dice `Permission Denied` tentando di aprire la porta MIDI ALSA.
2. **`sudo modprobe -r snd-usb-audio && sudo modprobe snd-usb-audio`**: È il "trucco magico" Linux che resetta il bus audio/MIDI senza dover riavviare il PC se la scheda madre perde la sincronia USB con la pedaliera.

*Sviluppato con successo tramite Reverse Engineering dei protocolli SysEx e firmware Zoom B1Xon/B1on.*
