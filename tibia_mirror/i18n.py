"""English (the default) and Polish text.

Wrap user-facing text in tr(), or tr_n() for counts (Polish has three plural
forms); a test checks every such text has a Polish version.
Polish wording: a mirror is an "odbicie", a region stays a "region".
"""

from tibia_mirror.config import LANGUAGES

_language = LANGUAGES[0]


def use(language: str) -> None:
    global _language
    _language = language if language in LANGUAGES else LANGUAGES[0]


def current() -> str:
    return _language


def tr(text: str, **fields: object) -> str:
    """`text` in the current language, with {fields} filled in."""
    if _language == "pl":
        text = POLISH.get(text, text)
    return text.format(**fields) if fields else text


def tr_n(count: int, one: str, other: str, **fields: object) -> str:
    """A phrase about `count` things, filled in as {n}: tr_n(2, "{n} region", "{n} regions")."""
    if _language == "pl" and one in POLISH_PLURALS:
        text = POLISH_PLURALS[one][polish_plural_form(count)]
    else:
        text = one if count == 1 else other
    return text.format(n=count, **fields)


def polish_plural_form(count: int) -> int:
    """0 for 1 ("region"), 1 for 2-4, 22-24... ("regiony"), 2 for the rest ("regionów")."""
    if count == 1:
        return 0
    if count % 10 in (2, 3, 4) and count % 100 not in (12, 13, 14):
        return 1
    return 2


POLISH = {
    # Panel and navigation
    "Mirrors": "Odbicia",
    "Settings": "Ustawienia",
    "Shortcuts": "Skróty",
    "About": "Informacje",
    "Tibia connected": "Tibia połączona",
    "Waiting for Tibia...": "Czekam na Tibię...",
    "Tibia is minimized": "Tibia jest zminimalizowana",
    "Mirrors hidden ({key})": "Odbicia ukryte ({key})",
    "This profile's mirrors appear once Tibia is running.": (
        "Odbicia z tego profilu pojawią się po uruchomieniu Tibii."
    ),
    "This profile's mirrors appear once Tibia is restored.": (
        "Odbicia z tego profilu pojawią się po przywróceniu okna Tibii."
    ),
    # Mirrors page
    "Add region": "Dodaj region",
    "REGIONS": "REGIONY",
    "Save": "Zapisz",
    "Revert": "Przywróć",
    "Changes are saved automatically": "Zmiany zapisują się automatycznie",
    "Unsaved changes - press Save": "Niezapisane zmiany - kliknij Zapisz",
    "All changes saved": "Wszystkie zmiany zapisane",
    "Click Add region, then drag a box over the part of the game to mirror.": (
        "Kliknij Dodaj region, a potem zaznacz fragment gry do odbicia."
    ),
    "New profile…": "Nowy profil…",
    "Duplicate…": "Duplikuj…",
    "Rename…": "Zmień nazwę…",
    "Characters…": "Postacie…",
    "Copy from…": "Kopiuj z…",
    "Import…": "Importuj…",
    "Export…": "Eksportuj…",
    "Delete profile": "Usuń profil",
    # Profile per character, and copying from another profile
    'Characters of "{name}"': "Postacie profilu „{name}”",
    "Logging in with one of these characters opens this profile, "
    "while Profile per character is on in Settings.": (
        "Zalogowanie się jedną z tych postaci otwiera ten profil, "
        "gdy w Ustawieniach włączony jest Profil dla postaci."
    ),
    "No characters yet.": "Nie ma jeszcze postaci.",
    "Add": "Dodaj",
    "Done": "Gotowe",
    'Linked to "{profile}" - adding moves it here.': (
        "Przypisana do „{profile}” - dodanie przeniesie ją tutaj."
    ),
    "Created for {character}": "Utworzono dla {character}",
    "Opened for {character}": "Otwarto dla {character}",
    "Copy from profile": "Kopiuj z profilu",
    'Replaces the mirrors of "{name}" with those of the chosen profile. '
    "Until you save, Revert brings them back.": (
        "Zastępuje odbicia profilu „{name}” odbiciami wybranego profilu. "
        "Dopóki nie zapiszesz, odzyskasz je przyciskiem Przywróć."
    ),
    "Replace": "Zastąp",
    'Copied {regions} from "{name}"': "Skopiowano {regions} z „{name}”",
    # Region cards and mirrors
    "Remove region": "Usuń region",
    "Remove": "Usuń",
    "Frame colour": "Kolor ramki",
    "Edit region": "Edytuj region",
    "Position, size and zoom.": "Położenie, rozmiar i powiększenie.",
    "Lock mirror": "Zablokuj odbicie",
    "Pins it in place. Clicks pass through it to the game.": (
        "Przypina je w miejscu. Kliknięcia przechodzą przez nie do gry."
    ),
    "Unlock mirror": "Odblokuj odbicie",
    "Lets you move it again. Clicks land on the mirror.": (
        "Znów można je przesuwać. Kliknięcia trafiają w odbicie."
    ),
    "Hide mirror": "Ukryj odbicie",
    "It stays in the profile; show it again any time.": (
        "Zostaje w profilu; możesz je pokazać w każdej chwili."
    ),
    "Show mirror": "Pokaż odbicie",
    # Dialogs
    "Cancel": "Anuluj",
    "OK": "OK",
    "Discard": "Odrzuć",
    "Delete": "Usuń",
    "Name this region": "Nazwij ten region",
    "Rename region": "Zmień nazwę regionu",
    "New profile": "Nowy profil",
    "Duplicate profile": "Duplikuj profil",
    "Rename profile": "Zmień nazwę profilu",
    "Unsaved changes": "Niezapisane zmiany",
    'Region "{name}"': "Region „{name}”",
    'Save changes to "{name}" before closing?': "Zapisać zmiany w „{name}” przed zamknięciem?",
    'Save changes to "{name}" before switching?': (
        "Zapisać zmiany w „{name}” przed przełączeniem?"
    ),
    'Delete "{name}" and all its mirrors? This can\'t be undone.': (
        "Usunąć „{name}” i wszystkie jego odbicia? Tego nie da się cofnąć."
    ),
    "Width": "Szerokość",
    "Height": "Wysokość",
    "Zoom %": "Powiększenie %",
    "Game pixels. Up/Down change a value by 1, Shift by 10.": (
        "Piksele gry. Strzałki zmieniają wartość o 1, z Shift o 10."
    ),
    "Apply size and zoom to all mirrors": "Zastosuj rozmiar i powiększenie do wszystkich odbić",
    "Select area again": "Zaznacz obszar ponownie",
    "Fill in every value": "Uzupełnij wszystkie wartości",
    "Width must be {lo} to {hi} pixels": "Szerokość musi wynosić od {lo} do {hi} pikseli",
    "Height must be {lo} to {hi} pixels": "Wysokość musi wynosić od {lo} do {hi} pikseli",
    "X must be 0 to {hi} for this width": "X musi wynosić od 0 do {hi} przy tej szerokości",
    "Y must be 0 to {hi} for this height": "Y musi wynosić od 0 do {hi} przy tej wysokości",
    "Zoom must be {lo} to {hi}%": "Powiększenie musi wynosić od {lo} do {hi}%",
    # Profile names
    "Enter a name": "Wpisz nazwę",
    "A name can't contain < > : \" / \\ | ? *": 'Nazwa nie może zawierać < > : " / \\ | ? *',
    "A name can't end with a dot or a space": "Nazwa nie może kończyć się kropką ani spacją",
    "That name is reserved by Windows": "Ta nazwa jest zarezerwowana przez Windows",
    "A profile with this name already exists": "Profil o tej nazwie już istnieje",
    "Profile": "Profil",
    "Region": "Region",
    "copy": "kopia",
    # Files
    "Import profile": "Importuj profil",
    "Export profile": "Eksportuj profil",
    "Tibia Mirror profile": "Profil Tibia Mirror",
    "All files": "Wszystkie pliki",
    # Status line
    "Saved {regions}": "Zapisano {regions}",
    "Save failed": "Nie udało się zapisać",
    "Start Tibia first": "Najpierw uruchom Tibię",
    "Restore Tibia first": "Najpierw przywróć Tibię",
    "Could not save settings": "Nie udało się zapisać ustawień",
    "Not a readable profile file": "To nie jest poprawny plik profilu",
    "Export failed": "Nie udało się wyeksportować",
    'Exported "{name}"': "Wyeksportowano „{name}”",
    "Could not create profile": "Nie udało się utworzyć profilu",
    "Could not duplicate profile": "Nie udało się zduplikować profilu",
    "Could not import profile": "Nie udało się zaimportować profilu",
    "Could not rename profile": "Nie udało się zmienić nazwy profilu",
    "Could not delete profile": "Nie udało się usunąć profilu",
    "Profile file is invalid": "Plik profilu jest uszkodzony",
    "Could not mirror": "Nie udało się utworzyć odbicia",
    # Timer
    "Timer": "Minutnik",
    'Timer for "{name}"': "Minutnik dla „{name}”",
    "Pause while logged out": "Wstrzymaj po wylogowaniu",
    "For timers that only count while your character is online: "
    "each character continues from where it logged out.": (
        "Dla minutników, które biegną tylko, gdy postać jest online: "
        "każda postać wznawia od miejsca, w którym się wylogowała."
    ),
    "Timer on": "Minutnik włączony",
    "Alert after": "Alarm po",
    "min": "min",
    "s": "s",
    "Count": "Liczenie",
    "Down": "W dół",
    "Up": "W górę",
    "Mouse button": "Przycisk myszy",
    "Left": "Lewy",
    "Right": "Prawy",
    "Both": "Oba",
    "Key": "Klawisz",
    "Click to set a key": "Kliknij, aby wybrać",
    "Press a key...": "Naciśnij klawisz...",
    "Sound": "Dźwięk",
    "Asterisk": "Gwiazdka",
    "Exclamation": "Wykrzyknik",
    "Notification": "Powiadomienie",
    "Critical stop": "Błąd krytyczny",
    "Beep": "Sygnał",
    "No sound": "Bez dźwięku",
    "A click on this region in the game, or the key, starts it again.": (
        "Kliknięcie tego regionu w grze lub klawisz uruchamia go od nowa."
    ),
    "The alert time must be 0:01 to 59:59.": "Czas alarmu musi wynosić od 0:01 do 59:59.",
    "On: alerts after {time}.": "Włączony: alarm po {time}.",
    "Counts time since you click this region or press its key.": (
        "Odmierza czas od kliknięcia tego regionu lub naciśnięcia klawisza."
    ),
    "{key} hides all mirrors (see Shortcuts). Pick another key.": (
        "{key} ukrywa wszystkie odbicia (zobacz Skróty). Wybierz inny klawisz."
    ),
    # Settings
    "GENERAL": "OGÓLNE",
    "PROFILES": "PROFILE",
    "Profile per character": "Profil dla postaci",
    "Logging in opens the character's profile, creating one the first time.": (
        "Po zalogowaniu otwiera profil postaci, a za pierwszym razem go tworzy."
    ),
    "SAVING": "ZAPISYWANIE",
    "MIRRORS": "ODBICIA",
    "Language": "Język",
    "Theme": "Motyw",
    "Dark": "Ciemny",
    "Light": "Jasny",
    "Keep this panel on top": "Panel zawsze na wierzchu",
    "Stays above other windows.": "Pozostaje nad innymi oknami.",
    "Save automatically": "Zapisuj automatycznie",
    "Saves every change as you make it.": "Zapisuje każdą zmianę od razu.",
    "Opacity of new mirrors": "Krycie nowych odbić",
    "Each mirror can still be set on its card.": "Każde odbicie ustawisz też na jego karcie.",
    "Mirror frame": "Ramka odbicia",
    "Grey outline on mirrors without a colour.": "Szara obwódka wokół odbić bez koloru.",
    "Tint with frame colour": "Barwienie kolorem ramki",
    "Shades coloured mirrors in their colour.": "Barwi kolorowe odbicia kolorem ramki.",
    "Rounded corners": "Zaokrąglone rogi",
    "Clips a few pixels at each corner.": "Ucina kilka pikseli w rogach.",
    "Hide all mirrors": "Ukryj wszystkie odbicia",
    "Press again to bring them back. Works while Tibia is active.": (
        "Naciśnij ponownie, aby je przywrócić. Działa, gdy Tibia jest aktywna."
    ),
    '{key} already starts the timer of "{name}".': "{key} już uruchamia minutnik „{name}”.",
    '{key} already starts the timer of "{name}" in profile "{profile}".': (
        "{key} już uruchamia minutnik „{name}” w profilu „{profile}”."
    ),
    "Fade animations": "Animacje zanikania",
    "Off: mirrors appear and hide instantly.": "Wyłączone: pojawiają się od razu.",
    "Tibia Mirror couldn't start. The details are in:\n{path}": (
        "Nie udało się uruchomić Tibia Mirror. Szczegóły są w pliku:\n{path}"
    ),
    # Footer and About page
    "Created by {author}": "Stworzone przez {author}",
    "© {years} · PolyForm Strict License": "© {years} · Licencja PolyForm Strict",
    "Version {version}": "Wersja {version}",
    "Keep your eyes on the fight, not on the corners of the screen. "
    "Tibia Mirror puts the parts of Tibia you care about - cooldowns, "
    "the minimap, anything you like - into small windows you can place "
    "wherever suits you.": (
        "Skup się na walce, a nie na rogach ekranu. "
        "Tibia Mirror pokazuje w małych okienkach to, co w Tibii jest dla ciebie ważne - "
        "cooldowny, minimapę, co tylko zechcesz - a okienka ustawisz, gdzie ci wygodnie."
    ),
    "It uses Windows' own window previews - the same ones you see on the taskbar. "
    "No screen capture, nothing changed in the game, nothing sent anywhere.": (
        "Korzysta z podglądu okien wbudowanego w Windows - tego samego, który widzisz "
        "na pasku zadań. "
        "Bez przechwytywania ekranu, bez zmian w grze, bez wysyłania czegokolwiek."
    ),
    # {coins} is "a few Tibia Coins", shown in gold.
    "Tibia Mirror is free. If you find it useful, you can say thanks "
    "by sending {coins} to this character:": (
        "Tibia Mirror jest darmowy. Jeśli ci się przydaje, możesz podziękować, "
        "wysyłając {coins} tej postaci:"
    ),
    "a few Tibia Coins": "kilka Tibia Coins",
    "Enjoying it?": "Podoba ci się?",
    "Tip {coins} to": "Podrzuć {coins} dla",
    # {discord} is "Discord", shown in Discord's blurple; Polish needs its locative form.
    "Questions or ideas? Message me on {discord}:": (
        "Pytania lub pomysły? Napisz do mnie na {discord}:"
    ),
    "Discord": "Discordzie",
    "Copy": "Kopiuj",
    "Copied": "Skopiowano",
    "A fan-made tool for the Tibia community. Tibia is a trademark of "
    "CipSoft GmbH, and this app is not affiliated with or endorsed by CipSoft.": (
        "Narzędzie stworzone przez fana dla społeczności Tibii. Tibia jest znakiem "
        "towarowym CipSoft GmbH, a ta aplikacja nie jest z CipSoft powiązana "
        "ani przez nią popierana."
    ),
}

# Keyed by the English singular; (1, 2-4, 5+) forms.
POLISH_PLURALS = {
    "{n} region": ("{n} region", "{n} regiony", "{n} regionów"),
    "{n} mirror failed to load": (
        "Nie udało się wczytać {n} odbicia",
        "Nie udało się wczytać {n} odbić",
        "Nie udało się wczytać {n} odbić",
    ),
    "{n} mirror failed to reconnect": (
        "Nie udało się ponownie podłączyć {n} odbicia",
        "Nie udało się ponownie podłączyć {n} odbić",
        "Nie udało się ponownie podłączyć {n} odbić",
    ),
}
