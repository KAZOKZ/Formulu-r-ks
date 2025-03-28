from flask import Flask, render_template, request, redirect, url_for, flash
import csv
import os
import pandas as pd
from werkzeug.utils import secure_filename

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

app = Flask(__name__)
app.secret_key = 'slepenais_atslēgas_vārds'
app.config['UPLOAD_FOLDER'] = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}

# ✅ Palīgfunkcija drošai skaitļu pārvēršanai
def safe_float(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

# ✅ Faila paplašinājuma pārbaude
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ✅ Formu nosaukumu standarti
nosaukumi = {
    'trijsturis': 'Trijstūris',
    'kvadrats': 'Kvadrāts',
    'taisnsturis': 'Taisnstūris',
    'paralelograms': 'Paralelograms',
    'romb': 'Rombs',
    'trapece': 'Trapecē',
    'aplis': 'Aplis'
}

# ✅ Sākumlapa
@app.route('/')
def index():
    return render_template('index.html')

# ✅ CSV augšupielāde
@app.route('/upload', methods=['GET', 'POST'])
def upload_csv():
    if request.method == 'POST':
        if 'csv_file' not in request.files:
            flash('Nav faila izvēles!')
            return redirect(request.url)

        file = request.files['csv_file']
        if file.filename == '':
            flash('Nav izvēlēts neviens fails.')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            uploaded_df = pd.read_csv(filepath)
            existing_df = pd.read_csv('dati.csv') if os.path.exists('dati.csv') else pd.DataFrame(columns=['forma', 'rezultats'])

            # ✅ Vienādo formu nosaukumus
            uploaded_df['forma'] = uploaded_df['forma'].str.lower().map(nosaukumi).fillna(uploaded_df['forma'])
            combined = pd.concat([existing_df, uploaded_df], ignore_index=True)
            combined.to_csv('dati.csv', index=False)

            flash('CSV fails veiksmīgi augšupielādēts un dati apvienoti!')
            return redirect(url_for('grafiki'))

        flash('Lūdzu augšupielādē tikai .csv failus.')
        return redirect(request.url)

    return render_template('upload.html')

# ✅ Figūras izvēles ievade
@app.route('/ievade', methods=['POST'])
def ievade():
    forma = request.form['forma']
    return render_template('ievade.html', forma=forma)

# ✅ Rezultāta aprēķins
@app.route('/rezultats', methods=['POST'])
def rezultats():
    forma = request.form['forma'].lower()
    dati = request.form.to_dict()
    errors = []
    rezultats = None
    formula = ""

    forma_standarta = nosaukumi.get(forma, forma.capitalize())

    def get_value(name):
        val = safe_float(dati.get(name))
        if val is None or val < 0:
            errors.append(f"Ievadītā vērtība “{name}” nav derīga (jābūt ≥ 0).")
            return 0
        return val

    # ✅ Aprēķini
    if forma == 'trijsturis':
        a = get_value('a')
        h = get_value('h')
        rezultats = 0.5 * a * h
        formula = "S = 0.5 × a × h"
    elif forma == 'kvadrats':
        a = get_value('a')
        rezultats = a ** 2
        formula = "S = a²"
    elif forma == 'taisnsturis':
        a = get_value('a')
        b = get_value('b')
        rezultats = a * b
        formula = "S = a × b"
    elif forma == 'paralelograms':
        a = get_value('a')
        h = get_value('h')
        rezultats = a * h
        formula = "S = a × h"
    elif forma == 'romb':
        d1 = get_value('d1')
        d2 = get_value('d2')
        rezultats = 0.5 * d1 * d2
        formula = "S = 0.5 × d₁ × d₂"
    elif forma == 'trapece':
        a = get_value('a')
        b = get_value('b')
        h = get_value('h')
        rezultats = 0.5 * (a + b) * h
        formula = "S = 0.5 × (a + b) × h"
    elif forma == 'aplis':
        r = get_value('r')
        rezultats = 3.1416 * r ** 2
        formula = "S = π × r²"

    if errors:
        return render_template('ievade.html', forma=forma, errors=errors)

    # ✅ Saglabā CSV
    csv_file = 'dati.csv'
    file_exists = os.path.exists(csv_file)
    with open(csv_file, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists or os.stat(csv_file).st_size == 0:
            writer.writerow(['forma', 'rezultats'])
        writer.writerow([forma_standarta, round(rezultats, 2)])

    return render_template('rezultats.html', forma=forma_standarta, rezultats=round(rezultats, 2), formula=formula)

# ✅ Grafiku attēlošana
@app.route('/grafiki')
def grafiki():
    df = pd.read_csv('dati.csv')
    df['forma'] = df['forma'].str.strip().str.lower().map(nosaukumi).fillna(df['forma'])

    # Histogramma
    plt.figure(figsize=(6, 4))
    plt.hist(df['rezultats'], bins=10, color='skyblue', edgecolor='black')
    plt.title('Laukumu sadalījums')
    plt.xlabel('Laukums')
    plt.ylabel('Skaits')
    plt.tight_layout()
    plt.savefig('static/histogram.png')
    plt.close()

    # Stabiņu diagramma
    plt.figure(figsize=(6, 4))
    df['forma'].value_counts().plot(kind='bar', color='salmon')
    plt.title('Figūru biežums')
    plt.xlabel('Forma')
    plt.ylabel('Skaits')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('static/bar_chart.png')
    plt.close()

    return render_template('grafiki.html')

# ✅ Palaist serveri
if __name__ == '__main__':
    app.run(debug=True, port=5003)
