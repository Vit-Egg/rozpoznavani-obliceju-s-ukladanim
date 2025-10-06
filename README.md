# rozpoznavani-obliceju-s-ukladanim
Reálné rozpoznávání obličejů pomocí OpenCV s možností přehrání zvuku a automatickým ukládáním snímků.

# Rozpoznávání obličejů s automatickým ukládáním

Projekt v Pythonu, který pomocí OpenCV rozpoznává obličeje v reálném čase z kamery, přehrává zvuk při rozpoznání známé osoby a ukládá snímky, pokud obličej zůstane v obraze po určitou dobu.

## 🧠 Funkce
- Reálné rozpoznávání obličejů pomocí OpenCV (LBPH).
- Přehrání zvukového upozornění pro vybrané osoby.
- Automatické ukládání snímků rozpoznaných obličejů.
- Nastavitelný minimální čas, po který musí být obličej viditelný, aby se uložil.
- Globální zpoždění (delay), které brání opakovanému ukládání v krátkých intervalech.

## 📦 Požadavky
- Python 3.11 nebo novější  
- Balíčky:
  - `opencv-contrib-python`
  - `numpy`
  - `pygame`

## ⚙️ Instalace
1. Naklonuj repozitář:
   ```bash
   git clone https://github.com/Vit-Egg/rozpoznavani-obliceju-s-ukladanim.git
   cd rozpoznavani-obliceju-s-ukladanim
   ```
2. Nainstaluj závislosti:
   ```bash
   pip install opencv-contrib-python numpy pygame
   ```
3. Vytvoř potřebné složky:
   ```bash
   mkdir known_faces captures
   ```
4. Přidej do složky `known_faces` složky osob, které chceš rozpoznávat např. mama/
                                                                               ├── mama1.jpg
                                                                               ├── mama2.jpg
                                                                               └── mama3.jpg


## ▶️ Spuštění
Skript spusť v terminálu:
```bash
python main_opencv_lbph_with_presence.py
```
- Stiskni `q` pro ukončení programu.
- Uprav parametry ve skriptu:
  - `ALERT_ONLY_FOR` – seznam osob, pro které se má přehrát zvuk.
  - `MIN_PRESENCE_SECONDS` – minimální doba, po kterou musí být obličej viditelný pro uložení.
  - `GLOBAL_SAVE_DELAY` – minimální doba mezi jednotlivými uloženými snímky.

## 📁 Struktura složek
```
rozpoznavani-obliceju-s-ukladanim/
── known_faces/                     # složka se známými osobami (vstupní data)
│   ├── mama/
│   │   ├── mama1.jpg
│   │   ├── mama2.jpg
│   │   └── mama3.jpg
│   │
│   ├── otec/
│   │   ├── otec1.jpg
│   │   ├── otec2.jpg
│   │   └── otec3.jpg
│   │
│   └── sestra/
│       ├── sestra1.jpg
│       ├── sestra2.jpg
│       └── sestra3.jpg
├── captures/          # Automaticky uložené snímky
├── main.py
├── alert.mp3          # Zvukové upozornění
└── README.md
```

## 🧩 Tipy
- Pro nejlepší výsledky používej jasné, čelní fotografie osob.
- Pokud se nenačítají žádné obličeje, zkontroluj formát souborů (ideálně JPEG, RGB).
- Doporučuji používat rozlišení kamery aspoň 720p pro spolehlivé rozpoznání.

