## Extended Configuration Examples

### CLI: Filename Format Options

**Prefix Format (default):**
```powershell
sports-flashcards --set mlb --filename-format prefix
# Output: front_san_francisco_49ers.png, back_san_francisco_49ers.png
```

**Suffix Format:**
```powershell
sports-flashcards --set mlb --filename-format suffix
# Output: san_francisco_49ers_front.png, san_francisco_49ers_back.png
```

---

### CLI: Name Format Options

**Full Name (default, City + Team):**
```powershell
sports-flashcards --set mlb --name-format full --name-order city_first
# Filenames: front_san_francisco_49ers.png
# Back text: San Francisco
#            49ers
```

**Team Only:**
```powershell
sports-flashcards --set mlb --name-format team_only
# Filenames: front_49ers.png
# Back text: 49ers
```

**City/Location Only:**
```powershell
sports-flashcards --set mlb --name-format city_only
# Filenames: front_san_francisco.png
# Back text: San Francisco
```

---

### CLI: Name Order Options (Full Format Only)

**City First (default):**
```powershell
sports-flashcards --set acc --name-format full --name-order city_first
# Filenames: front_university_of_north_carolina_tar_heels.png
# Back text: University of North Carolina
#            Tar Heels
```

**Team First:**
```powershell
sports-flashcards --set acc --name-format full --name-order team_first
# Filenames: front_tar_heels_university_of_north_carolina.png
# Back text: Tar Heels
#            University of North Carolina
```

---

### CLI: Combined Examples

**Minimal filenames, suffix format:**
```powershell
sports-flashcards --set nfl --filename-format suffix --name-format team_only
# Output: patriots_front.png, patriots_back.png
# Back: Patriots
```

**Print-quality college football, team-first:**
```powershell
sports-flashcards --set sec --dpi 600 --filename-format prefix --name-format full --name-order team_first --output-dir output/print_ready
# Output: front_crimson_tide_university_of_alabama.png (3600x2400px)
# Back: Crimson Tide
#       University of Alabama
```

**All pro sports in one command (batch):**
```powershell
foreach ($set in @("mlb", "nfl", "nba", "nhl", "wnba", "mls")) {
    sports-flashcards --set $set --name-format team_only --filename-format suffix --output-dir "output/pro_$set"
}
```

**Generate all college conferences with city-first order:**
```powershell
foreach ($conf in @("acc", "big_ten", "big_12", "sec")) {
    sports-flashcards --set $conf --name-format full --name-order city_first --output-dir "output/college/$conf"
}
```

---

### GUI Configuration

The GUI now includes three new sections:

**1. Filename Format (Radio Buttons)**
- Prefix: `front_NAME.png` / `back_NAME.png`
- Suffix: `NAME_front.png` / `NAME_back.png`

**2. Name Format (Radio Buttons)**
- Full: City + Team (e.g., San Francisco 49ers)
- Team Only (e.g., 49ers)
- City Only (e.g., San Francisco)

**3. Name Order (Radio Buttons - enabled only for Full format)**
- City First: San Francisco 49ers
- Team First: 49ers San Francisco

When you select "Team Only" or "City Only" in the Name Format, the Name Order buttons automatically disable since they only apply to "Full" format.

---

### Real-World Use Cases

**Scenario 1: Quick study flashcards (minimal filenames)**
```powershell
sports-flashcards --set acc --name-format team_only --filename-format suffix
```
Result: Simple, clean files like `tar_heels_front.png`

**Scenario 2: Print-ready full descriptions**
```powershell
sports-flashcards --set nfl --dpi 600 --name-format full --name-order city_first
```
Result: High-quality with full city+team names

**Scenario 3: Collection with consistent format**
```powershell
sports-flashcards --set mlb --filename-format suffix --name-format full
sports-flashcards --set nfl --filename-format suffix --name-format full
sports-flashcards --set nba --filename-format suffix --name-format full
```
Result: All use same naming convention for easier sorting/organization

---

### Configuration Defaults

| Option | Default |
|--------|---------|
| filename_format | prefix |
| name_format | full |
| name_order | city_first |
| dpi | 300 |
| output_dir | output/{set_code}/ |
| logos_dir | data/logos_raw/ |

---

### Tips

✅ **GUI is beginner-friendly** — Use radio buttons, all options visible, disabled options when N/A  
✅ **CLI is powerful** — All options available for advanced users and automation  
✅ **Consistent output** — Same core logic, same formatting in GUI and CLI  
✅ **Batch friendly** — Use CLI loops to generate all sets with consistent formatting
