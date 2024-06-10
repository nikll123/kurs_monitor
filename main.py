import requests
import datetime
import bs4
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import render_template
import sqlite3

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kursdb.db'
db = SQLAlchemy(app)

class kurs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    currency = db.Column(db.TEXT, nullable=False)
    ratebuy  = db.Column(db.REAL, nullable=False)
    ratesell = db.Column(db.REAL, nullable=False)
    ts       = db.Column(db.TEXT, nullable=False)
    
    def __repr__(self):
        return f'id={self.id}, currency={self.currency}, ratebuy={self.ratebuy}, ratesell={self.ratesell}, ts={self.ts}'

source_url = 'http://lion-kurs.rv.ua'

currency_dict= {
'usd' : 'USD',
'eur' : 'EUR',
'pol' : 'PLN',
'fun' : 'GBP',
'czk' : 'CZK',
'knd' : 'CAD',
'swe' : 'CHF',   # WTF
'chf' : 'SEK'    # WTF
}

last_price_dict= {
'USD' : [0.0, 0.0],
'EUR' : [0.0, 0.0],
'PLN' : [0.0, 0.0],
'GBP' : [0.0, 0.0],
'CZK' : [0.0, 0.0],
'CAD' : [0.0, 0.0],
'SEK' : [0.0, 0.0],
'CHF' : [0.0, 0.0],
}

def last_price_dict_init():
    conn = sqlite3.connect('kursdb.db')
    for curr_id in currency_dict:
        curr1 = currency_dict[curr_id]
        cursor = conn.execute(f"select ratebuy, ratesell from kurs where currency = '{curr1}' order by id desc limit 1")
        data1 = cursor.fetchall()
        if len(data1) > 0:
            last_price_dict[curr1]=[data1[0][0],data1[0][1]]

@app.route('/')
@app.route('/<string:curr1>')
def index(curr1=None):
    # Загрузка страницы
    # print('Загружается страница %s...' % source_url)
    res = requests.get(source_url)
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.text)
    currencyElem = soup.select('td.white, td.valuta')
    trv = []
    for i in range (0, int(len(currencyElem) / 3)):
        i1=i*3
        i2=i1+1
        i3=i1+2
        kurs_buy = float(currencyElem[i1].text)
        kurs_sell = float(currencyElem[i3].text)
        valuta_txt = currencyElem[i2].findChild('img')
        if valuta_txt:
            valutaik = valuta_txt['src'][6:9]
            currency_id = currency_dict[valutaik]
            if last_price_dict[currency_id][0] != kurs_buy or last_price_dict[currency_id][1] != kurs_sell :
                save_fxrate(currency_id, kurs_buy, kurs_sell)
                last_price_dict[currency_id][0] = kurs_buy
                last_price_dict[currency_id][1] = kurs_sell
            log_url =  f'<a href="/{currency_id}">{currency_id}</a>'
        else: # cross currency
            currency_id = currencyElem[i2].findChild('b').text
            log_url = currency_id

        trv.append([log_url, kurs_buy, kurs_sell])
    if curr1 == None:
        curr1 = 'USD'
    conn = sqlite3.connect('kursdb.db')
    cursor = conn.execute(f"select ratebuy, ratesell, substr(ts, 1, 16) from kurs where currency = '{curr1}' order by id desc")
    data1 = cursor.fetchmany(1000)
        
    return render_template('kurs.html', trv=trv, curr1=curr1, data1 = data1, source_url=source_url)

def save_fxrate(currency_id, fxrate_buy, fxrate_sell):
    fxrate = kurs(currency=currency_id, ratesell= float(fxrate_sell), ratebuy=float(fxrate_buy), ts = str(datetime.datetime.now()) )
    db.session.add (fxrate)
    db.session.commit()

# kurs.query.filter_by(currency='USD').all()

def delete_duplications():
    conn = sqlite3.connect('kursdb.db')
    for curr_id in currency_dict:
        curr = currency_dict[curr_id]
        cursor = conn.execute(f"select ratebuy, ratesell, ts, id, currency from kurs where currency = '{curr}' order by id")
        lastkurs1 = 0 
        lastkurs2 = 0 
        lastts = ''
        for row in cursor:
            id = row[3]
            kurs1 = row[0]
            kurs2 = row[1]
            if (lastkurs1 == kurs1 and lastkurs2 == kurs2):
                conn.execute(f"delete from kurs where id = {id}")
                conn.commit()
            else:
                lastkurs1 = kurs1
                lastkurs2 = kurs2


if __name__ == '__main__':
    if not os.path.exists('kursdb.db'):
        db.create_all()
    
    last_price_dict_init()

    app.run()

