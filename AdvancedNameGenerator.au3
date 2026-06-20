#include <GUIConstantsEx.au3>
#include <WindowsConstants.au3>
#include <EditConstants.au3>
#include <ComboConstants.au3>
#include <GuiComboBox.au3>
#include <ButtonConstants.au3>
#include <StaticConstants.au3>
#include <ListViewConstants.au3>
#include <GuiListView.au3>
#include <SliderConstants.au3>
#include <StructureConstants.au3>
#include <WindowsNotifsConstants.au3>

Opt("MustDeclareVars", 1)

Global Const $APP_TITLE = "Advanced Short Name Generator"
Global Const $DEFAULT_MAX_LEN = 9
Global Const $DEFAULT_COUNT = 50
Global Const $DISPLAY_COLUMNS = 4
Global Const $FAV_COLUMNS = 1

Global Const $CAT_ALL = "Any"
Global Const $CAT_RELIC = "Relic"
Global Const $CAT_MACHINE = "Machine"
Global Const $CAT_CREATURE = "Creature"
Global Const $CAT_PLACE = "Place"
Global Const $CAT_FACTION = "Faction"
Global Const $CAT_SPELL = "Spell"
Global Const $CAT_MINERAL = "Mineral"
Global Const $CAT_CUTE = "Cute"
Global Const $CAT_ELVEN = "Elven"
Global Const $CAT_PET = "Pet"
Global Const $CAT_CELESTIAL = "Celestial"
Global Const $CAT_NATURE = "Nature"
Global Const $CAT_FOOD = "Food"
Global Const $CAT_WEAPON = "Weapon"
Global Const $CAT_POTION = "Potion"
Global Const $CAT_SHIP = "Ship"
Global Const $CAT_DUNGEON = "Dungeon"
Global Const $CAT_TOY = "Toy"
Global Const $CAT_SPIRIT = "Spirit"
Global Const $CATEGORY_LIST = $CAT_RELIC & "|" & $CAT_MACHINE & "|" & $CAT_CREATURE & "|" & $CAT_PLACE & "|" & $CAT_FACTION & "|" & $CAT_SPELL & "|" & $CAT_MINERAL & "|" & $CAT_CUTE & "|" & $CAT_ELVEN & "|" & $CAT_PET & "|" & $CAT_CELESTIAL & "|" & $CAT_NATURE & "|" & $CAT_FOOD & "|" & $CAT_WEAPON & "|" & $CAT_POTION & "|" & $CAT_SHIP & "|" & $CAT_DUNGEON & "|" & $CAT_TOY & "|" & $CAT_SPIRIT

Global Const $STYLE_MIXED = "Mixed"
Global Const $STYLE_SHARP = "Sharp"
Global Const $STYLE_SOFT = "Soft"
Global Const $STYLE_ANCIENT = "Ancient"
Global Const $STYLE_TECH = "Tech"
Global Const $STYLE_ELDRITCH = "Eldritch"

Global Const $GENDER_ANY = "Any"
Global Const $GENDER_NEUTRAL = "Neutral"
Global Const $GENDER_MASC = "Masculine"
Global Const $GENDER_FEM = "Feminine"

Global Const $PRESET_CUSTOM = "Custom"
Global Const $PRESET_FANTASY = "Fantasy Relics"
Global Const $PRESET_SCIFI = "Sci-Fi Machines"
Global Const $PRESET_CREATURES = "Creatures"
Global Const $PRESET_PLACES = "Places"
Global Const $PRESET_FACTIONS = "Factions"
Global Const $PRESET_ARCANE = "Arcane Spells"
Global Const $PRESET_MINERALS = "Mineral Veins"
Global Const $PRESET_ANCIENT = "Ancient Dark"
Global Const $PRESET_SOFT = "Soft Mythic"
Global Const $PRESET_INDUSTRIAL = "Industrial"
Global Const $PRESET_CUTE = "Cute Trinkets"
Global Const $PRESET_ELVEN = "Elven Things"
Global Const $PRESET_PET = "Pet Names"
Global Const $PRESET_CELESTIAL = "Celestial"
Global Const $PRESET_NATURE = "Nature"
Global Const $PRESET_FOOD = "Snackable"
Global Const $PRESET_WEAPON = "Weapons"
Global Const $PRESET_POTION = "Potions"
Global Const $PRESET_SHIP = "Ships"
Global Const $PRESET_DUNGEON = "Dungeons"
Global Const $PRESET_TOY = "Toys"
Global Const $PRESET_SPIRIT = "Spirits"
Global Const $PRESET_LIST = $PRESET_FANTASY & "|" & $PRESET_SCIFI & "|" & $PRESET_CREATURES & "|" & $PRESET_PLACES & "|" & $PRESET_FACTIONS & "|" & $PRESET_ARCANE & "|" & $PRESET_MINERALS & "|" & $PRESET_ANCIENT & "|" & $PRESET_SOFT & "|" & $PRESET_INDUSTRIAL & "|" & $PRESET_CUTE & "|" & $PRESET_ELVEN & "|" & $PRESET_PET & "|" & $PRESET_CELESTIAL & "|" & $PRESET_NATURE & "|" & $PRESET_FOOD & "|" & $PRESET_WEAPON & "|" & $PRESET_POTION & "|" & $PRESET_SHIP & "|" & $PRESET_DUNGEON & "|" & $PRESET_TOY & "|" & $PRESET_SPIRIT

Global Const $L_START_SHARP = "k|kr|sk|v|z|x|dr|gr|t|tr|q|n|r|br|vr|cl|kh|zr|gh|kt|vrak|drek|zh"
Global Const $L_MID_SHARP = "ak|ekt|orn|rax|vek|isk|tor|zar|grim|nok|vak|rek|usk|drox|karn|thak|zorn|grix|vokt|krul|sark|qen|drek"
Global Const $L_END_SHARP = "k|x|r|n|th|z|v|m|sk|ct|g|rk|kt|zh|qr|dr|gh"

Global Const $L_START_SOFT = "a|ae|o|u|e|l|m|s|sh|n|w|y|v|li|mo|sa|lo|emi|ora|yel|hue|nali|vae|pim|bibi|lulu|fae|miri|tula|poppy"
Global Const $L_MID_SOFT = "ala|ori|une|mira|luma|sai|voro|ely|ona|iri|nua|sol|via|aro|lia|omi|evo|sela|yuna|hael|avel|boba|pipi|lala|momo|lili|tini|firi|aeri"
Global Const $L_END_SOFT = "a|o|u|el|en|is|or|um|ai|ia|on|il|iel|oa|ue|al|ea|ie|y|li|mi|wyn|bell"

Global Const $L_START_ODD = "ul|yr|az|oth|ix|nix|vael|qor|zhu|kh|dra|nyx|or|ark|esh|xoth|uln|qai|zuel|yrr|omth|ghul"
Global Const $L_MID_ODD = "oth|yrr|aza|uum|ix|esh|ohr|qul|vae|gath|noq|zeh|xil|uln|ryth|aun|qith|vohr|ux|yoth|zai"
Global Const $L_END_ODD = "oth|yx|ul|esh|az|um|ix|or|ael|uun|q|h|yr|yth|aun|qir|ohr|ryl"

Global Const $L_RELIC_A = "Shard|Orb|Sigil|Crown|Idol|Key|Rune|Lens|Mask|Seal|Core|Chime|Obel|Totem"
Global Const $L_MACHINE_A = "Cog|Node|Gear|Relay|Unit|Probe|Drone|Mech|Forge|Array|Servo|Kern|Spool"
Global Const $L_CREATURE_A = "Murk|Skitter|Gloom|Vex|Ridge|Ash|Fang|Mire|Thorn|Husk|Spine|Umber"
Global Const $L_PLACE_A = "Vale|Spire|Rift|Hollow|Reach|Basin|Fjord|Crag|Moor|Gate|Well|Barrow"
Global Const $L_FACTION_A = "Order|Circle|Cabal|Crew|Fleet|Host|Guild|Sect|Pack|Kin|Band|Cell"
Global Const $L_SPELL_A = "Hex|Ward|Blink|Gale|Flare|Veil|Bind|Pulse|Glim|Frost|Mend|Rend"
Global Const $L_MINERAL_A = "Onyx|Jade|Opal|Beryl|Cinn|Quartz|Flint|Amber|Ichor|Basalt|Cobalt|Mica"
Global Const $L_CUTE_A = "Charm|Pebble|Button|Pip|Puff|Mote|Nib|Sprig|Doodle|Wish|Glow|Bop|Tink|Pom|Bibble|Bumble"
Global Const $L_ELVEN_A = "Grove|Leaf|Moon|Vale|Glade|Star|Bloom|Spire|Bough|Aster|Lumen|Syl|Veya|Thorn|Lyre|Rune"
Global Const $L_PET_A = "Paw|Whisk|Nuzzle|Pip|Moss|Sprout|Biscuit|Pebble|Pounce|Snug|Tuff|Muff|Wiggle|Dapple|Tumble"
Global Const $L_CELESTIAL_A = "Nova|Comet|Astra|Halo|Orbit|Zenith|Eclipse|Meteor|Luna|Sol|Corona|Nebula|Vesper|Ray"
Global Const $L_NATURE_A = "Fern|Briar|Clover|Moss|Reed|Acorn|Thistle|Bloom|Root|Fawn|Dew|Grove|Petal|Bark|Lichen"
Global Const $L_FOOD_A = "Mochi|Nori|Boba|Dumpling|Pepper|Miso|Honey|Plum|Bean|Berry|Noodle|Toast|Waffle|Pickle|Taffy"
Global Const $L_WEAPON_A = "Blade|Pike|Axe|Spear|Fang|Edge|Glaive|Mace|Dart|Bow|Hook|Lance|Saber|Claw|Hammer"
Global Const $L_POTION_A = "Vial|Draught|Tonic|Elixir|Phial|Drop|Mist|Brew|Syrup|Dose|Ampoule|Essence|Flask"
Global Const $L_SHIP_A = "Skiff|Sloop|Ark|Cutter|Barge|Ketch|Dhow|Launch|Raft|Galley|Keel|Clipper|Cog"
Global Const $L_DUNGEON_A = "Vault|Crypt|Warren|Keep|Maze|Pit|Cellar|Gaol|Underhall|Lair|Lock|Den|Chasm|Burrow"
Global Const $L_TOY_A = "Kite|Top|YoYo|Marble|Doll|Puzzle|Block|Whistle|Rattle|Hoop|Card|Spinner|Bauble"
Global Const $L_SPIRIT_A = "Wisp|Shade|Echo|Glimmer|Whisper|Gleam|Murmur|Vapor|Phantom|Flicker|Sigh|Trace"

Global Const $L_RELIC_B = "lost|hush|void|star|iron|old|dusk|ember|glass|moon|thorn|pale"
Global Const $L_MACHINE_B = "zero|alpha|static|pulse|prime|ion|servo|nano|clock|vector|byte|phase"
Global Const $L_CREATURE_B = "fen|moss|cave|night|bone|salt|spore|brine|scar|reed|smoke|rust"
Global Const $L_PLACE_B = "low|red|grim|mist|ashen|cold|deep|north|salt|sunken|wild|black"
Global Const $L_FACTION_B = "red|gray|veiled|iron|amber|silent|outer|hollow|twin|lunar|brass"
Global Const $L_SPELL_B = "quick|cold|dire|mute|bright|thin|wild|nether|minor|grave|solar|vile"
Global Const $L_MINERAL_B = "blue|green|red|dark|bright|raw|vein|deep|cloud|star|ghost|iron"
Global Const $L_CUTE_B = "tiny|sweet|mint|soft|bright|snug|lucky|little|rosy|sunny|cozy|plush|pearl|bubble|daisy"
Global Const $L_ELVEN_B = "silver|aurel|lunar|willow|elder|green|white|golden|mist|sun|river|veil|fey|aerie|glass"
Global Const $L_PET_B = "small|happy|drowsy|spotted|fluffy|brave|silly|warm|muddy|sleepy|quick|pocket|curly|nimble"
Global Const $L_CELESTIAL_B = "star|void|solar|lunar|upper|bright|far|deep|blue|gold|radiant|silent|night|cosmic"
Global Const $L_NATURE_B = "wild|green|rain|river|pine|meadow|sun|root|mossy|spring|autumn|honey|dew|leafy"
Global Const $L_FOOD_B = "sweet|spiced|crispy|warm|golden|sour|berry|mint|honey|salted|toasty|sugar|soft|butter"
Global Const $L_WEAPON_B = "iron|sharp|black|red|keen|broken|brass|moon|ember|thorn|wolf|ash|hollow|bright"
Global Const $L_POTION_B = "clear|red|blue|bitter|sweet|sleep|quick|gold|frost|dream|moss|spark|ghost|warm"
Global Const $L_SHIP_B = "swift|salt|star|black|red|mist|wind|moon|reef|storm|brass|white|blue|lone"
Global Const $L_DUNGEON_B = "deep|old|black|damp|grim|sunken|hollow|lost|sealed|moss|bone|cold|lower|silent"
Global Const $L_TOY_B = "tiny|painted|bright|spinning|wooden|paper|lucky|striped|tin|clock|ribbon|pocket|plush"
Global Const $L_SPIRIT_B = "pale|soft|lost|quiet|silver|wan|dream|moon|thin|mist|old|hush|faint|blue"

Global Const $L_SPECIAL_START = "ael|ka|kha|mor|vor|nyx|ryn|tha|ul|esh|zor|ira|om|vyr|xan|qor|bel|dru|var|zul|myr|oan|thal|vek"
Global Const $L_SPECIAL_START_SHARP = "kha|kr|vyr|zor|xan|qor|dra|sk|vr|zha|tor|gr|ghor|krel|drax|zekt|qul|vorn|brak|thok"
Global Const $L_SPECIAL_START_SOFT = "ael|ira|omi|lue|sai|mira|ora|nua|ely|sha|yel|vae|sola|nori|mae|ulo|hira|lomi|suen|pim|bibi|lulu|mimi|tutu|fae|aeri|lora"
Global Const $L_SPECIAL_START_TECH = "cy|neo|hex|syn|tek|vox|ion|opt|dat|mod|xen|ark|bit|kern|nox|quant|servo|axi|loop"
Global Const $L_SPECIAL_END = "ith|oth|ryn|ael|yr|uun|ix|esh|or|ul|ara|ion|os|eth|rynth|um|ath|aul|eir|uun|aiq|eshk|ora"
Global Const $L_SPECIAL_END_SHARP = "ith|oth|yx|ix|ark|ekt|orn|sk|vak|z|ryn|drox|qath|gorn|vrek|kt|zoth|drak|thryn"
Global Const $L_SPECIAL_END_SOFT = "ael|ara|ia|iel|ora|une|ai|en|is|ryn|ella|um|oel|ielu|aun|iri|ae|lian|uen|wyn|bell|belle|li|mi|puff|pop"
Global Const $L_SPECIAL_END_TECH = "ix|ion|ex|0n|tek|x|v|q|ram|dat|sync|bit|bus|mod|core|byte|nix|loop|ware"
Global Const $L_BRIDGE = "a|e|i|o|u|ae|ia|io|oa|yr|ul|om|esh|ai|ei|au"
Global Const $L_COMPACT_CORE = "bar|cal|dur|fen|gol|hal|isk|jor|kel|lor|mak|nel|por|quil|ren|sor|tan|val|wex|yul|zen"

Global $g_idPreset, $g_idCategory, $g_idStyle, $g_idGender, $g_idCount, $g_idMaxLen, $g_idHyphen, $g_idNumbers
Global $g_idWeird, $g_idWeirdValue, $g_idSeed, $g_idOutput, $g_idFavorites
Global $g_idGenerate, $g_idCopyList, $g_idCopySelected, $g_idFavorite, $g_idCopyFavs, $g_idRemoveFav, $g_idSave, $g_idClear
Global $g_iRoll = 0
Global $g_sLastOutput = ""
Global $g_sSelectedName = ""
Global $g_sFavorites = "|"

Main()

Func Main()
    Local $hGui = GUICreate($APP_TITLE, 980, 620, -1, -1, BitOR($WS_CAPTION, $WS_SYSMENU, $WS_MINIMIZEBOX))
    GUISetBkColor(0xF4F1EA, $hGui)
    GUIRegisterMsg($WM_NOTIFY, "WM_NOTIFY")

    GUICtrlCreateLabel("Preset", 18, 18, 80, 20)
    $g_idPreset = GUICtrlCreateCombo($PRESET_CUSTOM, 18, 40, 150, 24, $CBS_DROPDOWNLIST)
    GUICtrlSetData($g_idPreset, $PRESET_LIST, $PRESET_CUSTOM)

    GUICtrlCreateLabel("Category", 186, 18, 80, 20)
    $g_idCategory = GUICtrlCreateCombo($CAT_ALL, 186, 40, 132, 24, $CBS_DROPDOWNLIST)
    GUICtrlSetData($g_idCategory, $CATEGORY_LIST, $CAT_ALL)

    GUICtrlCreateLabel("Style", 336, 18, 80, 20)
    $g_idStyle = GUICtrlCreateCombo($STYLE_MIXED, 336, 40, 132, 24, $CBS_DROPDOWNLIST)
    GUICtrlSetData($g_idStyle, $STYLE_SHARP & "|" & $STYLE_SOFT & "|" & $STYLE_ANCIENT & "|" & $STYLE_TECH & "|" & $STYLE_ELDRITCH, $STYLE_MIXED)

    GUICtrlCreateLabel("Gender", 486, 18, 80, 20)
    $g_idGender = GUICtrlCreateCombo($GENDER_ANY, 486, 40, 110, 24, $CBS_DROPDOWNLIST)
    GUICtrlSetData($g_idGender, $GENDER_NEUTRAL & "|" & $GENDER_MASC & "|" & $GENDER_FEM, $GENDER_ANY)

    GUICtrlCreateLabel("Count", 614, 18, 80, 20)
    $g_idCount = GUICtrlCreateInput($DEFAULT_COUNT, 614, 40, 64, 24, BitOR($ES_NUMBER, $ES_CENTER))

    GUICtrlCreateLabel("Max length", 696, 18, 90, 20)
    $g_idMaxLen = GUICtrlCreateInput($DEFAULT_MAX_LEN, 696, 40, 64, 24, BitOR($ES_NUMBER, $ES_CENTER))

    $g_idHyphen = GUICtrlCreateCheckbox("Allow hyphen", 780, 38, 105, 24)
    $g_idNumbers = GUICtrlCreateCheckbox("Tech digits", 780, 64, 105, 24)

    GUICtrlCreateLabel("Seed", 18, 78, 80, 20)
    $g_idSeed = GUICtrlCreateInput("", 18, 100, 150, 24)

    GUICtrlCreateLabel("Weirdness", 186, 78, 80, 20)
    $g_idWeird = GUICtrlCreateSlider(186, 98, 180, 32, BitOR($TBS_AUTOTICKS, $TBS_TOOLTIPS))
    GUICtrlSetLimit($g_idWeird, 10, 0)
    GUICtrlSetData($g_idWeird, 5)
    $g_idWeirdValue = GUICtrlCreateLabel("5", 372, 104, 24, 20, $SS_CENTER)

    $g_idGenerate = GUICtrlCreateButton("Generate", 414, 96, 96, 28)
    $g_idCopySelected = GUICtrlCreateButton("Copy Selected", 518, 96, 102, 28)
    $g_idFavorite = GUICtrlCreateButton("Favorite", 628, 96, 82, 28)
    $g_idCopyList = GUICtrlCreateButton("Copy List", 718, 96, 82, 28)
    $g_idSave = GUICtrlCreateButton("Save", 808, 96, 72, 28)
    $g_idClear = GUICtrlCreateButton("Clear", 888, 96, 72, 28)

    GUICtrlCreateLabel("Generated", 18, 164, 120, 20)
    GUICtrlCreateLabel("Favorites / Locks", 722, 164, 140, 20)
    $g_idCopyFavs = GUICtrlCreateButton("Copy Favs", 826, 160, 70, 24)
    $g_idRemoveFav = GUICtrlCreateButton("Remove", 904, 160, 56, 24)

    $g_idOutput = GUICtrlCreateListView("#|Name|#|Name|#|Name|#|Name", 18, 190, 690, 390, BitOR($LVS_REPORT, $LVS_SHOWSELALWAYS))
    GUICtrlSetFont($g_idOutput, 10, 400, 0, "Consolas")
    ConfigureOutputList()

    $g_idFavorites = GUICtrlCreateListView("Name", 722, 190, 238, 390, BitOR($LVS_REPORT, $LVS_SHOWSELALWAYS))
    GUICtrlSetFont($g_idFavorites, 10, 400, 0, "Consolas")
    ConfigureFavoritesList()

    GUISetState(@SW_SHOW, $hGui)
    GenerateToOutput()

    While 1
        Switch GUIGetMsg()
            Case $GUI_EVENT_CLOSE
                ExitLoop
            Case $g_idPreset
                ApplyPreset(GUICtrlRead($g_idPreset))
            Case $g_idWeird
                GUICtrlSetData($g_idWeirdValue, GUICtrlRead($g_idWeird))
            Case $g_idGenerate
                GenerateToOutput()
            Case $g_idCopySelected
                CopySelectedName()
            Case $g_idFavorite
                FavoriteSelectedName()
            Case $g_idCopyList
                ClipPut($g_sLastOutput)
            Case $g_idCopyFavs
                ClipPut(BuildFavoritesText())
            Case $g_idRemoveFav
                RemoveSelectedFavorite()
            Case $g_idSave
                SaveOutput()
            Case $g_idClear
                ClearOutput()
        EndSwitch
    WEnd

    GUIDelete($hGui)
EndFunc

Func GenerateToOutput()
    Local $sCategory = GUICtrlRead($g_idCategory)
    Local $sStyle = GUICtrlRead($g_idStyle)
    Local $sGender = GUICtrlRead($g_idGender)
    Local $iCount = _ClampInt(GUICtrlRead($g_idCount), 1, 250, $DEFAULT_COUNT)
    Local $iMaxLen = _ClampInt(GUICtrlRead($g_idMaxLen), 4, 14, $DEFAULT_MAX_LEN)
    Local $iWeirdness = _ClampInt(GUICtrlRead($g_idWeird), 0, 10, 5)
    Local $bHyphen = (GUICtrlRead($g_idHyphen) = $GUI_CHECKED)
    Local $bNumbers = (GUICtrlRead($g_idNumbers) = $GUI_CHECKED)
    Local $sSeed = StringStripWS(GUICtrlRead($g_idSeed), 3)

    If $sSeed <> "" Then
        SRandom(_SeedToInt($sSeed))
    Else
        $g_iRoll += 1
        SRandom(_FreshSeed($g_iRoll))
    EndIf

    Local $sOut = ""
    Local $sName = ""
    Local $sSeen = "|"
    Local $aNames[$iCount + 1]

    For $i = 1 To $iCount
        $sName = GenerateName($sCategory, $sStyle, $sGender, $iMaxLen, $iWeirdness, $bHyphen, $bNumbers)
        For $iTry = 1 To 12
            If Not StringInStr($sSeen, "|" & StringLower($sName) & "|") Then ExitLoop
            $sName = GenerateName($sCategory, $sStyle, $sGender, $iMaxLen, $iWeirdness, $bHyphen, $bNumbers)
        Next
        $sSeen &= StringLower($sName) & "|"
        $aNames[$i] = $sName
        $sOut &= StringRight("00" & $i, 3) & "  " & $sName & @CRLF
    Next

    $g_sLastOutput = $sOut
    PopulateOutputList($aNames, $iCount)
EndFunc

Func ConfigureOutputList()
    _GUICtrlListView_SetExtendedListViewStyle($g_idOutput, BitOR($LVS_EX_FULLROWSELECT, $LVS_EX_GRIDLINES))

    For $i = 0 To $DISPLAY_COLUMNS - 1
        _GUICtrlListView_SetColumnWidth($g_idOutput, $i * 2, 42)
        _GUICtrlListView_SetColumnWidth($g_idOutput, ($i * 2) + 1, 128)
    Next
EndFunc

Func ConfigureFavoritesList()
    _GUICtrlListView_SetExtendedListViewStyle($g_idFavorites, BitOR($LVS_EX_FULLROWSELECT, $LVS_EX_GRIDLINES))
    _GUICtrlListView_SetColumnWidth($g_idFavorites, 0, 214)
EndFunc

Func PopulateOutputList(ByRef $aNames, $iCount)
    _GUICtrlListView_DeleteAllItems($g_idOutput)

    Local $iRows = Int(($iCount + $DISPLAY_COLUMNS - 1) / $DISPLAY_COLUMNS)
    Local $sRow = ""
    Local $iIndex = 0

    For $iRow = 1 To $iRows
        $sRow = ""
        For $iCol = 0 To $DISPLAY_COLUMNS - 1
            $iIndex = $iRow + ($iCol * $iRows)
            If $iCol > 0 Then $sRow &= "|"

            If $iIndex <= $iCount Then
                $sRow &= StringRight("00" & $iIndex, 3) & "|" & $aNames[$iIndex]
            Else
                $sRow &= "|"
            EndIf
        Next
        GUICtrlCreateListViewItem($sRow, $g_idOutput)
    Next
EndFunc

Func ClearOutput()
    _GUICtrlListView_DeleteAllItems($g_idOutput)
    $g_sLastOutput = ""
    $g_sSelectedName = ""
EndFunc

Func ApplyPreset($sPreset)
    Switch $sPreset
        Case $PRESET_FANTASY
            SetComboValue($g_idCategory, $CAT_RELIC)
            SetComboValue($g_idStyle, $STYLE_ANCIENT)
            SetComboValue($g_idGender, $GENDER_ANY)
            SetWeirdness(6)
            GUICtrlSetState($g_idHyphen, $GUI_UNCHECKED)
            GUICtrlSetState($g_idNumbers, $GUI_UNCHECKED)
        Case $PRESET_SCIFI
            SetComboValue($g_idCategory, $CAT_MACHINE)
            SetComboValue($g_idStyle, $STYLE_TECH)
            SetComboValue($g_idGender, $GENDER_NEUTRAL)
            SetWeirdness(5)
            GUICtrlSetState($g_idHyphen, $GUI_UNCHECKED)
            GUICtrlSetState($g_idNumbers, $GUI_CHECKED)
        Case $PRESET_CREATURES
            SetComboValue($g_idCategory, $CAT_CREATURE)
            SetComboValue($g_idStyle, $STYLE_ELDRITCH)
            SetComboValue($g_idGender, $GENDER_ANY)
            SetWeirdness(7)
            GUICtrlSetState($g_idHyphen, $GUI_UNCHECKED)
            GUICtrlSetState($g_idNumbers, $GUI_UNCHECKED)
        Case $PRESET_PLACES
            SetComboValue($g_idCategory, $CAT_PLACE)
            SetComboValue($g_idStyle, $STYLE_MIXED)
            SetComboValue($g_idGender, $GENDER_NEUTRAL)
            SetWeirdness(4)
            GUICtrlSetState($g_idHyphen, $GUI_CHECKED)
            GUICtrlSetState($g_idNumbers, $GUI_UNCHECKED)
        Case $PRESET_FACTIONS
            SetComboValue($g_idCategory, $CAT_FACTION)
            SetComboValue($g_idStyle, $STYLE_SHARP)
            SetComboValue($g_idGender, $GENDER_MASC)
            SetWeirdness(4)
            GUICtrlSetState($g_idHyphen, $GUI_CHECKED)
            GUICtrlSetState($g_idNumbers, $GUI_UNCHECKED)
        Case $PRESET_ARCANE
            SetComboValue($g_idCategory, $CAT_SPELL)
            SetComboValue($g_idStyle, $STYLE_ELDRITCH)
            SetComboValue($g_idGender, $GENDER_FEM)
            SetWeirdness(8)
            GUICtrlSetState($g_idHyphen, $GUI_UNCHECKED)
            GUICtrlSetState($g_idNumbers, $GUI_UNCHECKED)
        Case $PRESET_MINERALS
            SetComboValue($g_idCategory, $CAT_MINERAL)
            SetComboValue($g_idStyle, $STYLE_MIXED)
            SetComboValue($g_idGender, $GENDER_NEUTRAL)
            SetWeirdness(3)
            GUICtrlSetState($g_idHyphen, $GUI_UNCHECKED)
            GUICtrlSetState($g_idNumbers, $GUI_UNCHECKED)
        Case $PRESET_ANCIENT
            SetComboValue($g_idCategory, $CAT_ALL)
            SetComboValue($g_idStyle, $STYLE_ANCIENT)
            SetComboValue($g_idGender, $GENDER_ANY)
            SetWeirdness(8)
            GUICtrlSetState($g_idHyphen, $GUI_CHECKED)
            GUICtrlSetState($g_idNumbers, $GUI_UNCHECKED)
        Case $PRESET_SOFT
            SetComboValue($g_idCategory, $CAT_ALL)
            SetComboValue($g_idStyle, $STYLE_SOFT)
            SetComboValue($g_idGender, $GENDER_FEM)
            SetWeirdness(5)
            GUICtrlSetState($g_idHyphen, $GUI_UNCHECKED)
            GUICtrlSetState($g_idNumbers, $GUI_UNCHECKED)
        Case $PRESET_INDUSTRIAL
            SetComboValue($g_idCategory, $CAT_MACHINE)
            SetComboValue($g_idStyle, $STYLE_SHARP)
            SetComboValue($g_idGender, $GENDER_NEUTRAL)
            SetWeirdness(4)
            GUICtrlSetState($g_idHyphen, $GUI_CHECKED)
            GUICtrlSetState($g_idNumbers, $GUI_CHECKED)
        Case $PRESET_CUTE
            SetComboValue($g_idCategory, $CAT_CUTE)
            SetComboValue($g_idStyle, $STYLE_SOFT)
            SetComboValue($g_idGender, $GENDER_FEM)
            SetWeirdness(2)
            GUICtrlSetState($g_idHyphen, $GUI_UNCHECKED)
            GUICtrlSetState($g_idNumbers, $GUI_UNCHECKED)
        Case $PRESET_ELVEN
            SetComboValue($g_idCategory, $CAT_ELVEN)
            SetComboValue($g_idStyle, $STYLE_SOFT)
            SetComboValue($g_idGender, $GENDER_ANY)
            SetWeirdness(5)
            GUICtrlSetState($g_idHyphen, $GUI_UNCHECKED)
            GUICtrlSetState($g_idNumbers, $GUI_UNCHECKED)
        Case $PRESET_PET
            SetComboValue($g_idCategory, $CAT_PET)
            SetComboValue($g_idStyle, $STYLE_SOFT)
            SetComboValue($g_idGender, $GENDER_ANY)
            SetWeirdness(1)
            GUICtrlSetState($g_idHyphen, $GUI_UNCHECKED)
            GUICtrlSetState($g_idNumbers, $GUI_UNCHECKED)
        Case $PRESET_CELESTIAL
            SetComboValue($g_idCategory, $CAT_CELESTIAL)
            SetComboValue($g_idStyle, $STYLE_ANCIENT)
            SetComboValue($g_idGender, $GENDER_NEUTRAL)
            SetWeirdness(6)
            GUICtrlSetState($g_idHyphen, $GUI_UNCHECKED)
            GUICtrlSetState($g_idNumbers, $GUI_UNCHECKED)
        Case $PRESET_NATURE
            SetComboValue($g_idCategory, $CAT_NATURE)
            SetComboValue($g_idStyle, $STYLE_SOFT)
            SetComboValue($g_idGender, $GENDER_NEUTRAL)
            SetWeirdness(3)
            GUICtrlSetState($g_idHyphen, $GUI_UNCHECKED)
            GUICtrlSetState($g_idNumbers, $GUI_UNCHECKED)
        Case $PRESET_FOOD
            SetComboValue($g_idCategory, $CAT_FOOD)
            SetComboValue($g_idStyle, $STYLE_SOFT)
            SetComboValue($g_idGender, $GENDER_ANY)
            SetWeirdness(2)
            GUICtrlSetState($g_idHyphen, $GUI_UNCHECKED)
            GUICtrlSetState($g_idNumbers, $GUI_UNCHECKED)
        Case $PRESET_WEAPON
            SetComboValue($g_idCategory, $CAT_WEAPON)
            SetComboValue($g_idStyle, $STYLE_SHARP)
            SetComboValue($g_idGender, $GENDER_MASC)
            SetWeirdness(5)
            GUICtrlSetState($g_idHyphen, $GUI_CHECKED)
            GUICtrlSetState($g_idNumbers, $GUI_UNCHECKED)
        Case $PRESET_POTION
            SetComboValue($g_idCategory, $CAT_POTION)
            SetComboValue($g_idStyle, $STYLE_SOFT)
            SetComboValue($g_idGender, $GENDER_NEUTRAL)
            SetWeirdness(4)
            GUICtrlSetState($g_idHyphen, $GUI_UNCHECKED)
            GUICtrlSetState($g_idNumbers, $GUI_UNCHECKED)
        Case $PRESET_SHIP
            SetComboValue($g_idCategory, $CAT_SHIP)
            SetComboValue($g_idStyle, $STYLE_MIXED)
            SetComboValue($g_idGender, $GENDER_NEUTRAL)
            SetWeirdness(4)
            GUICtrlSetState($g_idHyphen, $GUI_CHECKED)
            GUICtrlSetState($g_idNumbers, $GUI_UNCHECKED)
        Case $PRESET_DUNGEON
            SetComboValue($g_idCategory, $CAT_DUNGEON)
            SetComboValue($g_idStyle, $STYLE_ELDRITCH)
            SetComboValue($g_idGender, $GENDER_ANY)
            SetWeirdness(7)
            GUICtrlSetState($g_idHyphen, $GUI_CHECKED)
            GUICtrlSetState($g_idNumbers, $GUI_UNCHECKED)
        Case $PRESET_TOY
            SetComboValue($g_idCategory, $CAT_TOY)
            SetComboValue($g_idStyle, $STYLE_SOFT)
            SetComboValue($g_idGender, $GENDER_ANY)
            SetWeirdness(2)
            GUICtrlSetState($g_idHyphen, $GUI_UNCHECKED)
            GUICtrlSetState($g_idNumbers, $GUI_UNCHECKED)
        Case $PRESET_SPIRIT
            SetComboValue($g_idCategory, $CAT_SPIRIT)
            SetComboValue($g_idStyle, $STYLE_ELDRITCH)
            SetComboValue($g_idGender, $GENDER_FEM)
            SetWeirdness(6)
            GUICtrlSetState($g_idHyphen, $GUI_UNCHECKED)
            GUICtrlSetState($g_idNumbers, $GUI_UNCHECKED)
    EndSwitch
EndFunc

Func SetComboValue($idControl, $sValue)
    _GUICtrlComboBox_SelectString(GUICtrlGetHandle($idControl), $sValue)
EndFunc

Func SetWeirdness($iValue)
    GUICtrlSetData($g_idWeird, $iValue)
    GUICtrlSetData($g_idWeirdValue, $iValue)
EndFunc

Func CopySelectedName()
    Local $sName = $g_sSelectedName
    If $sName = "" Then $sName = GetFirstSelectedGeneratedName()
    If $sName = "" Then $sName = GetFirstSelectedFavoriteName()
    If $sName <> "" Then ClipPut($sName)
EndFunc

Func FavoriteSelectedName()
    Local $sName = $g_sSelectedName
    If $sName = "" Then $sName = GetFirstSelectedGeneratedName()
    If $sName <> "" Then AddFavorite($sName)
EndFunc

Func AddFavorite($sName)
    $sName = StringStripWS($sName, 3)
    If $sName = "" Then Return
    If StringInStr($g_sFavorites, "|" & StringLower($sName) & "|") Then Return

    $g_sFavorites &= StringLower($sName) & "|"
    GUICtrlCreateListViewItem($sName, $g_idFavorites)
EndFunc

Func RemoveSelectedFavorite()
    Local $aSelected = _GUICtrlListView_GetSelectedIndices($g_idFavorites, True)
    If Not IsArray($aSelected) Then Return

    For $i = $aSelected[0] To 1 Step -1
        _GUICtrlListView_DeleteItem($g_idFavorites, $aSelected[$i])
    Next

    RebuildFavoritesState()
EndFunc

Func RebuildFavoritesState()
    $g_sFavorites = "|"
    Local $iCount = _GUICtrlListView_GetItemCount($g_idFavorites)
    Local $sName = ""

    For $i = 0 To $iCount - 1
        $sName = _GUICtrlListView_GetItemText($g_idFavorites, $i, 0)
        If $sName <> "" Then $g_sFavorites &= StringLower($sName) & "|"
    Next
EndFunc

Func BuildFavoritesText()
    Local $sOut = ""
    Local $iCount = _GUICtrlListView_GetItemCount($g_idFavorites)
    Local $sName = ""

    For $i = 0 To $iCount - 1
        $sName = _GUICtrlListView_GetItemText($g_idFavorites, $i, 0)
        If $sName <> "" Then $sOut &= StringRight("00" & ($i + 1), 3) & "  " & $sName & @CRLF
    Next

    Return $sOut
EndFunc

Func GetFirstSelectedGeneratedName()
    Local $aSelected = _GUICtrlListView_GetSelectedIndices($g_idOutput, True)
    If Not IsArray($aSelected) Then Return ""

    Local $sName = ""
    For $i = 1 To $aSelected[0]
        For $iSub = 1 To (($DISPLAY_COLUMNS * 2) - 1) Step 2
            $sName = _GUICtrlListView_GetItemText($g_idOutput, $aSelected[$i], $iSub)
            If $sName <> "" Then Return $sName
        Next
    Next

    Return ""
EndFunc

Func GetFirstSelectedFavoriteName()
    Local $aSelected = _GUICtrlListView_GetSelectedIndices($g_idFavorites, True)
    If Not IsArray($aSelected) Then Return ""
    If $aSelected[0] < 1 Then Return ""
    Return _GUICtrlListView_GetItemText($g_idFavorites, $aSelected[1], 0)
EndFunc

Func GetNameFromHit($hList)
    Local $aHit = _GUICtrlListView_SubItemHitTest($hList)
    If Not IsArray($aHit) Then Return ""
    If $aHit[0] < 0 Then Return ""

    If $hList = GUICtrlGetHandle($g_idOutput) Then
        Local $iSub = $aHit[1]
        If Mod($iSub, 2) = 0 Then $iSub += 1
        If $iSub < 1 Or $iSub > (($DISPLAY_COLUMNS * 2) - 1) Then Return ""
        Return _GUICtrlListView_GetItemText($hList, $aHit[0], $iSub)
    EndIf

    If $hList = GUICtrlGetHandle($g_idFavorites) Then
        Return _GUICtrlListView_GetItemText($hList, $aHit[0], 0)
    EndIf

    Return ""
EndFunc

Func WM_NOTIFY($hWnd, $iMsg, $wParam, $lParam)
    Local $tNMHDR = DllStructCreate($tagNMHDR, $lParam)
    Local $hFrom = DllStructGetData($tNMHDR, "hWndFrom")
    Local $iCode = DllStructGetData($tNMHDR, "Code")
    Local $sName = ""

    If $hFrom = GUICtrlGetHandle($g_idOutput) Or $hFrom = GUICtrlGetHandle($g_idFavorites) Then
        If $iCode = $NM_CLICK Or $iCode = $NM_DBLCLK Then
            $sName = GetNameFromHit($hFrom)
            If $sName <> "" Then $g_sSelectedName = $sName
            If $iCode = $NM_DBLCLK And $sName <> "" Then ClipPut($sName)
        EndIf
    EndIf

    Return $GUI_RUNDEFMSG
EndFunc

Func GenerateName($sCategory, $sStyle, $sGender, $iMaxLen, $iWeirdness, $bHyphen, $bNumbers)
    Local $sName = ""

    For $iTry = 1 To 160
        Local $sCat = $sCategory
        Local $iPick = Random(1, 100, 1)
        If $sCat = $CAT_ALL Then $sCat = PickFromList($CATEGORY_LIST)
        Local $sMode = ChooseMode($sStyle, $sGender, $sCat)

        If $iPick <= 22 - Int($iWeirdness / 2) Then
            $sName = BuildSyllabic($sMode, $iMaxLen)
        ElseIf $iPick <= 38 - Int($iWeirdness / 3) Then
            $sName = BuildCategoryName($sCat, $sMode, $iMaxLen, $bHyphen)
        ElseIf $iPick <= 53 Then
            $sName = BuildCompound($sCat, $sMode, $iMaxLen, $bHyphen)
        ElseIf $iPick <= 56 + ($iWeirdness * 3) Then
            $sName = BuildFramedName($sMode, $iMaxLen)
        ElseIf $iPick <= 70 + ($iWeirdness * 2) Then
            $sName = BuildFusedName($sCat, $sMode, $iMaxLen)
        ElseIf $iPick <= 86 Then
            $sName = BuildCoreName($sCat, $sMode, $iMaxLen)
        ElseIf $iPick <= 94 Then
            $sName = BuildSyllabic($sMode, $iMaxLen - 1) & PickShortSuffix($sCat)
        Else
            $sName = BuildHybridName($sCat, $sMode, $iMaxLen, $bHyphen)
        EndIf

        $sName = ApplyGenderFlavor($sName, $sGender, $sMode, $iMaxLen, $iWeirdness)
        $sName = ApplySpecialGroups($sName, $sMode, $iMaxLen, $iWeirdness)

        If ($sMode = $STYLE_TECH Or $bNumbers) And Random(1, 100, 1) <= 18 + ($iWeirdness * 3) Then
            $sName = AddTechMark($sName, $iMaxLen, $bNumbers)
        EndIf

        $sName = CleanName($sName, $iMaxLen)
        If IsQualityName($sName, $iMaxLen, $iWeirdness) Then Return $sName
    Next

    Return CleanName(BuildSyllabic($STYLE_MIXED, $iMaxLen), $iMaxLen)
EndFunc

Func BuildSyllabic($sStyle, $iMaxLen)
    Local $sStartList = $L_START_SHARP
    Local $sMidList = $L_MID_SHARP
    Local $sEndList = $L_END_SHARP

    Switch $sStyle
        Case $STYLE_SOFT
            $sStartList = $L_START_SOFT
            $sMidList = $L_MID_SOFT
            $sEndList = $L_END_SOFT
        Case $STYLE_ANCIENT, $STYLE_ELDRITCH
            $sStartList = $L_START_ODD
            $sMidList = $L_MID_ODD
            $sEndList = $L_END_ODD
        Case $STYLE_TECH
            $sStartList = "cy|tek|vox|zen|neo|ion|ax|bit|syn|opt|hex|mod"
            $sMidList = "on|ex|ix|ar|ul|tek|vox|sync|dat|ion|ram|bus"
            $sEndList = "x|n|r|m|k|v|q|z|0"
        Case $STYLE_MIXED
            $sStartList = $L_START_SHARP & "|" & $L_START_SOFT & "|" & $L_START_ODD
            $sMidList = $L_MID_SHARP & "|" & $L_MID_SOFT & "|" & $L_MID_ODD
            $sEndList = $L_END_SHARP & "|" & $L_END_SOFT & "|" & $L_END_ODD
    EndSwitch

    Local $sName = PickFromList($sStartList) & PickFromList($sMidList)
    If StringLen($sName) + 2 <= $iMaxLen And Random(1, 100, 1) <= 55 Then $sName &= PickFromList($sEndList)
    Return TitleName($sName)
EndFunc

Func BuildCategoryName($sCat, $sStyle, $iMaxLen, $bHyphen)
    Local $sCore = PickCategoryCore($sCat)
    Local $sAdjective = PickCategoryAdjective($sCat)
    Local $sShortAdjective = PickShortAdjective($sCat)
    Local $sShortCore = PickShortSuffix($sCat)
    Local $sJoin = ""
    If $bHyphen And Random(1, 100, 1) <= 35 Then $sJoin = "-"

    Local $sA = TitleName($sAdjective)
    Local $sB = TitleName($sCore)
    Local $sShortA = TitleName($sShortAdjective)
    Local $sShortB = TitleName($sShortCore)
    Local $sName = ""

    If StringLen($sA & $sJoin & $sB) <= $iMaxLen Then
        $sName = $sA & $sJoin & $sB
    ElseIf StringLen($sShortA & $sJoin & $sB) <= $iMaxLen Then
        $sName = $sShortA & $sJoin & $sB
    ElseIf StringLen($sShortA & $sJoin & $sShortB) <= $iMaxLen Then
        $sName = $sShortA & $sJoin & $sShortB
    ElseIf StringLen($sCore) <= $iMaxLen Then
        $sName = $sCore
    Else
        $sName = BuildSyllabic($sStyle, $iMaxLen)
    EndIf

    Return $sName
EndFunc

Func BuildCompound($sCat, $sStyle, $iMaxLen, $bHyphen)
    Local $sLeft = BuildSyllabic($sStyle, Int($iMaxLen / 2) + 1)
    Local $sRight = PickShortSuffix($sCat)
    Local $sJoin = ""
    If $bHyphen And Random(1, 100, 1) <= 45 Then $sJoin = "-"

    If StringLen($sLeft & $sJoin & $sRight) <= $iMaxLen Then Return $sLeft & $sJoin & $sRight
    Return $sLeft
EndFunc

Func BuildFramedName($sStyle, $iMaxLen)
    Local $sStart = PickSpecialStartForStyle($sStyle)
    Local $sBridge = PickFromList($L_BRIDGE)
    Local $sEnd = PickSpecialEndForStyle($sStyle)
    Local $sName = $sStart & $sBridge & $sEnd

    If StringLen($sName) <= $iMaxLen Then Return TitleName($sName)

    $sName = $sStart & $sEnd
    If StringLen($sName) <= $iMaxLen Then Return TitleName($sName)

    If StringLen($sBridge & $sEnd) <= $iMaxLen Then Return TitleName($sBridge & $sEnd)
    Return TitleName(StringLeft($sStart & $sEnd, $iMaxLen))
EndFunc

Func BuildFusedName($sCat, $sStyle, $iMaxLen)
    Local $sStart = PickSpecialStartForStyle($sStyle)
    Local $sTail = PickShortSuffix($sCat)
    Local $sBridge = ""
    If Random(1, 100, 1) <= 45 Then $sBridge = PickFromList($L_BRIDGE)

    Local $sName = $sStart & $sBridge & $sTail
    If StringLen($sName) <= $iMaxLen Then Return TitleName($sName)

    $sName = $sStart & $sTail
    If StringLen($sName) <= $iMaxLen Then Return TitleName($sName)

    Return BuildFramedName($sStyle, $iMaxLen)
EndFunc

Func BuildCoreName($sCat, $sStyle, $iMaxLen)
    Local $sName = PickFromList($L_COMPACT_CORE)
    If Random(1, 100, 1) <= 55 Then $sName = PickSpecialStartForStyle($sStyle) & $sName
    If Random(1, 100, 1) <= 70 Then $sName = AddSpecialEnd($sName, PickSpecialEndForStyle($sStyle), $iMaxLen)
    If Random(1, 100, 1) <= 35 Then $sName = AddSpecialEnd($sName, PickShortSuffix($sCat), $iMaxLen)
    Return TitleName($sName)
EndFunc

Func BuildHybridName($sCat, $sStyle, $iMaxLen, $bHyphen)
    Local $sCore = PickCategoryCore($sCat)
    Local $sName = BuildFramedName($sStyle, Int($iMaxLen / 2) + 2)
    Local $sSuffix = PickShortSuffix($sCat)
    Local $sJoin = ""
    If $bHyphen And Random(1, 100, 1) <= 30 Then $sJoin = "-"

    If StringLen($sName & $sJoin & $sCore) <= $iMaxLen Then Return $sName & $sJoin & $sCore
    If StringLen($sName & $sJoin & $sSuffix) <= $iMaxLen Then Return $sName & $sJoin & $sSuffix
    Return $sName
EndFunc

Func PickCategoryCore($sCat)
    Switch $sCat
        Case $CAT_RELIC
            Return PickFromList($L_RELIC_A)
        Case $CAT_MACHINE
            Return PickFromList($L_MACHINE_A)
        Case $CAT_CREATURE
            Return PickFromList($L_CREATURE_A)
        Case $CAT_PLACE
            Return PickFromList($L_PLACE_A)
        Case $CAT_FACTION
            Return PickFromList($L_FACTION_A)
        Case $CAT_SPELL
            Return PickFromList($L_SPELL_A)
        Case $CAT_MINERAL
            Return PickFromList($L_MINERAL_A)
        Case $CAT_CUTE
            Return PickFromList($L_CUTE_A)
        Case $CAT_ELVEN
            Return PickFromList($L_ELVEN_A)
        Case $CAT_PET
            Return PickFromList($L_PET_A)
        Case $CAT_CELESTIAL
            Return PickFromList($L_CELESTIAL_A)
        Case $CAT_NATURE
            Return PickFromList($L_NATURE_A)
        Case $CAT_FOOD
            Return PickFromList($L_FOOD_A)
        Case $CAT_WEAPON
            Return PickFromList($L_WEAPON_A)
        Case $CAT_POTION
            Return PickFromList($L_POTION_A)
        Case $CAT_SHIP
            Return PickFromList($L_SHIP_A)
        Case $CAT_DUNGEON
            Return PickFromList($L_DUNGEON_A)
        Case $CAT_TOY
            Return PickFromList($L_TOY_A)
        Case $CAT_SPIRIT
            Return PickFromList($L_SPIRIT_A)
    EndSwitch
    Return PickFromList($L_RELIC_A & "|" & $L_MACHINE_A & "|" & $L_CREATURE_A & "|" & $L_PLACE_A & "|" & $L_CUTE_A & "|" & $L_ELVEN_A & "|" & $L_WEAPON_A & "|" & $L_POTION_A)
EndFunc

Func PickCategoryAdjective($sCat)
    Switch $sCat
        Case $CAT_RELIC
            Return PickFromList($L_RELIC_B)
        Case $CAT_MACHINE
            Return PickFromList($L_MACHINE_B)
        Case $CAT_CREATURE
            Return PickFromList($L_CREATURE_B)
        Case $CAT_PLACE
            Return PickFromList($L_PLACE_B)
        Case $CAT_FACTION
            Return PickFromList($L_FACTION_B)
        Case $CAT_SPELL
            Return PickFromList($L_SPELL_B)
        Case $CAT_MINERAL
            Return PickFromList($L_MINERAL_B)
        Case $CAT_CUTE
            Return PickFromList($L_CUTE_B)
        Case $CAT_ELVEN
            Return PickFromList($L_ELVEN_B)
        Case $CAT_PET
            Return PickFromList($L_PET_B)
        Case $CAT_CELESTIAL
            Return PickFromList($L_CELESTIAL_B)
        Case $CAT_NATURE
            Return PickFromList($L_NATURE_B)
        Case $CAT_FOOD
            Return PickFromList($L_FOOD_B)
        Case $CAT_WEAPON
            Return PickFromList($L_WEAPON_B)
        Case $CAT_POTION
            Return PickFromList($L_POTION_B)
        Case $CAT_SHIP
            Return PickFromList($L_SHIP_B)
        Case $CAT_DUNGEON
            Return PickFromList($L_DUNGEON_B)
        Case $CAT_TOY
            Return PickFromList($L_TOY_B)
        Case $CAT_SPIRIT
            Return PickFromList($L_SPIRIT_B)
    EndSwitch
    Return PickFromList($L_RELIC_B & "|" & $L_MACHINE_B & "|" & $L_CREATURE_B & "|" & $L_PLACE_B & "|" & $L_CUTE_B & "|" & $L_ELVEN_B & "|" & $L_WEAPON_B & "|" & $L_POTION_B)
EndFunc

Func PickShortAdjective($sCat)
    Switch $sCat
        Case $CAT_RELIC
            Return PickFromList("old|star|void|ash|moon|pale")
        Case $CAT_MACHINE
            Return PickFromList("ion|bit|zero|nano|sync|hex")
        Case $CAT_CREATURE
            Return PickFromList("fen|bone|moss|ash|scar|mire")
        Case $CAT_PLACE
            Return PickFromList("low|red|deep|mist|salt|wild")
        Case $CAT_FACTION
            Return PickFromList("red|gray|iron|veil|moon|brass")
        Case $CAT_SPELL
            Return PickFromList("cold|dire|wild|grave|solar|vile")
        Case $CAT_MINERAL
            Return PickFromList("blue|red|raw|deep|star|iron")
        Case $CAT_CUTE
            Return PickFromList("wee|tiny|mint|sun|cozy|pearl")
        Case $CAT_ELVEN
            Return PickFromList("fey|ael|moon|leaf|river|veil")
        Case $CAT_PET
            Return PickFromList("pup|mud|snug|spot|curly|warm")
        Case $CAT_CELESTIAL
            Return PickFromList("star|void|sun|moon|deep|blue")
        Case $CAT_NATURE
            Return PickFromList("dew|pine|root|rain|moss|leaf")
        Case $CAT_FOOD
            Return PickFromList("sweet|sour|mint|honey|salt|toast")
        Case $CAT_WEAPON
            Return PickFromList("ash|iron|keen|red|thorn|wolf")
        Case $CAT_POTION
            Return PickFromList("red|blue|dream|moss|frost|gold")
        Case $CAT_SHIP
            Return PickFromList("salt|reef|star|wind|mist|storm")
        Case $CAT_DUNGEON
            Return PickFromList("deep|old|bone|cold|lost|black")
        Case $CAT_TOY
            Return PickFromList("tin|paper|ribbon|plush|lucky|bright")
        Case $CAT_SPIRIT
            Return PickFromList("hush|pale|moon|mist|blue|faint")
    EndSwitch

    Return PickFromList("old|red|moon|ash|dew|star")
EndFunc

Func PickShortSuffix($sCat)
    Switch $sCat
        Case $CAT_RELIC
            Return PickFromList("orb|key|sig|rune|idol")
        Case $CAT_MACHINE
            Return PickFromList("bot|bit|node|gear|core")
        Case $CAT_CREATURE
            Return PickFromList("maw|fang|husk|claw|spine")
        Case $CAT_PLACE
            Return PickFromList("rift|vale|moor|crag|well")
        Case $CAT_FACTION
            Return PickFromList("kin|sect|host|cell|guild")
        Case $CAT_SPELL
            Return PickFromList("hex|ward|bind|flare|veil")
        Case $CAT_MINERAL
            Return PickFromList("ore|gem|mica|onyx|flint")
        Case $CAT_CUTE
            Return PickFromList("pip|puff|mote|bop|tink|pop")
        Case $CAT_ELVEN
            Return PickFromList("leaf|lume|vale|ael|wyn|syl")
        Case $CAT_PET
            Return PickFromList("paw|pip|muff|snug|tuff|bop")
        Case $CAT_CELESTIAL
            Return PickFromList("nova|star|halo|sol|ray|lune")
        Case $CAT_NATURE
            Return PickFromList("fern|moss|dew|root|leaf|briar")
        Case $CAT_FOOD
            Return PickFromList("bun|bean|boba|plum|miso|toast")
        Case $CAT_WEAPON
            Return PickFromList("edge|fang|pike|axe|bow|claw")
        Case $CAT_POTION
            Return PickFromList("vial|drop|brew|dose|mist|tonic")
        Case $CAT_SHIP
            Return PickFromList("keel|sail|ark|skiff|wake|mast")
        Case $CAT_DUNGEON
            Return PickFromList("vault|crypt|pit|keep|maze|lock")
        Case $CAT_TOY
            Return PickFromList("top|kite|block|bell|card|bauble")
        Case $CAT_SPIRIT
            Return PickFromList("wisp|echo|shade|sigh|gleam|trace")
    EndSwitch
    Return PickFromList("core|rift|hex|ore|kin|maw")
EndFunc

Func AddTechMark($sName, $iMaxLen, $bNumbers)
    Local $sMark = PickFromList("2|3|4|5|7|9|X|V|Q")
    If Not $bNumbers Then $sMark = PickFromList("X|V|Q")

    If StringLen($sName & $sMark) <= $iMaxLen Then Return $sName & $sMark
    If StringLen($sName & "-" & $sMark) <= $iMaxLen Then Return $sName & "-" & $sMark
    Return $sName
EndFunc

Func ChooseMode($sStyle, $sGender, $sCat)
    If $sStyle <> $STYLE_MIXED Then Return $sStyle

    If Random(1, 100, 1) <= 62 Then
        Switch $sCat
            Case $CAT_MACHINE
                Return $STYLE_TECH
            Case $CAT_CUTE, $CAT_PET, $CAT_FOOD, $CAT_TOY
                Return $STYLE_SOFT
            Case $CAT_ELVEN, $CAT_NATURE
                Return PickFromList($STYLE_SOFT & "|" & $STYLE_ANCIENT)
            Case $CAT_CELESTIAL, $CAT_RELIC, $CAT_POTION, $CAT_MINERAL
                Return PickFromList($STYLE_ANCIENT & "|" & $STYLE_SOFT & "|" & $STYLE_ELDRITCH)
            Case $CAT_WEAPON, $CAT_FACTION, $CAT_SHIP
                Return PickFromList($STYLE_SHARP & "|" & $STYLE_ANCIENT & "|" & $STYLE_TECH)
            Case $CAT_CREATURE, $CAT_SPELL, $CAT_DUNGEON, $CAT_SPIRIT
                Return PickFromList($STYLE_ELDRITCH & "|" & $STYLE_ANCIENT & "|" & $STYLE_SHARP)
            Case $CAT_PLACE
                Return PickFromList($STYLE_ANCIENT & "|" & $STYLE_SOFT & "|" & $STYLE_SHARP)
        EndSwitch
    EndIf

    Switch $sGender
        Case $GENDER_FEM
            If Random(1, 100, 1) <= 58 Then Return $STYLE_SOFT
            Return PickFromList($STYLE_ANCIENT & "|" & $STYLE_ELDRITCH & "|" & $STYLE_SHARP)
        Case $GENDER_MASC
            If Random(1, 100, 1) <= 58 Then Return PickFromList($STYLE_SHARP & "|" & $STYLE_ANCIENT)
            Return PickFromList($STYLE_ELDRITCH & "|" & $STYLE_TECH & "|" & $STYLE_SOFT)
        Case $GENDER_NEUTRAL
            If Random(1, 100, 1) <= 46 Then Return PickFromList($STYLE_TECH & "|" & $STYLE_ELDRITCH)
            Return PickFromList($STYLE_SHARP & "|" & $STYLE_SOFT & "|" & $STYLE_ANCIENT)
    EndSwitch

    Return PickFromList($STYLE_SHARP & "|" & $STYLE_SOFT & "|" & $STYLE_ANCIENT & "|" & $STYLE_TECH & "|" & $STYLE_ELDRITCH)
EndFunc

Func ApplyGenderFlavor($sName, $sGender, $sStyle, $iMaxLen, $iWeirdness)
    Local $sOut = StringLower($sName)
    Local $iChance = 10 + ($iWeirdness * 3)

    Switch $sGender
        Case $GENDER_FEM
            If Random(1, 100, 1) <= $iChance Then $sOut = AddSpecialEnd($sOut, PickFromList($L_SPECIAL_END_SOFT), $iMaxLen)
            If Random(1, 100, 1) <= 8 + $iWeirdness Then $sOut = AddSpecialStart($sOut, PickFromList($L_SPECIAL_START_SOFT), $iMaxLen)
        Case $GENDER_MASC
            If Random(1, 100, 1) <= $iChance Then $sOut = AddSpecialEnd($sOut, PickFromList($L_SPECIAL_END_SHARP), $iMaxLen)
            If Random(1, 100, 1) <= 8 + $iWeirdness Then $sOut = AddSpecialStart($sOut, PickFromList($L_SPECIAL_START_SHARP), $iMaxLen)
        Case $GENDER_NEUTRAL
            If Random(1, 100, 1) <= $iChance Then $sOut = AddSpecialEnd($sOut, PickFromList("ix|ion|um|or|ael|ryn|tek|core"), $iMaxLen)
            If $sStyle = $STYLE_TECH And Random(1, 100, 1) <= 10 + $iWeirdness Then $sOut = AddSpecialStart($sOut, PickFromList($L_SPECIAL_START_TECH), $iMaxLen)
    EndSwitch

    Return TitleName($sOut)
EndFunc

Func PickSpecialStartForStyle($sStyle)
    Switch $sStyle
        Case $STYLE_SHARP, $STYLE_ELDRITCH, $STYLE_ANCIENT
            Return PickFromList($L_SPECIAL_START_SHARP & "|" & $L_SPECIAL_START)
        Case $STYLE_SOFT
            Return PickFromList($L_SPECIAL_START_SOFT & "|" & $L_SPECIAL_START)
        Case $STYLE_TECH
            Return PickFromList($L_SPECIAL_START_TECH & "|" & $L_SPECIAL_START_SHARP)
    EndSwitch
    Return PickFromList($L_SPECIAL_START)
EndFunc

Func PickSpecialEndForStyle($sStyle)
    Switch $sStyle
        Case $STYLE_SHARP, $STYLE_ELDRITCH, $STYLE_ANCIENT
            Return PickFromList($L_SPECIAL_END_SHARP & "|" & $L_SPECIAL_END)
        Case $STYLE_SOFT
            Return PickFromList($L_SPECIAL_END_SOFT & "|" & $L_SPECIAL_END)
        Case $STYLE_TECH
            Return PickFromList($L_SPECIAL_END_TECH & "|" & $L_SPECIAL_END_SHARP)
    EndSwitch
    Return PickFromList($L_SPECIAL_END)
EndFunc

Func ApplySpecialGroups($sName, $sStyle, $iMaxLen, $iWeirdness)
    Local $sOut = StringLower($sName)
    Local $sStartList = $L_SPECIAL_START
    Local $sEndList = $L_SPECIAL_END
    Local $iStartChance = 6 + ($iWeirdness * 4)
    Local $iEndChance = 12 + ($iWeirdness * 5)

    Switch $sStyle
        Case $STYLE_SHARP, $STYLE_ELDRITCH, $STYLE_ANCIENT
            $sStartList = $L_SPECIAL_START_SHARP & "|" & $L_SPECIAL_START
            $sEndList = $L_SPECIAL_END_SHARP & "|" & $L_SPECIAL_END
        Case $STYLE_SOFT
            $sStartList = $L_SPECIAL_START_SOFT & "|" & $L_SPECIAL_START
            $sEndList = $L_SPECIAL_END_SOFT & "|" & $L_SPECIAL_END
        Case $STYLE_TECH
            $sStartList = $L_SPECIAL_START_TECH & "|" & $L_SPECIAL_START_SHARP
            $sEndList = $L_SPECIAL_END_TECH & "|" & $L_SPECIAL_END_SHARP
    EndSwitch

    If Random(1, 100, 1) <= $iStartChance Then
        $sOut = AddSpecialStart($sOut, PickFromList($sStartList), $iMaxLen)
    EndIf

    If Random(1, 100, 1) <= $iEndChance Then
        $sOut = AddSpecialEnd($sOut, PickFromList($sEndList), $iMaxLen)
    EndIf

    Return TitleName($sOut)
EndFunc

Func AddSpecialStart($sName, $sGroup, $iMaxLen)
    If StringLeft($sName, StringLen($sGroup)) = $sGroup Then Return $sName
    If StringLen($sGroup & $sName) <= $iMaxLen Then Return $sGroup & $sName

    Local $iTrim = StringLen($sGroup)
    If StringLen($sName) - $iTrim >= 2 Then
        Return $sGroup & StringTrimLeft($sName, $iTrim)
    EndIf

    Return $sName
EndFunc

Func AddSpecialEnd($sName, $sGroup, $iMaxLen)
    If StringRight($sName, StringLen($sGroup)) = $sGroup Then Return $sName
    If StringLen($sName & $sGroup) <= $iMaxLen Then Return $sName & $sGroup

    Local $iTrim = StringLen($sGroup)
    If StringLen($sName) - $iTrim >= 2 Then
        Return StringTrimRight($sName, $iTrim) & $sGroup
    EndIf

    Return $sName
EndFunc

Func CleanName($sName, $iMaxLen)
    $sName = StringStripWS($sName, 8)
    $sName = StringReplace($sName, "--", "-")
    If StringLeft($sName, 1) = "-" Then $sName = StringTrimLeft($sName, 1)
    If StringRight($sName, 1) = "-" Then $sName = StringTrimRight($sName, 1)

    If StringLen($sName) > $iMaxLen Then
        $sName = StringLeft($sName, $iMaxLen)
        If StringRight($sName, 1) = "-" Then $sName = StringTrimRight($sName, 1)
    EndIf

    Return TitleName($sName)
EndFunc

Func TitleName($sName)
    If $sName = "" Then Return ""
    Local $sOut = ""
    Local $bCap = True
    Local $sChar = ""

    For $i = 1 To StringLen($sName)
        $sChar = StringMid($sName, $i, 1)
        If $bCap Then
            $sOut &= StringUpper($sChar)
            $bCap = False
        Else
            $sOut &= StringLower($sChar)
        EndIf
        If $sChar = "-" Then $bCap = True
    Next

    Return $sOut
EndFunc

Func IsQualityName($sName, $iMaxLen, $iWeirdness)
    Local $sLower = StringLower($sName)
    Local $iLen = StringLen($sLower)
    If $iLen < 3 Or $iLen > $iMaxLen Then Return False
    If StringInStr($sLower, "--") Then Return False
    If StringLeft($sLower, 1) = "-" Or StringRight($sLower, 1) = "-" Then Return False
    If $iLen >= 4 And Not HasVowel($sLower) And $iWeirdness < 8 Then Return False
    If HasTripleRepeat($sLower) Then Return False
    If LongestVowelRun($sLower) > 4 Then Return False
    If LongestConsonantRun($sLower) > 4 + Int($iWeirdness / 3) Then Return False
    If StringRegExp($sLower, "(.)\1\1") Then Return False
    If StringRegExp($sLower, "(bop|pip|puff|pop).*\1") And $iWeirdness < 5 Then Return False
    If StringRegExp($sLower, "(core|node|gear).*\1") Then Return False
    If StringRegExp($sLower, "[qzx]{4,}") And $iWeirdness < 8 Then Return False
    Return True
EndFunc

Func HasVowel($sText)
    For $i = 1 To StringLen($sText)
        If IsVowel(StringMid($sText, $i, 1)) Then Return True
    Next
    Return False
EndFunc

Func HasTripleRepeat($sText)
    Local $sPrev = ""
    Local $iRun = 0
    Local $sChar = ""

    For $i = 1 To StringLen($sText)
        $sChar = StringMid($sText, $i, 1)
        If $sChar = $sPrev Then
            $iRun += 1
        Else
            $iRun = 1
            $sPrev = $sChar
        EndIf
        If $iRun >= 3 Then Return True
    Next

    Return False
EndFunc

Func LongestVowelRun($sText)
    Local $iBest = 0
    Local $iRun = 0
    Local $sChar = ""

    For $i = 1 To StringLen($sText)
        $sChar = StringMid($sText, $i, 1)
        If IsVowel($sChar) Then
            $iRun += 1
            If $iRun > $iBest Then $iBest = $iRun
        ElseIf StringRegExp($sChar, "[a-z]") Then
            $iRun = 0
        EndIf
    Next

    Return $iBest
EndFunc

Func LongestConsonantRun($sText)
    Local $iBest = 0
    Local $iRun = 0
    Local $sChar = ""

    For $i = 1 To StringLen($sText)
        $sChar = StringMid($sText, $i, 1)
        If StringRegExp($sChar, "[a-z]") And Not IsVowel($sChar) Then
            $iRun += 1
            If $iRun > $iBest Then $iBest = $iRun
        Else
            $iRun = 0
        EndIf
    Next

    Return $iBest
EndFunc

Func IsVowel($sChar)
    Return StringInStr("aeiouy", $sChar) > 0
EndFunc

Func PickFromList($sList)
    Local $aItems = StringSplit($sList, "|", 2)
    Return $aItems[Random(0, UBound($aItems) - 1, 1)]
EndFunc

Func _ClampInt($sValue, $iMin, $iMax, $iDefault)
    Local $iValue = Int($sValue)
    If $iValue = 0 And StringStripWS($sValue, 8) <> "0" Then $iValue = $iDefault
    If $iValue < $iMin Then $iValue = $iMin
    If $iValue > $iMax Then $iValue = $iMax
    Return $iValue
EndFunc

Func _SeedToInt($sSeed)
    Local $iSeed = 0
    For $i = 1 To StringLen($sSeed)
        $iSeed = Mod(($iSeed * 131) + Asc(StringMid($sSeed, $i, 1)), 2147483647)
    Next
    If $iSeed < 1 Then $iSeed = 1
    Return $iSeed
EndFunc

Func _FreshSeed($iRoll)
    Local $iSeed = TimerInit()
    $iSeed = Mod(($iSeed * 1009) + (@HOUR * 3600000) + (@MIN * 60000) + (@SEC * 1000) + @MSEC + ($iRoll * 7919), 2147483647)
    If $iSeed < 1 Then $iSeed = 1
    Return $iSeed
EndFunc

Func SaveOutput()
    Local $sPath = FileSaveDialog("Save generated names", @ScriptDir, "Text files (*.txt)|All files (*.*)", 18, "generated_names.txt")
    If @error Then Return

    Local $hFile = FileOpen($sPath, 2)
    If $hFile = -1 Then
        MsgBox(16, $APP_TITLE, "Could not save the file.")
        Return
    EndIf

    FileWrite($hFile, $g_sLastOutput)
    FileClose($hFile)
EndFunc
