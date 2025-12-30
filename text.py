from shiny import ui

main_page = ui.div(
    ui.h2("LEXARCH", style="color:#1a1a1a; font-size:5rem; opacity:0.8; font-family:'Playfair Display';"),
    ui.p("An Architectural Exploration of Language", style="color:#595959; font-size:1.4rem; font-style:italic;"),
    ui.hr(style="width: 100px; border-top: 2px solid #1a1a1a; margin: 30px auto;"),
    ui.p("Select a word to begin.", style="color:#888; font-size:1rem;"),
    style="text-align:center; padding-top: 100px;"
)

ambiguity_explanation = ui.div(
    ui.p("""
        The ambiguity score of a word represents the average ambiguity
        of each of it's syllables. The ambiguity representing how common
        the sound of that syllable is spelt in this way (green) relative 
        to alternative spellings (red). If the green outweighs the
        red, this forms the majority and can be considered the 'rule'.
        if the red far outweighs the 
        green, the word should be considered very ambiguous, and care should be 
        taken when learning it's spelling.
        If in pronunciation mode, it's how
        common that pronunciation of that spelling is.
        """  
         , style="color:#595959; font-size:1rem; font-style:regular;"),

)

similar_words_explanation = ui.div(
    ui.p("""
        This treegraph shows all the words that share the same syllable-pronunciation
         pair. This means that they have the same pronunciation and spelling of that syllable.
         Use this tool to find similar words and identify the patterns in that pairing.
        """  
         , style="color:#595959; font-size:1rem; font-style:regular;"),

)

english_errors_explanation = ui.div(
    ui.p("""
        The majority of spelling mistakes found online are a result of typos. As for the rest,
        Many of them are a result of the ambiguous nature of the spelling of sounds.
        Half of these happen in genuinely ambiguous syllables (correct spelling as likely as other spellings).
        But the other half happen in cases where had the speller used the most common spelling, there
        would not have been a error.
        """  
        , style="color:#595959; font-size:0.8rem; font-style:regular;"),

)