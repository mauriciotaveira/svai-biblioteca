import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
import re
import unicodedata

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Cine.IA", page_icon="🎬", layout="wide")

# --- 2. CSS FINAL (VISUAL PERFEITO) ---
st.markdown("""
<style>
    /* Força fundo branco */
    .stApp { background-color: #ffffff !important; }

    /* --- BOTÃO (FUNDO PRETO, TEXTO BRANCO) --- */
    div.stButton > button {
        background-color: #000000 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: bold !important;
    }
    div.stButton > button:hover {
        background-color: #333333 !important;
        color: #ffffff !important;
    }
    div.stButton > button p { color: #ffffff !important; }

    /* --- TEXTOS GERAIS (PRETO) --- */
    h1, h2, h3, h4, h5, h6, .stMarkdown p, .stMarkdown li, label, div {
        color: #000000 !important;
    }

    /* --- INPUTS --- */
    .stTextInput input {
        color: #000000 !important;
        background-color: #ffffff !important;
        border: 1px solid #ccc !important;
    }
    ::placeholder { color: #888888 !important; font-style: italic !important; opacity: 1 !important; }

    /* --- DESIGN GERAL --- */
    .titulo-tech {
        font-family: 'Helvetica', sans-serif; 
        color: #0
