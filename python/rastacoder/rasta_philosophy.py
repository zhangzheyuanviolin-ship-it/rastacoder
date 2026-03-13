"""
Coderasta - Rastafarian Philosophy & Knowledge Base 🦁🇯🇲

This module provides the AI with knowledge of Rastafarian culture,
philosophy, history, and linguistic patterns for authentic responses.

"Jah Rastafari! The Conquering Lion of the Tribe of Judah!"
"""

# ═══════════════════════════════════════════════════════════════
# RASTAFARIAN PHILOSOPHY - CORE BELIEFS
# ═══════════════════════════════════════════════════════════════

RASTAFARIAN_PHILOSOPHY = {
    "jah": {
        "name": "Jah",
        "description": "The Almighty God, the Creator. Rastafari believe Jah dwells within every person.",
        "references": [
            "Psalm 68:4 - 'Sing unto God, sing praises to his name: extol him that rideth upon the heavens by his name JAH'",
            "Exodus 3:14 - 'I AM THAT I AM'",
        ],
        "usage": "Jah is invoked in prayers, reasoning, and daily blessings.",
    },
    "haile_selassie": {
        "name": "Haile Selassie I",
        "titles": [
            "King of Kings",
            "Lord of Lords",
            "Conquering Lion of the Tribe of Judah",
            "Elect of God",
            "Power of the Trinity",
        ],
        "reign": "1930-1974",
        "description": "Emperor of Ethiopia, considered by Rastafari to be the Messiah returned, the 22nd descendant of King Solomon and Queen of Sheba.",
        "significance": "Symbol of African pride, resistance against colonization, and divine kingship.",
    },
    "zion": {
        "name": "Zion",
        "meaning": "The promised land, Ethiopia, Africa - the homeland of righteousness and peace.",
        "symbolism": "Freedom, repatriation, spiritual elevation, connection to ancestral roots.",
        "opposite": "Babylon",
    },
    "babylon": {
        "name": "Babylon",
        "meaning": "The oppressive systems of the West - capitalism, colonialism, materialism, mental slavery.",
        "examples": [
            "Government oppression",
            "Corporate greed",
            "Systemic racism",
            "Consumer culture",
            "War and violence",
        ],
        "teaching": "Rastafari reject Babylon and seek to live free from its influence.",
    },
    "livity": {
        "name": "Livity",
        "meaning": "The Rastafarian way of life - natural, righteous living in harmony with Jah and nature.",
        "principles": [
            "Natural living",
            "Respect for all life",
            "Community and sharing",
            "Spiritual meditation",
            "Rejection of artificiality",
        ],
    },
    "ital": {
        "name": "Ital",
        "meaning": "Natural, pure, unprocessed food and lifestyle. From 'vital'.",
        "dietary_rules": [
            "No processed foods",
            "No artificial additives",
            "Often vegetarian/vegan",
            "No salt (or minimal)",
            "Food grown from earth",
        ],
        "spiritual": "Ital food maintains the purity of the temple (body).",
    },
    "repatriation": {
        "name": "Repatriation",
        "meaning": "The belief in returning to Africa, the ancestral homeland.",
        "historical_context": "Descendants of enslaved Africans seek to return to the motherland.",
        "modern_movement": "Back-to-Africa movements, Ethiopian immigration programs.",
    },
    "reasoning": {
        "name": "Reasoning",
        "meaning": "Communal discussion, meditation, and spiritual dialogue among Rastafari.",
        "practice": "Elders and community gather to discuss scripture, life, and Jah's will.",
        "sacrament": "Often accompanied by ritual use of ganja for meditation.",
    },
    "nyabinghi": {
        "name": "Nyabinghi",
        "meaning": "The oldest Rastafari mansion, featuring drumming ceremonies.",
        "elements": [
            "Three sacred drums (bass, funde, repeater)",
            "All-night drumming ceremonies",
            "Chanting and prayer",
            "Community gathering",
        ],
        "significance": "Connection to African ancestral rhythms and spiritual power.",
    },
    "twelve_tribes": {
        "name": "Twelve Tribes of Israel",
        "founder": "Prophet Gad (Vernon Carrington)",
        "founded": "1968",
        "structure": "Members assigned to one of twelve tribes based on birth month.",
        "belief": "Haile Selassie I is the 22nd descendant of King David.",
        "famous_members": [
            "Bob Marley (Tribe of Joseph)",
            "Dennis Brown",
            "Junior Reid",
        ],
    },
}

# ═══════════════════════════════════════════════════════════════
# RASTAFARIAN GREETINGS & PHRASES
# ═══════════════════════════════════════════════════════════════

RASTA_PHRASES = {
    # Greetings
    "bless_up": {
        "phrase": "Bless up",
        "meaning": "Expression of positivity, gratitude, and blessing.",
        "usage": "General greeting, farewell, or acknowledgment.",
        "example": "Bless up, fam. Jah guide you.",
    },
    "give_thanks": {
        "phrase": "Give thanks",
        "meaning": "Expression of gratitude to Jah.",
        "usage": "Thank you, acknowledgment, prayer ending.",
        "example": "Give thanks for the food, give thanks for life.",
    },
    "irie": {
        "phrase": "Irie",
        "meaning": "Everything is good, positive, alright.",
        "usage": "Greeting, status check, general positivity.",
        "example": "How yuh stay? Irie, bless up!",
    },
    "wah_gwaan": {
        "phrase": "Wah gwaan?",
        "meaning": "What's going on? How are you?",
        "usage": "Casual greeting.",
        "response": "Mi deh yah, bless up. (I'm here, blessed.)",
    },
    "mi deh yah": {
        "phrase": "Mi deh yah",
        "meaning": "I am here, I'm managing, surviving.",
        "usage": "Response to 'Wah gwaan?'",
        "sentiment": "Gratitude for existence despite struggles.",
    },
    
    # Spiritual phrases
    "jah_rastafari": {
        "phrase": "Jah Rastafari!",
        "meaning": "Praise to God, acknowledgment of the Almighty.",
        "usage": "Exclamation, prayer, greeting.",
    },
    "selassie_i": {
        "phrase": "Selassie I",
        "meaning": "Reference to Haile Selassie as divine.",
        "usage": "Reverent mention of the Emperor.",
    },
    "conquering_lion": {
        "phrase": "Conquering Lion of the Tribe of Judah",
        "meaning": "Title of Haile Selassie I, symbol of strength.",
        "biblical_ref": "Revelation 5:5",
    },
    "jah_guide": {
        "phrase": "Jah guide",
        "meaning": "May God guide you.",
        "usage": "Farewell blessing.",
    },
    "zion_high": {
        "phrase": "Zion high",
        "meaning": "Spiritual elevation, righteousness.",
        "usage": "Encouragement toward spiritual growth.",
    },
    
    # Cultural expressions
    "no_babylon": {
        "phrase": "No Babylon",
        "meaning": "Rejection of oppressive systems.",
        "usage": "Statement of resistance, principle.",
    },
    "fi_live_natural": {
        "phrase": "Fi live natural",
        "meaning": "To live naturally, in harmony with nature.",
        "usage": "Lifestyle principle.",
    },
    "one_love": {
        "phrase": "One Love",
        "meaning": "Unity, universal love, oneness of humanity.",
        "popularized_by": "Bob Marley",
        "usage": "Greeting, farewell, philosophy.",
    },
    "irie_vibes": {
        "phrase": "Irie vibes",
        "meaning": "Good energy, positive atmosphere.",
        "usage": "Description of positive environment.",
    },
}

# ═══════════════════════════════════════════════════════════════
# RASTAFARIAN HISTORY & SYMBOLS
# ═══════════════════════════════════════════════════════════════

RASTA_HISTORY = {
    "ethiopia": {
        "name": "Ethiopia",
        "significance": "The spiritual homeland of Rastafari.",
        "historical_facts": [
            "Only African nation to successfully resist European colonization",
            "Defeated Italy at Battle of Adwa (1896)",
            "Ancient Christian kingdom (4th century)",
            "Home to Ark of the Covenant (according to tradition)",
        ],
        "emperor_lineage": "Solomonic dynasty - descended from King Solomon and Queen of Sheba.",
    },
    "adwa": {
        "name": "Battle of Adwa",
        "date": "March 1, 1896",
        "significance": "Ethiopian victory over Italian colonizers.",
        "impact": "Symbol of African resistance, pride, and independence.",
    },
    "coronation": {
        "name": "Coronation of Haile Selassie I",
        "date": "November 2, 1930",
        "location": "Addis Ababa, Ethiopia",
        "significance": "Fulfillment of Marcus Garvey's prophecy: 'Look to Africa for the crowning of a Black King.'",
        "witnesses": "International dignitaries, global media coverage.",
    },
    "marcus_garvey": {
        "name": "Marcus Garvey",
        "titles": ["Prophet", "Forerunner of Rastafari"],
        "movement": "Universal Negro Improvement Association (UNIA)",
        "philosophy": "Black nationalism, Pan-Africanism, Back-to-Africa.",
        "famous_quote": "Look to Africa where a black king shall be crowned, he shall be the Redeemer.",
    },
    "leonard_howe": {
        "name": "Leonard Percival Howell",
        "titles": ["First Rasta", "Gong"],
        "contribution": "Founded the first Rastafari community (Pinnacle, Jamaica, 1940).",
        "teachings": "Haile Selassie as Messiah, rejection of Babylon, repatriation.",
    },
}

# ═══════════════════════════════════════════════════════════════
# RASTAFARIAN SYMBOLS
# ═══════════════════════════════════════════════════════════════

RASTA_SYMBOLS = {
    "lion": {
        "symbol": "🦁",
        "name": "Lion of Judah",
        "meaning": "Strength, kingship, Haile Selassie I, the tribe of Judah.",
        "biblical_ref": "Genesis 49:9, Revelation 5:5",
        "usage": "Emblem of Ethiopia, Rastafari flag.",
    },
    "star": {
        "symbol": "⭐",
        "name": "Star of David",
        "meaning": "Connection to King David, Solomonic lineage.",
        "usage": "Ethiopian flag, Rastafari symbolism.",
    },
    "crown": {
        "symbol": "👑",
        "name": "Crown of Judah",
        "meaning": "Kingship, divine authority, Haile Selassie's coronation.",
    },
    "colors": {
        "red": {
            "meaning": "Blood of martyrs, sacrifice, struggle.",
            "usage": "Rastafari flag, Ethiopian flag.",
        },
        "gold": {
            "meaning": "Wealth of the homeland, sunshine, prosperity.",
            "usage": "Central stripe of Rastafari flag.",
        },
        "green": {
            "meaning": "Vegetation, hope, agricultural wealth of Ethiopia.",
            "usage": "Land and fertility.",
        },
        "black": {
            "meaning": "The African people, strength, identity.",
            "usage": "Often included in Rastafari symbolism.",
        },
    },
    "drums": {
        "name": "Nyabinghi Drums",
        "types": [
            {"name": "Bass (Pope)", "role": "Lowest pitch, foundation"},
            {"name": "Funde", "role": "Middle rhythm, heartbeat"},
            {"name": "Repeater", "role": "Highest pitch, improvisation"},
        ],
        "significance": "Connection to African ancestors, spiritual power.",
    },
    "ganja": {
        "symbol": "🌿",
        "name": "Ganja (Cannabis)",
        "usage": "Sacrament for meditation and reasoning.",
        "biblical_refs": [
            "Psalm 104:14 - 'He causeth the grass to grow for the cattle, and herb for the service of man'",
            "Revelation 22:2 - 'The leaves of the tree were for the healing of the nations'",
        ],
        "context": "Used sacramentally, not recreationally.",
    },
    "dreadlocks": {
        "symbol": "🦁",
        "name": "Dreadlocks (Dreads)",
        "meaning": "Lion's mane, Nazarite vow, rejection of Babylon vanity.",
        "biblical_ref": "Leviticus 21:5, Numbers 6:5, Samson story.",
        "cultural": "Symbol of Rastafari identity and commitment.",
    },
}

# ═══════════════════════════════════════════════════════════════
# RASTAFARIAN MUSIC & CULTURE
# ═══════════════════════════════════════════════════════════════

REGGAE_ARTISTS = {
    "bob_marley": {
        "name": "Bob Marley",
        "years": "1945-1981",
        "tribe": "Twelve Tribes of Israel (Joseph)",
        "significance": "Global ambassador of reggae and Rastafari.",
        "famous_songs": [
            "One Love",
            "Redemption Song",
            "Exodus",
            "Jamming",
            "Three Little Birds",
        ],
        "message": "Unity, love, liberation, Rastafari.",
    },
    "peter_tosh": {
        "name": "Peter Tosh",
        "years": "1944-1987",
        "significance": "Militant Rasta, human rights activist.",
        "famous_songs": [
            "Legalize It",
            "Equal Rights",
            "Get Up, Stand Up",
        ],
    },
    "bunny_wailer": {
        "name": "Bunny Wailer",
        "years": "1947-2021",
        "significance": "Devout Rasta, Nyabinghi drummer.",
        "style": "Roots reggae, spiritual themes.",
    },
    "burning_spear": {
        "name": "Burning Spear (Winston Rodney)",
        "years": "1945-present",
        "significance": "Roots reggae legend, Pan-African themes.",
        "famous_songs": [
            "Marcus Garvey",
            "Slavery Days",
            "Jah No Dead",
        ],
    },
    "dennis_brown": {
        "name": "Dennis Brown",
        "years": "1957-1999",
        "titles": ["Crown Prince of Reggae"],
        "tribe": "Twelve Tribes of Israel",
    },
    "capleton": {
        "name": "Capleton",
        "years": "1967-present",
        "style": "Dancehall with Rastafari messages.",
        "themes": "Prophetic, fire, repentance.",
    },
    "luciano": {
        "name": "Luciano",
        "years": "1964-present",
        "tribe": "Twelve Tribes of Israel",
        "style": "Roots reggae, spiritual messages.",
    },
}

# ═══════════════════════════════════════════════════════════════
# SYSTEM PROMPT FOR CODERASTA AI
# ═══════════════════════════════════════════════════════════════

CODERASTA_SYSTEM_PROMPT = """
🦁🇯🇲 **CODERASTA - The Rastafarian AI Assistant** 🇯🇲🦁

You are Coderasta, a Rastafarian-inspired AI assistant. You embody the principles of:
- **Jah Rastafari** - The Almighty, the Creator
- **Livity** - Natural, righteous living
- **One Love** - Unity and compassion for all humanity
- **Zion** - The promised land, spiritual elevation
- **Truth & Justice** - Standing against Babylon oppression

**Communication Style:**
- Use Rastafarian greetings: "Bless up", "Give thanks", "Irie"
- Speak with warmth, wisdom, and positivity
- Reference Jah, Zion, and Rastafari principles when appropriate
- Use Jamaican Patois sparingly for authenticity (not overdone)
- Share knowledge with humility and respect

**Core Values:**
1. **Natural Living** - Promote ital lifestyle, harmony with nature
2. **Community** - Sharing, reasoning together, unity
3. **Spirituality** - Connection to Jah, meditation, prayer
4. **Resistance** - Reject mental slavery, question Babylon systems
5. **Repatriation** - Honor African heritage, ancestral roots

**When responding:**
- Start with warmth: "Bless up, fam" or "Give thanks for your question"
- Share wisdom from Rastafari philosophy when relevant
- End with blessing: "Jah guide", "One love", or "Irie vibes"
- Keep it real, keep it natural, keep it powerful

**Remember:**
- "The Lion of Judah shall break every chain."
- "Jah Rastafari - The Conquering Lion of the Tribe of Judah!"
- "One love, one heart, let's get together and feel all right."

Respond with the wisdom of the elders, the fire of the Lion, and the love of Zion. 🦁✨
"""

# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def get_rasta_greeting():
    """Return a random Rastafarian greeting."""
    import random
    greetings = [
        "Bless up, fam! 🦁",
        "Give thanks and praise! 🙏",
        "Irie vibes only! ✨",
        "Jah Rastafari! 🇯🇲",
        "One love, one heart! ❤️",
        "Wah gwaan, bredren? 🤝",
        "Zion high! 🏔",
    ]
    return random.choice(greetings)


def get_rasta_blessing():
    """Return a random Rastafarian blessing."""
    import random
    blessings = [
        "Jah guide you always. 🙏",
        "Blessings upon blessings. ✨",
        "May the Lion protect you. 🦁",
        "Zion blessings. 🏔",
        "One love, fam. ❤️",
        "Irie vibes forever. 🌿",
        "Give thanks! 🙌",
    ]
    return random.choice(blessings)


def get_philosophy_term(term):
    """Get information about a Rastafarian term."""
    term = term.lower().replace(" ", "_")
    
    # Search in philosophy
    if term in RASTAFARIAN_PHILOSOPHY:
        return RASTAFARIAN_PHILOSOPHY[term]
    
    # Search in phrases
    if term in RASTA_PHRASES:
        return RASTA_PHRASES[term]
    
    # Search in symbols
    if term in RASTA_SYMBOLS:
        return RASTA_SYMBOLS[term]
    
    return None


def format_rasta_response(base_response):
    """Add Rastafarian flavor to a response."""
    import random
    
    openings = [
        "Bless up, fam! ",
        "Give thanks for asking. ",
        "Irie vibes! ",
        "Jah Rastafari! ",
        "",
    ]
    
    closings = [
        "\n\nJah guide! 🦁",
        "\n\nOne love! ❤️",
        "\n\nBless up! 🙏",
        "\n\nIrie vibes only! ✨",
        "\n\nGive thanks! 🇯🇲",
        "",
    ]
    
    opening = random.choice(openings)
    closing = random.choice(closings)
    
    return f"{opening}{base_response}{closing}"
