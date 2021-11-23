import json
import os
import random
import threading
from datetime import datetime
from flask import Flask, request


global newQuorum, totalCredits, mutex
mutex = False
totalCredits = 0

app = Flask(__name__)

"""
Description: This function is used for rectification of the credits records in the server in case of any 
correction in the number of credits owned by a node. The function takes in the credit info from a node 
and replaces it's own record of that node's credits with the value provided.
Input: JSONObject
output: JSONObject

"""


@app.route('/assigncredits', methods=['POST'])
def assigncreds():
    global mutex
    request_data = request.get_json()
    didHash = request_data['didHash']
    credits = request_data['credits']
    print("updating = " + str(didHash)+" creds " + str(credits))

    for i in newQuorum:
        if(i['didHash'] == didHash):
            i['credits'] = credits

    while mutex:
        pass

    mutex = True
    f = open("quorum.json", 'w')
    f.write(json.dumps(newQuorum))
    f.close()
    mutex = False

    response = {"status": True, "message": "Success"}
    return json.dumps(response)


"""
Description: The function is used to reduce the credits record of a node after it has successfully mined a 
token. The function reduces the number of credits of the node and updates the quorum file.
Input: JSONObject
output: JSONObject

"""


@app.route('/updatemine', methods=['POST'])
def creds():
    global mutex
    request_data = request.get_json()
    didHash = request_data['didhash']
    credits = request_data['credits']
    for i in newQuorum:
        if(i['didHash'] == didHash):
            i['credits'] -= credits

    while mutex:
        pass

    mutex = True
    f = open("quorum.json", 'w')
    f.write(json.dumps(newQuorum))
    f.close()
    mutex = False

    response = {"status": True, "message": "Success"}
    return json.dumps(response)


"""
Description: The function is used to free the assigned quorum members for a transaction. In case it is a 
successful transaction the quorum members' credits are also incremented.
Input: JSONObject
output: JSONObject

"""


@app.route('/updateQuorum', methods=['POST'])
def update():
    global mutex
    request_data = request.get_json()
    status = request_data['status']
    completeQuorum = request_data['completequorum']
    if(status):
        signedQuorum = request_data['signedquorum']
        signedQuorum = set(signedQuorum)

    for i in reversed(range(len(completeQuorum)-7, len(completeQuorum))):
        for j in newQuorum:
            if j['didHash'] == i:
                j['gamma'] = 0
                if status and (j['didHash'] in signedQuorum):
                    j['credits'] += 1

    for i in reversed(range(len(completeQuorum)-14, len(completeQuorum)-7)):
        for j in newQuorum:
            if j['didHash'] == i:
                j['beta'] = 0
                if status and (j['didHash'] in signedQuorum):
                    j['credits'] += 1

    for i in reversed(range(0, len(completeQuorum)-14)):
        for j in newQuorum:
            if j['didHash'] == i:
                j['alpha'] = 0
                if status and (j['didHash'] in signedQuorum):
                    j['credits'] += 1

    while mutex:
        pass

    mutex = True
    f = open("quorum.json", 'w')
    f.write(json.dumps(newQuorum))
    f.close()
    mutex = False

    response = {"status": True, "message": "Success"}
    return json.dumps(response)


"""
Description: This function is used to assign quorum for both mining and transaction based requests. The 
function computes number of alpha nodes for a transaction using the Byzantine Fault Tolerance scheme. The
N value is incemented based on the number of credits owned by nodes in the quorum file and the amount to 
be transferred(To make alpha nodes not cheat in a transaction, by selecting alpha nodes with a reasonable 
amount of their credits). The beta and gamma are chosen randomly, all while making sure no nodes are 
duplicated in the selection. The selection also makes sure currently unassigned nodes are only selected for a 
transaction
Input: JSONObject
output: JSONarray

"""


@app.route('/getQuorum', methods=['POST'])
def getQuorum():
    global newQuorum, totalCredits
    request_data = request.get_json()
    token = request_data['tokencount']
    sender = request_data['sender']
    receiver = request_data['receiver']
    f = open("mine.json", 'r')
    content = f.read()
    f.close()
    content = content.replace("'", '"')
    tokens = json.loads(content)
    level = tokens[0]["level"]

    quorumlist = []

    if(totalCredits < token):
        while(len(quorumlist) < 7):
            temp = random.randint(0, len(newQuorum)-1)
            # TODO do a curl here to nidhin's api after doing a readfile of local dataTable and fetch the did's corresponding peerid ,then get true or false back as reply after parsing then add that true/false variable with "and" operation to the following statement to check if node is pingable
            if(not(newQuorum[temp]['didHash'] in quorumlist) and not(newQuorum[temp]['didHash'] == sender) and not(newQuorum[temp]['didHash'] == receiver) and newQuorum[temp]['alpha'] == 0):
                quorumlist.append(newQuorum[temp]['didHash'])
                newQuorum[temp]['alpha'] = 1

    else:
        n = 2
        flag = True
        while(flag):
            i = 0
            count = 0
            alphaSize = 3*n+1
            minValue = (1/(2*n+1))*(2**(2+level)*token)
            alphaListIndices = []

            index = 0
            for j in newQuorum:
                if(j['credits'] < minValue):
                    break
                index += 1

            if(index+1 < alphaSize):
                n += 1
                print("Retrying with increment of n ", n+1)
                continue

            flag = False
            while(count < alphaSize):
                print("count is ", count)
                print("alphaSize is ", alphaSize)
                i = random.randint(0, index-1)
                # TODO do a curl here to nidhin's api after doing a readfile of local dataTable and fetch the did's corresponding peerid ,then get true or false back as reply after parsing then add that true/false variable with "and" operation to the following statement to check if node is pingable
                if(newQuorum[i]['credits'] >= minValue and newQuorum[i]['alpha'] == 0 and not(newQuorum[i]['didHash'] == sender) and not(newQuorum[i]['didHash'] == receiver) and not(i in alphaListIndices)):
                    count += 1
                    alphaListIndices.append(i)

        print("Alpha picking done flag is ", flag)

        for i in alphaListIndices:
            quorumlist.append(newQuorum[i]['didHash'])
            newQuorum[i]['alpha'] = 1

    while(len(quorumlist) < count+7):
        temp = random.randint(0, len(newQuorum)-1)
        if(not(newQuorum[temp]['didHash'] in quorumlist) and not(newQuorum[temp]['didHash'] == sender) and not(newQuorum[temp]['didHash'] == receiver) and newQuorum[temp]['beta'] == 0):
            quorumlist.append(newQuorum[temp]['didHash'])
            newQuorum[temp]['beta'] = 1

    while(len(quorumlist) < count+14):
        temp = random.randint(0, len(newQuorum)-1)
        if(not(newQuorum[temp]['didHash'] in quorumlist) and not(newQuorum[temp]['didHash'] == sender) and not(newQuorum[temp]['didHash'] == receiver) and newQuorum[temp]['gamma'] == 0):
            quorumlist.append(newQuorum[temp]['didHash'])
            newQuorum[temp]['gamma'] = 1

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print("=======================================================================================")
    print("Sender = ", sender)
    print("receiver = ", receiver)
    print("token = ", token)
    print("alpha = ", count)
    print("n = ", n)
    print("3n+1 = ", alphaSize)
    print("2n+1 = ", 2*n+1)
    print("Allocation Time =", current_time)
    # print(*quorumlist)
    for i in quorumlist:
        for j in newQuorum:
            if(i == j['didHash']):
                print(i+" "+str(j['credits']))
                continue
    print("=======================================================================================")

    return json.dumps(quorumlist)


"""
Description: The function is used to synchronise the files dataTable.json and quorum.json files. In case a
new node is added the corresponding record is made in quorum.json. In case a node is removed from the file
that node's corresponding records are removed from the quorum.json file. The function also sorts the quorum
based on the number of credits they hold. The function runs every 20 secs.

"""


def IntegrityCheck():
    global mutex, totalCredits
    threading.Timer(20.0, IntegrityCheck).start()
    changes = False

    while(mutex):
        pass

    mutex = True
    f = open("quorum.json", 'r')
    quorum = json.load(f)
    f.close()

    f = open("dataTable.json", 'r')
    dataTable = json.load(f)
    f.close()

    for i in dataTable:
        flag = False
        temp = i['didHash']
        for j in quorum:
            if(j['didHash'] == temp):
                flag = True
                break
        if(flag == False):
            changes = True
            data = {}
            data['didHash'] = temp
            data['credits'] = 0
            data['alpha'] = 0
            data['beta'] = 0
            data['gamma'] = 0
            newQuorum.append(data)

    for i in quorum:
        flag = False
        temp = i['didHash']
        for j in dataTable:
            if(j['didHash'] == temp):
                flag = True
                break
        if(flag == False):
            changes = True
            print('remove'+str(i))
            newQuorum.remove(i)

    if(changes):
        f = open("quorum.json", 'w')
        f.write(json.dumps(newQuorum))
        f.close()

        j = len(newQuorum)-1
        while(j > 0):
            i = 0
            while(i < j):
                if(newQuorum[i]['credits'] < newQuorum[i+1]['credits']):
                    temp = newQuorum[i]
                    newQuorum[i] = newQuorum[i+1]
                    newQuorum[i+1] = temp
                i += 1
            j -= 1

        tempcredit = 0
        for k in newQuorum:
            tempcredit += k['credits']
        totalCredits = tempcredit

    mutex = False
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    # print(*newQuorum)
    print("20sec Time =", current_time)


"""
Description: The function is called to initialize the server and synchronise the files dataTable.json and quorum.json files. In case a
new node is added the corresponding record is made in quorum.json. In case a node is removed from the file
that node's corresponding records are removed from the quorum.json file. The function also sorts the quorum
based on the number of credits they hold. This script only runs once when the server starts up.

"""


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=105)

stat = os.path.isfile("quorum.json")

if(stat):
    f = open("quorum.json", 'r')
    quorum = json.load(f)
    newQuorum = quorum
    f.close()
else:
    f = open("quorum.json", 'w+')
    quorum = json.loads("[]")
    newQuorum = quorum
    f.write("[]")
    f.close()

f = open("dataTable.json", 'r')
dataTable = json.load(f)
f.close()

for i in dataTable:
    flag = False
    temp = i['didHash']
    for j in quorum:
        if(j['didHash'] == temp):
            flag = True
            break
    if(flag == False):
        data = {}
        data['didHash'] = temp
        data['credits'] = 0
        newQuorum.append(data)

for i in quorum:
    flag = False
    temp = i['didHash']
    for j in dataTable:
        if(j['didHash'] == temp):
            flag = True
            break
    if(flag == False):
        newQuorum.remove(i)

f = open("quorum.json", 'w')
f.write(json.dumps(newQuorum))
f.close()

j = len(newQuorum)-1
while(j > 0):
    i = 0
    while(i < j):
        if(newQuorum[i]['credits'] < newQuorum[i+1]['credits']):
            temp = newQuorum[i]
            newQuorum[i] = newQuorum[i+1]
            newQuorum[i+1] = temp
        i += 1
    j -= 1

for k in newQuorum:
    totalCredits = totalCredits + k['credits']
    k['alpha'] = 0
    k['beta'] = 0
    k['gamma'] = 0

IntegrityCheck()
