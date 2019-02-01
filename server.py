import asyncio
import json
import sqlite3
import shelve
import uuid
import websockets

import model

session = model.Session()

from aioconsole import ainput

ACTIVE_OBJECTS = {}
ACTIVE_USERS = {}
USER_TO_WS = {}

class WSClient(object):

	def __init__(self, uid, ws):
		self.uid = uid
		self.ws = ws
		self.logged_as = None
	
	async def sendJSON(self, dic):
		await self.ws.send(json.dumps(dic))

	async def kick_out(self):
		print("Kicking out {0} as {1}.".format(self.uid, self.logged_as))
		await self.sendJSON({'event' : 'kick'})
		await self.ws.close()

	async def log_in(self, name, firstname, password):
		if(self.logged_as != None):
			await self.sendJSON({'error' : 'You are already logged in.'})
			return
		if(name == '' or firstname == '' or password == ''):
			await self.sendJSON({'error' : 'You provided empty parameters.'})
			return
		user = model.get_user(session, firstname, name, password)
		if(user == None):
			await self.sendJSON({'error' : 'Wrong credentials.'})
			return
		else:
			if (user.id in ACTIVE_USERS):
				await ACTIVE_USERS[user.id].kick_out()
			self.logged_as = user
			print("Logged {0} as {1}.".format(self.uid, self.logged_as))
			ACTIVE_USERS[user.id] = self
			await self.sendJSON({'event' : 'login'})
			

	def is_connected(self):
		return self.logged_as != None

	def log_out(self):
		if(self.logged_as != None and ACTIVE_USERS.get(self.logged_as.id) == self):
			print("Logout {0} as {1}.".format(self.uid, self.logged_as))
			del ACTIVE_USERS[self.logged_as.id]


	def move_to_room(id, room_id):
        pass
		

	async def act_on(self, message):
		print("User ", self.uid, " acting on ", message)
		try:
			cmd = json.loads(message)
			if(cmd['cmd'] == 'ping'):
				await self.sendJSON({'event' : 'pong'})
			elif(cmd['cmd'] == 'identify'):
				await self.log_in(name=cmd['name'], firstname=cmd['first_name'], password=cmd['password'])
			elif(cmd['cmd'] == 'list' and self.logged_as != None):
				await self.ws.send(json.dumps({'rooms' : model.list_rooms(session, self.logged_as)}))
			else:
				await self.ws.send(json.dumps({'error' : 'Unknown command "{0}".'.format(cmd['cmd'])}))
		except KeyError as error:
			await self.ws.send(json.dumps({'error' : 'Error, missing parameter "{0}".'.format(error.args[0])}))
		except json.decoder.JSONDecodeError:
			await self.ws.send(json.dumps({'error' : "Error, you didn't send valid JSON."}))
			await self.ws.close()


async def register(websocket):
	uid = uuid.uuid4().hex
	print("Registering ", uid)
	ACTIVE_OBJECTS[uid] = WSClient(uid, websocket)
	return ACTIVE_OBJECTS[uid]

async def unregister(uid):
	print("Losing ", uid)
	ACTIVE_OBJECTS[uid].log_out()
	del ACTIVE_OBJECTS[uid]

async def new_connection(websocket, path):
	user_object = await register(websocket)
	try:
		async for message in websocket:
			await user_object.act_on(message)
	finally:
		await unregister(user_object.uid)

async def console_input():
	k = "send_all "
	while True:
		cmd = await ainput(">")
		if(cmd.startswith(k)):
			for _, user in ACTIVE_OBJECTS.items():
				await user.ws.send(cmd[len(k):])
		print("You entered : ", cmd)

start_server = websockets.serve(new_connection, "0.0.0.0", 8081)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_until_complete(console_input())
asyncio.get_event_loop().run_forever()
