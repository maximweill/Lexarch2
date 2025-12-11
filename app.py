from shiny import App, ui, render, reactive
from shinywidgets import output_widget, render_plotly
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import ast
import os
import sys
import random
import requests
import urllib.parse

# Ensure local modules can be imported
sys.path.append(os.path.dirname(__file__))

try:
    import spelling_bee_map
except ImportError:
    spelling_bee_map = None
    print("Warning: spelling_bee_map.py not found.")

from data_processing import load_word_data, load_search_csv

# -----------------------------------------------------------------------------
# 1. DATA LOADING
# -----------------------------------------------------------------------------
words_df = load_word_data("word_dataset_with_difficulties.csv")
search_df = load_search_csv("search.csv") 

# Generate Word List for Dropdowns
if not words_df.empty:
    ALL_WORDS = sorted([str(w) for w in words_df['Word'].dropna().unique()])
else:
    ALL_WORDS = []

# Create "Parts Database" for Similarity Search (Exploded View)
def create_parts_database(df):
    if df.empty: return pd.DataFrame()
    rows = []
    for _, row in df.iterrows():
        word = row['Word']
        diff = row.get('Spelling Difficulty', 0)
        freq = row.get('Frequency', 1)
        # Safe eval
        syls = ast.literal_eval(row['Syllables']) if isinstance(row['Syllables'], str) else row['Syllables']
        prons = ast.literal_eval(row['Pronunciation']) if isinstance(row['Pronunciation'], str) else row['Pronunciation']
        
        if len(syls) == len(prons):
            for s, p in zip(syls, prons):
                rows.append([word, f"{s} ({p})", diff, freq])
                
    return pd.DataFrame(rows, columns=['Word', 'Signature', 'Difficulty', 'Frequency'])

parts_df = create_parts_database(words_df)

# -----------------------------------------------------------------------------
# 2. HELPER FUNCTIONS
# -----------------------------------------------------------------------------
def fetch_ngram_data(query, start_year=1800, end_year=2019, corpus=26, smoothing=3):
    """Fetches historical frequency data from Google Books Ngram Viewer."""
    try:
        query_encoded = urllib.parse.quote(query)
        url = f'https://books.google.com/ngrams/json?content={query_encoded}&year_start={start_year}&year_end={end_year}&corpus={corpus}&smoothing={smoothing}'
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except:
        return []

def organize_rounds(word_list):
    """Splits a list of words into game rounds of 5."""
    if not word_list: return []
    random.shuffle(word_list)
    n = len(word_list)
    if n < 5: return [word_list]
    
    rounds = [word_list[i:i + 5] for i in range(0, (n // 5) * 5, 5)]
    remainder = n % 5
    
    if remainder >= 3:
        rounds.append(word_list[-remainder:])
    elif remainder > 0:
        # Distribute extras to previous rounds
        extras = word_list[-remainder:]
        for i, word in enumerate(extras):
            if i < len(rounds): rounds[-(i+1)].append(word)
            
    return rounds

# -----------------------------------------------------------------------------
# 3. UI CONFIGURATION (THEME)
# -----------------------------------------------------------------------------
custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Lora:ital,wght@0,400;0,600;1,400&display=swap');
    :root { --bg-color: #fdfbf7; --card-bg: #ffffff; --text-main: #1a1a1a; --text-muted: #595959; --accent: #8b0000; --border-color: #dcd6cc; }
    body { background-color: var(--bg-color) !important; color: var(--text-main) !important; font-family: 'Lora', serif !important; }
    h1, h2, h3, h4, h5, h6 { color: var(--text-main) !important; font-family: 'Playfair Display', serif !important; font-weight: 700; letter-spacing: -0.02em; }
    .card { background-color: var(--card-bg) !important; border: 1px solid var(--border-color) !important; box-shadow: 0 2px 10px rgba(0,0,0,0.03) !important; border-radius: 2px !important; }
    .card-header { background-color: #f9f7f1 !important; border-bottom: 1px solid var(--border-color) !important; font-family: 'Playfair Display', serif; font-weight: 600; text-transform: uppercase; font-size: 0.9rem; letter-spacing: 0.1em; }
    .form-control, .selectize-input { background-color: #ffffff !important; border: 1px solid #b0b0b0 !important; color: var(--text-main) !important; font-family: 'Lora', serif; border-radius: 2px !important; }
    .btn-primary { background-color: var(--text-main) !important; color: #fff !important; border: none; font-family: 'Playfair Display', serif; font-weight: 700; text-transform: uppercase; letter-spacing: 0.15em; border-radius: 2px; }
    .btn-secondary { background-color: #f0f0f0 !important; border: 1px solid #ccc !important; color: #333 !important; font-family: 'Lora', serif; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 0.1em; }
    .bslib-sidebar-layout > .sidebar { background-color: #f4f1ea !important; border-right: 1px solid var(--border-color) !important; }
    .syllable-chip { background: transparent; color: var(--text-main); padding: 4px 10px; border: 1px solid #dcd6cc; margin: 0 12px 0 0; font-family: 'Georgia', serif; font-weight: bold; display: inline-block; }
    #results_container { animation: fadeIn 0.8s ease-out; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
</style>
"""

tts_script = """
<script>
function speakWord(text) {
    if ('speechSynthesis' in window) {
        var msg = new SpeechSynthesisUtterance();
        msg.text = text; msg.lang = 'en-US'; msg.rate = 0.85; 
        window.speechSynthesis.cancel(); window.speechSynthesis.speak(msg);
    }
}
</script>
"""

app_ui = ui.page_navbar(
    ui.head_content(ui.HTML(custom_css + tts_script)),
    
    ui.nav_panel("Explore Mode",
        ui.layout_sidebar(
            ui.sidebar(
                ui.h4("Lexicon Search", style="margin-bottom: 20px; font-style:italic;"),
                ui.input_selectize("explore_word", "Select Word", choices=[], multiple=False),
                ui.input_radio_buttons("explore_mode", "Analysis Mode", choices=["Spelling", "Pronunciation"], selected="Spelling"),
                ui.br(),
                ui.input_action_button("btn_explore", "Analyze Word", class_="btn-primary", width="100%")
            ),
            ui.output_ui("results_container")
        )
    ),
    
    ui.nav_panel("Test Mode",
        ui.layout_sidebar(
            ui.sidebar(
                ui.h4("Examination Setup", style="margin-bottom: 20px; font-style:italic;"),
                ui.input_numeric("num_words", "Word Count", value=1, min=1, max=10),
                ui.input_action_button("btn_step1", "Initialize Inputs", class_="btn-secondary", width="100%"),
                ui.hr(style="border-color:#dcd6cc"),
                ui.output_ui("ui_step2_inputs"), 
                ui.output_ui("ui_step3_action")
            ),
            ui.card(
                ui.card_header("Examination Area"),
                ui.output_ui("ui_step4_selection"),
                ui.hr(style="border-color:#dcd6cc"),
                ui.output_ui("game_container")
            )
        )
    ),
    title=ui.span("LEXARCH", style="font-family:'Playfair Display'; letter-spacing: 0.1em; font-weight:900;")
)

# -----------------------------------------------------------------------------
# 4. SERVER LOGIC
# -----------------------------------------------------------------------------
def server(input, output, session):
    
    # Initialize Search Dropdown
    ui.update_selectize("explore_word", choices=ALL_WORDS, server=True)
    search_triggered = reactive.Value(False)
    
    # --- CALCULATIONS ---
    @reactive.Calc
    def get_word_data():
        w = input.explore_word().strip().upper()
        if search_df.empty or words_df.empty: return None
        row = words_df[words_df['Word'] == w]
        return row.iloc[0] if not row.empty else None

    @reactive.Calc
    @reactive.event(input.btn_explore)
    def check_ambiguity_data():
        data = get_word_data()
        if data is None: return False
        
        mode = input.explore_mode()
        parent_col = "Syllables" if mode == "Spelling" else "Pronunciation"
        if parent_col not in search_df.columns: return False
        
        # Check if any rows match the parent syllables
        df_parent = search_df[search_df[parent_col].isin(data[parent_col])]
        return not df_parent.empty

    @reactive.Calc
    @reactive.event(input.btn_explore)
    def get_ngram_data():
        w = input.explore_word().strip().upper()
        return fetch_ngram_data(w) if w else []

    @reactive.Calc
    @reactive.event(input.btn_explore)
    def get_frequency_ratios():
        w = input.explore_word().strip().upper()
        data = get_word_data()
        if data is None or parts_df.empty: return []
        
        target_freq = data.get('Frequency', 1)
        target_signatures = [f"{s} ({p})" for s, p in zip(data['Syllables'], data['Pronunciation'])]
        
        matched_df = parts_df[parts_df['Signature'].isin(target_signatures)].copy()
        matched_df = matched_df[matched_df['Word'] != w]
        
        if matched_df.empty: return []
        
        ratios = []
        for _, m_row in matched_df.iterrows():
            n_freq = m_row.get('Frequency', 0)
            ratios.append(n_freq / target_freq if target_freq > 0 else 0)
        return ratios

    @reactive.Effect
    @reactive.event(input.btn_explore)
    def trigger_search():
        search_triggered.set(True)

    # --- UI RENDERERS ---
    @render.ui
    def results_container():
        if not search_triggered.get():
            return ui.div(
                ui.h2("LEXARCH", style="color:#1a1a1a; font-size:5rem; opacity:0.8; font-family:'Playfair Display';"),
                ui.p("An Architectural Exploration of Language", style="color:#595959; font-size:1.4rem; font-style:italic;"),
                ui.hr(style="width: 100px; border-top: 2px solid #1a1a1a; margin: 30px auto;"),
                ui.p("Select a word to begin.", style="color:#888; font-size:1rem;"),
                style="text-align:center; padding-top: 100px;"
            )
        
        show_ambiguity = check_ambiguity_data()
        ngram_data = get_ngram_data()
        
        # Build Bottom Section Dynamically
        bottom_content = []
        
        if show_ambiguity:
            bottom_content.append(ui.h5("I. Ambiguity Mapping"))
            bottom_content.append(output_widget("treeplot", height="500px"))
            bottom_content.append(ui.br())
            
        sim_num = "II" if show_ambiguity else "I"
        bottom_content.append(ui.h5(f"{sim_num}. Similar Words"))
        bottom_content.append(output_widget("similar_treemap", height="500px"))
        
        if ngram_data:
            bottom_content.append(ui.br())
            hist_num = "III" if show_ambiguity else "II"
            bottom_content.append(ui.h5(f"{hist_num}. Historical Usage"))
            bottom_content.append(output_widget("ngram_plot", height="400px"))

        return ui.div(
            ui.card(
                ui.card_header("Analysis Report"),
                ui.layout_columns(
                    ui.div(ui.h5("Overview"), ui.output_ui("explore_result")),
                    ui.div(
                        ui.h5("Relevance"), 
                        ui.navset_tab(
                            ui.nav_panel("Distribution", output_widget("relevance_plot", height="350px")), 
                            ui.nav_panel("Proportions", output_widget("pie_plot", height="350px"))
                        )
                    ),
                    col_widths=[6, 6]
                ),
                ui.hr(style="border-color:#dcd6cc"),
                ui.div(*bottom_content),
                full_screen=True
            ),
            id="results_container"
        )

    @render.ui
    @reactive.event(input.btn_explore)
    def explore_result():
        w = input.explore_word().strip().upper()
        data = get_word_data()
        if data is None: return ui.div(ui.h3(w), ui.p("Word not found."))
        
        mode = input.explore_mode()
        diff_key = 'Spelling Difficulty' if mode == "Spelling" else 'Reading Difficulty'
        diff_val = data.get(diff_key, 0)
        
        chips = data['Syllables'] if mode == "Spelling" else data['Pronunciation']
        chips_ui = [ui.span(c, class_="syllable-chip") for c in chips]

        return ui.div(
            ui.h3(w, style="font-size: 3.5rem; color:#1a1a1a !important; text-decoration: underline; text-decoration-color: #dcd6cc;"),
            ui.span("VERIFIED ENTRY", style="color:#2e7d32; font-size:0.7em; font-weight:bold; letter-spacing: 1px; font-family:'Courier New';"),
            ui.br(), ui.br(),
            ui.div(
                ui.span("DIFFICULTY INDEX: ", style="color:#595959; font-weight:bold; letter-spacing:0.05em;"),
                ui.span(f"{diff_val:.2f}", style="color:#1a1a1a; font-size:1.4em; font-weight:bold; font-family:'Georgia', serif;")
            ),
            ui.h6(f"{mode.upper()} BREAKDOWN:", style="margin-top: 25px; color: #595959 !important; font-style:italic;"),
            ui.div(chips_ui)
        )

    # --- PLOTS ---
    @render_plotly
    def pie_plot():
        ratios = get_frequency_ratios()
        if not ratios: return px.pie(title="No Data")
        
        counts = {
            "Ratio < 1 (Unlikely)": sum(1 for x in ratios if x <= 1),
            "Ratio > 1 (Likely)": sum(1 for x in ratios if x > 1)
        }
        fig = px.pie(names=list(counts.keys()), values=list(counts.values()), color_discrete_sequence=["#a5d6a7", "#ef9a9a"])
        
        # FIX: Increased bottom margin and moved legend to bottom to prevent cutoff
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#1a1a1a', family="Lora, serif"),
            margin=dict(t=20, b=80, l=20, r=20),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        return fig

    @render_plotly
    def relevance_plot():
        ratios = get_frequency_ratios()
        if not ratios: return go.Figure().update_layout(title="No Data")
        
        data = np.array([x for x in ratios if x > 0])
        if len(data) == 0: return go.Figure().update_layout(title="No Data")
        
        data_sorted = np.sort(data)
        cdf_vals = np.arange(1, len(data_sorted)+1) / len(data_sorted)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data_sorted, y=cdf_vals, mode='lines', name='CDF', line=dict(color='#1a1a1a', width=2)))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#1a1a1a', family="Lora, serif"),
            xaxis_title="Freq Ratio", yaxis_title="Probability",
            margin=dict(t=20, b=40, l=40, r=20),
            xaxis=dict(showgrid=True, gridcolor='#dcd6cc'), yaxis=dict(showgrid=True, gridcolor='#dcd6cc')
        )
        return fig

    @render_plotly
    @reactive.event(input.btn_explore)
    def treeplot():
        if not check_ambiguity_data(): return None 
        w = input.explore_word().strip().upper()
        mode = input.explore_mode()
        data = get_word_data()
        
        parent_col = "Syllables" if mode == "Spelling" else "Pronunciation"
        child_col = "Pronunciation" if mode == "Spelling" else "Syllables"
        
        df_parent = search_df[search_df[parent_col].isin(data[parent_col])].copy()
        df_parent["color"] = df_parent[child_col].apply(lambda x: "teal" if x in data[child_col] else "salmon")
        df_parent["label"] = df_parent[child_col]
        
        fig = px.treemap(df_parent, path=[parent_col, "label", "Word"], values="Show", color="color", 
                        color_discrete_map={"teal": "#81C784", "salmon": "#E57373"})
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#1a1a1a', family="Lora, serif"), margin=dict(t=0, l=0, r=0, b=0))
        return fig

    @render_plotly
    @reactive.event(input.btn_explore)
    def similar_treemap():
        w = input.explore_word().strip().upper()
        data = get_word_data()
        if data is None or parts_df.empty: return None
        
        target_signatures = [f"{s} ({p})" for s, p in zip(data['Syllables'], data['Pronunciation'])]
        matched_df = parts_df[parts_df['Signature'].isin(target_signatures)].copy()
        matched_df = matched_df[matched_df['Word'] != w]
        
        if matched_df.empty: return px.treemap(title="No similar words found.")

        fig = px.treemap(matched_df, path=['Signature', 'Word'], values='Frequency', color='Difficulty', color_continuous_scale='RdYlGn_r', range_color=[0, 1])
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#1a1a1a', family="Lora, serif"), margin=dict(t=0, l=0, r=0, b=0))
        return fig

    @render_plotly
    @reactive.event(input.btn_explore)
    def ngram_plot():
        data_list = get_ngram_data()
        if not data_list: return None
        fig = go.Figure()
        years = list(range(1800, 2020))
        for item in data_list:
            limit = min(len(years), len(item['timeseries']))
            fig.add_trace(go.Scatter(x=years[:limit], y=item['timeseries'][:limit], mode='lines', name=item['ngram'], line=dict(width=2, color='#1a1a1a')))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#1a1a1a', family="Lora, serif"),
            xaxis=dict(showgrid=True, gridcolor='#dcd6cc', title="Year"), yaxis=dict(showgrid=True, gridcolor='#dcd6cc', title="Frequency"),
            margin=dict(t=20, l=40, r=20, b=40), showlegend=False
        )
        return fig

    # --- GAME LOGIC ---
    game_state = reactive.Value("IDLE") 
    game_rounds = reactive.Value([])
    current_round_idx = reactive.Value(0)
    round_scores = reactive.Value([])
    words_data_store = reactive.Value({}) 
    word_syllable_map = reactive.Value({}) 
    user_inputs = reactive.Value({})

    @render.ui
    @reactive.event(input.btn_step1)
    def ui_step2_inputs():
        n = input.num_words()
        return ui.div(*[ui.div(ui.input_selectize(f"word_input_{i}", f"Word {i+1}", choices=[], multiple=False), style="margin-bottom: 15px;") for i in range(n)])
    
    @reactive.Effect
    @reactive.event(input.btn_step1)
    def update_test_inputs():
        n = input.num_words()
        for i in range(n): ui.update_selectize(f"word_input_{i}", choices=ALL_WORDS, server=True)

    @render.ui
    @reactive.event(input.btn_step1)
    def ui_step3_action():
        return ui.div(ui.br(), ui.input_action_button("btn_step2", "Find Syllables", class_="btn-secondary", width="100%"))

   
    @render.ui
    @reactive.event(input.btn_step2)
    def ui_step4_selection():
        game_state.set("IDLE")
        n = input.num_words()
        valid_words_data = {}
        ui_elements = []
        
        for i in range(n):
            try:
                w_val = getattr(input, f"word_input_{i}")()
                if not w_val: continue
            except AttributeError: continue
            
            w_clean = str(w_val).strip().upper()
            row = words_df[words_df['Word'] == w_clean]
            if row.empty: continue
            
            data = row.iloc[0]
            valid_words_data[w_clean] = {'Syllables': data['Syllables'], 'Pronunciation': data['Pronunciation']}
            choices = {str(idx): f"{syl} ({pron})" for idx, (syl, pron) in enumerate(zip(data['Syllables'], data['Pronunciation']))}
            
            # Create the card UI for this word
            card = ui.div(
                ui.h5(f"{w_clean}", style="color:#1a1a1a; margin-bottom:5px; border-bottom:1px solid #ddd;"),
                ui.input_checkbox_group(f"select_syl_{i}", "Target Syllables:", choices=choices),
                style="border:1px solid #dcd6cc; padding:15px; margin-bottom:15px; background-color:#f9f7f1; border-radius:4px;"
            )
            ui_elements.append(card)
            
        words_data_store.set(valid_words_data)
        
        if valid_words_data:
            # FIX: Append items one by one
            ui_elements.append(ui.br())
            ui_elements.append(ui.input_action_button("btn_generate_game", "START EXAMINATION", class_="btn-primary", width="100%"))
        else:
            ui_elements.append(ui.p("No valid words selected."))
            
        return ui.div(*ui_elements)

    @reactive.Effect
    @reactive.event(input.btn_generate_game)
    def start_game_logic():
        if spelling_bee_map is None: return
        valid_data = words_data_store.get()
        n = input.num_words()
        tested_words = []
        for i in range(n):
            try:
                w_val = getattr(input, f"word_input_{i}")()
                if not w_val: continue
                w_clean = str(w_val).strip().upper()
                if w_clean not in valid_data: continue
                selected_indices = getattr(input, f"select_syl_{i}")()
                if not selected_indices: continue
                word_map = {}
                syls = valid_data[w_clean]['Syllables']
                prons = valid_data[w_clean]['Pronunciation']
                for idx_str in selected_indices:
                    idx = int(idx_str)
                    word_map[syls[idx]] = prons[idx]
                tested_words.append({w_clean: word_map})
            except AttributeError: continue
        
        if not tested_words:
            ui.notification_show("Select at least one syllable.", type="warning")
            return
        
        try:
            saved_dicts, _, all_words_res = spelling_bee_map.generate_test_words(tested_words, 0.05, 0.10)
            mapping = {}
            for gen_word, reason in saved_dicts.items():
                label = reason[0] if isinstance(reason, list) and reason else "Unknown"
                if isinstance(reason, set): label = list(reason)[0]
                mapping[gen_word] = label
            
            for item in tested_words:
                for orig_word, syl_map in item.items():
                    if syl_map: mapping[orig_word] = list(syl_map.keys())[0]

            word_syllable_map.set(mapping)
            rounds = organize_rounds(all_words_res)
            game_rounds.set(rounds)
            current_round_idx.set(0)
            round_scores.set([])
            user_inputs.set({})
            game_state.set("PLAYING")
        except Exception as e:
            ui.notification_show(f"Error: {e}", type="error")

    @render.ui
    def game_container():
        state = game_state.get()
        if state == "IDLE": return ui.div("Select syllables above to begin.", style="font-style:italic; color:#666;")
        
        elif state == "PLAYING":
            rounds = game_rounds.get()
            idx = current_round_idx.get()
            if not rounds: return ui.p("No rounds.")
            current_words = rounds[idx]
            
            inputs = [ui.h4(f"ROUND {idx + 1} / {len(rounds)}", style="letter-spacing:2px; color:#1a1a1a;")]
            inputs.append(ui.p("Listen and spell:", style="color:#666; font-style:italic;"))
            
            for i, word in enumerate(current_words):
                btn_html = ui.HTML(f"""<button class="btn btn-sm btn-secondary" onclick="speakWord('{word}')" style="margin-right:5px; background:#fff;">🔊</button>""")
                inputs.append(ui.div(
                    ui.div(btn_html, style="display:inline-block;"),
                    ui.div(ui.input_text(f"guess_{idx}_{i}", label=None, placeholder="Type here..."), style="display:inline-block; width:200px;"),
                    style="margin-bottom:10px;"
                ))
            inputs.append(ui.input_action_button("btn_submit_round", "SUBMIT ROUND", class_="btn-primary", width="100%"))
            return ui.div(*inputs)
        
        elif state == "FEEDBACK":
            rounds = game_rounds.get()
            idx = current_round_idx.get()
            log = user_inputs.get()[idx]
            rows = []
            for word, data in log.items():
                color = "#2e7d32" if data['correct'] else "#c62828"
                rows.append(ui.tags.tr(
                    ui.tags.td(word, style="color:#1a1a1a; border-color:#dcd6cc; font-weight:bold;"),
                    ui.tags.td(data['guess'], style=f"color:{color}; border-color:#dcd6cc; font-family:'Courier New';"),
                    ui.tags.td("✓" if data['correct'] else "✗", style="color:#1a1a1a; border-color:#dcd6cc;")
                ))
            tbl = ui.tags.table(ui.tags.tbody(*rows), class_="table", style="color:#1a1a1a; border-color:#dcd6cc;")
            btn_txt = "NEXT ROUND" if idx < len(rounds)-1 else "VIEW RESULTS"
            return ui.div(ui.h4("RESULTS"), tbl, ui.input_action_button("btn_next_round", btn_txt, class_="btn-primary", width="100%"))
        
        elif state == "FINAL":
            scores = round_scores.get()
            rounds = game_rounds.get()
            total_correct = sum(scores)
            total_words = sum(len(r) for r in rounds)
            
            bars = []
            for i, s in enumerate(scores):
                total = len(rounds[i])
                pct = (s/total)*100 if total > 0 else 0
                bars.append(ui.div(
                    ui.div(f"Round {i+1}: {s}/{total}", style="font-size:0.8em; color:#666; font-family:'Courier New';"),
                    ui.div(ui.div(style=f"width:{pct}%; background:#1a1a1a; height:6px;"), style="width:100%; background:#e0e0e0; margin-bottom:10px;")
                ))
            return ui.div(
                ui.h3("EXAMINATION COMPLETE"), 
                ui.h4(f"SCORE: {total_correct} / {total_words}"), 
                ui.hr(style="border-color:#dcd6cc;"), 
                ui.h5("PROGRESS"), *bars, 
                ui.hr(style="border-color:#dcd6cc;"), 
                ui.h5("WEAKNESS RADAR"), output_widget("radar_plot"), 
                ui.br(), ui.input_action_button("btn_reset", "RESTART EXAMINATION", class_="btn-secondary", width="100%")
            )

    @render_plotly
    def radar_plot():
        if game_state.get() != "FINAL": return None
        all_inputs = user_inputs.get()
        mapping = word_syllable_map.get()
        stats = {}
        for round_idx, guesses in all_inputs.items():
            for word, data in guesses.items():
                syl = mapping.get(word, "Unknown")
                if syl not in stats: stats[syl] = {'correct': 0, 'total': 0}
                stats[syl]['total'] += 1
                if data['correct']: stats[syl]['correct'] += 1
        
        if not stats: return px.scatter(title="No data")
        categories = list(stats.keys())
        values = [(stats[c]['correct'] / stats[c]['total']) for c in categories]
        categories.append(categories[0])
        values.append(values[0])
        
        fig = go.Figure(data=go.Scatterpolar(
            r=values, theta=categories, 
            fill='toself', name='Accuracy',
            line_color='#1a1a1a', 
            fillcolor='rgba(26, 26, 26, 0.2)'
        ))
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 1], gridcolor='#ccc', linecolor='#1a1a1a'),
                angularaxis=dict(gridcolor='#ccc', linecolor='#1a1a1a'),
                bgcolor='rgba(0,0,0,0)'
            ),
            font=dict(color='#1a1a1a', family="Lora, serif"), 
            showlegend=False,
            margin=dict(t=20, b=20, l=40, r=40)
        )
        return fig

    @reactive.Effect
    @reactive.event(input.btn_submit_round)
    def submit_round():
        rounds = game_rounds.get()
        idx = current_round_idx.get()
        words = rounds[idx]
        current_guesses = {}
        correct = 0
        for i, word in enumerate(words):
            try: val = getattr(input, f"guess_{idx}_{i}")()
            except AttributeError: val = ""
            val_clean = str(val).strip().upper()
            is_correct = (val_clean == word)
            if is_correct: correct += 1
            current_guesses[word] = {'guess': val_clean, 'correct': is_correct}
        
        all_inputs = user_inputs.get()
        all_inputs[idx] = current_guesses
        user_inputs.set(all_inputs)
        
        sc = round_scores.get()
        sc.append(correct)
        round_scores.set(sc)
        game_state.set("FEEDBACK")

    @reactive.Effect
    @reactive.event(input.btn_next_round)
    def next_round():
        rounds = game_rounds.get()
        idx = current_round_idx.get()
        if idx < len(rounds) - 1:
            current_round_idx.set(idx + 1)
            game_state.set("PLAYING")
        else:
            game_state.set("FINAL")
            
    @reactive.Effect
    @reactive.event(input.btn_reset)
    def reset_game():
        game_state.set("IDLE")
        round_scores.set([])
        game_rounds.set([])
        word_syllable_map.set({})

app = App(app_ui, server)