from flask import Flask, render_template, request, redirect, url_for, session
from web3 import Web3
from web3.middleware import geth_poa_middleware
from contractinfo import abi, contract_address
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'

w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
contract = w3.eth.contract(address=contract_address, abi=abi)

def validate_password(password):
    if len(password) < 12:
        return False, "Password must be at least 12 characters long"
    if not re.search("[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search("[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search("[0-9]", password):
        return False, "Password must contain at least one digit"
    if not re.search("[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"
    if re.fullmatch(r"(password123|qwerty123)", password):
        return False, "Please avoid common and simple passwords"
    return True, ""

@app.route('/')
def main():
    return render_template('main.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'public_key' in session:
        return redirect(url_for('general'))
    if request.method == 'POST':
        public_key = request.form['public_key']
        password = request.form['password']
        try:
            w3.geth.personal.unlock_account(public_key, password, 300)
            session['public_key'] = public_key
            return redirect(url_for('general'))
        except Exception as e:
            error = str(e)
            return render_template('login.html', error=error)
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        password = request.form['password']
        valid, message = validate_password(password)
        if not valid:
            return render_template('register.html', message=message)
        try:
            account = w3.geth.personal.new_account(password)
            message = f"Account created successfully. Your public key is: {account}"
            return render_template('register.html', message=message)
        except Exception as e:
            return str(e)
    return render_template('register.html')

@app.route('/general')
def general():
    if 'public_key' not in session:
        return redirect(url_for('login'))
    return render_template('general.html')

@app.route('/create_estate', methods=['GET', 'POST'])
def create_estate():
    if request.method == 'POST':
        address_estate = request.form['address_estate']
        square = int(request.form['square'])
        es_type = int(request.form['es_type'])
        account = w3.eth.accounts[0]  # replace with the actual account address
        try:
            tx_hash = contract.functions.createEstate(address_estate, square, es_type).transact({'from': account})
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            message = f"Estate created successfully. Transaction hash: {receipt.transactionHash.hex()}"
            return render_template('create_estate.html', message=message)
        except Exception as e:
            return str(e)
    return render_template('create_estate.html')

@app.route('/change_estate_status', methods=['GET', 'POST'])
def change_estate_status():
    if request.method == 'POST':
        estate_id = int(request.form['estate_id'])
        is_active = 'is_active' in request.form
        account = w3.eth.accounts[0]  # replace with the actual account address
        try:
            tx_hash = contract.functions.updateEstateActive(estate_id, is_active).transact({'from': account})
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            message = f"Estate status changed successfully. Transaction hash: {receipt.transactionHash.hex()}"
            return render_template('change_estate_status.html', message=message)
        except Exception as e:
            return str(e)
    return render_template('change_estate_status.html')


@app.route('/create_advertisement', methods=['GET', 'POST'])
def create_advertisement():
    if request.method == 'POST':
        estate_id = int(request.form['estate_id'])
        price = int(request.form['price'])
        account = w3.eth.accounts[0]  # replace with the actual account address
        try:
            tx_hash = contract.functions.createAd(estate_id, price).transact({'from': account})
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            message = f"Advertisement created successfully. Transaction hash: {receipt.transactionHash.hex()}"
            return render_template('create_advertisement.html', message=message)
        except Exception as e:
            return str(e)
    return render_template('create_advertisement.html')

@app.route('/change_ad_status', methods=['GET', 'POST'])
def change_ad_status():
    if request.method == 'POST':
        ad_id = int(request.form['ad_id'])
        ad_type = int(request.form['ad_type'])
        account = w3.eth.accounts[0]  # replace with the actual account address
        try:
            ad = contract.functions.ads(ad_id).call()
            tx_hash = contract.functions.updateAdType(ad_id, ad_type).transact({'from': account})
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            message = f"Ad status changed successfully. Transaction hash: {receipt.transactionHash.hex()}"
            return render_template('change_ad_status.html', message=message)
        except Exception as e:
            return str(e)
    return render_template('change_ad_status.html')

@app.route('/buy_estate', methods=['GET', 'POST'])
def buy_estate():
    if request.method == 'POST':
        ad_id = int(request.form['ad_id'])
        account = w3.eth.accounts[0]  # replace with the actual account address
        try:
            ad = contract.functions.ads(ad_id).call()
            ad_price = ad[1]
            if ad[5] != 0:
                return "The ad must be opened"
            if ad_price > w3.eth.get_balance(account):
                return "Insufficient funds"
            tx_hash = contract.functions.buyEstate(ad_id).transact({'from': account, 'value': ad_price})
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            message = f"Estate bought successfully. Transaction hash: {receipt.transactionHash.hex()}"
            return render_template('buy_estate.html', message=message)
        except Exception as e:
            return str(e)
    return render_template('buy_estate.html')

@app.route('/withdraw_funds', methods=['GET', 'POST'])
def withdraw_funds():
    if request.method == 'POST':
        amount = int(request.form['amount'])
        account = w3.eth.accounts[0]  # replace with the actual account address
        try:
            balance = contract.functions.userBalances(account).call()
            if amount > balance:
                return "Insufficient funds"
            tx_hash = contract.functions.withdraw(amount).transact({'from': account})
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            message = f"Funds withdrawn successfully. Transaction hash: {receipt.transactionHash.hex()}"
            return render_template('withdraw_funds.html', message=message)
        except Exception as e:
            return str(e)
    return render_template('withdraw_funds.html')

@app.route('/logout')
def logout():
    session.pop('public_key', None)
    return redirect(url_for('login'))

@app.route('/get_balance_on_contract')
def get_balance_on_contract():
    account = w3.eth.accounts[0]  # replace with the actual account address
    try:
        balance = contract.functions.getBalance().call({'from': account})
        message = f"Ваш баланс на смарт-контракте: {Web3.from_wei(balance, 'ether')} ether"
        return render_template('get_balance_on_contract.html', message=message)
    except Exception as e:
        return str(e)

@app.route('/get_estates')
def get_estates():
    account = w3.eth.accounts[0]  # replace with the actual account address
    try:
        estates = contract.functions.getEstates().call({'from': account})
        if not estates:
            message = "Нет доступных недвижимостей."
        else:
            message = ""
            for estate in estates:
                message += f"ID: {estate[0]}, Адрес: {estate[1]}, Площадь: {estate[2]} кв.м, Тип: {estate[3]}, Владелец: {estate[4]}, Активна: {'Да' if estate[5] else 'Нет'}<br>"
        return render_template('get_estates.html', message=message)
    except Exception as e:
        return str(e)

@app.route('/get_ads')
def get_ads():
    account = w3.eth.accounts[0]  # replace with the actual account address
    try:
        ads = contract.functions.getAds().call({'from': account})
        if not ads:
            message = "Нет доступных объявлений."
        else:
            message = ""
            for ad in ads:
                message += f"ID объявления: {ad[0]}, Цена: {Web3.from_wei(ad[1], 'ether')} ether, ID недвижимости: {ad[2]}, Владелец: {ad[3]}, Покупатель: {ad[4]}, Статус: {'Открыто' if ad[5] == 0 else 'Закрыто'}<br>"
        return render_template('get_ads.html', message=message)
    except Exception as e:
        return str(e)


if __name__ == '__main__':
    app.run(debug=True)
