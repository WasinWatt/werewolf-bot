from flask import Flask, request, send_file, jsonify
from flask_pymongo import PyMongo
from pymongo import MongoClient
from bson import json_util
import json
import requests
import random
import string
import Constant

global room_map
room_map = dict()
global roles
roles = ['']*5
roles.append('Werewolf Doctor Seer Hunter Villager')
roles.append('Werewolf Doctor Seer Hunter Villager Villager')
roles.append('Werewolf Doctor Seer Hunter Villager Villager Villager')
roles.append('Werewolf Doctor Seer Hunter Villager Villager Villager Villager')
roles.append('Werewolf Doctor Seer Hunter Villager Villager Villager Villager Villager')
roles.append('Werewolf Doctor Seer Hunter Villager Villager Villager Villager Villager Villager')

global desc
desc = dict()
desc['Werewolf'] = 'Werewolf [Bad guy] \uDBC0\uDC5E\n    มี Active Ability ในช่วงกลางคืน สามารถเลือกฆ่าใครก็ได้ 1 คน|\uDBC0\uDC77 Tip!\n    พยายามหลบหนีการสงสัย การถูกจับจากคนอื่นๆ (โกหก) ให้อยู่รอดจนเหลือ 2 คนสุดท้ายในวง (รวมหมาป่า) และคนที่เหลือไม่ใช่ Hunter จึงจะถือว่าชนะ!'
desc['Doctor'] = 'Docter [Good guy] \uDBC0\uDC90\n    มี Active Ability ในช่วงกลางคืน สามารถเลือกช่วยชีวิตใครก็ได้ 1 คน รวมทั้งตัวเองด้วย|\uDBC0\uDC77 Tip!\n    พยายามเลือกช่วยคนที่มีแนวโน้มจะโดนหมาป่าฆ่า เช่น "พูดมาก" เป็นต้น'
desc['Seer'] = 'Seer [Good guy] \uDBC0\uDC90\n    มี Active Ability ในช่วงกลางคืน สามารถชี้ถามใครก็ได้ 1 คน ว่าเป็นหมาป่าหรือไม่?|\uDBC0\uDC77 Tip!\n    พยายามเลือกชี้หมาป่าให้ได้เร็วที่สุด และ พยายามไม่พูดมากจนหมาป่ารู้ว่าเป็น Seer เพราะจะโดนฆ่า'
desc['Hunter'] = 'Hunter [Good guy] \uDBC0\uDC90\n   มี Passive Ability คือถ้าสามารถอยู่รอดจนเหลือ 2 คนสุดท้ายในวง (รวมหมาป่า) ได้ จะสามารถสู้กับหมาป่าได้และทำให้ทีม [Villager] เป็นผู้ชนะ!|\uDBC0\uDC77 Tip!\n    พยายามทำตัวนิ่งๆ ให้รอจบเกมก็พอ อย่าให้โดนฆ่าระหว่างก่อนจบเกม หรือ พยายามบอกให้ หมอ ช่วย'
desc['Villager'] = 'Villager [Good guy] \uDBC0\uDC90\n   ทำอะไรไม่ได้นอกจากบัฟคนอื่นและช่วยหาหมาป่า \uDBC0\uDC95|\uDBC0\uDC77 Tip!\n    พยายามช่วยทีมละกันนะ สู้ๆ 5555'

global LINE_API_KEY
LINE_API_KEY = 'Bearer ' + Constant.Token

client = MongoClient(Constant.MONGO_URI)
client.drop_database('werewolf-bot')

app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'werewolf-bot'
app.config['MONGO_URI'] = Constant.MONGO_URI

mongo = PyMongo(app)
@app.route('/')
def index():
    room_model = mongo.db.rooms
    rooms = room_model.find()
    data = [json.dumps(r, default=json_util.default) for r in rooms]
    return jsonify(data=data)

@app.route('/img')
def img():
    filename = 'img/'+request.args.get('role')+'.jpg'
    return send_file(filename, mimetype='image/jpeg')

@app.route('/bot', methods=['POST'])
def bot():
    #locked = getLockingStatus()
    room_model = mongo.db.rooms
    player_model = mongo.db.players
    replyStack = []
    msg_in_json = request.get_json()
    msg_in_string = json.dumps(msg_in_json)
    replyToken = msg_in_json["events"][0]['replyToken']

    userID =  msg_in_json["events"][0]['source']['userId']
    name = getProfiles(userID)['displayName']
    msgType =  msg_in_json["events"][0]['message']['type']
    
    if msgType != 'text':
        reply(replyToken, ['Only text is allowed.'])
        return 'OK',200
    
    text = msg_in_json["events"][0]['message']['text'].lower().strip()
    words = text.split()
    '''
    if text in ['!lock','!locked']:
        lock()
        pushSticker(userID,"1","408")
        reply(replyToken, ['See you! chatbot is locked.'])
        return 'OK',200

    if locked:
        if text == 'qwertyasd11':
            unlock()
            pushSticker(userID,"2","144")
            reply(replyToken, ['Yay! chatbot is ready.'])
            return 'OK',200
        pushSticker(userID,"2","39")
        replyStack.append('Chatbot is locked!')
        replyStack.append('Passcode needed.')
        reply(replyToken, replyStack)
        return 'OK',200
    '''
    if words[0] in ['create', 'สร้าง', 'สร้างห้อง']:
        if room_map.get(userID) != None:
            replyStack.append('You are already in anothr room.\nPlease leave first')
            reply(replyToken, replyStack)
            return 'OK',200

        new_id = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(5))
        while room_model.find_one({'id': new_id}!=None):
            new_id = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(5))
        newroom_id = room_model.insert({'id': new_id, 'creator': userID, 'status': 'waiting'})
        room_map[userID] = new_id
        player_model.insert({'id': userID, 'room': new_id})
        replyStack.append('Your room id is : ' + new_id)
        reply(replyToken, replyStack)
        return 'OK',200

    elif words[0] in ['join','play','เล่น','เล่นด้วย']:
        # Acknowledge all player that already in room.
        if len(words) == 1:
            replyStack.append('Please specify a Room ID')
            reply(replyToken, replyStack)
            return 'OK',200
        if room_model.find_one({'id': words[1]}) == None:
            replyStack.append('This Room ID is invalid')
            reply(replyToken, replyStack)
            return 'OK',200
        if room_map.get(userID) != None:
            replyStack.append('You are already in anothr room.\nPlease leave first')
            reply(replyToken, replyStack)
            return 'OK',200
        room_map[userID] = words[1]
        number_of_player = countPlayer(room_map[userID])+1
        players_in_room = player_model.find({'room': room_map[userID]})
        for player in players_in_room:
            push(player['id'],[name +' has joined the room : ' + room_map[userID] + '! ('+str(number_of_player)+')'])

        player_model.insert({'room': room_map[userID], 'id': userID})
        replyStack.append('You have joined the room : ' + room_map[userID] + '! ('+str(number_of_player)+')')
        reply(replyToken, replyStack)
        return 'OK',200

    elif words[0] in ['quit','เลิก','ออก','เลิกเล่น','ออกจากห้อง','leave']:
        
        if room_map.get(userID) == None:
            replyStack.append('Fail. You have not joined any room')
            reply(replyToken, replyStack)
            return 'OK',200
        
        player_model.delete_one({'id': userID})
        number_of_player = countPlayer(room_map[userID])
        players_in_room = player_model.find({'room': room_map[userID]})
        for player in players_in_room:
            push(line,[name +' has left the room! ('+str(number_of_player)+')'])

        replyStack.append('You have left the room!')
        reply(replyToken, replyStack)
        return 'OK',200
        
    elif words[0] == '!reset':
        with open('db/registered.txt','r') as data_file:
            for line in data_file:
                pushSticker(userID,"2","23")
                push(line,['You have been kicked!'])
        open('db/registered.txt', 'w').close()
        return 'OK',200

    elif words[0] in ['ls','list','มีใครบ้าง','มีใครมั่ง']:
        lists = 'Users List\n'
        if room_map.get(userID) == None:
            replyStack.append('Fail. You have not joined any room')
            reply(replyToken, replyStack)
            return 'OK',200
        
        players_in_room = player_model.find({'room': room_map[userID]})
        count = players_in_room.count()
        if count == 0:
            lists = 'Room is empty.'
        else:
            for player in players_in_room:
                name = getProfiles(player['id'])['displayName']
                lists += name + '\n'
        reply(replyToken, [lists])
        return 'OK',200
    elif words[0] in ['go','เริ่ม','เริ่มเล่น','เริ่มเกม','แจกไพ่','แจกเลย','แจก']:
        if room_map.get(userID) == None:
            replyStack.append('Fail. You have not joined any room')
            reply(replyToken, replyStack)
            return 'OK',200
        room = room_model.find_one({'id': room_map[userID]})
        if room['creator'] != userID:
            replyStack.append('Fail. You do not have permission to start the game')
    
        number_of_player = countPlayer(room_map[userID])
        if number_of_player < 5:
            pushSticker(userID,"1","107")
            reply(replyToken, ['Sorry, minimum players is 5'])
            return 'OK',200
        role = roles[number_of_player].split()
        with open('db/registered.txt','r') as data_file:
            for line in data_file:
                draw = ''
                while len(draw) <= 0:
                    lucky = random.randrange(number_of_player)
                    draw = role[lucky]
                    role[lucky] = ''
                pushImage(line,draw)
                description = desc[draw].split('|')
                push(line,['\uDBC0\uDC35 '+draw+' \uDBC0\uDC35', description[0], description[1]])
        open('db/registered.txt', 'w').close()
        return '0K',200
    elif words[0] in ['เล่นยังไง','how','อะไรวะ','เล่นไง','ทำไง','help','?']:
        replyStack.append('\uDBC0\uDC77 How To Play?')
        replyStack.append('ต้องการสร้างห้องใหม่ให้พิมพ์คำว่า "create" หรือ "สร้าง"')
        replyStack.append('ต้องการเล่นเกมให้พิมพ์คำว่า "เล่น" หรือ "join" ตามด้วยรหัสห้อง')
        replyStack.append('ต้องการดูรายชื่อของผู้เล่นในห้องให้พิมพ์คำว่า "list" หรือ "มีใครบ้าง"')
        replyStack.append('ต้องการออกจากเกมให้พิมพ์คำว่า "ออก" หรือ "quit"')
        replyStack.append('เมื่อคนเล่นครบ 5+ คนแล้วให้พิมพ์คำว่า "เริ่มเกม" หรือ "go"')
    else:
        replyStack.append('\uDBC0\uDC5E พิมพ์ ? เพื่อดูวิธีการใช้งาน')
    reply(replyToken, replyStack[:5])
    return 'OK',200

def countPlayer(roomId):
    count = player_model.find({'room': roomId}).count()
    return count

def reply(replyToken, textList):
    LINE_API = 'https://api.line.me/v2/bot/message/reply'
    headers = {
        'Content-Type': 'application/json; charset=UTF-8',
        'Authorization': LINE_API_KEY
    }
    msgs = []
    for text in textList:
        msgs.append({
            "type":"text",
            "text":text
        })
    data = json.dumps({
        "replyToken":replyToken,
        "messages":msgs
    })
    requests.post(LINE_API, headers=headers, data=data)
    return

def pushSticker(userID, packId, stickerId):
    LINE_API = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json; charset=UTF-8',
        'Authorization': LINE_API_KEY
    }
    msgs = [{
        "type": "sticker",
        "packageId": packId,
        "stickerId": stickerId
    }]
    data = json.dumps({
        "to": userID,
        "messages":msgs
    })
    requests.post(LINE_API, headers=headers, data=data)
    return
    
def pushImage(userID, role):
    LINE_API = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json; charset=UTF-8',
        'Authorization': LINE_API_KEY
    }
    msgs = [{
        "type": "image",
        "originalContentUrl": "https://werewolf-bot-server.herokuapp.com/img?role="+role,
        "previewImageUrl": "https://werewolf-bot-server.herokuapp.com/img?role="+role+"_p"
    }]
    data = json.dumps({
        "to": userID,
        "messages":msgs
    })
    requests.post(LINE_API, headers=headers, data=data)
    return
    

def push(userID, textList):
    LINE_API = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json; charset=UTF-8',
        'Authorization': LINE_API_KEY
    }
    msgs = []
    for text in textList:
        msgs.append({
            "type":"text",
            "text":text
        })
    data = json.dumps({
        "to": userID,
        "messages":msgs
    })
    requests.post(LINE_API, headers=headers, data=data)
    return

def getContent(id):
    LINE_API = 'https://api.line.me/v2/bot/message/'+str(id)+'/content'
    r = requests.get(LINE_API, headers={'Authorization': LINE_API_KEY})
    r = r.content
    return r

def getProfiles(id):
    LINE_API = 'https://api.line.me/v2/bot/profile/'+str(id)
    r = requests.get(LINE_API, headers={'Authorization': LINE_API_KEY})
    r = r.content
    return json.loads(r.decode('utf8'))

if __name__ == '__main__':
    app.run()