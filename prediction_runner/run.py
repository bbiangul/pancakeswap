import random
import time
import datetime as dt
from web3 import Web3
from web3.middleware import geth_poa_middleware
from contract import PREDICTION_ABI, PREDICTION_CONTRACT
from config import *  

import threading

w3 = Web3(Web3.HTTPProvider('https://bsc-dataseed1.binance.org/'))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)


ADDRESS = w3.toChecksumAddress(ADDRESS_STR)
PRIVATE_KEY = str(PRIVATE_KEY_STR).lower()

predictionContract = w3.eth.contract(address=PREDICTION_CONTRACT, abi=PREDICTION_ABI)

def result(round):
    
    global w3
    global predictionContract
    global ADDRESS
    global GAS
    global GAS_PRICE
    global SELL_AFTER_WIN
    
    win = predictionContract.functions.claimable(round,ADDRESS_STR).call()
    print(win)
    if (win and SELL_AFTER_WIN):
        print("going to collect")
        r = [round]
        claim = predictionContract.functions.claim(r).buildTransaction({
            'from': ADDRESS,
            'nonce': w3.eth.getTransactionCount(ADDRESS),
            'value':0,
            'gas': GAS,
            'gasPrice': GAS_PRICE,
        })
        signed_tx = w3.eth.account.signTransaction(claim, private_key=PRIVATE_KEY)
        w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        print(f'{w3.eth.waitForTransactionReceipt(signed_tx.hash)}')
        #0xe9e7cea3dedca5984780bafc599bd69add087d56
        #chaging for dollar


def betBull(value, round):
    
    global w3
    global predictionContract
    global ADDRESS
    global GAS
    global GAS_PRICE

    bull_bet = predictionContract.functions.betBull(round).buildTransaction({
        'from': ADDRESS,
        'nonce': w3.eth.getTransactionCount(ADDRESS),
        'value': value,
        'gas': GAS,
        'gasPrice': GAS_PRICE,
    })
    signed_tx = w3.eth.account.signTransaction(bull_bet, private_key=PRIVATE_KEY)
    w3.eth.sendRawTransaction(signed_tx.rawTransaction)     
    print(f'{w3.eth.waitForTransactionReceipt(signed_tx.hash)}')
    time.sleep(360)
    result(round)



def betBear(value, round):
    
    global w3
    global predictionContract
    global ADDRESS
    global GAS
    global GAS_PRICE

    bear_bet = predictionContract.functions.betBear(round).buildTransaction({
        'from': ADDRESS,
        'nonce': w3.eth.getTransactionCount(ADDRESS),
        'value': value,
        'gas': GAS,
        'gasPrice': GAS_PRICE,
    })
    signed_tx = w3.eth.account.signTransaction(bear_bet, private_key=PRIVATE_KEY)
    w3.eth.sendRawTransaction(signed_tx.rawTransaction)
    print(f'{w3.eth.waitForTransactionReceipt(signed_tx.hash)}')
    time.sleep(360)
    result(round)

def makeBet(epoch,up):
    """
    Add your bet logic here

    This example bet random either up or down:
    """
    global w3
    value = w3.toWei(0.001, 'ether')
    
    if up:
        print(f'Going Bull #{epoch} | {value} BNB  ')
        betBull(value, epoch)        
    else:
        print(f'Going Bear #{epoch} | {value} BNB  ')
        betBear(value, epoch)
        


def newRound():
    try:
        current = predictionContract.functions.currentEpoch().call()
        data = predictionContract.functions.rounds(current).call()
        bet_time = dt.datetime.fromtimestamp(data[2]) - dt.timedelta(seconds=SECONDS_LEFT)
        #data[9] #bull amount
        #data[10] #bear amount
        total = data[9] + data[10]
        up_payout = total / data[9]
        down_payout = total / data[10]
        print(f'New round: #{current}')
        return [bet_time, current,up_payout,down_payout]
    except Exception as e:
        print(f'New round fail - {e}')


def run():
    round = newRound()
    n = True
    while n:
        try:
            now = dt.datetime.now()
            if now >= round[0]:
                up = True
                if (round[2] < round[3]):
                    up = False
                
                threading.Thread(target=makeBet, args=(round[1],up,)).start()
                time.sleep(180)
                round = newRound()
            else:
                round = newRound()
                time.sleep(2)    
        except Exception as e:
            print(f'(error) Restarting...% {e}')
            round = newRound()


if __name__ == '__main__':
    run()

